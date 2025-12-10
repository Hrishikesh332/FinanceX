import { Sidebar } from "@/components/sidebar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"

export default function SettingsPage() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Settings</h1>
            <p className="mt-1 text-sm text-muted-foreground">Configure your invoice reconciliation system</p>
          </div>

          <div className="mt-8 space-y-6 max-w-2xl">
            {/* Agent Configuration */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold text-foreground">Agent Configuration</h3>
              <p className="mt-1 text-sm text-muted-foreground">Configure how the AI agents process your invoices</p>

              <div className="mt-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="auto-approve" className="text-foreground">
                      Auto-approve matches
                    </Label>
                    <p className="text-xs text-muted-foreground">Automatically approve 100% confidence matches</p>
                  </div>
                  <Switch id="auto-approve" defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="duplicate-detection" className="text-foreground">
                      Duplicate detection
                    </Label>
                    <p className="text-xs text-muted-foreground">Flag potential duplicate invoices</p>
                  </div>
                  <Switch id="duplicate-detection" defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="anomaly-detection" className="text-foreground">
                      Anomaly detection
                    </Label>
                    <p className="text-xs text-muted-foreground">Detect unusual patterns in invoice data</p>
                  </div>
                  <Switch id="anomaly-detection" defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="email-notifications" className="text-foreground">
                      Email notifications
                    </Label>
                    <p className="text-xs text-muted-foreground">Notify accountant of flagged issues</p>
                  </div>
                  <Switch id="email-notifications" defaultChecked />
                </div>
              </div>
            </div>

            {/* Matching Thresholds */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold text-foreground">Matching Thresholds</h3>
              <p className="mt-1 text-sm text-muted-foreground">Set confidence thresholds for automatic processing</p>

              <div className="mt-6 space-y-4">
                <div>
                  <Label htmlFor="auto-approve-threshold" className="text-foreground">
                    Auto-approve threshold
                  </Label>
                  <div className="mt-2 flex items-center gap-4">
                    <Input
                      id="auto-approve-threshold"
                      type="number"
                      defaultValue="95"
                      min="0"
                      max="100"
                      className="w-24"
                    />
                    <span className="text-sm text-muted-foreground">% confidence</span>
                  </div>
                </div>

                <div>
                  <Label htmlFor="review-threshold" className="text-foreground">
                    Manual review threshold
                  </Label>
                  <div className="mt-2 flex items-center gap-4">
                    <Input id="review-threshold" type="number" defaultValue="70" min="0" max="100" className="w-24" />
                    <span className="text-sm text-muted-foreground">% confidence</span>
                  </div>
                </div>

                <div>
                  <Label htmlFor="amount-variance" className="text-foreground">
                    Amount variance tolerance
                  </Label>
                  <div className="mt-2 flex items-center gap-4">
                    <Input id="amount-variance" type="number" defaultValue="50" min="0" className="w-24" />
                    <span className="text-sm text-muted-foreground">USD</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Integration Settings */}
            

            {/* Save Button */}
            <div className="flex justify-end">
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90">Save Changes</Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
