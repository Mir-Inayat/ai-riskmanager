# AGENTS.md

## Architecture Standards
- **Stack**: Next.js (frontend), FastAPI / Python (backend), LightGBM/Pandas (ML)
- **API Contract**: Standard JSON schemas defined in `/shared/types.ts`
- **Mock Data**: `/frontend/src/fixtures/*.json` provides static shapes for parallel development.

## Domain Boundaries
To execute the Sentinel plan efficiently, work is split into three isolated streams:

### 1. Agent Stream 1: Core ML & Data
- **Allowed paths**: `/scripts/**`, `/data/**`
- **Forbidden paths**: `/frontend/**`, `/backend/**`
- **Responsibilities**: Data prep, model training (`LightGBM`), calibration, threshold optimization, graph building, generating metric JSONs.

### 2. Agent Stream 2: Backend API & Workflow
- **Allowed paths**: `/backend/**`, `/shared/**`
- **Forbidden paths**: `/frontend/**`, `/scripts/**` (except reading model outputs in `/data/models`)
- **Responsibilities**: FastAPI server, cost-routing logic, audit hash chain, endpoints matching the frozen contract.

### 3. Agent Stream 3: Frontend Developer
- **Allowed paths**: `/frontend/**`, `/shared/**` (read-only)
- **Forbidden paths**: `/backend/**`, `/scripts/**`
- **Responsibilities**: Next.js 14 UI, Command Center, Alert Queue, Case Investigation Hero Page, Policy simulator. Must build against fixture JSONs until integration.

## Critical Rules
- **Contract First**: The `/shared/types.ts` and `/frontend/src/fixtures/` must be finalized before parallel work begins.
- **Isolation**: Agents must strictly adhere to their domain boundaries to prevent merge conflicts.
- **Dependencies**: Each domain manages its own dependencies (`package.json` for frontend, `requirements.txt` for backend/ML).
