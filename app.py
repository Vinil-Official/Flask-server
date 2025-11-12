from flask import Flask, request, jsonify
import os, base64
from datetime import datetime
from io import BytesIO
from supabase import create_client, Client

# ==========================================================
# 🔧 Load environment variables (edit .env file or Render vars)
# ==========================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ayyeebkyroxnvsrfbldm.supabase.co")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF5eWVlYmt5cm94bnZzcmZibGRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjgzNjY0MSwiZXhwIjoyMDc4NDEyNjQxfQ.73UigmrHfsanehPPAIdDjN2BcEdEaCEOdRkLxqyxkC8")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "photos")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# ==========================================================
# 🧠 Flask setup
# ==========================================================
app = Flask(__name__)

# ✅ Optional local backup folder
ROOT_SAVE = r"C:\Users\HP\Desktop\pyth"
os.makedirs(ROOT_SAVE, exist_ok=True)

def get_save_folder():
    """Create a daily subfolder for local backups"""
    today = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(ROOT_SAVE, today)
    os.makedirs(folder, exist_ok=True)
    return folder


# ==========================================================
# ☁️ Supabase Upload Helper
# ==========================================================
def upload_to_supabase(image_bytes: bytes, filename: str) -> str:
    """Uploads an image to Supabase Storage and returns its public URL"""
    day = datetime.now().strftime("%Y-%m-%d")
    storage_path = f"uploads/{day}/{filename}"

    file_obj = BytesIO(image_bytes)
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        storage_path,
        file_obj,
        file_options={"content-type": "image/jpeg", "upsert": "true"},
    )

    # Get public URL (if bucket is public)
    public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
    return public_url


# ==========================================================
# 📤 Endpoint: Upload Photo (Base64 or Multipart)
# ==========================================================
@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    try:
        # --- Case 1: JSON base64 ---
        if request.is_json:
            data = request.get_json()
            filename = data.get("filename", f"photo_{datetime.now().strftime('%H%M%S')}.jpg")
            img_b64 = data.get("data")
            if not img_b64:
                return jsonify({"error": "Missing image data"}), 400

            img_bytes = base64.b64decode(img_b64)

            # Save locally (optional)
            folder = get_save_folder()
            local_path = os.path.join(folder, filename)
            with open(local_path, "wb") as f:
                f.write(img_bytes)

            # Upload to Supabase
            public_url = upload_to_supabase(img_bytes, filename)
            print(f"✅ Uploaded → {public_url}")

            return jsonify({"status": "success", "url": public_url}), 200

        # --- Case 2: Multipart file upload ---
        elif "file" in request.files:
            file = request.files["file"]
            filename = file.filename or f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
            img_bytes = file.read()

            folder = get_save_folder()
            local_path = os.path.join(folder, filename)
            with open(local_path, "wb") as f:
                f.write(img_bytes)

            public_url = upload_to_supabase(img_bytes, filename)
            print(f"✅ Uploaded → {public_url}")

            return jsonify({"status": "success", "url": public_url}), 200

        # --- Invalid format ---
        return jsonify({"error": "Invalid upload format"}), 400

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({"error": str(e)}), 500


# ==========================================================
# 📨 Endpoint: Receive general text / device info
# ==========================================================
@app.route("/receive_output", methods=["POST"])
def receive_output():
    try:
        text = request.get_data(as_text=True)
        print("=== 📩 Received Text Data ===")
        print(text)
        print("==================================")

        # Save logs locally
        folder = get_save_folder()
        log_file = os.path.join(folder, "received_logs.txt")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")

        return jsonify({"status": "success", "message": "Text received"}), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


# ==========================================================
# 🏠 Home Route (Health Check)
# ==========================================================
@app.route("/", methods=["GET"])
def home():
    return "✅ Flask + Supabase server running! Use /upload_photo or /receive_output", 200


# ==========================================================
# 🚀 Run the Server
# ==========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
