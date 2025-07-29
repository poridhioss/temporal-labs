from temporalio import activity
import random
import uuid
from datetime import datetime

from models.order_models import Order, PaymentResult

@activity.defn
async def process_payment(order: Order) -> PaymentResult:
    """Simulate payment processing"""
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