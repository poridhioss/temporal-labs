from temporalio import activity
import asyncpg
import os

from decimal import Decimal

from models.order_models import Order, ValidationResult, OrderItem, OrderStatus

@activity.defn
async def validate_order_items(order_data: dict) -> ValidationResult:
    """Validate order items against inventory"""
    # Convert dictionary to Order object
    order = Order(
        order_id=order_data["order_id"],
        customer_email=order_data["customer_email"],
        items=[OrderItem(**item) for item in order_data["items"]],
        total_amount=order_data["total_amount"],
        status=OrderStatus(order_data["status"]),
        created_at=order_data["created_at"]
    )
    
    errors = []
    validated_items = []
    
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'temporal'),
        password=os.getenv('POSTGRES_PASSWORD', 'temporal'),
        database=os.getenv('POSTGRES_DB', 'temporal')
    )
    
    try:
        for item in order.items:
            # Check if product exists and has sufficient stock
            row = await conn.fetchrow(
                """
                SELECT product_id, product_name, available_quantity, price 
                FROM order_system.inventory 
                WHERE product_id = $1
                """,
                item.product_id
            )
            
            if not row:
                errors.append(f"Product {item.product_id} not found")
                continue
            
            if row['available_quantity'] < item.quantity:
                errors.append(
                    f"Insufficient stock for {row['product_name']}. "
                    f"Requested: {item.quantity}, Available: {row['available_quantity']}"
                )
                continue
            
            # Validate price hasn't changed significantly
            if abs(row['price'] - Decimal(str(item.price))) > Decimal('0.01'):
                errors.append(
                    f"Price mismatch for {row['product_name']}. "
                    f"Expected: ${item.price}, Current: ${row['price']}"
                )
                continue
            
            validated_items.append(item)
            activity.logger.info(f"Validated item: {item.product_id} x {item.quantity}")
    
    finally:
        await conn.close()
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors if errors else None,
        validated_items=validated_items
    ) 