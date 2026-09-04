import os
import sys
import traceback
import cv2
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Support running from project root (gunicorn/Railway) or inside backend/
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from subtitle_parser import parse_srt
from dialogue_matcher import match_dialogue_to_characters
from character_detector import track_characters
from death_engine import (
    analyze_dialogue,
    calculate_character_risk,
    add_screen_time_score,
    generate_final_results
)

# ==========================================
# CONFIGURATION & PATHS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
CHAR_IMG_DIR = os.path.join(UPLOAD_FOLDER, "characters")
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHAR_IMG_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR)
# Allow all origins so the Vercel frontend can call this Railway backend
CORS(app, origins="*")


# ==========================================
# STATIC FILE SERVING
# ==========================================
@app.route("/")
def index():
    if os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"status": "Death Predictor backend is running", "endpoints": ["/analyze", "/samples"]})


@app.route("/<path:path>")
def serve_frontend_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"error": "Not found"}), 404


@app.route("/character_image/<filename>")
def get_character_image(filename):
    return send_from_directory(CHAR_IMG_DIR, filename)


@app.route("/uploads/<path:filename>")
def get_uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ==========================================
# SAMPLES ENDPOINT
# ==========================================
@app.route("/samples", methods=["GET"])
def get_samples():
    samples = [
        {
            "id": "spiderman",
            "title": "Spider-Man 2: The Clock Tower Climax",
            "video_file": "The.Amazing.Spiderman.2.2014.[@UCParadiso].720p.BluRay - Trim.mp4",
            "subtitle_file": "subtitle.srt",
            "description": "Peter Parker battles Harry Osborn inside the clock tower while Gwen Stacy's fate hangs in the balance."
        },
        {
            "id": "drishyam",
            "title": "Drishyam: Suspense Thriller Clip",
            "video_file": "Drishyam (2013) BR-RIP x264  400MB @stamssl - Trim.mp4",
            "subtitle_file": None,
            "description": "High-stakes police investigation drama clip without external subtitles."
        }
    ]

    # Filter to only existing files
    available = []
    for s in samples:
        vpath = os.path.join(UPLOAD_FOLDER, s["video_file"])
        if os.path.exists(vpath):
            available.append(s)

    return jsonify({"success": True, "samples": available})


# ==========================================
# VIDEO ANALYSIS PIPELINE
# ==========================================
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        sample_id = request.form.get("sample_id")
        video_path = None
        subtitle_path = None
        video_name = ""

        # Case 1: Pre-loaded sample selected
        if sample_id == "spiderman":
            video_name = "The.Amazing.Spiderman.2.2014.[@UCParadiso].720p.BluRay - Trim.mp4"
            video_path = os.path.join(UPLOAD_FOLDER, video_name)
            subtitle_path = os.path.join(UPLOAD_FOLDER, "subtitle.srt")
        elif sample_id == "drishyam":
            video_name = "Drishyam (2013) BR-RIP x264  400MB @stamssl - Trim.mp4"
            video_path = os.path.join(UPLOAD_FOLDER, video_name)

        # Case 2: Direct file upload
        if not video_path:
            if "video" not in request.files or request.files["video"].filename == "":
                return jsonify({"success": False, "error": "No video file provided"}), 400

            video_file = request.files["video"]
            video_name = video_file.filename
            video_path = os.path.join(UPLOAD_FOLDER, video_name)
            video_file.save(video_path)

            if "subtitle" in request.files and request.files["subtitle"].filename != "":
                sub_file = request.files["subtitle"]
                subtitle_path = os.path.join(UPLOAD_FOLDER, sub_file.filename)
                sub_file.save(subtitle_path)

        print()
        print("=" * 50)
        print(f"[Backend] Starting Analysis for: {video_name}")
        print("=" * 50)

        # Step 1: Video properties
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        video_duration = round(frame_count / fps, 2) if fps > 0 else 0
        cap.release()

        print(f"[Backend] Video FPS: {fps:.2f} | Frames: {int(frame_count)} | Duration: {video_duration}s")

        # Step 2: Character Tracking & Cropping
        character_data = track_characters(video_path)
        print(f"[Backend] Character tracking finished: {len(character_data)} characters detected.")

        # Step 3: Subtitle Parsing
        subtitle_data = []
        if subtitle_path and os.path.exists(subtitle_path):
            subtitle_data = parse_srt(subtitle_path)
            print(f"[Backend] Parsed {len(subtitle_data)} subtitles.")
        else:
            print("[Backend] No subtitle file provided. Proceeding with video presence analysis.")

        # Step 4: Dialogue Matching
        dialogue_matches = match_dialogue_to_characters(
            subtitle_data,
            character_data,
            fps=fps,
            video_duration=video_duration
        )

        # Step 5: Death Trope Risk Calculation
        character_risk = calculate_character_risk(character_data, dialogue_matches)

        # Step 6: Screen Presence Score
        character_risk = add_screen_time_score(character_data, character_risk)

        # Step 7: Final Cinematic Results & Verdict
        analysis_package = generate_final_results(character_risk, character_data)

        # Video stream url
        video_url = f"/uploads/{os.path.basename(video_path)}"

        return jsonify({
            "success": True,
            "message": "Analysis completed successfully",
            "filename": video_name,
            "video_url": video_url,
            "duration": video_duration,
            "character_count": len(character_data),
            "characters": character_data,
            "dialogue": dialogue_matches,
            "results": analysis_package["characters"],
            "verdict": analysis_package["verdict"]
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


# ==========================================
# SERVER STARTUP
# ==========================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    print()
    print("=" * 50)
    print("   DEATH PREDICTOR AI - BACKEND SERVER")
    print(f"   Running on http://{host}:{port}")
    print("=" * 50)
    app.run(host=host, port=port, debug=False)
