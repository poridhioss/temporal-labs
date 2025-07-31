from temporalio import activity
import asyncpg
import os

@activity.defn
async def update_order_status_in_db(order_id: str, status: str) -> bool:
    """Update order status in the database"""
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'temporal'),
        password=os.getenv('POSTGRES_PASSWORD', 'temporal'),
        database=os.getenv('POSTGRES_DB', 'temporal')
    )
    try:
        await conn.execute(
            """
            UPDATE order_system.orders
            SET status = $1, updated_at = CURRENT_TIMESTAMP
            WHERE order_id = $2
            """,
            status,
            order_id
        )
        activity.logger.info(f"Updated status for order {order_id} to {status}")
        return True
    except Exception as e:
        activity.logger.error(f"Failed to update status for order {order_id}: {str(e)}")
        return False
    finally:
        await conn.close()
