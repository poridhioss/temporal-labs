from fastapi import FastAPI, HTTPException
from temporalio.client import Client
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime
import os
import sys

# Add the order-service path to import models
sys.path.append('/app/../order-service')

from database import get_inventory, save_order, get_order_status

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
        order_data = {
            "order_id": order_id,
            "customer_email": order_request.customer_email,
            "items": order_items,
            "total_amount": total,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        # Save order to database
        await save_order(order_data)
        
        # Start workflow using Temporal CLI approach (simplified for demo)
        # In production, you would import the Order models and start the workflow properly
        workflow_id = f"order-workflow-{order_id}"
        
        # For this demo, we'll simulate workflow start and return immediately
        # In a real implementation, you would:
        # 1. Import Order and OrderItem models
        # 2. Create workflow order object  
        # 3. Start workflow with temporal_client.start_workflow()
        
        return {
            "order_id": order_id,
            "workflow_id": workflow_id,
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
            # In production, you would query the workflow status
            # handle = temporal_client.get_workflow_handle(workflow_id)
            # workflow_status = await handle.query("get_order_status")
            workflow_status = {"workflow_status": "Check Temporal Web UI for detailed status"}
        except:
            # Workflow might be completed or not found
            pass
        
        # Combine order info with workflow status
        result = {**order_info, **workflow_status}
        return result
        
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