"use client"

import { Sidebar } from "@/components/sidebar"
import { StatCard } from "@/components/stat-card"
import { AgentWorkflow } from "@/components/agent-workflow"
import { KnowledgeGraph } from "@/components/knowledge-graph"
import { PDFUpload } from "@/components/pdf-upload"
import { FileText, AlertCircle, CheckCircle2, CreditCard, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useEffect, useState } from "react"
import Link from "next/link"

interface Invoice {
  invoice_number: string
  vendor_id: number
  total: number
  date: string
}

interface Transaction {
  transaction_id: string
  vendor_id: number
  amount: number
  date: string
  discount: number
}

interface KPIData {
  total_invoices: number
  total_transactions: number
  anomalies: number
  total_vendors: number
}

export default function DashboardPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [kpis, setKpis] = useState<KPIData | null>(null)
  const [loading, setLoading] = useState(true)
  const [kpiLoading, setKpiLoading] = useState(true)

  useEffect(() => {
    // Fetch invoices and transactions from unified API
    Promise.all([
      fetch('http://localhost:8000/data/invoices').then(res => res.json()),
      fetch('http://localhost:8000/data/transactions').then(res => res.json())
    ])
      .then(([invoicesData, transactionsData]) => {
        setInvoices(invoicesData.slice(0, 3))
        setTransactions(transactionsData.slice(0, 3))
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching data:', err)
        setLoading(false)
      })

    // Fetch KPIs from unified API (now using fast CSV-based calculation)
    fetch('http://localhost:8000/kpi/kpis')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch KPIs')
        return res.json()
      })
      .then(data => {
        setKpis(data)
        setKpiLoading(false)
      })
      .catch(err => {
        console.error('Error fetching KPIs:', err)
        setKpiLoading(false)
      })
  }, [])

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Monitor your autonomous invoice reconciliation system
              </p>
            </div>
            <PDFUpload onUploadComplete={() => {
              // Optionally refresh data after upload
              window.location.reload()
            }} />
          </div>

          {/* Stats Grid */}
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Invoices"
              value={kpiLoading ? "..." : (kpis?.total_invoices.toString() || "0")}
              description="From CSV data"
              icon={FileText}
              trend={kpis && kpis.total_invoices > 0 ? { value: "Active", positive: true } : undefined}
            />
            <StatCard
              title="Transactions"
              value={kpiLoading ? "..." : (kpis?.total_transactions.toString() || "0")}
              description="Payment records"
              icon={CreditCard}
              variant="highlight"
            />
            <StatCard
              title="Unique Vendors"
              value={kpiLoading ? "..." : (kpis?.total_vendors.toString() || "0")}
              description="Active vendors"
              icon={Users}
            />
            <StatCard
              title="Anomalies"
              value={kpiLoading ? "..." : (kpis?.anomalies.toString() || "0")}
              description="Flagged for review"
              icon={AlertCircle}
              trend={kpis && kpis.anomalies === 0 ? { value: "None found", positive: true } : undefined}
            />
          </div>

          {!kpiLoading && !kpis && (
            <div className="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 p-4">
              <p className="text-sm text-destructive">
                ⚠ API not responding. Make sure it's running on port 8000
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Run: <code className="bg-muted px-2 py-1 rounded">python app.py</code>
              </p>
            </div>
          )}

          {/* Recent Data Grid */}
          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            {/* Recent Invoices */}
            <div className="rounded-lg border border-border bg-card">
              <div className="border-b border-border p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-foreground">Recent Invoices</h2>
                    <p className="mt-1 text-sm text-muted-foreground">Latest from data API</p>
                  </div>
                  <Link href="/invoices">
                    <Button variant="outline" size="sm">
                      View All
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="p-6">
                {loading ? (
                  <div className="text-center text-muted-foreground py-8">Loading...</div>
                ) : invoices.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">No invoices available</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Start the API: <code className="bg-muted px-2 py-1 rounded">python app.py</code>
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {invoices.map((invoice) => (
                      <div
                        key={invoice.invoice_number}
                        className="flex items-center justify-between rounded-lg border border-border p-4 transition-colors hover:bg-muted/50"
                      >
                        <div className="flex items-center gap-4">
                          <div className="rounded-lg bg-muted p-3">
                            <FileText className="h-5 w-5 text-foreground" />
                          </div>
                          <div>
                            <p className="font-medium text-foreground font-mono text-sm">{invoice.invoice_number}</p>
                            <p className="text-sm text-muted-foreground">Vendor {invoice.vendor_id}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-foreground">
                            ${invoice.total.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </p>
                          <p className="text-sm text-muted-foreground">{invoice.date}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Recent Transactions */}
            <div className="rounded-lg border border-border bg-card">
              <div className="border-b border-border p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-foreground">Recent Transactions</h2>
                    <p className="mt-1 text-sm text-muted-foreground">Latest from data API</p>
                  </div>
                  <Link href="/transactions">
                    <Button variant="outline" size="sm">
                      View All
                    </Button>
                  </Link>
                </div>
              </div>
              <div className="p-6">
                {loading ? (
                  <div className="text-center text-muted-foreground py-8">Loading...</div>
                ) : transactions.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">No transactions available</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Start the API: <code className="bg-muted px-2 py-1 rounded">python app.py</code>
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {transactions.map((transaction) => (
                      <div
                        key={transaction.transaction_id}
                        className="flex items-center justify-between rounded-lg border border-border p-4 transition-colors hover:bg-muted/50"
                      >
                        <div className="flex items-center gap-4">
                          <div className="rounded-lg bg-muted p-3">
                            <CreditCard className="h-5 w-5 text-foreground" />
                          </div>
                          <div>
                            <p className="font-medium text-foreground font-mono text-sm">{transaction.transaction_id}</p>
                            <p className="text-sm text-muted-foreground">Vendor {transaction.vendor_id}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-foreground">
                            ${transaction.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </p>
                          <div className="flex items-center gap-2 justify-end">
                            <p className="text-sm text-muted-foreground">{transaction.date}</p>
                            {transaction.discount > 0 && (
                              <Badge variant="secondary" className="bg-green-500/10 text-green-500 text-xs">
                                -${transaction.discount}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Knowledge Graph Visualization */}
          <div className="mt-8">
            <KnowledgeGraph />
          </div>

          {/* Agent Workflow */}
          <div className="mt-8">
            <AgentWorkflow />
          </div>
        </div>
      </main>
    </div>
  )
}
