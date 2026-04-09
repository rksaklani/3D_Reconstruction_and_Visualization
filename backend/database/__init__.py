"""Database initialization and connection."""

from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional

# MongoDB connection
mongodb_client: Optional[AsyncIOMotorClient] = None
database = None


async def connect_to_mongo():
    """Connect to MongoDB."""
    global mongodb_client, database
    
    # Get MongoDB URL from environment or use default
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:admin123@localhost:27017"
    )
    database_name = os.getenv("MONGODB_DATABASE", "reconstruction")
    
    # Create client
    mongodb_client = AsyncIOMotorClient(mongodb_url)
    database = mongodb_client[database_name]
    
    # Test connection
    try:
        await mongodb_client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {database_name}")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection."""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("✓ Closed MongoDB connection")


def get_database():
    """Get database instance."""
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database
