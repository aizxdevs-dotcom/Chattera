import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from neomodel import config, db
from neo4j import GraphDatabase
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")       
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE") 

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise ValueError("❌ Missing Neo4j environment variables")


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


encoded_password = quote_plus(NEO4J_PASSWORD)
host = NEO4J_URI.split("://")[1] 

config.DATABASE_URL = f"bolt+s://{NEO4J_USER}:{encoded_password}@{host}:7687"
config.DATABASE_NAME = NEO4J_DATABASE 

print(f"[ℹ️] Neomodel DATABASE_URL set to: {config.DATABASE_URL}")
print(f"[ℹ️] Using Neo4j database: {config.DATABASE_NAME}")

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def query(self, query, parameters=None):
        with self._driver.session() as session:
            return session.run(query, parameters)

# Neo4j Aura connection details
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

neo4j_conn = Neo4jConnection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def setup_constraints():
    db.cypher_query("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")
    db.cypher_query("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")

# Reconnect to the database on startup
def reconnect_to_db():
    db.set_connection(config.DATABASE_URL)

setup_constraints()
reconnect_to_db()
