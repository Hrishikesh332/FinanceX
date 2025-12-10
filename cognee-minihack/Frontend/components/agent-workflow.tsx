import { CheckCircle2, Circle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface WorkflowStep {
  name: string
  status: "completed" | "active" | "pending"
  description: string
}

const steps: WorkflowStep[] = [
  {
    name: "Perception",
    status: "completed",
    description: "Extracts text and structure from documents",
  },
  {
    name: "Understanding",
    status: "completed",
    description: "Builds invoice graph and normalizes data",
  },
  {
    name: "Matching",
    status: "active",
    description: "Matches invoices with PO and payment records",
  },
  {
    name: "Reconciliation",
    status: "pending",
    description: "Auto-approves or flags mismatches",
  },
  {
    name: "Q&A",
    status: "pending",
    description: "Answers natural language queries",
  },
]

export function AgentWorkflow() {
  return (
    null
  )
}
