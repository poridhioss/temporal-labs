from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError
from datetime import timedelta
import uuid

from models.order_models import Order, OrderStatus
from workflows.child_workflows import ValidationWorkflow, PaymentWorkflow
from activities.inventory_activity import reserve_stock, release_stock
from activities.notification_activity import send_confirmation
from activities.status_activity import update_order_status_in_db
from models.order_models import OrderItem

@workflow.defn
class OrderWorkflow:
    def __init__(self):
        self.order_status = OrderStatus.PENDING
        self.reservation_ids = []
        
    @workflow.run
    async def process_order(self, order_data: dict) -> dict:
        """Main order processing workflow"""
        # Convert dictionary to Order object
        order = Order(
            order_id=order_data["order_id"],
            customer_email=order_data["customer_email"],
            items=[OrderItem(**item) for item in order_data["items"]],
            total_amount=order_data["total_amount"],
            status=OrderStatus(order_data["status"]),
            created_at=order_data["created_at"]
        )
        
        workflow.logger.info(f"Starting order processing for {order.order_id}")
        
        try:
            # Step 1: Validate Order using child workflow
            validation_result = await workflow.execute_child_workflow(
                ValidationWorkflow.run,
                order_data,  # Pass the dictionary
                id=f"validation-{order.order_id}",
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            if not validation_result["is_valid"]:
                self.order_status = OrderStatus.FAILED
                await workflow.execute_activity(
                    update_order_status_in_db,
                    args=[order.order_id, self.order_status.value],
                    start_to_close_timeout=timedelta(seconds=10)
                )
                return {
                    "success": False,
                    "order_id": order.order_id,
                    "status": self.order_status.value,
                    "errors": validation_result["errors"]
                }
            
            self.order_status = OrderStatus.VALIDATED
            await workflow.execute_activity(
                update_order_status_in_db,
                args=[order.order_id, self.order_status.value],
                start_to_close_timeout=timedelta(seconds=10)
            )
            workflow.logger.info(f"Order {order.order_id} validated successfully")
            
            # Step 2: Reserve Stock
            reservation_result = await workflow.execute_activity(
                reserve_stock,
                order_data,  # Pass the dictionary
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    backoff_coefficient=2
                )
            )
            
            if not reservation_result.success:
                self.order_status = OrderStatus.FAILED
                await workflow.execute_activity(
                    update_order_status_in_db,
                    args=[order.order_id, self.order_status.value],
                    start_to_close_timeout=timedelta(seconds=10)
                )
                return {
                    "success": False,
                    "order_id": order.order_id,
                    "status": self.order_status.value,
                    "error": reservation_result.error
                }
            
            self.reservation_ids = reservation_result.reservation_ids
            workflow.logger.info(f"Stock reserved for order {order.order_id}")
            
            # Step 3: Process Payment using child workflow
            self.order_status = OrderStatus.PAYMENT_PROCESSING
            await workflow.execute_activity(
                update_order_status_in_db,
                args=[order.order_id, self.order_status.value],
                start_to_close_timeout=timedelta(seconds=10)
            )
            payment_result = await workflow.execute_child_workflow(
                PaymentWorkflow.run,
                order_data,  # Pass the dictionary
                id=f"payment-{order.order_id}",
                retry_policy=RetryPolicy(maximum_attempts=1)
            )
            
            if not payment_result["success"]:
                # Compensate: Release reserved stock
                await self._compensate_stock_reservation(order)
                self.order_status = OrderStatus.FAILED
                await workflow.execute_activity(
                    update_order_status_in_db,
                    args=[order.order_id, self.order_status.value],
                    start_to_close_timeout=timedelta(seconds=10)
                )
                return {
                    "success": False,
                    "order_id": order.order_id,
                    "status": self.order_status.value,
                    "error": payment_result["error"]
                }
            
            self.order_status = OrderStatus.PAYMENT_COMPLETED
            await workflow.execute_activity(
                update_order_status_in_db,
                args=[order.order_id, self.order_status.value],
                start_to_close_timeout=timedelta(seconds=10)
            )
            workflow.logger.info(f"Payment processed for order {order.order_id}")
            
            # Step 4: Send Confirmation
            confirmation_result = await workflow.execute_activity(
                send_confirmation,
                order_data,  # Pass the dictionary
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=5,
                    backoff_coefficient=2
                )
            )
            
            self.order_status = OrderStatus.CONFIRMED
            await workflow.execute_activity(
                update_order_status_in_db,
                args=[order.order_id, self.order_status.value],
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            return {
                "success": True,
                "order_id": order.order_id,
                "status": self.order_status.value,
                "transaction_id": payment_result["transaction_id"],
                "confirmation_number": confirmation_result.confirmation_number,
                "message": "Order processed successfully"
            }
            
        except Exception as e:
            workflow.logger.error(f"Order processing failed: {str(e)}")
            await self._compensate_stock_reservation(order)
            self.order_status = OrderStatus.FAILED
            await workflow.execute_activity(
                update_order_status_in_db,
                args=[order.order_id, self.order_status.value],
                start_to_close_timeout=timedelta(seconds=10)
            )
            return {
                "success": False,
                "order_id": order.order_id,
                "status": self.order_status.value,
                "error": str(e)
            }
    
    async def _compensate_stock_reservation(self, order: Order):
        """Release reserved stock if order fails"""
        if self.reservation_ids:
            try:
                await workflow.execute_activity(
                    release_stock,
                    self.reservation_ids,
                    start_to_close_timeout=timedelta(seconds=30)
                )
                workflow.logger.info(f"Released stock reservations for order {order.order_id}")
            except Exception as e:
                workflow.logger.error(f"Failed to release stock: {str(e)}")
    
    @workflow.query
    def get_order_status(self) -> dict:
        """Get current order status"""
        return {
            "status": self.order_status.value,
            "reservation_ids": self.reservation_ids
        } 