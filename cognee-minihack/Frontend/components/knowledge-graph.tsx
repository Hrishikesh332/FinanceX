"use client"

import { useEffect, useState, useRef } from "react"
import { Card } from "@/components/ui/card"

interface GraphNode {
  id: string
  label: string
  type: string
}

interface GraphEdge {
  source: string
  target: string
  relationship: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  stats: {
    total_nodes: number
    total_edges: number
    vendors: number
    invoices: number
    transactions: number
    products: number
  }
}

export function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    // Fetch graph data
    fetch('http://localhost:8000/graph/graph')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch graph data')
        return res.json()
      })
      .then(data => {
        setGraphData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching graph:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!graphData || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Simple force-directed layout simulation
    const nodePositions = new Map<string, { x: number; y: number }>()
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    const radius = Math.min(canvas.width, canvas.height) / 3

    // Position nodes in a circle by type
    const nodesByType = graphData.nodes.reduce((acc, node) => {
      if (!acc[node.type]) acc[node.type] = []
      acc[node.type].push(node)
      return acc
    }, {} as Record<string, GraphNode[]>)

    const types = Object.keys(nodesByType)
    types.forEach((type, typeIndex) => {
      const nodesOfType = nodesByType[type]
      const angleStep = (2 * Math.PI) / nodesOfType.length
      const typeRadius = radius * (0.5 + typeIndex * 0.3)

      nodesOfType.forEach((node, index) => {
        const angle = index * angleStep
        nodePositions.set(node.id, {
          x: centerX + typeRadius * Math.cos(angle),
          y: centerY + typeRadius * Math.sin(angle)
        })
      })
    })

    // Draw edges
    ctx.strokeStyle = '#666'
    ctx.lineWidth = 1
    graphData.edges.forEach(edge => {
      const source = nodePositions.get(edge.source)
      const target = nodePositions.get(edge.target)
      if (source && target) {
        ctx.beginPath()
        ctx.moveTo(source.x, source.y)
        ctx.lineTo(target.x, target.y)
        ctx.stroke()
      }
    })

    // Draw nodes
    graphData.nodes.forEach(node => {
      const pos = nodePositions.get(node.id)
      if (!pos) return

      // Node color by type
      const colors: Record<string, string> = {
        vendor: '#3b82f6',
        invoice: '#10b981',
        transaction: '#f59e0b',
        product: '#8b5cf6'
      }
      ctx.fillStyle = colors[node.type] || '#6b7280'

      // Draw node circle
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI)
      ctx.fill()

      // Draw label
      ctx.fillStyle = '#fff'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(node.label.substring(0, 15), pos.x, pos.y + 20)
    })
  }, [graphData])

  if (loading) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Knowledge Graph</h3>
        <div className="flex items-center justify-center h-96">
          <p className="text-muted-foreground">Loading graph...</p>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Knowledge Graph</h3>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <p className="text-destructive">Error: {error}</p>
            <p className="text-sm text-muted-foreground mt-2">
              Make sure the API is running: <code className="bg-muted px-2 py-1 rounded">python app.py</code>
            </p>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Knowledge Graph</h3>
          <p className="text-sm text-muted-foreground">
            Visualizing {graphData?.stats.total_nodes} nodes and {graphData?.stats.total_edges} edges
          </p>
        </div>
        <div className="flex gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="text-muted-foreground">Vendors ({graphData?.stats.vendors})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-muted-foreground">Invoices ({graphData?.stats.invoices})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span className="text-muted-foreground">Transactions ({graphData?.stats.transactions})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span className="text-muted-foreground">Products ({graphData?.stats.products})</span>
          </div>
        </div>
      </div>
      <canvas
        ref={canvasRef}
        className="w-full h-96 bg-muted/30 rounded-lg border border-border"
      />
    </Card>
  )
}

