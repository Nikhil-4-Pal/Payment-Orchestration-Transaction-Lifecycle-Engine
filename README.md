# 💳 Payment Orchestration & Transaction Lifecycle Engine

A production-grade backend system designed to handle the complexities of asynchronous payment processing. This project implements a **Finite State Machine (FSM)** for transaction integrity, **Idempotency** for safety, and a **Reconciliation Worker** for self-healing capability against "zombie" transactions.

---

## 🏗 System Architecture

The system mimics a real-world fintech infrastructure where payment providers (PSPs) operate asynchronously.

**Core Components:**
1.  **API Service (FastAPI):** Handles payment requests and webhooks.
2.  **Database (PostgreSQL):** Stores transaction states with strict ACID compliance.
3.  **Mock PSP (Bank):** A simulation service that introduces random latency and failures to test system resilience.
4.  **Reconciliation Worker:** A background process that polls for "stuck" transactions and syncs state.

### 🔄 The Transaction Lifecycle (State Machine)
We enforce strict transitions to prevent invalid states (e.g., a payment cannot go from `FAILED` to `SUCCESS`).

`CREATED` → `PROCESSING` → `SUCCESS` or `FAILED` ↘ `REFUNDED`

---

## 🚀 Key Features (Why this matters)

### 1. 🛡️ Idempotency (Double-Charge Protection)
Network jitters often cause users to click "Pay" multiple times.
- **Solution:** The API checks the `Idempotency-Key` header.
- **Behavior:** If a key is reused, the system returns the **cached response** immediately without hitting the database or the bank again.

### 2. ⚡ Asynchronous Webhook Handling
Real banks don't respond instantly.
- **Solution:** We return `202 Accepted` to the user immediately. The system waits for the PSP's webhook to update the status to `SUCCESS` or `FAILED` in the background.

### 3. 🩺 Self-Healing Reconciliation
What if the bank takes the money, but the webhook fails to reach us?
- **Solution:** A reconciliation script scans for transactions stuck in `PROCESSING` and proactively polls the PSP to sync the final status.

---

## 🛠 Tech Stack

* **Language:** Python 3.12+
* **Framework:** FastAPI
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Concurrency:** Asyncio / HTTPX
* **Reliability:** Pydantic (Validation), BackgroundTasks

---

## ⚙️ Setup & Installation

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd payment_system
