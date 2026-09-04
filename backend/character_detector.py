import os
import cv2
import time
import numpy as np
import torch
from ultralytics import YOLO

# Utilize all available CPU threads
torch.set_num_threads(os.cpu_count() or 4)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "yolo11n.pt")
CHAR_IMG_DIR = os.path.join(BASE_DIR, "uploads", "characters")
os.makedirs(CHAR_IMG_DIR, exist_ok=True)

# Preload YOLO model
model = YOLO(MODEL_PATH)


def box_iou(b1, b2):
    """Compute Intersection over Union between two bounding boxes [x1, y1, x2, y2]."""
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0


def track_characters(video_path):
    t_start = time.time()
    print("\n[UltraFast Vision AI] Commencing accelerated scene analysis...")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return {}

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    video_dur = total_frames / fps if fps > 0 else 0

    # Dynamic adaptive sampling: cap max sampled frames at 80-90 for guaranteed sub-10s analysis
    target_samples = min(90, max(25, int(video_dur * 1.1)))
    stride = max(1, int(total_frames / target_samples)) if target_samples > 0 else int(fps)

    print(f"[UltraFast Vision AI] FPS: {fps:.1f} | Duration: {video_dur:.1f}s | Stride: {stride} frames (Sampling ~{total_frames // stride} keyframes)")

    # Phase 1: High-Speed Keyframe Extraction (Sub-4 seconds)
    frames = []
    timestamps = []
    t_read_start = time.time()

    if stride > 150:
        # Long video (> 60s clips / full movies): Direct millisecond seeks
        print(f"[UltraFast Vision AI] Long video detected. Using direct timestamp seeks...")
        for i in range(target_samples):
            t_sec = round((i * stride) / fps, 2)
            if t_sec > video_dur:
                break
            cap.set(cv2.CAP_PROP_POS_MSEC, t_sec * 1000)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                timestamps.append(t_sec)
    else:
        # Short/medium scenes: Sequential demux grab skipping
        idx = 0
        while True:
            if idx % stride == 0:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
                timestamps.append(round(idx / fps, 2))
            else:
                ret = cap.grab()
                if not ret:
                    break
            idx += 1
    cap.release()
    print(f"[UltraFast Vision AI] Grabbed {len(frames)} keyframes in {time.time() - t_read_start:.2f}s")

    if not frames:
        return {}

    # Phase 2: High-Speed Batched Neural Inference (batch=16, imgsz=320)
    t_infer_start = time.time()
    detections = model.predict(
        source=frames,
        classes=[0],
        imgsz=320,
        batch=16,
        verbose=False
    )
    print(f"[UltraFast Vision AI] Neural inference complete in {time.time() - t_infer_start:.2f}s")

    # Phase 3: Microsecond Spatial IoU Tracking & Portrait Cropping
    t_track_start = time.time()
    next_id = 1
    active_tracks = {}  # tid -> last_box
    raw_tracks = {}

    for frame, t_sec, det in zip(frames, timestamps, detections):
        if det.boxes is None or len(det.boxes) == 0:
            continue

        boxes = det.boxes.xyxy.cpu().numpy()
        matched_tids = set()

        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            w, h = x2 - x1, y2 - y1
            if w < 20 or h < 30:
                continue

            best_iou = 0.18
            best_tid = None

            for tid, last_box in active_tracks.items():
                if tid in matched_tids:
                    continue
                iou = box_iou(box, last_box)
                if iou > best_iou:
                    best_iou = iou
                    best_tid = tid

            if best_tid is None:
                best_tid = next_id
                next_id += 1
                raw_tracks[best_tid] = {
                    "count": 0,
                    "timestamps": [],
                    "best_crop": None,
                    "best_area": 0
                }

            matched_tids.add(best_tid)
            active_tracks[best_tid] = box
            track_info = raw_tracks[best_tid]
            track_info["count"] += 1
            track_info["timestamps"].append(t_sec)

            # Crop best portrait
            area = w * h
            if area > track_info["best_area"] and frame is not None:
                pad_y = int(h * 0.05)
                pad_x = int(w * 0.05)
                h_img, w_img = frame.shape[:2]
                cy1 = max(0, y1 - pad_y)
                cy2 = min(h_img, y2 + pad_y)
                cx1 = max(0, x1 - pad_x)
                cx2 = min(w_img, x2 + pad_x)

                crop = frame[cy1:cy2, cx1:cx2]
                if crop.size > 0 and crop.shape[0] > 40 and crop.shape[1] > 30:
                    track_info["best_crop"] = crop
                    track_info["best_area"] = area

    print(f"[UltraFast Vision AI] Tracking finished in {time.time() - t_track_start:.2f}s | Raw tracks: {len(raw_tracks)}")

    # Phase 4: Noise Filtering & Primary Cast Selection
    valid_tracks = {tid: t for tid, t in raw_tracks.items() if t["count"] >= 2}
    if not valid_tracks and raw_tracks:
        valid_tracks = raw_tracks

    sorted_tids = sorted(valid_tracks.keys(), key=lambda tid: valid_tracks[tid]["count"], reverse=True)
    top_tids = sorted_tids[:6]

    character_data = {}
    time_per_sample = stride / fps

    for tid in top_tids:
        t = valid_tracks[tid]
        ts_list = t["timestamps"]
        first_time = ts_list[0] if ts_list else 0.0
        last_time = ts_list[-1] if ts_list else 0.0
        screen_sec = round(len(ts_list) * time_per_sample, 1)

        # Build active presence intervals
        intervals = []
        if ts_list:
            int_start = ts_list[0]
            prev_t = ts_list[0]
            max_gap = time_per_sample * 3.5
            for cur_t in ts_list[1:]:
                if cur_t - prev_t > max_gap:
                    intervals.append((round(int_start, 2), round(prev_t + 0.8, 2)))
                    int_start = cur_t
                prev_t = cur_t
            intervals.append((round(int_start, 2), round(prev_t + 0.8, 2)))

        # Save thumbnail portrait
        img_filename = f"char_{tid}.jpg"
        img_path = os.path.join(CHAR_IMG_DIR, img_filename)
        if t["best_crop"] is not None:
            ch, cw = t["best_crop"].shape[:2]
            scale = min(300 / ch, 300 / cw, 1.0)
            resized_crop = cv2.resize(t["best_crop"], (int(cw * scale), int(ch * scale)))
            cv2.imwrite(img_path, resized_crop)
            image_url = f"/character_image/{img_filename}"
        else:
            image_url = None

        character_data[tid] = {
            "id": tid,
            "name": f"Character {tid}",
            "frames_seen": int(len(ts_list) * stride),
            "detection_count": len(ts_list),
            "first_frame": int(first_time * fps),
            "last_frame": int(last_time * fps),
            "first_time": first_time,
            "last_time": last_time,
            "screen_time_seconds": screen_sec,
            "intervals": intervals,
            "image_url": image_url
        }

    total_pipeline_time = time.time() - t_start
    print(f"⚡ [UltraFast Vision AI] COMPLETE in {total_pipeline_time:.2f}s! Kept {len(character_data)} characters.")
    return character_data