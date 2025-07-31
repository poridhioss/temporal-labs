from temporalio import activity
import uuid
from datetime import datetime

from models.order_models import Order, ConfirmationResult, OrderItem, OrderStatus

@activity.defn
async def send_confirmation(order_data: dict) -> ConfirmationResult:
    """Send order confirmation email"""
    # Convert dictionary to Order object
    order = Order(
        order_id=order_data["order_id"],
        customer_email=order_data["customer_email"],
        items=[OrderItem(**item) for item in order_data["items"]],
        total_amount=order_data["total_amount"],
        status=OrderStatus(order_data["status"]),
        created_at=order_data["created_at"]
    )
    
    try:
        # Generate confirmation number
        confirmation_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Simulate email sending
        activity.logger.info(f"Sending confirmation email to {order.customer_email}")
        activity.logger.info(f"Confirmation number: {confirmation_number}")
        
        # In real implementation, this would:
        # 1. Render email template
        # 2. Send via email service (SendGrid, AWS SES, etc.)
        # 3. Send SMS if configured
        # 4. Create PDF invoice
        
        email_content = f"""
        Dear Customer,
        
        Your order {order.order_id} has been confirmed!
        
        Confirmation Number: {confirmation_number}
        Total Amount: ${order.total_amount}
        
        Order Details:
        """
        
        for item in order.items:
            email_content += f"\n- Product: {item.product_id}, Quantity: {item.quantity}, Price: ${item.price}"
        
        email_content += f"\n\nThank you for your purchase!"
        
        activity.logger.info(f"Email content:\n{email_content}")
        
        return ConfirmationResult(
            success=True,
            confirmation_number=confirmation_number
        )
    
    except Exception as e:
        activity.logger.error(f"Failed to send confirmation: {str(e)}")
        return ConfirmationResult(
            success=False,
            error=str(e)
        ) 