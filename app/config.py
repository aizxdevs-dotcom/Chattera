import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from neomodel import config as neomodel_config, db
from neo4j import GraphDatabase
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from redis.asyncio import Redis   # async Redis for presence tracking

# =========================================================
#  Environment setup
# =========================================================
load_dotenv()

# =========================================================
#  Neo4j configuration
# =========================================================
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise ValueError("❌ Missing Neo4j environment variables")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def query(self, query, parameters=None):
        with self._driver.session() as session:
            return session.run(query, parameters)

neo4j_conn = Neo4jConnection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

encoded_password = quote_plus(NEO4J_PASSWORD)
host = NEO4J_URI.split("://")[1]
neomodel_config.DATABASE_URL = f"bolt+s://{NEO4J_USER}:{encoded_password}@{host}"
neomodel_config.DATABASE_NAME = NEO4J_DATABASE

print(f"[ℹ️] Neomodel connected → {neomodel_config.DATABASE_URL}")
print(f"[ℹ️] Using database     → {NEO4J_DATABASE}")

# =========================================================
#  Redis configuration  (non‑TLS by default)
# =========================================================
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 13027))
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"

# Create placeholder; FastAPI sets it on startup
redis_client: Redis | None = None

# =========================================================
#  Email / SMTP configuration
# =========================================================
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Soceyo")

if not SMTP_USERNAME or not SMTP_PASSWORD:
    print("⚠️ Warning: SMTP credentials not configured. Email features will not work.")

# =========================================================
#  JWT helpers
# =========================================================
SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32).hex()
ALGORITHM = "HS256"
ISSUER = "chattera-backend"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token issuer")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expired",
                            headers={"WWW-Authenticate": "Bearer"})
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or malformed token",
                            headers={"WWW-Authenticate": "Bearer"})

# =========================================================
#  Neo4j constraints and reconnection
# =========================================================
def setup_constraints():
    db.cypher_query("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")
    db.cypher_query("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")

def reconnect_to_db():
    try:
        db.set_connection(neomodel_config.DATABASE_URL)
        print("[✅] Database reconnected successfully")
    except Exception as e:
        print(f"[❌] Database reconnection failed: {e}")

setup_constraints()
reconnect_to_db()