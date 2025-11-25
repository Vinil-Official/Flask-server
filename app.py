from flask import Flask, request, jsonify
import os
import base64
from datetime import datetime
import boto3

# === Cloudflare R2 Credentials ===
R2_ACCOUNT_ID = "60c038f2076d034c5b7f26c79e1e5d3d"
R2_ACCESS_KEY_ID = "9a667fbd282cc2c4ce76f5a10ee56788"
R2_SECRET_ACCESS_KEY = "09db609dcfd6cb1916b41af104038ad3842b74750c16f47ded8bdcaf3e3312ba"
R2_BUCKET_NAME = "my-images"

# R2 S3 endpoint (DO NOT include bucket name)
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Public Development URL (for browser images)
PUBLIC_R2_URL = "https://pub-b9adaa800b9d4a67a13dbeae2cdda0c4.r2.dev"

# Local backup folder
ROOT_SAVE = r"C:\Users\HP\Desktop\pyth"
os.makedirs(ROOT_SAVE, exist_ok=True)

# Flask app
app = Flask(__name__)

# Initialize R2 S3 client
s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY
)


# === Create daily folder ===
def get_save_folder():
    today = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(ROOT_SAVE, today)
    os.makedirs(folder, exist_ok=True)
    return folder


# === Upload Image to Cloudflare R2 ===
@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload"}), 400

        filename = data.get(
            "filename",
            f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
        )
        img_data = data.get("data")

        if not img_data:
            return jsonify({"error": "Missing image data"}), 400

        # base64 → bytes
        img_bytes = base64.b64decode(img_data)

        # Path inside bucket
        today = datetime.now().strftime("%Y-%m-%d")
        r2_path = f"{today}/{filename}"

        # Upload to Cloudflare R2
        s3.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=r2_path,
            Body=img_bytes,
            ContentType="image/jpeg",
            ACL="public-read"
        )

        # Local backup
        local_folder = get_save_folder()
        with open(os.path.join(local_folder, filename), "wb") as f:
            f.write(img_bytes)

        # Public accessible URL
        public_url = f"{PUBLIC_R2_URL}/{R2_BUCKET_NAME}/{r2_path}"

        return jsonify({
            "status": "success",
            "url": public_url,
            "bucket": R2_BUCKET_NAME
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Save device text logs ===
@app.route("/receive_output", methods=["POST"])
def receive_output():
    try:
        text = request.get_data(as_text=True)

        folder = get_save_folder()
        log_path = os.path.join(folder, "received_logs.txt")

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")

        return jsonify({"status": "success", "message": "Logged"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Health Check ===
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "message": "Flask + Cloudflare R2 Active"
    })


# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
