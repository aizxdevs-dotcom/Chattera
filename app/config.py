import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from neomodel import config, db
from neo4j import GraphDatabase
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status

# Load env vars (works locally if .env exists, ignored in Render if not provided)
load_dotenv()

# Required Neo4j env vars
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")  # Aura default DB name

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise ValueError("❌ Missing Neo4j environment variables")

# Neo4j Driver connection
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# -------------------------------
# Legacy connection wrapper (for CRUD code)
# -------------------------------
class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def query(self, query, parameters=None):
        with self._driver.session() as session:
            return session.run(query, parameters)

# Exportable connection (import this in CRUD files: from app.config import neo4j_conn)
neo4j_conn = Neo4jConnection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

# -------------------------------
# Configure Neomodel connection
# -------------------------------
encoded_password = quote_plus(NEO4J_PASSWORD)
host = NEO4J_URI.split("://")[1]  # Extract host part only
config.DATABASE_URL = f"bolt+s://{NEO4J_USER}:{encoded_password}@{host}"
config.DATABASE_NAME = NEO4J_DATABASE

print(f"[ℹ️] Neomodel DATABASE_URL set to: {config.DATABASE_URL}")
print(f"[ℹ️] Using Neo4j database: {config.DATABASE_NAME}")

# -------------------------------
# JWT Authentication
# -------------------------------
SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32).hex() 
ALGORITHM = "HS256"
ISSUER = "chattera-backend" 
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iss": ISSUER})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iss": ISSUER})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str):
    """Verify JWT token and return payload (raises if invalid or expired)."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iss"]},
        )
        if payload.get("iss") != ISSUER:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )
# -------------------------------
# Neo4j constraints
# -------------------------------
def setup_constraints():
    db.cypher_query("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")
    db.cypher_query("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")

# Ensure connection on startup
def reconnect_to_db():
    try:
        db.set_connection(config.DATABASE_URL)
        print("[✅] Database reconnected successfully")
    except Exception as e:
        print(f"[❌] Database reconnection failed: {e}")

# Run startup tasks
setup_constraints()
reconnect_to_db()
