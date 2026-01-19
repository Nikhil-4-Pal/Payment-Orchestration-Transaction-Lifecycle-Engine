from sqlalchemy.orm import Session
import httpx
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from app.models import TransactionStatus, IdempotencyKey
from app import models, schemas, services, database, mock_psp




app = FastAPI(title="Payment Orchestration System")

app.include_router(mock_psp.router)

@app.post("/payments", response_model=schemas.PaymentResponse)
async def create_payment(
    payment: schemas.PaymentCreate, 
    request: Request,
    idempotency_key: str = Header(None), 
    db: Session = Depends(database.get_db)
):
    if idempotency_key:
        cached_response = db.query(IdempotencyKey).filter(
            IdempotencyKey.key == idempotency_key
        ).first()

        if cached_response:
            print(f"🛑 IDEMPOTENCY HIT: Returning cached response for key {idempotency_key}")
            return cached_response.response_body

    new_transaction = models.Transaction(
        user_id=payment.user_id,
        amount=payment.amount,
        currency=payment.currency,
        status=TransactionStatus.CREATED
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    services.PaymentService.transition_state(new_transaction, TransactionStatus.PROCESSING, db)

    psp_payload = {
        "amount": payment.amount,
        "currency": payment.currency,
        "transaction_id": new_transaction.id,
        "callback_url": "http://127.0.0.1:8000/webhooks/psp" 
    }

    async with httpx.AsyncClient() as client:
        try:
            await client.post("http://127.0.0.1:8000/mock-psp/pay", json=psp_payload)
            services.PaymentService.create_attempt(db, new_transaction.id, "PENDING", psp_payload)
        except Exception as e:
            print(f"Failed to contact PSP: {e}")
            raise HTTPException(status_code=502, detail="Payment Provider Unavailable")

    if idempotency_key:
        response_data = {
            "id": new_transaction.id,
            "user_id": new_transaction.user_id,
            "amount": new_transaction.amount,
            "currency": new_transaction.currency,
            "status": new_transaction.status, 
            "created_at": new_transaction.created_at.isoformat()
        }
        
        new_key = IdempotencyKey(
            key=idempotency_key,
            response_body=response_data,
            response_code=200
        )
        db.add(new_key)
        db.commit()

    return new_transaction

@app.post("/webhooks/psp")
async def handle_psp_webhook(
    payload: schemas.WebhookPayload, 
    db: Session = Depends(database.get_db)
):
    print(f"📩 WEBHOOK RECEIVED: {payload}")

    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == payload.transaction_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    new_status = None
    if payload.status == "COMPLETED":
        new_status = TransactionStatus.SUCCESS
    elif payload.status == "FAILED":
        new_status = TransactionStatus.FAILED
    else:
        print(f"Unknown status received: {payload.status}")
        return {"status": "ignored"}

    try:
        services.PaymentService.transition_state(transaction, new_status, db)
    except Exception as e:
        print(f"State transition failed: {e}")
        
        return {"status": "error", "detail": str(e)}

    return {"status": "processed"}


@app.get("/payments/{payment_id}", response_model=schemas.PaymentResponse)
def get_payment_status(payment_id: int, db: Session = Depends(database.get_db)):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == payment_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    return transaction