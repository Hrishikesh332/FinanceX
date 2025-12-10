"use client"

import { Sidebar } from "@/components/sidebar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Upload, Search, Filter, FileText, ImageIcon, Mail, FileSpreadsheet } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useEffect, useState } from "react"

interface Invoice {
  invoice_number: string
  date: string
  due_date: string
  vendor_id: number
  total: number
  items: string
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Fetch invoices from the unified API
    fetch('http://localhost:8000/data/invoices')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch invoices')
        return res.json()
      })
      .then(data => {
        // Get only first 5 invoices
        setInvoices(data.slice(0, 5))
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching invoices:', err)
        setError(err.message)
        setLoading(false)
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
              <h1 className="text-3xl font-bold text-foreground">Invoices</h1>
              <p className="mt-1 text-sm text-muted-foreground">Manage and track all invoice submissions (First 5 Records)</p>
            </div>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Upload className="mr-2 h-4 w-4" />
              Upload Invoice
            </Button>
          </div>

          {/* Upload Area */}
          <div className="mt-8 rounded-lg border-2 border-dashed border-border bg-muted/30 p-12 text-center">
            <div className="flex justify-center gap-4 mb-6">
              <div className="rounded-lg bg-card border border-border p-4">
                <FileText className="h-8 w-8 text-primary mx-auto" />
                <p className="mt-2 text-xs text-muted-foreground">PDF</p>
              </div>
              <div className="rounded-lg bg-card border border-border p-4">
                <Mail className="h-8 w-8 text-primary mx-auto" />
                <p className="mt-2 text-xs text-muted-foreground">Email</p>
              </div>
              <div className="rounded-lg bg-card border border-border p-4">
                <FileSpreadsheet className="h-8 w-8 text-primary mx-auto" />
                <p className="mt-2 text-xs text-muted-foreground">CSV</p>
              </div>
              <div className="rounded-lg bg-card border border-border p-4">
                <ImageIcon className="h-8 w-8 text-primary mx-auto" />
                <p className="mt-2 text-xs text-muted-foreground">Photo</p>
              </div>
            </div>
            <h3 className="text-lg font-semibold text-foreground">Drop invoice files here</h3>
            <p className="mt-2 text-sm text-muted-foreground">Supports PDFs, emails, CSVs, and scanned images</p>
            <Button className="mt-4 bg-transparent" variant="outline">
              Choose Files
            </Button>
          </div>

          {/* Filters */}
          <div className="mt-8 flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Search invoices..." className="pl-9" />
            </div>
            <Button variant="outline">
              <Filter className="mr-2 h-4 w-4" />
              Filters
            </Button>
          </div>

          {/* Invoice List */}
          <div className="mt-6 rounded-lg border border-border bg-card">
            <div className="overflow-x-auto">
              {loading ? (
                <div className="p-8 text-center text-muted-foreground">Loading invoices...</div>
              ) : error ? (
                <div className="p-8 text-center">
                  <p className="text-destructive">Error: {error}</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Make sure the API is running on port 8000
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Run: <code className="bg-muted px-2 py-1 rounded">python app.py</code>
                  </p>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="border-b border-border">
                    <tr className="bg-muted/50">
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Invoice Number
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Vendor ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Due Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {invoices.map((invoice) => (
                      <tr key={invoice.invoice_number} className="hover:bg-muted/50 transition-colors cursor-pointer">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-mono text-foreground">{invoice.invoice_number}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant="outline">Vendor {invoice.vendor_id}</Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-semibold text-foreground">
                            ${invoice.total.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-muted-foreground">{invoice.date}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-muted-foreground">{invoice.due_date}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {!loading && !error && invoices.length > 0 && (
            <p className="mt-4 text-sm text-muted-foreground text-center">
              Showing first 5 of {invoices.length} invoices from the data API
            </p>
          )}
        </div>
      </main>
    </div>
  )
}
