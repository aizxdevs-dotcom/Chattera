import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from neomodel import config
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")       
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE") 

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise ValueError("❌ Missing Neo4j environment variables")

# ---- Official Driver (for health checks, startup/shutdown) ----
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ---- Neomodel OOP ORM ----
encoded_password = quote_plus(NEO4J_PASSWORD)
host = NEO4J_URI.split("://")[1]  # strip scheme (e.g. b0f67d69.databases.neo4j.io)

config.DATABASE_URL = f"bolt+s://{NEO4J_USER}:{encoded_password}@{host}:7687"
config.DATABASE_NAME = NEO4J_DATABASE  # ✅ set DB explicitly

print(f"[ℹ️] Neomodel DATABASE_URL set to: {config.DATABASE_URL}")
print(f"[ℹ️] Using Neo4j database: {config.DATABASE_NAME}")
