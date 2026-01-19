from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from .models import TransactionStatus, AttemptStatus


class PaymentCreate(BaseModel):
    user_id : str
    amount : float
    currency : str = "INR"
    
    
class PaymentResponse(BaseModel):
    id : int
    user_id : str
    amount : int 
    currency : str
    status : TransactionStatus
    created_at : datetime
    
    class config:
        from_attributes = True 
        
class WebhookPayload(BaseModel):
    transaction_id : int
    psp_reference : str
    status : str
    

class RefundCreate(BaseModel):
    amount : float
    reason : Optional[str] = None