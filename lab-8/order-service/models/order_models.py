from dataclasses import dataclass, field
from typing import List, Union, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_COMPLETED = "payment_completed"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    

@dataclass
class OrderItem:
    product_id: str
    quantity: int
    price: float

@dataclass
class Order:
    order_id: str
    customer_email: str
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: str = None
    
    def __post_init__(self):
        # Ensure created_at is always a string
        from datetime import datetime
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        elif isinstance(self.created_at, datetime):
            self.created_at = self.created_at.isoformat()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "order_id": self.order_id,
            "customer_email": self.customer_email,
            "items": [{"product_id": item.product_id, "quantity": item.quantity, "price": item.price} for item in self.items],
            "total_amount": self.total_amount,
            "status": self.status.value,  # Convert enum to string
            "created_at": self.created_at
        }

@dataclass
class ValidationResult:
    is_valid: bool
    errors: Optional[List[str]]  # ← Make sure this is Optional
    validated_items: List[OrderItem] = None

@dataclass
class ReservationResult:
    success: bool
    reservation_ids: Optional[List[str]] = None
    error: Optional[str] = None

@dataclass
class PaymentResult:
    success: bool
    transaction_id: Optional[str] = None
    error: Optional[str] = None

@dataclass
class ConfirmationResult:
    success: bool
    confirmation_number: str = None
    error: Optional[str] = None