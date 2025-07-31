from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

from models.order_models import Order, OrderItem, OrderStatus
from activities.validation_activity import validate_order_items
from activities.payment_activity import process_payment

@workflow.defn
class ValidationWorkflow:
    @workflow.run
    async def run(self, order_data: dict) -> dict:
        """Child workflow for order validation"""
        # Convert dictionary to Order object
        order = Order(
            order_id=order_data["order_id"],
            customer_email=order_data["customer_email"],
            items=[OrderItem(**item) for item in order_data["items"]],
            total_amount=order_data["total_amount"],
            status=OrderStatus(order_data["status"]),
            # status=order_data["status"],
            created_at=order_data["created_at"]
        )
        
        validation_result = await workflow.execute_activity(
            validate_order_items,
            order_data,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return {
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "validated_items": validation_result.validated_items
        }

@workflow.defn
class PaymentWorkflow:
    @workflow.run
    async def run(self, order_data: dict) -> dict:
        """Child workflow for payment processing"""
        # Convert dictionary to Order object
        order = Order(
            order_id=order_data["order_id"],
            customer_email=order_data["customer_email"],
            items=[OrderItem(**item) for item in order_data["items"]],
            total_amount=order_data["total_amount"],
            status=OrderStatus(order_data["status"]),
            created_at=order_data["created_at"]
        )
        
        payment_result = await workflow.execute_activity(
            process_payment,
            order_data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                non_retryable_error_types=["InsufficientFundsError", "CardDeclinedError"]
            )
        )
        
        return {
            "success": payment_result.success,
            "transaction_id": payment_result.transaction_id,
            "error": payment_result.error
        } 