import asyncpg
import os
from typing import List, Dict, Any
from datetime import datetime

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'temporal'),
        password=os.getenv('POSTGRES_PASSWORD', 'temporal'),
        database=os.getenv('POSTGRES_DB', 'temporal')
    )

async def get_inventory() -> List[Dict[str, Any]]:
    """Get all inventory items"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT product_id, product_name, available_quantity, reserved_quantity, price
            FROM order_system.inventory
            ORDER BY product_name
            """
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()

async def save_order(order_data: Dict[str, Any]) -> None:
    """Save order to database"""
    conn = await get_db_connection()
    try:
        async with conn.transaction():
            # Insert order
            await conn.execute(
                """
                INSERT INTO order_system.orders (order_id, customer_email, total_amount, status, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                order_data['order_id'],
                order_data['customer_email'],
                order_data['total_amount'],
                order_data['status'],
                order_data['created_at']
            )
            
            # Insert order items
            for item in order_data['items']:
                await conn.execute(
                    """
                    INSERT INTO order_system.order_items (order_id, product_id, quantity, price)
                    VALUES ($1, $2, $3, $4)
                    """,
                    order_data['order_id'],
                    item['product_id'],
                    item['quantity'],
                    item['price']
                )
    finally:
        await conn.close()

async def get_order_status(order_id: str) -> Dict[str, Any]:
    """Get order status from database"""
    conn = await get_db_connection()
    try:
        # Get order
        order = await conn.fetchrow(
            """
            SELECT order_id, customer_email, total_amount, status, created_at
            FROM order_system.orders
            WHERE order_id = $1
            """,
            order_id
        )
        
        if not order:
            return None
        
        # Get order items
        items = await conn.fetch(
            """
            SELECT oi.product_id, oi.quantity, oi.price, i.product_name
            FROM order_system.order_items oi
            JOIN order_system.inventory i ON oi.product_id = i.product_id
            WHERE oi.order_id = $1
            """,
            order_id
        )
        
        return {
            "order_id": order['order_id'],
            "customer_email": order['customer_email'],
            "total_amount": float(order['total_amount']),
            "status": order['status'],
            "created_at": order['created_at'].isoformat(),
            "items": [dict(item) for item in items]
        }
    finally:
        await conn.close() 