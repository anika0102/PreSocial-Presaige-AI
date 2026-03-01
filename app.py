# app.py

import os
import time
import json
from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv
from nlp_engine import extract_keywords, compute_trend_alignment, generate_trend_recommendation
from ai_rewriter import build_rewrite_prompt, rewrite_with_openai

# Load environment variables
load_dotenv()

print("Loaded Key:", os.getenv("PRESAIGE_API_KEY"))

# Create Flask app BEFORE routes
app = Flask(__name__, static_folder="static", template_folder="templates")

PRESAIGE_BASE = "https://api.presaige.ai/v1"
PRESAIGE_KEY = os.getenv("PRESAIGE_API_KEY")

if not PRESAIGE_KEY:
    raise Exception("Set PRESAIGE_API_KEY in your .env file")

HEADERS = {
    "x-api-key": PRESAIGE_KEY,
    "Content-Type": "application/json"
}

# --------------------------------------------------
# Poll Presaige Async Job
# --------------------------------------------------
def poll_presaige(poll_path: str, timeout: int = 120):

    if poll_path.startswith("/"):
        url = PRESAIGE_BASE + poll_path
    elif poll_path.startswith("http"):
        url = poll_path
    else:
        url = PRESAIGE_BASE + "/" + poll_path

    start = time.time()

    while True:
        r = requests.get(url, headers={"x-api-key": PRESAIGE_KEY})

        if r.status_code != 200:
            raise Exception(f"Presaige returned {r.status_code}: {r.text}")

        data = r.json()
        status = data.get("status")

        if status == "complete":
            return data

        if status == "failed":
            raise Exception(f"Presaige job failed: {json.dumps(data)}")

        if time.time() - start > timeout:
            raise Exception("Polling timeout")

        time.sleep(2)


# --------------------------------------------------
# Home Route
# --------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# --------------------------------------------------
# Request Signed Upload URL
# --------------------------------------------------
@app.route("/api/request-upload", methods=["POST"])
def request_upload():
    data = request.get_json()

    body = {
        "filename": data.get("filename"),
        "content_type": data.get("content_type")
    }

    resp = requests.post(
        f"{PRESAIGE_BASE}/upload",
        headers=HEADERS,
        json=body
    )

    if resp.status_code not in (200, 201):
        return jsonify({"error": "Upload URL request failed", "details": resp.text}), 500

    return jsonify(resp.json())


# --------------------------------------------------
# Upload File THROUGH Backend (No CORS, No Headers)
# --------------------------------------------------
@app.route("/api/upload-file", methods=["POST"])
def upload_file_backend():

    upload_url = request.form.get("upload_url")
    file = request.files.get("file")

    if not upload_url or not file:
        return jsonify({"error": "Missing upload_url or file"}), 400

    try:
        # 🚀 IMPORTANT: DO NOT SEND HEADERS
        resp = requests.put(
            upload_url,
            data=file.read()
        )

        print("Upload status:", resp.status_code)
        print("Upload response:", resp.text)

        if resp.status_code not in (200, 201):
            return jsonify({
                "error": "Upload to signed URL failed",
                "details": resp.text
            }), 500

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# Analyze Content
# --------------------------------------------------
@app.route("/api/analyze", methods=["POST"])
def analyze():

    data = request.get_json()
    asset_key = data.get("asset_key")
    use_generate = data.get("use_generate", True)

    if not asset_key:
        return jsonify({"error": "asset_key required"}), 400

    # 1️⃣ Score
    score_resp = requests.post(
        f"{PRESAIGE_BASE}/score",
        headers=HEADERS,
        json={"asset_key": asset_key, "extended": True}
    )

    if score_resp.status_code not in (200, 201):
        return jsonify({"error": "Score request failed", "details": score_resp.text}), 500

    score_job = score_resp.json()
    score_result = poll_presaige(score_job.get("poll_url"))

    # 2️⃣ Recommendations
    rec_resp = requests.post(
        f"{PRESAIGE_BASE}/recommendations",
        headers=HEADERS,
        json={"asset_key": asset_key}
    )

    if rec_resp.status_code not in (200, 201):
        return jsonify({"error": "Recommendations request failed", "details": rec_resp.text}), 500

    rec_job = rec_resp.json()
    rec_result = poll_presaige(rec_job.get("poll_url"))

    # 3️⃣ NLP
    rec_obj = rec_result.get("result", {})
    recommendation_text = json.dumps(rec_obj)

    keywords = extract_keywords(recommendation_text)
    alignment_score, matched = compute_trend_alignment(keywords)
    trend_advice = generate_trend_recommendation(alignment_score, matched)

    # 4️⃣ GPT (Optional)
    ai_output = None
    if use_generate:
        prompt = build_rewrite_prompt(
            score_result.get("scores", {}),
            recommendation_text,
            {
                "alignment_score": alignment_score,
                "matched_trends": matched,
                "advice": trend_advice
            }
        )

        try:
            ai_output = rewrite_with_openai(prompt)
        except Exception as e:
            ai_output = {"error": str(e)}

    return jsonify({
        "scores": score_result,
        "recommendations": rec_result,
        "keywords": keywords,
        "trend_alignment_percentage": alignment_score,
        "matched_trends": matched,
        "trend_advice": trend_advice,
        "ai_rewrite": ai_output
    })


# --------------------------------------------------
# Run App
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)