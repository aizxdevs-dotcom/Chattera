from fastapi import FastAPI
from neo4j.exceptions import AuthError, ServiceUnavailable
from app.config import driver  # official driver
from app.routers import user, conversation, message, file, post, reaction, comment # your routes
from app.routers import invitation, contact


app = FastAPI(title="Chattera")

# Register routers
app.include_router(user.router)
app.include_router(conversation.router)
app.include_router(message.router)
app.include_router(file.router)
app.include_router(invitation.router)
app.include_router(contact.router)
app.include_router(post.router)
app.include_router(reaction.router)   # 🆕
app.include_router(comment.router)

@app.on_event("startup")
def startup_db_check():
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        print("[✅] Official driver connected to Neo4j successfully!")
    except AuthError:
        print("[❌] Authentication failed. Check NEO4J_USER / NEO4J_PASSWORD in .env")
        raise
    except ServiceUnavailable:
        print("[❌] Cannot connect to Neo4j Aura. Check NEO4J_URI and internet.")
        raise
    except Exception as e:
        print(f"[❌] Unexpected Neo4j error: {e}")
        raise

@app.on_event("shutdown")
def shutdown_db_connection():
    driver.close()
    print("[ℹ️] Official driver connection closed.")
