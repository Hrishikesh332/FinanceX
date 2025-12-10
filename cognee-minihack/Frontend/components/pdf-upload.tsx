"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Upload, FileText, Image as ImageIcon, Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"

interface PDFUploadProps {
  onUploadComplete?: () => void
}

type FileType = "pdf" | "image"

export function PDFUpload({ onUploadComplete }: PDFUploadProps) {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [fileType, setFileType] = useState<FileType>("pdf")
  const [dataType, setDataType] = useState<"invoice" | "transaction">("invoice")
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState<string>("")
  const { toast } = useToast()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      // Determine file type
      const fileName = selectedFile.name.toLowerCase()
      const isPDF = selectedFile.type === "application/pdf" || fileName.endsWith('.pdf')
      const isImage = selectedFile.type.startsWith('image/') || 
                     ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'].some(ext => fileName.endsWith(ext))
      
      if (!isPDF && !isImage) {
        toast({
          title: "Invalid file type",
          description: "Please select a PDF file or an image (jpg, png, etc.)",
          variant: "destructive",
        })
        return
      }
      
      // Auto-detect file type
      if (isPDF) {
        setFileType("pdf")
      } else if (isImage) {
        setFileType("image")
      }
      
      setFile(selectedFile)
      setUploadStatus("idle")
      setErrorMessage("")
    }
  }

  const handleUpload = async () => {
    if (!file) {
      toast({
        title: "No file selected",
        description: `Please select a ${fileType === "pdf" ? "PDF" : "image"} file to upload`,
        variant: "destructive",
      })
      return
    }

    setUploading(true)
    setUploadStatus("idle")
    setErrorMessage("")

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("data_type", dataType)

      // Use appropriate endpoint based on file type
      // Note: /api is already included because the app is mounted at /api
      const endpoint = fileType === "pdf" 
        ? "http://localhost:8000/api/v1/ingest/pdf"
        : "http://localhost:8000/api/v1/ingest/image"

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
        throw new Error(errorData.detail || `Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      
      setUploadStatus("success")
      toast({
        title: "Upload successful",
        description: result.message || `Successfully ingested ${result.items_processed} items`,
      })

      // Reset form
      setFile(null)
      if (onUploadComplete) {
        onUploadComplete()
      }

      // Close dialog after a short delay
      setTimeout(() => {
        setOpen(false)
        setUploadStatus("idle")
      }, 2000)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Failed to upload PDF"
      setUploadStatus("error")
      setErrorMessage(errorMsg)
      toast({
        title: "Upload failed",
        description: errorMsg,
        variant: "destructive",
      })
    } finally {
      setUploading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
          <Upload className="mr-2 h-4 w-4" />
          Upload Invoice
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>
            Upload a PDF file or image to extract text using Mistral OCR and add it to the knowledge graph.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {/* File Input */}
          <div className="space-y-2">
            <Label htmlFor="file-upload">File (PDF or Image)</Label>
            <div className="flex items-center gap-2">
              <Input
                id="file-upload"
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp"
                onChange={handleFileChange}
                disabled={uploading}
                className="flex-1"
              />
              {file && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  {fileType === "pdf" ? (
                    <FileText className="h-4 w-4" />
                  ) : (
                    <ImageIcon className="h-4 w-4" />
                  )}
                  <span className="truncate max-w-[150px]">{file.name}</span>
                </div>
              )}
            </div>
            {file && (
              <p className="text-xs text-muted-foreground">
                File type: {fileType === "pdf" ? "PDF" : "Image"}
              </p>
            )}
          </div>

          {/* Data Type Selection */}
          <div className="space-y-2">
            <Label htmlFor="data-type">Data Type</Label>
            <Select
              value={dataType}
              onValueChange={(value) => setDataType(value as "invoice" | "transaction")}
              disabled={uploading}
            >
              <SelectTrigger id="data-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="invoice">Invoice</SelectItem>
                <SelectItem value="transaction">Transaction</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Status Messages */}
          {uploadStatus === "success" && (
            <div className="flex items-center gap-2 rounded-lg bg-green-500/10 p-3 text-sm text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              <span>PDF uploaded and processed successfully!</span>
            </div>
          )}

          {uploadStatus === "error" && errorMessage && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Upload Button */}
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload & Process
                </>
              )}
            </Button>
          </div>

          {/* Info Note */}
          <div className="rounded-lg bg-muted p-3 text-xs text-muted-foreground">
            <p className="font-medium mb-1">Note:</p>
            <p>
              The {fileType === "pdf" ? "PDF" : "image"} will be processed using Mistral OCR to extract text, 
              then added to the knowledge graph. This may take a few moments depending on the file size.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

