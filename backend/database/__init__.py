"""Database initialization and connection."""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from typing import Optional

# Async MongoDB connection (for FastAPI endpoints)
mongodb_client: Optional[AsyncIOMotorClient] = None
database = None

# Sync MongoDB connection (for threaded pipeline)
sync_mongodb_client: Optional[MongoClient] = None
sync_database = None


async def connect_to_mongo():
    """Connect to MongoDB (async)."""
    global mongodb_client, database, sync_mongodb_client, sync_database
    
    # Get MongoDB URL from environment or use default
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:admin123@localhost:27017"
    )
    database_name = os.getenv("MONGODB_DATABASE", "reconstruction")
    
    # Create async client
    mongodb_client = AsyncIOMotorClient(mongodb_url)
    database = mongodb_client[database_name]
    
    # Create sync client for threaded pipeline
    sync_mongodb_client = MongoClient(mongodb_url)
    sync_database = sync_mongodb_client[database_name]
    
    # Test connection
    try:
        await mongodb_client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {database_name}")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection."""
    global mongodb_client, sync_mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("✓ Closed async MongoDB connection")
    if sync_mongodb_client:
        sync_mongodb_client.close()
        print("✓ Closed sync MongoDB connection")


def get_database():
    """Get database instance (async)."""
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database


def get_sync_database():
    """Get sync database instance (for threaded pipeline)."""
    if sync_database is None:
        raise RuntimeError("Sync database not initialized. Call connect_to_mongo() first.")
    return sync_database
