from temporalio import activity
import asyncpg
import uuid
from datetime import datetime, timedelta
from typing import List
import os

from models.order_models import Order, ReservationResult

@activity.defn
async def reserve_stock(order: Order) -> ReservationResult:
    """Reserve inventory for order"""
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'temporal'),
        password=os.getenv('POSTGRES_PASSWORD', 'temporal'),
        database=os.getenv('POSTGRES_DB', 'temporal')
    )
    
    reservation_ids = []
    
    try:
        # Start transaction
        async with conn.transaction():
            for item in order.items:
                # Check and update inventory atomically
                result = await conn.fetchval(
                    """
                    UPDATE order_system.inventory 
                    SET available_quantity = available_quantity - $1,
                        reserved_quantity = reserved_quantity + $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = $2 AND available_quantity >= $1
                    RETURNING product_id
                    """,
                    item.quantity,
                    item.product_id
                )
                
                if not result:
                    raise Exception(f"Cannot reserve stock for {item.product_id}")
                
                # Create reservation record
                reservation_id = f"res-{uuid.uuid4().hex[:8]}"
                await conn.execute(
                    """
                    INSERT INTO order_system.stock_reservations 
                    (reservation_id, order_id, product_id, quantity, expires_at)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    reservation_id,
                    order.order_id,
                    item.product_id,
                    item.quantity,
                    datetime.now() + timedelta(minutes=15)
                )
                
                reservation_ids.append(reservation_id)
                activity.logger.info(f"Reserved {item.quantity} units of {item.product_id}")
        
        return ReservationResult(
            success=True,
            reservation_ids=reservation_ids
        )
    
    except Exception as e:
        activity.logger.error(f"Stock reservation failed: {str(e)}")
        return ReservationResult(
            success=False,
            error=str(e)
        )
    
    finally:
        await conn.close()

@activity.defn
async def release_stock(reservation_ids: List[str]) -> bool:
    """Release reserved stock"""
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'temporal'),
        password=os.getenv('POSTGRES_PASSWORD', 'temporal'),
        database=os.getenv('POSTGRES_DB', 'temporal')
    )
    
    try:
        async with conn.transaction():
            for reservation_id in reservation_ids:
                # Get reservation details
                reservation = await conn.fetchrow(
                    """
                    SELECT product_id, quantity 
                    FROM order_system.stock_reservations 
                    WHERE reservation_id = $1 AND status = 'active'
                    """,
                    reservation_id
                )
                
                if reservation:
                    # Return stock to available
                    await conn.execute(
                        """
                        UPDATE order_system.inventory 
                        SET available_quantity = available_quantity + $1,
                            reserved_quantity = reserved_quantity - $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = $2
                        """,
                        reservation['quantity'],
                        reservation['product_id']
                    )
                    
                    # Mark reservation as released
                    await conn.execute(
                        """
                        UPDATE order_system.stock_reservations 
                        SET status = 'released' 
                        WHERE reservation_id = $1
                        """,
                        reservation_id
                    )
                    
                    activity.logger.info(f"Released reservation {reservation_id}")
        
        return True
    
    except Exception as e:
        activity.logger.error(f"Failed to release stock: {str(e)}")
        return False
    
    finally:
        await conn.close() 