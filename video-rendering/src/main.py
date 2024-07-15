from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import tempfile
import os
import subprocess
import uuid
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from rq import Queue, Connection, Worker
from redis import Redis
import json
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)

# Redis connection
redis_conn = Redis(host='localhost', port=6379)

# Azure Blob Storage setup
connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
container_name = 'manim-animations'
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

try:
    blob_service_client.create_container(container_name)
except ResourceExistsError:
    pass

# Function to process Manim code
def process_manim_code(code):
    if not code:
        raise ValueError("No Manim code provided")
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        output_dir = tempfile.mkdtemp()
        command = f"manim -qm -o {output_dir} {temp_file_path}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Manim execution failed: {result.stderr}")

        video_file = next((f for f in os.listdir(output_dir) if f.endswith('.mp4')), None)

        if not video_file:
            raise FileNotFoundError("No output video found")
        
        video_path = os.path.join(output_dir, video_file)
        blob_name = f"{uuid.uuid4()}.mp4"
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        with open(video_path, "rb") as data:
            blob_client.upload_blob(data)

        sas_url = blob_client.url + blob_client.generate_sas(
            permission="r",
            expiry=datetime.utcnow() + timedelta(hours=1)
        )

        return {
            "message": "Manim code executed successfully",
            "output": result.stdout,
            "video_url": sas_url
        }

    finally:
        # Clean up temporary files
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))
        os.rmdir(output_dir)

# Worker function to handle jobs
def handle_job(job):
    code = job.args[0]
    return process_manim_code(code['code'])

@app.route('/')
def index():
    return "Subscriber is running and listening to the queue."

if __name__ == '__main__':
    with Connection(redis_conn):
        queue = Queue('manim-queue', connection=redis_conn)
        worker = Worker([queue], connection=redis_conn)
        worker.push_exc_handler(handle_job)
        worker.work()

    app.run(host='0.0.0.0', port=5000)
