import os
import json
from typing import List, Optional, Literal
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

app = FastAPI(title="QueueStorm Investigator Copilot")

# --- REQUEST SCHEMA ---
class TransactionEntry(BaseModel):
    transaction_id: str
    timestamp: str
    type: Literal["transfer", "payment", "cash_in", "cash_out", "settlement", "refund"]
    amount: float
    counterparty: str
    status: Literal["completed", "failed", "pending", "reversed"]

class TicketRequest(BaseModel):
    ticket_id: str
    complaint: str
    language: Optional[str] = "en"
    channel: Optional[str] = "in_app_chat"
    user_type: Optional[str] = "customer"
    campaign_context: Optional[str] = None
    transaction_history: Optional[List[TransactionEntry]] = Field(default_factory=list)
    metadata: Optional[dict] = None

# --- RESPONSE SCHEMA ---
class TicketResponse(BaseModel):
    ticket_id: str  # Must match request ticket_id
    relevant_transaction_id: Optional[str] = None
    evidence_verdict: Literal["consistent", "inconsistent", "insufficient_data"]
    case_type: Literal[
        "wrong_transfer", "payment_failed", "refund_request", 
        "duplicate_payment", "merchant_settlement_delay", 
        "agent_cash_in_issue", "phishing_or_social_engineering", "other"
    ]
    severity: Literal["low", "medium", "high", "critical"]
    department: Literal[
        "customer_support", "dispute_resolution", "payments_ops", 
        "merchant_operations", "agent_operations", "fraud_risk"
    ]
    agent_summary: str
    recommended_next_action: str
    customer_reply: str
    human_review_required: bool
    confidence: Optional[float] = 1.0
    reason_codes: Optional[List[str]] = Field(default_factory=list)

# --- ENDPOINTS ---

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/analyze-ticket", response_model=TicketResponse, status_code=200)
async def analyze_ticket(request: TicketRequest):
    if not request.complaint.strip():
        raise HTTPException(status_code=422, detail="Complaint text cannot be empty.")
        
    if not client:
        raise HTTPException(
            status_code=500, 
            detail="API Key configuration missing or invalid. Please check your .env file."
        )

    try:
        prompt = f"""
        You are an advanced fintech triage agent. Analyze the customer complaint and transaction history to determine fraud risk, severity, case type, and next steps.
        
        Ticket Details:
        - Ticket ID: {request.ticket_id}
        - Language: {request.language}
        - Channel: {request.channel}
        - User Type: {request.user_type}
        - Campaign Context: {request.campaign_context}
        
        Customer Complaint:
        "{request.complaint}"
        
        Transaction History:
        {request.transaction_history}
        
        Metadata:
        {request.metadata}

        Instructions:
        1. Set the `ticket_id` to exactly match: "{request.ticket_id}".
        2. Evaluate if the complaint is 'consistent', 'inconsistent', or contains 'insufficient_data' relative to the provided transaction history.
        3. Determine the correct case_type, severity, and responsible department.
        4. Provide an accurate internal `agent_summary` and `recommended_next_action`.
        5. Write a friendly, professional `customer_reply` addressing the issue in the tone appropriate for a response.
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TicketResponse,
                temperature=0.1,
            ),
        )

        cleaned_json_text = response.text.replace("```json", "").replace("```", "").strip()
        
        response_data = json.loads(cleaned_json_text)
        
        return response_data

    except json.JSONDecodeError as json_err:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Gemini output into schema JSON. Raw output: {response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal agent handling crash: {str(e)}"
        )
        
        return response.text

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal processing error occurred.")