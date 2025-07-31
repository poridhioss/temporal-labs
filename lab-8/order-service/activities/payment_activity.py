from temporalio import activity
import random
import uuid
from datetime import datetime

from models.order_models import Order, PaymentResult, OrderItem, OrderStatus

@activity.defn
async def process_payment(order_data: dict) -> PaymentResult:
    """Simulate payment processing"""
    # Convert dictionary to Order object
    order = Order(
        order_id=order_data["order_id"],
        customer_email=order_data["customer_email"],
        items=[OrderItem(**item) for item in order_data["items"]],
        total_amount=order_data["total_amount"],
        status=OrderStatus(order_data["status"]),
        created_at=order_data["created_at"]
    )
    
    activity.logger.info(f"Processing payment for order {order.order_id}, amount: ${order.total_amount}")
    
    # Simulate payment gateway call
    # In real implementation, this would call Stripe, PayPal, etc.
    
    # Simulate 80% success rate for demonstration
    if random.random() < 0.8:
        transaction_id = f"txn-{uuid.uuid4().hex[:12]}"
        activity.logger.info(f"Payment successful: {transaction_id}")
        
        return PaymentResult(
            success=True,
            transaction_id=transaction_id
        )
    else:
        # Simulate different payment failures
        error_types = [
            "Insufficient funds",
            "Card declined", 
            "Payment gateway timeout"
        ]
        error = random.choice(error_types)
        activity.logger.error(f"Payment failed: {error}")
        
        return PaymentResult(
            success=False,
            error=error
        ) 