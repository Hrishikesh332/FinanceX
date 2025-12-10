"use client"

import { Sidebar } from "@/components/sidebar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Filter, Download } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useEffect, useState } from "react"

interface Transaction {
  transaction_id: string
  date: string
  vendor_id: number
  amount: number
  items: string
  discount: number
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Fetch transactions from the unified API
    fetch('http://localhost:8000/data/transactions')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch transactions')
        return res.json()
      })
      .then(data => {
        // Get only first 5 transactions
        setTransactions(data.slice(0, 5))
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching transactions:', err)
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
              <h1 className="text-3xl font-bold text-foreground">Transactions</h1>
              <p className="mt-1 text-sm text-muted-foreground">View and manage all payment transactions (First 5 Records)</p>
            </div>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Download className="mr-2 h-4 w-4" />
              Export Data
            </Button>
          </div>

          {/* Filters */}
          <div className="mt-8 flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Search transactions..." className="pl-9" />
            </div>
            <Button variant="outline">
              <Filter className="mr-2 h-4 w-4" />
              Filters
            </Button>
          </div>

          {/* Transaction List */}
          <div className="mt-6 rounded-lg border border-border bg-card">
            <div className="overflow-x-auto">
              {loading ? (
                <div className="p-8 text-center text-muted-foreground">Loading transactions...</div>
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
                        Transaction ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Vendor ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Discount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {transactions.map((transaction) => (
                      <tr key={transaction.transaction_id} className="hover:bg-muted/50 transition-colors cursor-pointer">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-mono text-foreground">{transaction.transaction_id}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant="outline">Vendor {transaction.vendor_id}</Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-semibold text-foreground">
                            ${transaction.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {transaction.discount > 0 ? (
                            <Badge variant="secondary" className="bg-green-500/10 text-green-500">
                              -${transaction.discount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                            </Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">No discount</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm text-muted-foreground">{transaction.date}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant="default">Completed</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {!loading && !error && transactions.length > 0 && (
            <p className="mt-4 text-sm text-muted-foreground text-center">
              Showing first 5 of {transactions.length} transactions from the data API
            </p>
          )}
        </div>
      </main>
    </div>
  )
}

