import asyncio
import httpx 
import random
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/mock-psp", tags=["Mock Bank"])

class PSPPaymentRequest(BaseModel):
    amount: float
    currency: str
    callback_url: str 
    transaction_id: int

async def process_payment_async(payload: PSPPaymentRequest):
    print(f"🏦 MOCK BANK: Processing payment for ${payload.amount}...")
    
    await asyncio.sleep(random.randint(2, 5))
    
    status = "COMPLETED" if random.random() < 0.8 else "FAILED"
    
    webhook_payload = {
        "transaction_id": payload.transaction_id,
        "psp_reference": f"PSP-{random.randint(1000,9999)}",
        "status": status
    }

    print(f"🏦 MOCK BANK: Sending Webhook -> {status}")
    async with httpx.AsyncClient() as client:
        try:
            await client.post(payload.callback_url, json=webhook_payload)
        except Exception as e:
            print(f"❌ MOCK BANK: Failed to send webhook: {e}")

@router.post("/pay")
async def initiate_mock_payment(request: PSPPaymentRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_payment_async, request)
    return {"status": "ACCEPTED", "message": "Processing started"}



@router.get("/status/{transaction_id}")
async def get_mock_transaction_status(transaction_id: int):
    if transaction_id % 2 == 0:
        return {"status": "COMPLETED", "psp_reference": "PSP-RECOVERED"}
    else:
        return {"status": "FAILED", "psp_reference": "PSP-FAILED"}