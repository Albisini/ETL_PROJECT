from dotenv import load_dotenv
import os
import pymongo
from pymongo import MongoClient
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["Bandi"]
collection = db["Lombardia"]
numero = db.list_collection_names()
print(numero)

