from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

from models.order_models import Order
from activities.validation_activity import validate_order_items
from activities.payment_activity import process_payment

@workflow.defn
class ValidationWorkflow:
    @workflow.run
    async def run(self, order: Order) -> dict:
        """Child workflow for order validation"""
        validation_result = await workflow.execute_activity(
            validate_order_items,
            order,
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
    async def run(self, order: Order) -> dict:
        """Child workflow for payment processing"""
        payment_result = await workflow.execute_activity(
            process_payment,
            order,
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