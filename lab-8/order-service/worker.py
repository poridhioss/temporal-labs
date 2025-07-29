import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

# Import workflows
from workflows.order_workflow import OrderWorkflow
from workflows.child_workflows import ValidationWorkflow, PaymentWorkflow

# Import activities
from activities.validation_activity import validate_order_items
from activities.inventory_activity import reserve_stock, release_stock
from activities.payment_activity import process_payment
from activities.notification_activity import send_confirmation

async def main():
    """Start the worker"""
    # Connect to Temporal server
    client = await Client.connect("temporal:7233", namespace="default")
    
    # Create worker with all workflows and activities
    worker = Worker(
        client,
        task_queue="order-processing-queue",
        workflows=[OrderWorkflow, ValidationWorkflow, PaymentWorkflow],
        activities=[
            validate_order_items,
            reserve_stock,
            release_stock,
            process_payment,
            send_confirmation
        ]
    )
    
    print("🛒 Order Processing Worker Started!")
    print("📋 Registered Workflows: OrderWorkflow, ValidationWorkflow, PaymentWorkflow")
    print("⚡ Registered Activities: validate, reserve, payment, notification")
    print("👂 Listening on task queue: order-processing-queue")
    
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main()) 