# ⚰️ Shavapetti — Death Predictor AI ☠️

> *"Someone is definitely going to die."*  
> **Deep Learning Character Tracking & Fatal Foreshadowing Engine for Movie Scenes.**

---

## 🎬 Overview
**Shavapetti** (Death Predictor) is an AI-powered multimedia analysis web application that scans movie clips to predict character mortality. By combining state-of-the-art computer vision (YOLOv11 person detection) with narrative trope analysis and subtitle synchronization, it calculates mortality risk and generates a cinematic **Casualty Assessment Dossier**.

---

## ⚡ Key Features

- **High-Speed Vision AI**: Optimized sequential demuxing (`cap.grab()`) and batched neural inference with YOLOv11 delivers scene analysis in **under 10 seconds** on standard multi-core CPUs.
- **Character Portrait Isolation**: Automatically tracks persons across shot cuts and crops high-resolution portrait cards for each primary character.
- **SRT Timestamp Auto-Alignment**: Automatically synchronizes movie-offset subtitles (e.g. clips cut from 2-hour movies) with the video timeline.
- **Narrative Death Trope Engine**: Scans dialogue for classic cinematic death omens:
  - *False Reassurance* ("we're gonna make it", "it's gonna be okay")
  - *Post-Mission Dreams / Retirement* ("when I get home", "make your flight", "one last job")
  - *Heroic Sacrifice & Protection* ("stay there", "protect you", "save yourself")
  - *Fatal Betrayal & Confrontation* ("you betrayed me", "what did you do")
  - *Desperate Last Pleas* ("look at me", "hold on", "stay with me")
  - *Farewell & Family Entrustment* ("take care of my family", "promise me", "goodbye")
- **Cinematic Web Dashboard**:
  - Dark glassmorphism UI with Google Fonts (`Cinzel` & `Outfit`).
  - Animated risk meters and survival odds.
  - Ominous Casualty Verdict Banner.
  - Video playback preview alongside the analysis.
  - One-click sample loader for instant demoing.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-CORS, OpenCV (`cv2`), Ultralytics YOLOv11 (`yolo11n.pt`), PyTorch
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism, animations), Vanilla JavaScript (Async/Await, Fetch API)

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/JoswinThomas/shavapetti.git
cd shavapetti
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Launch the Server
```bash
python backend/app.py
```

### 4. Open in Browser
Visit **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser:
1. Click **⚡ PREDICT DEATH RISK** to run with the pre-loaded Spider-Man 2 sample.
2. Or upload your own video clip and matching `.srt` subtitle file.
