from flask import Flask, request, jsonify
import os
from datetime import datetime
import boto3

# ============================
# ⚠️ CLOUDLFARE R2 CREDENTIALS
# ============================
R2_ACCOUNT_ID = "60c038f2076d034c5b7f26c79e1e5d3d"
R2_ACCESS_KEY_ID = "9a667fbd282cc2c4ce76f5a10ee56788"
R2_SECRET_ACCESS_KEY = "09db609dcfd6cb1916b41af104038ad3842b74750c16f47ded8bdcaf3e3312ba"
R2_BUCKET_NAME = "my-images"

# R2 endpoint
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Public R2 URL (static domain)
PUBLIC_R2_URL = "https://pub-b9adaa800b9d4a67a13dbeae2cdda0c4.r2.dev"

# Local Save Folder
ROOT_SAVE = r"C:\Users\HP\Desktop\pyth"
os.makedirs(ROOT_SAVE, exist_ok=True)

app = Flask(__name__)

# ============================
# R2 CLIENT
# ============================
s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)


# ============================
# Create Per-Day Folder
# ============================
def get_save_folder():
    today = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(ROOT_SAVE, today)
    os.makedirs(folder, exist_ok=True)
    return folder


# ============================
# 1️⃣ UPLOAD PHOTO (RAW FILE)
# ============================
@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    try:
        # React Native sends the field name: "file"
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        filename = file.filename or f"photo_{datetime.now().strftime('%H%M%S')}.jpg"

        # Read binary data
        img_bytes = file.read()

        # Path inside R2 bucket
        today = datetime.now().strftime("%Y-%m-%d")
        r2_path = f"{today}/{filename}"

        # Upload to Cloudflare R2
        s3.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=r2_path,
            Body=img_bytes,
            ContentType="image/jpeg",
            ACL="public-read",
        )

        # Save local copy
        folder = get_save_folder()
        local_path = os.path.join(folder, filename)
        with open(local_path, "wb") as f:
            f.write(img_bytes)

        # Public URL
        public_url = f"{PUBLIC_R2_URL}/{R2_BUCKET_NAME}/{r2_path}"

        print(f"[R2 UPLOAD] → {public_url}")

        return jsonify({"status": "success", "url": public_url})

    except Exception as e:
        print("Photo Upload Error:", e)
        return jsonify({"error": str(e)}), 500


# ==================================
# 2️⃣ RECEIVE TEXT / PROMPT / LOGS
# ==================================
@app.route("/receive_output", methods=["POST"])
def receive_output():
    try:
        text = request.get_data(as_text=True)

        folder = get_save_folder()
        log_path = os.path.join(folder, "received_logs.txt")

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")

        print(f"[LOG] {text}")

        return jsonify({"status": "success", "message": "Logged"})

    except Exception as e:
        print("Log Error:", e)
        return jsonify({"error": str(e)}), 500


# ============================
# 3️⃣ HEALTH CHECK
# ============================
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "message": "Flask + Cloudflare R2 Active",
        "time": datetime.now().strftime("%H:%M:%S")
    })


# ============================
# START SERVER
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
