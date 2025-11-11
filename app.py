from flask import Flask, request, jsonify
import os
import base64
from datetime import datetime

# === Flask Setup ===
app = Flask(__name__)

# ✅ Save folder (auto-creates subfolder by date)
ROOT_SAVE = r"C:\Users\HP\Desktop\pyth"
os.makedirs(ROOT_SAVE, exist_ok=True)

# ✅ Helper: create daily subfolder
def get_save_folder():
    today = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(ROOT_SAVE, today)
    os.makedirs(folder, exist_ok=True)
    return folder

# === Route: Upload photo (Base64 or multipart) ===
@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    try:
        # 📦 Case 1: JSON base64 upload
        if request.is_json:
            data = request.get_json()
            filename = data.get("filename") or f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
            img_data = data.get("data")
            if not img_data:
                return jsonify({"error": "Missing image data"}), 400

            img_bytes = base64.b64decode(img_data)
            folder = get_save_folder()
            path = os.path.join(folder, filename)
            with open(path, "wb") as f:
                f.write(img_bytes)

            print(f"✅ [Base64] Saved: {path}")
            return jsonify({"status": "success", "file": path}), 200

        # 📦 Case 2: multipart/form-data (file upload)
        elif "file" in request.files:
            file = request.files["file"]
            filename = file.filename or f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
            folder = get_save_folder()
            path = os.path.join(folder, filename)
            file.save(path)
            print(f"✅ [Multipart] Saved: {path}")
            return jsonify({"status": "success", "file": path}), 200

        # 🚫 Invalid format
        return jsonify({"error": "Invalid upload format"}), 400

    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return jsonify({"error": str(e)}), 500


# === Route: Receive general text or device info ===
@app.route("/receive_output", methods=["POST"])
def receive_output():
    try:
        text = request.get_data(as_text=True)
        print("=== 📩 Received Text Data ===")
        print(text)
        print("==================================")

        # Save logs to file
        folder = get_save_folder()
        log_file = os.path.join(folder, "received_logs.txt")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")

        return jsonify({"status": "success", "message": "Text received"}), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


# === Health check route ===
@app.route("/", methods=["GET"])
def index():
    return "✅ Flask server running! Use /upload_photo or /receive_output", 200


# === Run the Flask server ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
