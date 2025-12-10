import { Sidebar } from "@/components/sidebar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle2, XCircle, AlertCircle, Eye, Construction } from "lucide-react"

export default function ReconciliationPage() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-foreground">Reconciliation</h1>
            <p className="mt-1 text-sm text-muted-foreground">Review matched invoices and resolve discrepancies</p>
          </div>

          {/* Summary Cards */}
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-border bg-card p-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Perfect Match</p>
                <CheckCircle2 className="h-5 w-5 text-primary" />
              </div>
              <p className="mt-2 text-3xl font-bold text-primary">-</p>
              <p className="mt-1 text-xs text-muted-foreground">100% confidence</p>
            </div>

            <div className="rounded-lg border border-border bg-card p-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Mismatches</p>
                <AlertCircle className="h-5 w-5 text-yellow-500" />
              </div>
              <p className="mt-2 text-3xl font-bold text-foreground">-</p>
              <p className="mt-1 text-xs text-muted-foreground">Requires review</p>
            </div>

            <div className="rounded-lg border border-border bg-card p-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Duplicates</p>
                <XCircle className="h-5 w-5 text-destructive" />
              </div>
              <p className="mt-2 text-3xl font-bold text-foreground">-</p>
              <p className="mt-1 text-xs text-muted-foreground">Needs action</p>
            </div>

            <div className="rounded-lg border border-border bg-card p-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Total Processed</p>
                <Eye className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="mt-2 text-3xl font-bold text-foreground">-</p>
              <p className="mt-1 text-xs text-muted-foreground">This period</p>
            </div>
          </div>

          {/* Coming Soon Section */}
          <div className="mt-8">
            <div className="rounded-lg border-2 border-dashed border-border bg-muted/30 p-12 text-center">
              <Construction className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-xl font-semibold text-foreground">Reconciliation Engine Coming Soon</h3>
              <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
                The automated reconciliation engine is currently being configured. 
                This feature will automatically match invoices with transactions and flag discrepancies.
              </p>
              <div className="mt-6 space-y-2">
                <p className="text-xs text-muted-foreground">Features in development:</p>
                <ul className="text-xs text-muted-foreground space-y-1">
                  <li>✓ Automatic invoice-transaction matching</li>
                  <li>✓ Duplicate detection</li>
                  <li>✓ Amount discrepancy alerts</li>
                  <li>✓ PO validation</li>
                  <li>✓ Vendor verification</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
