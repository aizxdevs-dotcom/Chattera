import boto3
import os
from dotenv import load_dotenv

# load .env file
load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

bucket = os.getenv("AWS_BUCKET_NAME")
file_name = "hello.txt"

# create a small test file
with open(file_name, "w") as f:
    f.write("Hello from FastAPI + AWS S3!")

# upload it to your bucket
s3.upload_file(file_name, bucket, file_name)

print(f"✅ Uploaded {file_name} to bucket {bucket}")