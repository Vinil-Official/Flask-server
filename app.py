from flask import Flask, request, jsonify
import base64
from datetime import datetime
import boto3

# === Cloudflare R2 Credentials ===
R2_ACCOUNT_ID = "sLArTpRwbB62toF371Y7gzABNN7oTVZCl6hwmw-e"
R2_ACCESS_KEY_ID = "9a667fbd282cc2c4ce76f5a10ee56788"
R2_SECRET_ACCESS_KEY = "09db609dcfd6cb1916b41af104038ad3842b74750c16f47ded8bdcaf3e3312ba"
R2_BUCKET_NAME = "my-images"

# R2 endpoint (S3-compatible)
R2_ENDPOINT = f"https://60c038f2076d034c5b7f26c79e1e5d3d.r2.cloudflarestorage.com/my-images
"

app = Flask(__name__)

# Initialize the S3 client for Cloudflare R2
s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY
)

@app.route("/upload_r2", methods=["POST"])
def upload_r2():
    try:
        data = request.get_json()

        filename = data.get("filename", f"img_{datetime.now().strftime('%H%M%S')}.jpg")
        img_base64 = data.get("data")

        if not img_base64:
            return jsonify({"error": "Missing image data"}), 400

        # Decode Base64 image → bytes
        img_bytes = base64.b64decode(img_base64)

        # Create folder based on date
        today = datetime.now().strftime("%Y-%m-%d")
        r2_path = f"{today}/{filename}"

        # Upload to R2 bucket
        s3.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=r2_path,
            Body=img_bytes,
            ContentType="image/jpeg",
            ACL="public-read"
        )

        # Public URL
        file_url = f"{R2_ENDPOINT}/{R2_BUCKET_NAME}/{r2_path}"

        return jsonify({
            "status": "success",
            "url": file_url,
            "bucket": R2_BUCKET_NAME
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "R2 Upload API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
