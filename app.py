from flask import Flask, request, jsonify
import os
import base64
from datetime import datetime
from supabase import create_client, Client

# === 🧩 Configuration ===
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ayyeebkyroxnvsrfbldm.supabase.co")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "photos")

# Local backup folder (optional)
ROOT_SAVE = r"C:\Users\HP\Desktop\pyth"
os.makedirs(ROOT_SAVE, exist_ok=True)

# Initialize Flask and Supabase
app = Flask(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)


# === Helper: Create daily subfolder for local logs ===
def get_save_folder():
    today = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(ROOT_SAVE, today)
    os.makedirs(folder, exist_ok=True)
    return folder


# === Upload Photo (Base64) ===
@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload received"}), 400

        filename = data.get("filename", f"photo_{datetime.now().strftime('%H%M%S')}.jpg")
        img_data = data.get("data")
        if not img_data:
            return jsonify({"error": "Missing image data"}), 400

        # Decode base64 → bytes
        img_bytes = base64.b64decode(img_data)

        # Create a Supabase path (by date)
        today = datetime.now().strftime("%Y-%m-%d")
        supa_path = f"{today}/{filename}"

        # Upload to Supabase
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(supa_path, img_bytes)

        # Also save locally for backup
        local_folder = get_save_folder()
        local_path = os.path.join(local_folder, filename)
        with open(local_path, "wb") as f:
            f.write(img_bytes)

        # Generate public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{supa_path}"

        print(f"✅ Uploaded: {filename} → {public_url}")
        return jsonify({"status": "success", "url": public_url}), 200

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({"error": str(e)}), 500


# === Receive Text or Device Info ===
@app.route("/receive_output", methods=["POST"])
def receive_output():
    try:
        text = request.get_data(as_text=True)
        print("=== 📩 Received Text Data ===")
        print(text)
        print("==================================")

        # Log to local file
        folder = get_save_folder()
        log_path = os.path.join(folder, "received_logs.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")

        return jsonify({"status": "success", "message": "Text received"}), 200

    except Exception as e:
        print(f"❌ Error receiving text: {e}")
        return jsonify({"error": str(e)}), 500


# === Health Check ===
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "running", "message": "✅ Flask + Supabase connected"}), 200


# === Start the Server ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
