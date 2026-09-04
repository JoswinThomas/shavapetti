import re


def time_to_seconds(time_str):
    """Convert '00:01:25,500' or '00:01:25.500' to seconds float."""
    time_str = time_str.strip().replace(",", ".")
    parts = time_str.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    elif len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    return float(time_str)


def parse_srt(file_path):
    """Parse SRT subtitle file with multi-encoding fallback and robust regex."""
    content = ""
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, Exception):
            continue

    if not content:
        return []

    # Normalize line breaks
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Match SRT entries: (optional number) -> timestamp line -> subtitle text
    # Timestamp format: 00:00:00,000 --> 00:00:00,000
    pattern = re.compile(
        r"(?:(\d+)\n)?"
        r"(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})"
        r"(?:[^\n]*)\n"
        r"([\s\S]*?)(?=\n\s*(?:\d+\n)?\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3}\s*-->|\Z)",
        re.MULTILINE
    )

    subtitles = []
    idx = 1

    for match in pattern.finditer(content):
        num_str = match.group(1) or str(idx)
        start_ts = match.group(2)
        end_ts = match.group(3)
        raw_text = match.group(4).strip()

        # Clean HTML / formatting tags
        text = re.sub(r"<[^>]+>", "", raw_text)
        text = re.sub(r"\{[^}]+\}", "", text)
        text = " ".join(text.split())

        if not text:
            continue

        try:
            start_sec = time_to_seconds(start_ts)
            end_sec = time_to_seconds(end_ts)
        except Exception:
            continue

        subtitles.append({
            "number": int(num_str) if num_str.isdigit() else idx,
            "timestamp": f"{start_ts} --> {end_ts}",
            "start": round(start_sec, 3),
            "end": round(end_sec, 3),
            "text": text
        })
        idx += 1

    print(f"[Subtitle Parser] Successfully parsed {len(subtitles)} subtitles from {file_path}")
    return subtitles


def get_full_dialogue(file_path):
    subtitles = parse_srt(file_path)
    return " ".join(s["text"] for s in subtitles)