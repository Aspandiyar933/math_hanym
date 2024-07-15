from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import tempfile
import os
import subprocess
import uuid
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError


server = Flask(__name__)

connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
container_name = 'manim-animations'

blob_service_client = BlobServiceClient.from_connection_string(connection_string)

try:
    blob_service_client.create_container(container_name)
except ResourceExistsError:
    pass


@server.route('/video-rendering', methods=['POST'])
def run_manim():
    manim_code = request.json.get('code')
    if not manim_code:
        return jsonify({"error":"No Manim code provided"}), 400
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(manim_code)
            temp_file_path = temp_file.name

        output_dir = '/app/output/'
        command = f"manim -qm -o {output_dir} {temp_file_path}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({"error": "Manim execution failed", "details": result.stderr}), 500

        video_file = next((f for f in os.listdir(output_dir) if f.endswith('.mp4')), None)

        if not video_file:
            return jsonify({"error":"No output video found"}), 500
        
        video_path = os.path.join(output_dir, video_file)
        blob_name = f"{uuid.uuid4()}.mp4"
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        with open(video_path, "rb") as data:
            blob_client.upload_blob(data)

        sas_url = blob_client.url + blob_client.generate_sas(
            permission="r",
            expiry=datetime.utcnow() + timedelta(hours=1)
        )

        return jsonify({
            "message": "Manim code executed successfully",
            "output": result.stdout,
            "video_url": sas_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up temporary files
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000)
                     