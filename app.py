#!/usr/bin/env python3
"""TrailQuest AI: local-first outdoor mission generator.

Uses Python's standard library and a local Ollama server. If Ollama/model is
not available, the app returns a clearly labelled sample preview.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("TRAILQUEST_HOST", "127.0.0.1")
PORT = int(os.environ.get("TRAILQUEST_PORT", "8000"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("TRAILQUEST_MODEL", "qwen2.5:1.5b")

VALID_INTERESTS = {"birds", "plants", "sounds", "mindful", "photo", "surprise"}
VALID_ENVIRONMENTS = {"park", "garden", "trail", "campus", "neighbourhood", "balcony"}
VALID_LANGUAGES = {"English", "Hindi", "Assamese (experimental)"}


def clean_text(value: Any, default: str, max_length: int = 240) -> str:
    if not isinstance(value, str):
        return default
    value = re.sub(r"\s+", " ", value).strip()
    return value[:max_length] or default


def normalize_request(data: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize browser input before putting it into a model prompt."""
    try:
        duration = int(data.get("duration", 30))
    except (TypeError, ValueError):
        duration = 30
    duration = min((15, 30, 45, 60), key=lambda n: abs(n - duration))
    interest = str(data.get("interest", "surprise")).lower()
    environment = str(data.get("environment", "park")).lower()
    language = str(data.get("language", "English"))
    return {
        "location": clean_text(data.get("location"), "My local area", 100),
        "duration": duration,
        "interest": interest if interest in VALID_INTERESTS else "surprise",
        "environment": environment if environment in VALID_ENVIRONMENTS else "park",
        "language": language if language in VALID_LANGUAGES else "English",
        "energy": "gentle" if str(data.get("energy", "gentle")).lower() != "active" else "active",
    }


def fallback_quest(options: dict[str, Any]) -> dict[str, Any]:
    """A useful deterministic sample for demos where Ollama isn't installed."""
    interest = options["interest"]
    duration = options["duration"]
    environment_name = {
        "park": "park", "garden": "garden", "trail": "nature trail",
        "campus": "campus green space", "neighbourhood": "neighbourhood",
        "balcony": "balcony or windowside spot",
    }[options["environment"]]
    title_bank = {
        "birds": ("The Birdwatcher’s Five", "Notice five bird-related details without chasing or feeding any birds."),
        "plants": ("Tiny Botanical Detective", "Spot patterns in leaves, stems, and shades of green without picking anything."),
        "sounds": ("The Outdoor Sound Map", "Listen carefully and map the different sounds around you."),
        "mindful": ("Five-Sense Reset", "Slow down and reconnect with the place around you through your senses."),
        "photo": ("Nature’s Mini Gallery", "Make a small visual collection of natural patterns, textures, and light."),
        "surprise": ("The Curiosity Loop", "Find three small details in nature that you would normally walk past."),
    }
    title, intro = title_bank.get(interest, title_bank["surprise"])
    step_sets = {
        "birds": [
            ("Pause and scan", "Stand in a safe spot and watch from a distance for two quiet minutes.", 3),
            ("Look for movement", "Notice birds, if present, in the sky, on branches, or on the ground. Do not approach them.", 6),
            ("Find a pattern", "Observe beak shape, colour, movement, or the way a bird travels. Do not guess a species if unsure.", 7),
            ("Record a moment", "Write or remember one thing you noticed and one question you now have.", 4),
        ],
        "plants": [
            ("Find three leaf shapes", "Look for different leaf outlines and compare their edges from where you stand.", 4),
            ("Trace the textures", "Notice smooth, ridged, shiny, or fuzzy-looking surfaces without touching unknown plants.", 5),
            ("Spot a colour gradient", "Look for three shades of green or another natural colour in the same area.", 5),
            ("Make a field note", "Sketch one leaf shape from memory or describe it in three words.", 4),
        ],
        "sounds": [
            ("Listen in silence", "Stay in a safe spot and listen for one full minute without using your phone.", 3),
            ("Separate the layers", "Notice the nearest sound, the farthest sound, and a sound that comes and goes.", 6),
            ("Find a rhythm", "Listen for repeating patterns such as footsteps, wind, or birdsong if present.", 5),
            ("Draw a sound map", "Mark where two or three sounds seemed to come from, without recording anyone’s private conversation.", 4),
        ],
        "mindful": [
            ("Arrive", "Walk slowly to a safe place and take three comfortable, unforced breaths.", 3),
            ("Notice colours", "Find five colours in your surroundings, including one you had not noticed at first.", 5),
            ("Notice textures and shapes", "Look for a curved line, a repeated pattern, and a rough or smooth-looking texture.", 6),
            ("Choose a favourite detail", "Spend one quiet minute observing the detail you liked most.", 4),
        ],
        "photo": [
            ("Frame a close-up", "Find a natural pattern and frame it with your eyes or take a photo if you choose.", 4),
            ("Hunt for symmetry", "Look for repeated shapes, spirals, branching lines, or balanced patterns.", 6),
            ("Follow the light", "Notice how sunlight or shade changes the look of one object. Never look directly at the sun.", 5),
            ("Build a three-shot story", "Capture or remember a wide view, a detail, and a texture. Keep your surroundings safe.", 5),
        ],
        "surprise": [
            ("Find something tiny", "Notice a small natural detail you would usually overlook. Observe without touching it.", 4),
            ("Find a repeating pattern", "Look for repeated leaves, branches, stones, clouds, or shadows.", 5),
            ("Compare two places", "Notice how light, sound, or plant cover differs between two nearby safe spots.", 6),
            ("Ask a question", "Write down one question your observations sparked. You do not need to answer it today.", 4),
        ],
    }
    raw_steps = step_sets.get(interest, step_sets["surprise"])
    # Scale step minutes to the chosen duration while keeping each step meaningful.
    base = sum(s[2] for s in raw_steps)
    steps = []
    assigned = 0
    for index, (name, instruction, minutes) in enumerate(raw_steps):
        if index == len(raw_steps) - 1:
            planned_minutes = max(2, duration - assigned)
        else:
            planned_minutes = max(2, round(duration * minutes / base))
            assigned += planned_minutes
        steps.append({"title": name, "instruction": instruction, "minutes": planned_minutes})
    # If rounding led to a total that differs slightly, normalize the last step.
    steps[-1]["minutes"] = max(2, duration - sum(s["minutes"] for s in steps[:-1]))
    language_note = {
        "English": "Try to describe what you noticed in your own words.",
        "Hindi": "Jo dekha, use apne shabdon mein yaad karein ya likhein.",
        "Assamese (experimental)": "আপুনি কি লক্ষ্য কৰিলে, নিজৰ ভাষাত মনত ৰাখক বা লিখি থওক।",
    }.get(options["language"], "Describe what you noticed in your own words.")
    return {
        "title": title,
        "intro": intro,
        "duration": duration,
        "location_label": f"{environment_name.title()} · {options['location']}",
        "supplies": "Just your curiosity; a notebook is optional.",
        "steps": steps,
        "takeaway": "Before you leave, name one detail you noticed and one question you want to explore later.",
        "safety_note": "Stay in a familiar, permitted area during daylight. Keep to paths, watch for traffic, do not touch or eat unknown plants, and observe wildlife from a distance. Let someone know where you are going.",
        "reflection": language_note,
    }


def ollama_status() -> dict[str, Any]:
    try:
        request = urllib.request.Request(f"{OLLAMA_URL.rstrip('/')}/api/tags", method="GET")
        with urllib.request.urlopen(request, timeout=2.0) as response:
            body = json.loads(response.read().decode("utf-8"))
        names = [m.get("name", "") for m in body.get("models", [])]
        installed = any(n == MODEL or n.startswith(MODEL + "-") for n in names)
        return {"ollama_reachable": True, "model_installed": installed, "model": MODEL, "models": names}
    except Exception:
        return {"ollama_reachable": False, "model_installed": False, "model": MODEL, "models": []}


def parse_model_json(content: str) -> dict[str, Any]:
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("Model did not return a JSON object")
    return json.loads(content[start:end + 1])


def normalize_model_quest(candidate: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    steps_in = candidate.get("steps")
    if not isinstance(steps_in, list) or not steps_in:
        raise ValueError("Model response had no steps")
    steps = []
    for item in steps_in[:5]:
        if not isinstance(item, dict):
            continue
        try:
            mins = int(item.get("minutes", 5))
        except (TypeError, ValueError):
            mins = 5
        steps.append({
            "title": clean_text(item.get("title"), "Observe", 70),
            "instruction": clean_text(item.get("instruction"), "Pause and notice your surroundings.", 300),
            "minutes": max(1, min(30, mins)),
        })
    if not steps:
        raise ValueError("Model response had no valid steps")
    duration = options["duration"]
    total = sum(s["minutes"] for s in steps)
    # Rescale to the requested duration while preserving at least one minute per step.
    for step in steps:
        step["minutes"] = max(1, round(step["minutes"] * duration / total))
    steps[-1]["minutes"] = max(1, duration - sum(s["minutes"] for s in steps[:-1]))
    fallback = fallback_quest(options)
    return {
        "title": clean_text(candidate.get("title"), fallback["title"], 80),
        "intro": clean_text(candidate.get("intro"), fallback["intro"], 280),
        "duration": duration,
        "location_label": fallback["location_label"],
        "supplies": clean_text(candidate.get("supplies"), fallback["supplies"], 160),
        "steps": steps,
        "takeaway": clean_text(candidate.get("takeaway"), fallback["takeaway"], 260),
        "safety_note": fallback["safety_note"],
        "reflection": clean_text(candidate.get("reflection"), fallback["reflection"], 260),
    }


def generate_local_quest(options: dict[str, Any]) -> dict[str, Any]:
    status = ollama_status()
    if not status["ollama_reachable"] or not status["model_installed"]:
        result = fallback_quest(options)
        result["mode"] = "preview"
        result["model"] = MODEL
        result["notice"] = "Sample preview: start Ollama and install the configured model to generate a fresh AI mission locally."
        return result

    system_prompt = (
        "You are TrailQuest, a careful outdoor activity designer. Create a simple, practical, "
        "screen-light nature mission that encourages a person to spend time outdoors. "
        "Return ONLY valid JSON with keys title, intro, supplies, steps, takeaway, reflection. "
        "steps must be an array of 3 to 5 objects with title, instruction, minutes. "
        "Use the requested language. Adapt to the selected environment and time. Do not promise "
        "that a particular animal or plant will appear. Do not recommend touching, eating, collecting, "
        "or disturbing plants or wildlife; do not encourage trespassing, going near traffic or water, "
        "or entering isolated places. Keep the plan suitable for a beginner and avoid medical claims. "
        "Make the phone unnecessary after the mission is generated."
    )
    user_prompt = (
        f"Create one outdoor mission. Location context: {options['location']}. "
        f"Environment: {options['environment']}. Duration: {options['duration']} minutes. "
        f"Interest: {options['interest']}. Pace: {options['energy']}. Language: {options['language']}. "
        "Keep actions low-cost and accessible. Include specific observation steps, not generic advice. "
        "Minutes across steps should add up to the requested duration."
    )
    payload = {
        "model": MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.75, "num_predict": 650},
    }
    request = urllib.request.Request(
        f"{OLLAMA_URL.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90.0) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body.get("message", {}).get("content", "")
        quest = normalize_model_quest(parse_model_json(content), options)
        quest["mode"] = "local-ai"
        quest["model"] = MODEL
        quest["notice"] = "Generated on your device by a local open-weight model. Your form inputs are not sent to a hosted AI service."
        return quest
    except Exception as exc:
        result = fallback_quest(options)
        result["mode"] = "preview"
        result["model"] = MODEL
        result["notice"] = f"Sample preview shown because local generation failed ({type(exc).__name__}). Check that Ollama is running and the model is installed."
        return result


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json(200, {"ok": True, "app": "TrailQuest AI"})
            return
        if path == "/api/status":
            status = ollama_status()
            self.send_json(200, status)
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/quest":
            self.send_json(404, {"error": "Endpoint not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 20_000:
                self.send_json(400, {"error": "Request body is empty or too large"})
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
            options = normalize_request(data)
            self.send_json(200, generate_local_quest(options))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self.send_json(400, {"error": f"Invalid request: {exc}"})
        except Exception:
            self.send_json(500, {"error": "Unexpected server error. Please try again."})

    def log_message(self, format: str, *args: Any) -> None:
        # Keep logs useful without printing request bodies or user-entered location text.
        print(f"[{self.log_date_time_string()}] {self.address_string()} {format % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"\nTrailQuest AI is running at http://{HOST}:{PORT}")
    print(f"Local model target: {MODEL}")
    print("Press Ctrl+C to stop. Preview mode works without Ollama.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down TrailQuest AI...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
