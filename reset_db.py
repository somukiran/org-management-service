import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def reset_database():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    print("Connected to MongoDB")
    
    database_names = await client.list_database_names()
    print(f"Existing databases: {database_names}")
    
    if "master_database" in database_names:
        await client.drop_database("master_database")
        print("Dropped 'master_database'")
    else:
        print("'master_database' does not exist")
    
    client.close()
    print("\nDatabase reset complete!")

if __name__ == "__main__":
    asyncio.run(reset_database())