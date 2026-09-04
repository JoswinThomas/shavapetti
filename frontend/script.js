const API_BASE = window.location.origin.includes(":5000")
    ? window.location.origin
    : "http://127.0.0.1:5000";

let currentSample = "spiderman";
let progressTimer = null;

// ==========================================
// SAMPLE SELECTION
// ==========================================
function selectSample(sampleId) {
    currentSample = sampleId;

    const spidermanBtn = document.getElementById("sampleSpidermanBtn");
    const drishyamBtn = document.getElementById("sampleDrishyamBtn");
    const videoInput = document.getElementById("videoInput");
    const subtitleInput = document.getElementById("subtitleInput");
    const videoFileName = document.getElementById("videoFileName");
    const subFileName = document.getElementById("subFileName");

    // Clear file inputs
    videoInput.value = "";
    subtitleInput.value = "";

    if (sampleId === "spiderman") {
        spidermanBtn.classList.add("active-sample");
        drishyamBtn.classList.remove("active-sample");
        videoFileName.innerText = "Sample selected: Spider-Man 2 (Clock Tower Climax)";
        subFileName.innerText = "Sample selected: subtitle.srt (12 entries)";
    } else if (sampleId === "drishyam") {
        drishyamBtn.classList.add("active-sample");
        spidermanBtn.classList.remove("active-sample");
        videoFileName.innerText = "Sample selected: Drishyam Investigation Scene";
        subFileName.innerText = "No subtitles (Visual tracking mode)";
    }
}

// ==========================================
// CUSTOM FILE SELECTION
// ==========================================
function handleFileSelect(type) {
    currentSample = null;
    document.getElementById("sampleSpidermanBtn").classList.remove("active-sample");
    document.getElementById("sampleDrishyamBtn").classList.remove("active-sample");

    if (type === "video") {
        const input = document.getElementById("videoInput");
        const nameLabel = document.getElementById("videoFileName");
        if (input.files.length > 0) {
            nameLabel.innerText = `Selected: ${input.files[0].name} (${(input.files[0].size / (1024 * 1024)).toFixed(1)} MB)`;
        }
    } else if (type === "subtitle") {
        const input = document.getElementById("subtitleInput");
        const nameLabel = document.getElementById("subFileName");
        if (input.files.length > 0) {
            nameLabel.innerText = `Selected: ${input.files[0].name} (${(input.files[0].size / 1024).toFixed(1)} KB)`;
        }
    }
}

// ==========================================
// PROGRESS BAR SIMULATOR
// ==========================================
function startProgressAnimation() {
    const statusCard = document.getElementById("statusCard");
    const progressBar = document.getElementById("progressBar");
    const statusTitle = document.getElementById("statusTitle");
    const statusDesc = document.getElementById("statusDesc");
    const step1 = document.getElementById("step1");
    const step2 = document.getElementById("step2");
    const step3 = document.getElementById("step3");
    const step4 = document.getElementById("step4");

    statusCard.style.display = "flex";
    progressBar.style.width = "5%";

    let percent = 5;
    const stages = [
        { at: 15, title: "1. Vision AI: Running YOLOv11...", desc: "Scanning video frames at high speed with deep learning...", step: step1 },
        { at: 45, title: "2. Person Tracking & Extraction...", desc: "Identifying unique characters and cropping high-res portraits...", step: step2 },
        { at: 75, title: "3. Subtitle Alignment & Trope Scan...", desc: "Synchronizing movie dialogue timeline and scanning fatal patterns...", step: step3 },
        { at: 92, title: "4. Synthesizing Death Risk...", desc: "Computing mortality probabilities and generating final verdict...", step: step4 }
    ];

    if (progressTimer) clearInterval(progressTimer);

    progressTimer = setInterval(() => {
        if (percent < 92) {
            percent += Math.random() * 4 + 1.5;
            progressBar.style.width = `${Math.min(percent, 92)}%`;

            for (const s of stages) {
                if (percent >= s.at) {
                    statusTitle.innerText = s.title;
                    statusDesc.innerText = s.desc;
                    [step1, step2, step3, step4].forEach(chip => chip.classList.remove("active"));
                    s.step.classList.add("active");
                }
            }
        }
    }, 600);
}

function completeProgressAnimation() {
    if (progressTimer) clearInterval(progressTimer);
    const progressBar = document.getElementById("progressBar");
    const statusTitle = document.getElementById("statusTitle");
    const statusDesc = document.getElementById("statusDesc");

    progressBar.style.width = "100%";
    statusTitle.innerText = "☠ Analysis Complete!";
    statusDesc.innerText = "Mortality dossier assembled. Displaying results below.";

    setTimeout(() => {
        document.getElementById("statusCard").style.display = "none";
    }, 1200);
}

// ==========================================
// MAIN ANALYSIS CALL
// ==========================================
async function analyzeVideo() {
    const videoInput = document.getElementById("videoInput");
    const subtitleInput = document.getElementById("subtitleInput");
    const predictBtn = document.getElementById("predictBtn");
    const resultsSection = document.getElementById("results");

    const formData = new FormData();

    if (currentSample) {
        formData.append("sample_id", currentSample);
    } else {
        if (videoInput.files.length === 0) {
            alert("Please select a video file or click one of the quick demo buttons above.");
            return;
        }
        formData.append("video", videoInput.files[0]);

        if (subtitleInput.files.length > 0) {
            formData.append("subtitle", subtitleInput.files[0]);
        }
    }

    predictBtn.disabled = true;
    predictBtn.style.opacity = "0.6";
    startProgressAnimation();

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || `Server responded with status ${response.status}`);
        }

        const data = await response.json();
        console.log("[Death Predictor Response]", data);

        if (!data.success) {
            alert("Analysis failed: " + data.error);
            return;
        }

        completeProgressAnimation();
        renderResults(data);

    } catch (error) {
        console.error("Connection or analysis error:", error);
        alert(`❌ Could not connect to Death Predictor backend.\n\nDetails: ${error.message}\n\nPlease ensure the Flask server is running on http://127.0.0.1:5000.`);
        if (progressTimer) clearInterval(progressTimer);
        document.getElementById("statusCard").style.display = "none";
    } finally {
        predictBtn.disabled = false;
        predictBtn.style.opacity = "1";
    }
}

// ==========================================
// RENDER RESULTS
// ==========================================
function renderResults(data) {
    const resultsSection = document.getElementById("results");
    const verdictBanner = document.getElementById("verdictBanner");
    const verdictTag = document.getElementById("verdictTag");
    const verdictHeadline = document.getElementById("verdictHeadline");
    const verdictSummary = document.getElementById("verdictSummary");
    const verdictTarget = document.getElementById("verdictTarget");
    const characterGrid = document.getElementById("characterResults");
    const videoPreviewCard = document.getElementById("videoPreviewCard");
    const sceneVideo = document.getElementById("sceneVideo");

    // Clear previous cards
    characterGrid.innerHTML = "";

    const verdict = data.verdict || {};
    const results = data.results || [];

    // 1. Verdict Banner
    verdictBanner.className = `verdict-banner ${verdict.level || "danger"}`;
    verdictTag.innerText = verdict.level === "danger"
        ? "⚠️ HIGH CASUALTY ALERT"
        : verdict.level === "warning"
            ? "⚠️ DANGER ELEVATED"
            : "🟢 SURVIVAL LIKELY";
    verdictHeadline.innerText = verdict.headline || "SCENE ANALYSIS COMPLETE";
    verdictSummary.innerText = verdict.summary || "";
    verdictTarget.innerText = verdict.primary_target || "Unknown";

    // 2. Character Cards (Render once only)
    results.forEach((character, idx) => {
        const card = document.createElement("div");
        card.className = `character-card ${character.risk_class || "danger"}`;

        const portraitHTML = character.image_url
            ? `<img src="${API_BASE}${character.image_url}" alt="${character.name}" class="portrait-img">`
            : `<div class="portrait-placeholder">${character.emoji || "👤"}</div>`;

        let evidenceHTML = "";
        if (character.evidence && character.evidence.length > 0) {
            character.evidence.forEach(ev => {
                evidenceHTML += `
                    <div class="evidence-item">
                        <div class="evidence-top">
                            <span class="evidence-title">${ev.title || "Fatal Indicator"}</span>
                            <span class="evidence-pts">+${ev.score} pts</span>
                        </div>
                        <div class="evidence-quote">${ev.phrase}</div>
                    </div>
                `;
            });
        } else {
            evidenceHTML = `<div style="font-size: 12px; color: #778;">No overt death tropes triggered.</div>`;
        }

        card.innerHTML = `
            <div class="card-top">
                <div class="portrait-frame">
                    ${portraitHTML}
                </div>
                <div class="card-title-area">
                    <div class="char-badge-line">
                        <span class="status-badge ${character.risk_class}">${character.emoji} ${character.status}</span>
                    </div>
                    <div class="char-name">${character.name}</div>
                    <div class="screen-time-info">⏱️ ${character.screen_time} screen presence</div>
                </div>
            </div>

            <div class="risk-gauge-box">
                <div class="risk-label-row">
                    <span class="risk-val">Death Risk: ${character.score}%</span>
                    <span class="survival-val">Survival: ${character.survival_odds}</span>
                </div>
                <div class="gauge-track">
                    <div class="gauge-fill ${character.risk_class}" style="width: ${character.score}%"></div>
                </div>
            </div>

            <div class="evidence-section">
                <div class="evidence-header">Fatal Indicators & Evidence:</div>
                <div class="evidence-list">
                    ${evidenceHTML}
                </div>
            </div>
        `;

        characterGrid.appendChild(card);
    });

    // 3. Video Playback Preview
    if (data.video_url) {
        sceneVideo.src = `${API_BASE}${data.video_url}`;
        videoPreviewCard.style.display = "block";
    }

    // 4. Show & Smooth Scroll
    resultsSection.style.display = "block";
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
}