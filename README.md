# QueueStorm Investigator — Backend

An advanced fintech triage and automated transaction dispute analyzer built for the **SUST CSE Carnival 2026 · Codex Community Hackathon · Online Preliminary**.

This service exposes a high-performance API endpoint to analyze incoming customer tickets, match them against transaction logs, and safely classify potential issues using structured AI outputs.

## 🚀 Features
* **Automated Triage:** Instantly classifies incoming customer complaints into standard fintech case types (e.g., wrong transfers, failed payments, duplicate billing).
* **Evidence Validation:** Cross-references user complaints with transaction history to evaluate factual consistency.
* **Structured AI Engine:** Integrates the `gemini-2.5-flash` model utilizing structured JSON schemas for predictable and safe internal routing.
* **Safety Rules Enforcement:** Formulates customer-facing support responses that safely guard sensitive data (never asks for OTPs/PINs) and avoids unauthorized refund promises.

## 🛠️ Tech Stack
* **Framework:** FastAPI (Python)
* **AI Client:** Google GenAI SDK (`gemini-2.5-flash`)
* **Validation:** Pydantic

## 📥 API Endpoint
### `POST /analyze-ticket`
Accepts customer complaint payloads along with transaction histories, validating and rendering detailed internal analysis alongside user-facing communications.
