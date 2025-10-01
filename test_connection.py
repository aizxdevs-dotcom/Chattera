import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from app.models.user import User

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

print("🔎 Testing connection with:")
print("URI:", uri)
print("USER:", user)

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 1 AS num")
        print("✅ Connection successful, result:", result.single()["num"])
except Exception as e:
    print("❌ Connection failed:", e)

