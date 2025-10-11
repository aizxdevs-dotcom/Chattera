from fastapi import FastAPI
from neo4j.exceptions import AuthError, ServiceUnavailable
from app.config import (
    driver,
    Redis, redis_client,
    REDIS_HOST, REDIS_PORT, REDIS_USERNAME, REDIS_PASSWORD, REDIS_SSL,
)
from app.routers import (
    user, conversation, message, file,
    post, reaction, comment,
    invitation, contact, presence
)
from fastapi.middleware.cors import CORSMiddleware
from app.routers import notification
from app.routers import ws_chat



app = FastAPI(title="Soceyo")

origins = [
    "http://localhost:3000",
    "https://soceyo.vercel.app",
    "https://soceyo.onrender.com", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ——— Routers ———
app.include_router(user.router, prefix="/api")
app.include_router(conversation.router, prefix="/api")
app.include_router(message.router, prefix="/api")
app.include_router(file.router, prefix="/api")
app.include_router(invitation.router, prefix="/api")
app.include_router(contact.router, prefix="/api")
app.include_router(post.router, prefix="/api")
app.include_router(reaction.router, prefix="/api")
app.include_router(comment.router, prefix="/api")
app.include_router(presence.router, prefix="/api")
app.include_router(notification.router, prefix="/api")
app.include_router(ws_chat.router)


# ——— Startup / Shutdown ———
@app.on_event("startup")
def startup_db_check():
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        print("[✅] Official driver connected to Neo4j successfully!")
    except AuthError:
        print("[❌] Authentication failed. Check NEO4J_USER / NEO4J_PASSWORD .env")
        raise
    except ServiceUnavailable:
        print("[❌] Cannot connect to Neo4j Aura. Check NEO4J_URI and internet.")
        raise
    except Exception as e:
        print(f"[❌] Unexpected Neo4j error: {e}")
        raise

@app.on_event("startup")
async def connect_redis():
    from app import config
    config.redis_client = Redis(
        host=REDIS_HOST, port=REDIS_PORT,
        username=REDIS_USERNAME, password=REDIS_PASSWORD,
        ssl=REDIS_SSL,
        decode_responses=True,
    )
    try:
        pong = await config.redis_client.ping()
        print(f"[✅] Redis connected (PING → {pong})")
    except Exception as e:
        print(f"[❌] Redis connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_connections():
    from app import config
    if config.redis_client:
        await config.redis_client.close()
        print("[ℹ️] Redis connection closed.")
    driver.close()
    print("[ℹ️] Official driver connection closed.")