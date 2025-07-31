from fastapi import FastAPI, HTTPException
from temporalio.client import Client
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime
import os
import sys

# Add the order-service path to import models
sys.path.append('/app/order-service')

from database import get_inventory, save_order, get_order_status
from models.order_models import Order, OrderItem, OrderStatus
from workflows.order_workflow import OrderWorkflow

app = FastAPI(title="Order Processing API", description="Real-world order processing system using Temporal")
temporal_client = None

class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int

class OrderRequest(BaseModel):
    customer_email: str
    items: List[OrderItemRequest]

@app.on_event("startup")
async def startup():
    global temporal_client
    temporal_client = await Client.connect("temporal:7233", namespace="default")
    print("🚀 FastAPI Order Service Started!")
    print("📋 Connected to Temporal server")

@app.get("/")
async def root():
    return {
        "message": "Order Processing System API", 
        "version": "1.0",
        "endpoints": {
            "inventory": "/inventory",
            "create_order": "/orders (POST)",
            "get_order": "/orders/{order_id}",
            "docs": "/docs"
        }
    }

@app.get("/inventory")
async def list_inventory():
    """Get available inventory"""
    try:
        inventory = await get_inventory()
        return {"inventory": inventory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/orders")
async def create_order(order_request: OrderRequest):
    """Create a new order and start processing workflow"""
    try:
        # Generate order ID
        order_id = f"order-{uuid.uuid4().hex[:12]}"
        
        # Get current prices from inventory
        inventory = await get_inventory()
        inventory_map = {item['product_id']: item for item in inventory}
        
        # Calculate total and prepare order items
        total = 0.0
        order_items = []
        
        for item in order_request.items:
            if item.product_id not in inventory_map:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            
            product = inventory_map[item.product_id]
            price = float(product['price'])
            total += price * item.quantity
            
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": price
            })
        
        # Create order object
        current_time = datetime.now()
        order_data = {
            "order_id": order_id,
            "customer_email": order_request.customer_email,
            "items": order_items,
            "total_amount": total,
            "status": "pending",
            "created_at": current_time.isoformat()
        }
        
        # Save order to database
        await save_order(order_data)
        
        # Create the Order object for the workflow
        workflow_order = Order(
            order_id=order_id,
            customer_email=order_request.customer_email,
            items=[OrderItem(**item) for item in order_items],
            total_amount=total,
            status=OrderStatus.PENDING,
            created_at=None  # Let the model handle it
        )

        # Start the workflow
        handle = await temporal_client.start_workflow(
            OrderWorkflow.process_order,
            workflow_order.to_dict(),  # Convert to dict for JSON serialization
            id=f"order-workflow-{order_id}",
            task_queue="order-processing-queue",
        )
        
        return {
            "order_id": order_id,
            "workflow_id": handle.id,
            "status": "processing",
            "total_amount": total,
            "message": "Order created and processing started",
            "tracking_url": f"/orders/{order_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order status and details"""
    try:
        # Get order from database
        order_info = await get_order_status(order_id)
        if not order_info:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Try to get workflow status if available
        workflow_id = f"order-workflow-{order_id}"
        workflow_status = {}
        
        try:
            handle = temporal_client.get_workflow_handle(workflow_id)
            workflow_status = await handle.query(OrderWorkflow.get_order_status)
        except Exception as e:
            # Workflow might be completed or not found, this is not a fatal error
            workflow_status = {"workflow_query_error": str(e)}
        
        # Combine order info with workflow status
        order_info.update(workflow_status)
        return order_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "order-api",
        "temporal_connected": temporal_client is not None
    } 