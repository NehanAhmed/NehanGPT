from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Correct MongoDB URI with username and password
uri = "mongodb+srv://flaskuser:flaskUser@nehangpt.wvuhxnq.mongodb.net/?retryWrites=true&w=majority&appName=nehangpt"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Ping the database to confirm connection
try:
    client.admin.command('ping')
    print("✅ Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("❌ Connection failed:", e)
