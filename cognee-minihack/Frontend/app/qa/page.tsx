"use client"

import { Sidebar } from "@/components/sidebar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Sparkles, AlertCircle } from "lucide-react"
import { useState } from "react"

const sampleQuestions = [
  "Vendor 2 says they received a wrong payment, can you check whether all payments to Vendor 2 are correct?",
  "We ordered a new laptop from Vendor 3 but it was not delivered, can you check whether we ever paid for a laptop from Vendor 3?",
  "We are auditing our hardware budget. Have we paid for any storage devices or hard drives recently?",
  "Which vendors consistently give us discounts on our orders?",
]

export default function QAPage() {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput("")
    setMessages(prev => [...prev, { role: "user", content: userMessage }])
    setLoading(true)
    setError(null)

    try {
      // Call the real API
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage,
          session_id: sessionId
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || `API returned ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      // Add the assistant's response
      // The API returns { answer: string, session_id?: string }
      const answer = data.answer || data.response || data.message || "I received your question but couldn't generate a response."
      
      if (!answer || answer.trim() === "") {
        throw new Error("Empty response from API")
      }
      
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: answer
        }
      ])
    } catch (err) {
      console.error('Error calling chat API:', err)
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I'm having trouble connecting to the knowledge graph. Please ensure:\n\n1. The API is running: `python app.py` in cognee-minihack/\n2. Ollama is running with the required models\n3. The knowledge graph has been set up\n\nError: " + (err instanceof Error ? err.message : 'Connection failed')
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-hidden flex flex-col">
        <div className="border-b border-border p-8">
          <h1 className="text-3xl font-bold text-foreground">Finance Q&A</h1>
          <p className="mt-1 text-sm text-muted-foreground">Ask questions about your invoices and financial data using the knowledge graph</p>
        </div>

        <div className="flex-1 overflow-y-auto p-8">
          {/* Sample Questions */}
          {messages.length === 0 && (
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-8">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-primary/20 mb-4">
                  <Sparkles className="h-8 w-8 text-primary" />
                </div>
                <h2 className="text-2xl font-bold text-foreground">What would you like to know?</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Ask me anything about your invoices, payments, and vendors
                </p>
              </div>

              <div className="grid gap-3">
                <p className="text-sm font-medium text-muted-foreground mb-2">Try asking:</p>
                {sampleQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInput(question)}
                    className="rounded-lg border border-border bg-card p-4 text-left text-sm hover:bg-muted/50 transition-colors"
                  >
                    <span className="text-foreground">{question}</span>
                  </button>
                ))}
              </div>

              <div className="mt-8 p-4 rounded-lg bg-muted/50 border border-border">
                <p className="text-xs text-muted-foreground text-center">
                  💡 Connected to knowledge graph API at http://localhost:8000/api/v1/chat
                </p>
              </div>
            </div>
          )}

          {/* Conversation */}
          {messages.length > 0 && (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((message, index) => (
                <div key={index} className={`flex gap-4 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  {message.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                      <Sparkles className="h-4 w-4 text-primary-foreground" />
                    </div>
                  )}
                  <div
                    className={`rounded-lg px-4 py-3 max-w-[80%] ${
                      message.role === "user" 
                        ? "bg-primary text-primary-foreground" 
                        : "bg-card border border-border text-foreground"
                    }`}
                  >
                    <p
                      className={`text-sm whitespace-pre-wrap break-words leading-relaxed ${
                        message.role === "user" ? "text-primary-foreground" : "text-foreground"
                      }`}
                    >
                      {message.content}
                    </p>
                  </div>
                  {message.role === "user" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                      <span className="text-xs font-medium text-foreground">You</span>
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-4 justify-start">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                    <Sparkles className="h-4 w-4 text-primary-foreground animate-pulse" />
                  </div>
                  <div className="rounded-lg px-4 py-3 bg-card border border-border">
                    <p className="text-sm text-muted-foreground">Querying knowledge graph...</p>
                  </div>
                </div>
              )}
              {error && (
                <div className="flex gap-4 justify-start">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-destructive">
                    <AlertCircle className="h-4 w-4 text-destructive-foreground" />
                  </div>
                  <div className="rounded-lg px-4 py-3 bg-destructive/10 border border-destructive">
                    <p className="text-sm text-destructive">{error}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-border p-8">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-4">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your financial data..."
              className="flex-1"
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </main>
    </div>
  )
}
