# reconcile.py
import asyncio
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Transaction, TransactionStatus
from app.services import PaymentService


STALE_TIMEFRAME_MINUTES = 1 
PSP_STATUS_URL = "http://127.0.0.1:8000/mock-psp/status"

def get_stale_transactions(db: Session):
    time_threshold = datetime.now() - timedelta(minutes=STALE_TIMEFRAME_MINUTES)
    return db.query(Transaction).filter(
        Transaction.status == TransactionStatus.PROCESSING,
        Transaction.created_at < time_threshold
    ).all()

async def reconcile_payment(transaction: Transaction, db: Session):
    print(f"🔎 Checking stuck transaction #{transaction.id}...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PSP_STATUS_URL}/{transaction.id}")
            data = response.json()
            bank_status = data["status"]
            
            print(f"   -> Bank says: {bank_status}")

            new_status = None
            if bank_status == "COMPLETED":
                new_status = TransactionStatus.SUCCESS
            elif bank_status == "FAILED":
                new_status = TransactionStatus.FAILED
            
            if new_status:
                PaymentService.transition_state(transaction, new_status, db)
                print(f"   ✅ Fixed! Updated to {new_status}")
                
        except Exception as e:
            print(f"   ❌ Error checking bank: {e}")

async def main():
    db = SessionLocal()
    try:
        stale_txns = get_stale_transactions(db)
        print(f"Found {len(stale_txns)} stuck transactions.")
        
        for txn in stale_txns:
            await reconcile_payment(txn, db)
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())