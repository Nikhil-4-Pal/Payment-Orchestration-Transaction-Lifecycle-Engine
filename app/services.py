from sqlalchemy.orm import Session
from .models import Transaction, TransactionStatus, PaymentAttempt, AttemptStatus
from fastapi import HTTPException

class PaymentService:
    VALID_TRANSITIONS = {
        TransactionStatus.CREATED: [TransactionStatus.PROCESSING, TransactionStatus.FAILED],
        TransactionStatus.PROCESSING: [TransactionStatus.SUCCESS, TransactionStatus.FAILED],
        TransactionStatus.SUCCESS: [TransactionStatus.REFUNDED],
        TransactionStatus.FAILED: [], 
        TransactionStatus.REFUNDED: [] 
    }

    @staticmethod
    def transition_state(transaction: Transaction, new_state: TransactionStatus, db: Session):
        """
        Validates if the status change is legal.
        If yes, updates the DB.
        If no, raises an error.
        """
        current_state = transaction.status

        if current_state == new_state:
            return transaction
        
        
        if new_state not in PaymentService.VALID_TRANSITIONS[current_state]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid state transition: Cannot move from {current_state} to {new_state}"
            )

        transaction.status = new_state
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def create_attempt(db: Session, transaction_id: int, psp_reference: str, payload: dict):
        """
        Logs a new interaction with the Bank (PSP).
        """
        attempt = PaymentAttempt(
            transaction_id=transaction_id,
            psp_reference=psp_reference,
            status=AttemptStatus.INITIATED,
            request_payload=payload
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt