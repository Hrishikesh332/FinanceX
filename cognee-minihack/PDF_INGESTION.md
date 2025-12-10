# PDF and Image Ingestion with Mistral OCR

This document explains how to use the PDF and image ingestion features that extract text using Mistral OCR and process it through the knowledge graph.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements_api.txt
```

This will install:
- `mistralai>=1.0.0` - Mistral AI SDK for OCR
- `httpx>=0.24.0` - For async HTTP requests (used for downloading OCR results)

### 2. Set Mistral API Key

Set the `MISTRAL_API_KEY` environment variable:

```bash
export MISTRAL_API_KEY="your-mistral-api-key-here"
```

Or add it to your `.env` file:

```
MISTRAL_API_KEY=your-mistral-api-key-here
```

## API Endpoints

### POST `/api/v1/ingest/pdf`

Upload a PDF file to extract text using Mistral OCR and add it to the knowledge graph.

### POST `/api/v1/ingest/image`

Upload an image file (jpg, png, gif, bmp, webp) to extract text using Mistral OCR and add it to the knowledge graph.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Parameters:
  - `file` (required): PDF file to upload
  - `data_type` (optional): Type of data - "invoice" or "transaction" (default: "invoice")
  - `custom_prompt` (optional): Custom prompt for processing (overrides data_type prompt)

**Response:**
```json
{
  "message": "Successfully ingested PDF 'document.pdf' (5 text chunks) as invoice",
  "items_processed": 5,
  "data_type": "invoice"
}
```

**Example using curl (PDF):**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/pdf" \
  -F "file=@invoice.pdf" \
  -F "data_type=invoice"
```

**Example using curl (Image):**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/image" \
  -F "file=@invoice.jpg" \
  -F "data_type=invoice"
```

**Example using Python (PDF):**
```python
import requests

with open("invoice.pdf", "rb") as f:
    files = {"file": ("invoice.pdf", f, "application/pdf")}
    data = {"data_type": "invoice"}
    response = requests.post(
        "http://localhost:8000/api/v1/ingest/pdf",
        files=files,
        data=data
    )
    print(response.json())
```

**Example using Python (Image):**
```python
import requests

with open("invoice.jpg", "rb") as f:
    files = {"file": ("invoice.jpg", f, "image/jpeg")}
    data = {"data_type": "invoice"}
    response = requests.post(
        "http://localhost:8000/api/v1/ingest/image",
        files=files,
        data=data
    )
    print(response.json())
```

## How It Works

### PDF Processing:
1. **PDF Upload**: PDF file is uploaded to the API endpoint
2. **Mistral OCR**: PDF is sent to Mistral OCR API for text extraction
3. **Wait for Processing**: API polls Mistral API until OCR processing is complete
4. **Text Extraction**: Extracted text is retrieved from Mistral
5. **Text Chunking**: Text is split into chunks (by paragraphs)
6. **Cognee Processing**: 
   - Text chunks are added to cognee using `cognee.add()`
   - Embeddings are created and graph is built using `cognee.cognify()`
7. **Response**: Success message with number of chunks processed

### Image Processing:
1. **Image Upload**: Image file is uploaded to the API endpoint
2. **Base64 Encoding**: Image is encoded as base64
3. **Mistral OCR**: Image is sent to Mistral OCR API using `client.ocr.process()` with base64 data
4. **Text Extraction**: Extracted text is retrieved from OCR response
5. **Text Chunking**: Text is split into chunks (by paragraphs or lines)
6. **Cognee Processing**: 
   - Text chunks are added to cognee using `cognee.add()`
   - Embeddings are created and graph is built using `cognee.cognify()`
7. **Response**: Success message with number of chunks processed

## Frontend Integration

The frontend includes a document upload component (`components/pdf-upload.tsx`) that:

- Supports both PDF and image files (jpg, png, gif, bmp, webp)
- Auto-detects file type (PDF or image)
- Provides a dialog for file selection
- Allows selection of data type (invoice/transaction)
- Shows upload progress
- Displays success/error messages
- Automatically refreshes data after successful upload

The upload button is integrated into the main dashboard page and automatically uses the correct endpoint based on file type.

## Error Handling

The API handles various error cases:

- **Missing Mistral API Key**: Returns 500 error with clear message
- **Invalid File Type**: Returns 400 error if file is not a PDF (for PDF endpoint) or not an image (for image endpoint)
- **Empty PDF**: Returns 400 error if PDF contains no extractable text
- **OCR Processing Timeout**: Returns 500 error if OCR takes longer than 60 seconds
- **Text Retrieval Failure**: Returns 500 error with details about what went wrong

## Notes

- **Processing Time**: OCR processing can take 10-60 seconds depending on PDF size
- **File Size**: Large PDFs may take longer to process
- **Text Quality**: OCR quality depends on image/PDF quality (scanned vs. text-based, image resolution)
- **Supported Image Formats**: jpg, jpeg, png, gif, bmp, webp
- **Chunking**: Text is automatically split into chunks for better processing
- **Prompt Selection**: Uses `invoice_prompt.txt` or `transaction_prompt.txt` based on `data_type`

## Troubleshooting

### "Mistral AI library not installed"
```bash
pip install mistralai>=1.0.0
```

### "MISTRAL_API_KEY environment variable not set"
Set the environment variable:
```bash
export MISTRAL_API_KEY="your-key"
```

### "Could not retrieve extracted text from Mistral OCR"
- Check that Mistral API is responding correctly
- Verify the file was processed successfully (check file status)
- Check Mistral API documentation for any changes in response format

### "No text could be extracted from the PDF"
- PDF might be image-only without OCR-able text
- PDF might be corrupted
- Try a different PDF file

## API Response Format

### Success Response
```json
{
  "message": "Successfully ingested PDF 'invoice.pdf' (10 text chunks) as invoice",
  "items_processed": 10,
  "data_type": "invoice"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Integration with Knowledge Graph

After successful ingestion, the extracted text is:
1. Added to the knowledge graph as nodes
2. Embedded using the configured embedding model (Ollama nomic-embed-text)
3. Available for querying through the chat endpoint (`/api/v1/chat`)

You can immediately query the knowledge graph about content from the uploaded PDF.

