import re


STOP_WORDS = {
    "no", "yes", "hey", "look", "wait", "stop", "what", "where", "why", "who",
    "how", "when", "well", "come", "let", "see", "please", "god", "oh", "ok",
    "okay", "man", "sir", "mr", "mrs", "ms", "dr", "yeah", "nope", "hello",
    "hi", "bye", "goodbye", "help", "this", "that", "there", "here", "they"
}


def extract_names_from_dialogue(subtitles):
    """Detect mentioned character names in dialogue (e.g. 'Gwen, stay there', 'Peter.', 'Harry, what did you do?')."""
    candidates = {}

    for sub in subtitles:
        text = sub["text"]

        # Matches: "Name," or "- Name," or "No, Name." or "Name, what..."
        patterns = [
            r"(?:^|[\-\?!,]\s*)([A-Z][a-z]{2,15})(?:,\s*|\s*[\?!])",
            r"(?:^|[\-\?!,]\s*)([A-Z][a-z]{2,15})\.(?:\s*|$)",
            r"(?:,\s*|\b(?:to|with|about|hey|no|dear|love|call)\s+)([A-Z][a-z]{2,15})(?:[,\.\?!]|\s+)"
        ]

        for pat in patterns:
            for m in re.finditer(pat, text):
                word = m.group(1)
                w_lower = word.lower()
                if w_lower not in STOP_WORDS and len(word) >= 3:
                    candidates[word] = candidates.get(word, 0) + 1

    # Sort by frequency
    sorted_names = sorted(candidates.keys(), key=lambda n: candidates[n], reverse=True)
    return sorted_names


def align_subtitles_to_video(subtitles, video_duration):
    """
    If subtitles were trimmed from a full movie, their timestamps start at e.g. 01:57:05 (7025s),
    while the video starts at 0s. Auto-align if start exceeds video duration.
    """
    if not subtitles:
        return subtitles, 0.0

    first_start = subtitles[0]["start"]
    last_end = subtitles[-1]["end"]
    span = last_end - first_start

    # If first subtitle is beyond video duration, check if it's a trimmed movie subtitle
    offset = 0.0
    if first_start > video_duration and span <= (video_duration * 1.5 + 10):
        offset = first_start
        print(f"[Dialogue Matcher] Detected movie timestamp offset: {offset:.2f}s. Auto-aligning to video timeline [0s - {video_duration:.1f}s].")

    aligned = []
    for sub in subtitles:
        norm_start = max(0.0, round(sub["start"] - offset, 2))
        norm_end = max(norm_start + 0.1, round(sub["end"] - offset, 2))

        aligned.append({
            "number": sub.get("number", 0),
            "original_timestamp": sub.get("timestamp", ""),
            "start": norm_start,
            "end": norm_end,
            "text": sub["text"]
        })

    return aligned, offset


def match_dialogue_to_characters(subtitles, character_data, fps=24.0, video_duration=80.0):
    """
    Matches each subtitle line to the most likely character based on active presence intervals,
    screen time prominence, and timestamp proximity.
    """
    if not subtitles:
        return []

    if not character_data:
        # If no characters detected, return dialogues unassigned
        return [{
            "text": s["text"],
            "start": s.get("start", 0),
            "end": s.get("end", 0),
            "character": None
        } for s in subtitles]

    # Align timestamps if necessary
    aligned_subs, _ = align_subtitles_to_video(subtitles, video_duration)

    # Extract detected character names
    detected_names = extract_names_from_dialogue(aligned_subs)
    print(f"[Dialogue Matcher] Names detected in dialogue: {detected_names}")

    # Assign names to characters if available
    char_list = list(character_data.values())
    for i, name in enumerate(detected_names):
        if i < len(char_list):
            cid = char_list[i]["id"]
            character_data[cid]["assigned_name"] = name
            character_data[cid]["name"] = f"{name} (Character {cid})"

    # Find fallback character (the most prominent character)
    fallback_char_id = max(character_data.keys(), key=lambda k: character_data[k].get("frames_seen", 0))

    matches = []

    for sub in aligned_subs:
        sub_start = sub["start"]
        sub_end = sub["end"]
        sub_mid = (sub_start + sub_end) / 2.0

        best_character = None
        best_overlap_score = -1.0
        min_distance = 999999.0
        closest_char = None

        for cid, cinfo in character_data.items():
            intervals = cinfo.get("intervals", [])
            first_t = cinfo.get("first_time", 0.0)
            last_t = cinfo.get("last_time", video_duration)

            # Check exact presence during subtitle window
            is_active_now = False
            for (st, et) in intervals:
                # Subtitle overlaps interval with small padding
                if not (sub_end < st - 0.5 or sub_start > et + 0.5):
                    overlap = min(sub_end, et) - max(sub_start, st)
                    if overlap > best_overlap_score:
                        best_overlap_score = overlap
                        best_character = cid
                    is_active_now = True

            # Also track distance from subtitle midpoint to character's active window
            dist_to_window = 0.0
            if sub_mid < first_t:
                dist_to_window = first_t - sub_mid
            elif sub_mid > last_t:
                dist_to_window = sub_mid - last_t

            if dist_to_window < min_distance:
                min_distance = dist_to_window
                closest_char = cid

        # If no character directly in interval, use the closest character in timeline
        if best_character is None:
            best_character = closest_char if closest_char is not None else fallback_char_id

        # Determine speaker name for display
        char_name = character_data[best_character].get("name", f"Character {best_character}")

        matches.append({
            "text": sub["text"],
            "start": sub_start,
            "end": sub_end,
            "character": best_character,
            "character_name": char_name
        })

    print(f"[Dialogue Matcher] Matched {len(matches)} dialogue lines across {len(character_data)} characters.")
    return matches