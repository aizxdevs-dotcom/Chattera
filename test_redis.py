import os
from dotenv import load_dotenv
import redis

# Load variables from .env file
load_dotenv()

host = os.getenv("REDIS_HOST")
port = int(os.getenv("REDIS_PORT", 13027))
username = os.getenv("REDIS_USERNAME", "default")
password = os.getenv("REDIS_PASSWORD", "")

r = redis.Redis(
    host=host,
    port=port,
    username=username,
    password=password,
    decode_responses=True,
    ssl=False,   
)

r.set("foo", "bar")
print(r.get("foo"))