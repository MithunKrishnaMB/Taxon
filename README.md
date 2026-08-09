# Project Title

Taxon - Enterprise CA Compliance Platform

## Live Demo

- [Website Link](http://localhost:5173/) (Local development server)
- [Design Document](DESIGN.md)

## The Problem

Chartered Accountants (CAs) and enterprise tax teams struggle with manual reconciliation of internal ERP ledgers against government auto-drafted statements (like GSTR-2B). Processing thousands of invoices manually leads to missed Input Tax Credit (ITC), compliance errors (such as missing Section 17(5) blockages) and inconsistent audit trails when manual overrides are applied.

## The Solution

Taxon is an AI-driven, multi-tenant enterprise compliance platform designed specifically for CA firms. It features automated Auto-IMS reconciliation using AI to evaluate compliance records, a bulk ingestion engine for ERP and government JSON files, an immutable statutory audit trail for tracking overrides and justifications and role-based access control (RBAC) for team management. The app provides a React/Vite dashboard and a FastAPI backend powered by advanced LLMs for tax analysis.

## Tech Stack

- Programming languages: Python, TypeScript, HTML/CSS
- Frontend frameworks and UI: React, React Router, Tailwind CSS, Vite, Lucide Icons, TanStack Query
- Backend frameworks and orchestration: FastAPI, SQLAlchemy, Pydantic, LangChain
- AI and model runtimes: Google Gemini API (google-genai)
- Databases: Compatible with PostgreSQL/SQLite (via SQLAlchemy/asyncpg/aiosqlite)
- APIs and third-party tools: Uvicorn, Alembic

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository_url>
cd Taxon
```

### 2. Backend setup (Python)

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Create `backend/.env` and set necessary environment variables:

```env
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite+aiosqlite:///./test.db # Or your PostgreSQL connection string
```

Apply database migrations:

```bash
alembic upgrade head
```

### 3. Frontend setup (React)

```bash
cd ../frontend
npm install
```

### 4. Run the project locally

Start backend (Terminal 1):

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start frontend (Terminal 2):

```bash
cd frontend
npm run dev
```

Open:

- Frontend: http://localhost:5173 
- Backend API docs: http://localhost:8000/docs



## Sample Input

You can ingest standard `.xlsx`, `.csv` or `.json` files in the **Ingestion** tab by selecting either "Internal ERP Ledger" or "GSTR-2B Statement".
