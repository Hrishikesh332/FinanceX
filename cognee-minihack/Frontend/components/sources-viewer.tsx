"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp, Network, ExternalLink, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface Source {
  source: string
  relationship: string
  target: string
}

interface SourcesViewerProps {
  sources: Source[]
  graphUrl?: string
  className?: string
}

export function SourcesViewer({ sources, graphUrl, className }: SourcesViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showGraph, setShowGraph] = useState(false)

  if (!sources || sources.length === 0) {
    return null
  }

  const displayedSources = isExpanded ? sources : sources.slice(0, 3)

  return (
    <div className={cn("mt-3 space-y-2", className)}>
      {/* Sources List */}
      <div className="rounded-lg border border-border bg-muted/30 p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
            <Network className="h-3 w-3" />
            Knowledge Graph Sources ({sources.length})
          </span>
          {graphUrl && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs px-2"
              onClick={() => setShowGraph(true)}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              View Graph
            </Button>
          )}
        </div>
        
        <div className="space-y-1.5">
          {displayedSources.map((source, index) => (
            <div
              key={index}
              className="flex items-center gap-2 text-xs text-muted-foreground bg-background/50 rounded px-2 py-1.5"
            >
              <span className="font-medium text-foreground truncate max-w-[120px]" title={source.source}>
                {source.source || "Entity"}
              </span>
              <span className="text-primary font-mono text-[10px] bg-primary/10 px-1.5 py-0.5 rounded">
                {source.relationship}
              </span>
              <span className="text-muted-foreground">→</span>
              <span className="font-medium text-foreground truncate max-w-[120px]" title={source.target}>
                {source.target || "Entity"}
              </span>
            </div>
          ))}
        </div>
        
        {sources.length > 3 && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full mt-2 h-6 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-3 w-3 mr-1" />
                Show less
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3 mr-1" />
                Show {sources.length - 3} more sources
              </>
            )}
          </Button>
        )}
      </div>

      {/* Graph Modal */}
      {showGraph && graphUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="relative w-[90vw] h-[85vh] bg-card rounded-lg border border-border shadow-2xl overflow-hidden">
            <div className="absolute top-0 left-0 right-0 flex items-center justify-between p-4 bg-card/90 backdrop-blur border-b border-border z-10">
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <Network className="h-5 w-5 text-primary" />
                Knowledge Graph Visualization
              </h3>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setShowGraph(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <iframe
              src={`http://localhost:8000${graphUrl}`}
              className="w-full h-full pt-14"
              title="Knowledge Graph Visualization"
            />
          </div>
        </div>
      )}
    </div>
  )
}
