# Taxon – Enterprise CA Compliance Platform

## Overview

Taxon is a multi-tenant enterprise compliance platform that turns raw financial data into statutory reconciliation and audit-ready exports.
It uses distinct domain modules:

- **Ingestion** → extracts and parses internal ERP ledgers and government GSTR-2B JSON statements.
- **IMS Recon** → evaluates compliance records and reconciles invoices using AI.
- **Audit Log** → maintains an immutable chronological ledger of all manual overrides and justifications.
- **Tally Bridge & TDS Align** → manages external accounting software integrations and complex tax deduction logic.

The system is **stateful**, **multi-tenant** and streams progress via client-side **polling**.

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic, LangChain
- **Frontend:** React, Vite, TypeScript, TailwindCSS, TanStack Query, Lucide React
- **Models:**
  - Reconciliation AI → Google Gemini API (google-genai)

**Why:** High throughput, robust type-safety for complex financial data and scalable relational database models essential for compliance.

## Architecture Decisions

- **Relational Database (SQLAlchemy/PostgreSQL/SQLite)** → strict data integrity and relationships required for compliance audits.
- **Polling (TanStack Query)** → simpler implementation for background job progress (5-second intervals), avoids WebSocket overhead.
- **Multi-tenancy** → strict data isolation per CA client workspace to prevent data leakage.
- **AI Integration (Gemini)** → flexible reasoning capabilities for evaluating complex statutory rules like Section 17(5).

## Reliability Strategy

- **Circuit Breaker Pattern** (via Tally Bridge) to prevent cascading failures on external integrations.
- **Structured validation** across all data ingestion pipelines (Excel, CSV, JSON).
- **Immutable Audit Trail** ensuring every manual override is tracked with a user-provided statutory justification.
- **Strict RBAC (Role-Based Access Control)** limiting destructive actions (e.g., removing users) to `OWNER` and `ADMIN` roles.
- **Background Job Processing** handling heavy file parsing and embedding to keep the API responsive.

## Trade-offs

- **Polling instead of WebSockets** → introduces a slight delay in progress updates but reduces connection state management.
- **AI-Driven Recon** → requires manual review (Overrides) for edge cases to ensure absolute compliance.
- **Strict Multi-tenancy** → makes cross-tenant analytics more complex, as data is heavily siloed.
