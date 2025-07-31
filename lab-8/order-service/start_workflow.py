import asyncio
from temporalio.client import Client
from datetime import datetime
import sys

from models.order_models import Order, OrderItem, OrderStatus
from workflows.order_workflow import OrderWorkflow

async def main():
    """Test script to start an order workflow"""
    # Connect to Temporal
    client = await Client.connect("temporal:7233", namespace="default")
    
    # Create a test order
    test_order = Order(
        order_id="test-order-001",
        customer_email="test@example.com",
        items=[
            OrderItem(product_id="LAPTOP-001", quantity=1, price=1299.99),
            OrderItem(product_id="MOUSE-001", quantity=2, price=49.99)
        ],
        total_amount=1399.97,
        status=OrderStatus.PENDING,
        created_at=None  # Let the model handle it
    )
    
    print(f"🛒 Starting order workflow for order {test_order.order_id}")
    print(f"📧 Customer: {test_order.customer_email}")
    print(f"💰 Total: ${test_order.total_amount}")
    
    # Start workflow
    handle = await client.start_workflow(
        OrderWorkflow.process_order,
        test_order.to_dict(),  # Convert to dict for JSON serialization
        id=f"order-workflow-{test_order.order_id}",
        task_queue="order-processing-queue"
    )
    
    print(f"✅ Workflow started with ID: {handle.id}")
    
    # Wait for result
    result = await handle.result()
    print(f"\n📋 Workflow Result:")
    print(f"   Success: {result['success']}")
    print(f"   Status: {result['status']}")
    if result.get('confirmation_number'):
        print(f"   Confirmation: {result['confirmation_number']}")
    if result.get('error'):
        print(f"   Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 