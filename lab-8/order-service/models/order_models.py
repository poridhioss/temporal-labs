from dataclasses import dataclass
from typing import List
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
    created_at: datetime = None

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = None
    validated_items: List[OrderItem] = None

@dataclass
class ReservationResult:
    success: bool
    reservation_ids: List[str] = None
    error: str = None

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str = None
    error: str = None

@dataclass
class ConfirmationResult:
    success: bool
    confirmation_number: str = None
    error: str = None 