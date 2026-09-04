import re

DEATH_FLAGS = {
    "false_reassurance": {
        "title": "False Reassurance Trope",
        "patterns": [
            "gonna be okay", "gonna be alright", "we're gonna make it", "going to be okay",
            "don't worry", "we can still make", "you're safe now", "it's okay", "i'm okay",
            "it's going to be fine", "we made it", "everything is fine", "nobody is gonna die"
        ],
        "score": 30,
        "description": "False sense of security right before catastrophe strikes."
    },
    "future_plans": {
        "title": "Post-Battle Retirement Trope",
        "patterns": [
            "when i get home", "when this is over", "after this mission", "when we get back",
            "make your flight", "start a new life", "getting married", "one last job",
            "days until retirement", "retire", "go home together", "buy a house",
            "see you tomorrow", "one last time", "last time", "for the last time"
        ],
        "score": 25,
        "description": "Making future plans or talking about post-mission dreams is a classic death omen."
    },
    "protective_sacrifice": {
        "title": "Heroic Protection / Sacrifice",
        "patterns": [
            "stay there", "protect you", "trying to protect you", "get out of here",
            "save yourself", "leave me behind", "go on without me", "there's no time",
            "i'll hold them off", "just go", "get to safety", "take my hand", "don't let go"
        ],
        "score": 35,
        "description": "Urging loved ones to stay back or taking the frontline to protect others."
    },
    "fatal_conflict": {
        "title": "Tragic Betrayal & Confrontation",
        "patterns": [
            "you betrayed me", "what did you do", "what you made me do", "forgive me",
            "why did you do this", "it didn't have to be like this", "you were my friend",
            "take it away", "you don't give people hope", "i trusted you", "end of the line"
        ],
        "score": 30,
        "description": "Intense personal showdown with a former ally or nemesis."
    },
    "dire_situation": {
        "title": "Desperate Last Plea",
        "patterns": [
            "look at me", "hold on", "stay with me", "don't leave me", "please no",
            "breathe", "help me", "i can't", "no no no", "it's too late", "run away"
        ],
        "score": 25,
        "description": "Desperate emotional pleas during high-lethal action sequences."
    },
    "impending_doom": {
        "title": "Impending Doom Pre-monition",
        "patterns": [
            "if i don't make it", "if i don't come back", "if something happens to me",
            "i might not make it", "this could be my last", "bad feeling about this",
            "too quiet", "not gonna make it", "we're trapped"
        ],
        "score": 35,
        "description": "Explicit acknowledgment of probable mortality."
    },
    "farewell_entrustment": {
        "title": "Final Words & Entrustment",
        "patterns": [
            "goodbye", "farewell", "take care of my family", "look after my family",
            "look after my daughter", "look after my son", "tell her i love her",
            "tell them i love them", "promise me", "give me your word", "see you on the other side",
            "remember me", "it was an honor"
        ],
        "score": 30,
        "description": "Entrusting loved ones or uttering final goodbyes."
    }
}


def analyze_dialogue(text):
    text_lower = text.lower()
    detected_flags = []
    total_score = 0

    for flag_id, flag_info in DEATH_FLAGS.items():
        for pattern in flag_info["patterns"]:
            if pattern in text_lower:
                detected_flags.append({
                    "flag": flag_id,
                    "title": flag_info["title"],
                    "phrase": pattern,
                    "score": flag_info["score"],
                    "description": flag_info["description"]
                })
                total_score += flag_info["score"]
                break  # match once per category

    return {
        "death_score": min(total_score, 100),
        "flags": detected_flags
    }


def calculate_character_risk(character_data, dialogue_matches):
    character_scores = {}

    for cid in character_data:
        character_scores[cid] = {
            "score": 0,
            "evidence": [],
            "dialogue_count": 0
        }

    for dialogue in dialogue_matches:
        cid = dialogue.get("character")
        if cid is None or cid not in character_scores:
            continue

        text = dialogue["text"]
        character_scores[cid]["dialogue_count"] += 1

        analysis = analyze_dialogue(text)
        score = analysis["death_score"]

        if score > 0:
            character_scores[cid]["score"] += score

            for flag in analysis["flags"]:
                character_scores[cid]["evidence"].append({
                    "reason": flag["flag"],
                    "title": flag["title"],
                    "phrase": f'"{text}" (flag: {flag["phrase"]})',
                    "score": flag["score"],
                    "description": flag["description"]
                })

    # Clamp dialogue score to 85 max before screen time
    for cid in character_scores:
        character_scores[cid]["score"] = min(character_scores[cid]["score"], 85)

    return character_scores


def add_screen_time_score(character_data, character_scores):
    if not character_data:
        return character_scores

    max_frames = max((d.get("frames_seen", 1) for d in character_data.values()), default=1)

    for cid, data in character_data.items():
        if cid not in character_scores:
            character_scores[cid] = {"score": 0, "evidence": [], "dialogue_count": 0}

        frames = data.get("frames_seen", 0)
        ratio = frames / max_frames if max_frames > 0 else 0
        screen_score = round(ratio * 15, 1)

        character_scores[cid]["score"] += screen_score
        character_scores[cid]["evidence"].append({
            "reason": "screen_time",
            "title": "High Scene Exposure",
            "phrase": f"{data.get('screen_time_seconds', 0)}s active scene presence",
            "score": screen_score,
            "description": "Characters with heavy focal presence in climax scenes bear elevated mortality hazard."
        })

        # Final cap at 100
        character_scores[cid]["score"] = min(100, round(character_scores[cid]["score"]))

    return character_scores


def generate_final_results(character_risk, character_data=None):
    results = []
    character_data = character_data or {}

    for cid, data in character_risk.items():
        score = int(round(data["score"]))
        char_info = character_data.get(cid, {})

        if score >= 70:
            status = "CERTAIN DOOM"
            emoji = "☠️"
            risk_class = "danger"
        elif score >= 45:
            status = "HIGH MORTALITY RISK"
            emoji = "⚠️"
            risk_class = "warning"
        elif score >= 20:
            status = "MODERATE DANGER"
            emoji = "⚡"
            risk_class = "caution"
        else:
            status = "SURVIVOR STATUS"
            emoji = "🟢"
            risk_class = "safe"

        survival_odds = max(2, 100 - score)

        name = char_info.get("name", f"Character {cid}")
        image_url = char_info.get("image_url")

        results.append({
            "character_id": cid,
            "name": name,
            "image_url": image_url,
            "score": score,
            "survival_odds": f"{survival_odds}%",
            "status": status,
            "emoji": emoji,
            "risk_class": risk_class,
            "screen_time": f"{char_info.get('screen_time_seconds', 0)}s",
            "evidence": data["evidence"]
        })

    # Sort descending by death risk
    results.sort(key=lambda x: x["score"], reverse=True)

    # Generate overarching verdict
    verdict = {}
    if results:
        top_risk = results[0]
        if top_risk["score"] >= 70:
            verdict = {
                "level": "danger",
                "headline": "☠️ CASUALTY IMMINENT: SOMEONE IS NOT MAKING IT OUT",
                "primary_target": top_risk["name"],
                "summary": f"{top_risk['name']} triggered multiple high-lethal foreshadowing tropes. With a {top_risk['score']}% death score, survival probability has plummeted to {top_risk['survival_odds']}."
            }
        elif top_risk["score"] >= 45:
            verdict = {
                "level": "warning",
                "headline": "⚠️ LETHAL PERIL: HIGH RISK DETECTED",
                "primary_target": top_risk["name"],
                "summary": f"Ominous dialogue and high focal intensity detected. Keep your eyes on {top_risk['name']}—fate hangs by a thread."
            }
        else:
            verdict = {
                "level": "safe",
                "headline": "🟢 LOW RISK: CAST MAY SURVIVE THIS SCENE",
                "primary_target": "None",
                "summary": "No critical death flags or ominous farewell tropes were triggered in this scene."
            }

    return {
        "characters": results,
        "verdict": verdict
    }