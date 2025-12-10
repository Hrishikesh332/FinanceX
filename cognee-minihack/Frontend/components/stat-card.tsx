import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatCardProps {
  title: string
  value: string | number
  description?: string
  icon: LucideIcon
  trend?: {
    value: string
    positive: boolean
  }
  variant?: "default" | "highlight"
}

export function StatCard({ title, value, description, icon: Icon, trend, variant = "default" }: StatCardProps) {
  return (
    <div className={cn("rounded-lg border border-border p-6", variant === "highlight" ? "bg-primary/10" : "bg-card")}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <h3 className={cn("mt-2 text-3xl font-bold", variant === "highlight" ? "text-primary" : "text-foreground")}>
            {value}
          </h3>
          {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
          {trend && (
            <div
              className={cn(
                "mt-2 flex items-center gap-1 text-xs font-medium",
                trend.positive ? "text-primary" : "text-destructive",
              )}
            >
              <span>{trend.value}</span>
              <span className="text-muted-foreground">vs last month</span>
            </div>
          )}
        </div>
        <div className={cn("rounded-lg p-3", variant === "highlight" ? "bg-primary/20" : "bg-muted")}>
          <Icon className={cn("h-6 w-6", variant === "highlight" ? "text-primary" : "text-muted-foreground")} />
        </div>
      </div>
    </div>
  )
}
