# Finance Frontend

Modern Next.js frontend for the Finance Invoice Reconciliation System.

## Features

- 📊 **Dashboard** - Overview of invoices and transactions from data API
- 🧾 **Invoices Page** - Display first 5 invoices from CSV via API
- 💳 **Transactions Page** - Display first 5 transactions from CSV via API
- 🤖 **Finance Q&A** - AI-powered question answering
- ✅ **Reconciliation** - Invoice reconciliation workflow
- ⚙️ **Settings** - System configuration

## Setup

### 1. Install Dependencies

```bash
npm install
# or
pnpm install
```

### 2. Start the Data API (Required)

The frontend fetches invoice and transaction data from the data API running on port 8001.

In a separate terminal:

```bash
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate
python services/data.py
```

The data API should be running at `http://localhost:8001`

### 3. Start the Frontend

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Integration

The frontend connects to the following API endpoints:

### Data API (Port 8001)
- `GET /invoices` - Returns all invoices from CSV
- `GET /transactions` - Returns all transactions from CSV

The Dashboard, Invoices, and Transactions pages automatically fetch and display the first 5 records from these endpoints.

## Pages

### Dashboard (`/`)
- Displays overview statistics
- Shows first 3 invoices and transactions
- Links to detailed pages

### Invoices (`/invoices`)
- Displays first 5 invoices from the data API
- Shows: Invoice Number, Vendor ID, Amount, Date, Due Date

### Transactions (`/transactions`)
- Displays first 5 transactions from the data API
- Shows: Transaction ID, Vendor ID, Amount, Discount, Date, Status

## Troubleshooting

### "Failed to fetch" errors

Make sure the data API is running:

```bash
# Check if the API is running
curl http://localhost:8001/invoices

# If not running, start it:
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate
python services/data.py
```

### CORS Issues

The data API has CORS enabled for all origins. If you still face issues, check the browser console for specific errors.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **Icons**: Lucide React
- **TypeScript**: Full type safety

## Data Flow

```
CSV Files → Data API (Python FastAPI) → Frontend (Next.js)
    ↓
new_invoices.csv  →  http://localhost:8001/invoices  →  /invoices page
new_transactions.csv  →  http://localhost:8001/transactions  →  /transactions page
```

