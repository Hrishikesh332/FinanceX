"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { MessageSquare, X, Send, Sparkles, Bot, User, Network, ExternalLink, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

interface Source {
  source: string
  relationship: string
  target: string
}

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
  sources?: Source[]
  graphUrl?: string
}

function CompactSourcesViewer({ sources, graphUrl }: { sources: Source[], graphUrl?: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showGraph, setShowGraph] = useState(false)

  if (!sources || sources.length === 0) return null

  const displayedSources = isExpanded ? sources : sources.slice(0, 2)

  return (
    <div className="mt-2 space-y-1">
      <div className="rounded-md border border-border/50 bg-background/30 p-2">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] font-medium text-muted-foreground flex items-center gap-1">
            <Network className="h-2.5 w-2.5" />
            Sources ({sources.length})
          </span>
          {graphUrl && (
            <button
              className="text-[10px] text-primary hover:underline flex items-center gap-0.5"
              onClick={() => setShowGraph(true)}
            >
              <ExternalLink className="h-2.5 w-2.5" />
              Graph
            </button>
          )}
        </div>
        
        <div className="space-y-1">
          {displayedSources.map((source, index) => (
            <div
              key={index}
              className="flex items-center gap-1 text-[10px] text-muted-foreground bg-muted/30 rounded px-1.5 py-1"
            >
              <span className="font-medium text-foreground truncate max-w-[70px]" title={source.source}>
                {source.source || "?"}
              </span>
              <span className="text-primary font-mono text-[9px]">
                {source.relationship}
              </span>
              <span>→</span>
              <span className="font-medium text-foreground truncate max-w-[70px]" title={source.target}>
                {source.target || "?"}
              </span>
            </div>
          ))}
        </div>
        
        {sources.length > 2 && (
          <button
            className="w-full mt-1 text-[10px] text-muted-foreground hover:text-foreground flex items-center justify-center gap-0.5"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-2.5 w-2.5" />
                Less
              </>
            ) : (
              <>
                <ChevronDown className="h-2.5 w-2.5" />
                +{sources.length - 2} more
              </>
            )}
          </button>
        )}
      </div>

      {/* Graph Modal */}
      {showGraph && graphUrl && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-background/80 backdrop-blur-sm">
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

export function ChatSidebar() {
  const [isOpen, setIsOpen] = useState(false)
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your finance assistant. I can help you with invoice queries, payment status, vendor information, and financial insights. How can I assist you today?",
      timestamp: new Date()
    }
  ])
  const [loading, setLoading] = useState(false)
  const [showSources, setShowSources] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const suggestedPrompts = [
    "How many invoices do we have in total?",
    "Are there any payment discrepancies?",
    "Which vendors have the most invoices?"
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (message.trim() && !loading) {
      const userMessage = message.trim()
      setMessage("")
      
      // Add user message
      const newUserMessage: Message = {
        role: "user",
        content: userMessage,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, newUserMessage])
      setLoading(true)

      try {
        // Call the API with sources
        const response = await fetch('http://localhost:8000/api/v1/chat/with-sources', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: userMessage
          })
        })

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }

        const data = await response.json()
        
        // Add assistant response with sources
        const assistantMessage: Message = {
          role: "assistant",
          content: data.answer || data.response || "I received your question but couldn't generate a response.",
          timestamp: new Date(),
          sources: data.sources || [],
          graphUrl: data.graph_url
        }
        setMessages(prev => [...prev, assistantMessage])
      } catch (error) {
        console.error('Error calling chat API:', error)
        const errorMessage: Message = {
          role: "assistant",
          content: "Sorry, I'm having trouble connecting to the knowledge graph. Please make sure the API is running with: `python services/api.py`",
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setLoading(false)
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <>
      {/* Toggle Button - Fixed position */}
      <Button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "fixed bottom-4 z-50 h-10 w-10 rounded-lg p-0 shadow-lg transition-all",
          isOpen ? "right-[384px]" : "right-4",
        )}
        variant="default"
      >
        {isOpen ? <X className="h-5 w-5" /> : <MessageSquare className="h-5 w-5" />}
      </Button>

      {/* Chat Sidebar */}
      <div
        className={cn(
          "fixed right-0 top-0 z-40 h-screen w-96 transform border-l border-border bg-card transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full",
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex h-16 items-center justify-between border-b border-border px-6">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Finance Assistant</h2>
            </div>
            <Button
              variant={showSources ? "default" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => setShowSources(!showSources)}
            >
              <Network className="h-3 w-3 mr-1" />
              {showSources ? "On" : "Off"}
            </Button>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 space-y-6 overflow-y-auto p-6">
            {messages.map((msg, index) => (
              <div key={index} className={cn("flex gap-3", msg.role === "user" && "flex-row-reverse")}>
                <div className={cn(
                  "flex h-9 w-9 shrink-0 items-center justify-center rounded-full shadow-sm",
                  msg.role === "assistant" ? "bg-primary" : "bg-primary/20"
                )}>
                  {msg.role === "assistant" ? (
                    <Bot className="h-5 w-5 text-primary-foreground" />
                  ) : (
                    <User className="h-5 w-5 text-primary" />
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <div className={cn("flex items-center gap-2", msg.role === "user" && "flex-row-reverse")}>
                    <p className="text-sm font-semibold text-foreground">
                      {msg.role === "assistant" ? "Flow AI" : "You"}
                    </p>
                    <span className="text-xs text-muted-foreground">{formatTime(msg.timestamp)}</span>
                  </div>
                  <div className={cn(
                    "rounded-2xl p-4 shadow-sm",
                    msg.role === "assistant" 
                      ? "rounded-tl-sm bg-muted/60" 
                      : "rounded-tr-sm bg-primary/10"
                  )}>
                    <p className="text-sm leading-relaxed text-foreground whitespace-pre-line">
                      {msg.content}
                    </p>
                    
                    {/* Show sources for assistant messages */}
                    {msg.role === "assistant" && showSources && msg.sources && msg.sources.length > 0 && (
                      <CompactSourcesViewer sources={msg.sources} graphUrl={msg.graphUrl} />
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary shadow-sm">
                  <Bot className="h-5 w-5 text-primary-foreground animate-pulse" />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-foreground">Flow AI</p>
                  </div>
                  <div className="rounded-2xl rounded-tl-sm bg-muted/60 p-4 shadow-sm">
                    <p className="text-sm leading-relaxed text-muted-foreground">Thinking...</p>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-border bg-card/50 p-4">
            <div className="mb-3 flex flex-wrap gap-2">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => setMessage(prompt)}
                  disabled={loading}
                  className="rounded-full border border-border bg-muted/50 px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:bg-primary/10 hover:text-foreground disabled:opacity-50"
                >
                  <Sparkles className="mr-1 inline-block h-3 w-3" />
                  {prompt}
                </button>
              ))}
            </div>

            <div className="relative">
              <Textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about your invoices, payments, or vendors..."
                className="min-h-[100px] resize-none pr-14"
                disabled={loading}
              />
              <Button
                size="icon"
                onClick={handleSend}
                disabled={!message.trim() || loading}
                className="absolute bottom-2 right-2 h-10 w-10 transition-all disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>

            <p className="mt-2 text-xs text-muted-foreground">
              <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-xs">Enter</kbd> to send •{" "}
              <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-xs">Shift + Enter</kbd> for new
              line
            </p>
          </div>
        </div>
      </div>

      {/* Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-30 bg-background/80 backdrop-blur-sm" onClick={() => setIsOpen(false)} />
      )}
    </>
  )
}
