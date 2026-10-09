# TrailQuest AI 🌿

**A little less scroll. A little more wild.**

TrailQuest turns a small block of free time into a practical, beginner-friendly nature mission. Choose a setting, duration, interest, pace, and language; receive a short field checklist; then put the phone away and explore.

This project is built for the **Touch Grass** open-source AI challenge. The real experience is outdoors: the screen helps you prepare, then gets out of your way.

## Demo

- **Run instantly in preview mode:** the app displays a sample mission and can generate a deterministic sample without Ollama or an API key.
- **Run the real local-AI path:** connect a local Ollama server and install `qwen2.5:1.5b`. TrailQuest then generates new missions with local inference.
- **Demo script:** see [`docs/DEMO.md`](docs/DEMO.md) for a suggested 60–90 second screen recording and judging walkthrough.

> This repository includes the runnable app and a repeatable demo flow. It does not claim to be a hosted live demo; the AI-enabled version runs on the computer where Ollama is installed.

## Why open innovation matters

- **Local inference:** after the model is downloaded, mission generation can run without a hosted AI API.
- **Privacy by design:** the backend sends prompts only to the local Ollama endpoint (`127.0.0.1:11434` by default). The app does not collect accounts, analytics, or exact GPS location.
- **No API key or per-request fee:** the application uses Python's standard library and a model on your computer. Hardware and electricity still have a cost, and the first model download requires internet.
- **Inspectable and adaptable:** the prompt, safety guardrails, output validation, and UI are all in the repository. Swap the model by changing `TRAILQUEST_MODEL`.
- **Graceful demo:** without a local model, TrailQuest labels the result as a *sample preview* instead of pretending it came from AI.

## Features

- Outdoor missions for birds, plants, outdoor sounds, mindful observation, nature photography, or a surprise prompt.
- Six settings: park, garden, nature trail, campus, neighbourhood, and balcony.
- 15, 30, 45, or 60 minute missions.
- English, Hindi, and experimental Assamese output selection. Assamese quality depends on the selected model; review translations before relying on them.
- Checklist with progress tracking, a simple timer, and copy-to-clipboard mission export.
- Built-in safety reminder: stay in familiar permitted places, keep to paths, don't touch/eat unknown plants, and observe wildlife from a distance.
- Local AI status indicator and sample-preview fallback.

## Tech stack

- **Frontend:** HTML, CSS, vanilla JavaScript
- **Backend:** Python 3 standard library (`http.server`, `urllib`, `json`)
- **Open-weight model runtime:** [Ollama](https://ollama.com/)
- **Suggested model:** [Qwen2.5 1.5B on Ollama](https://ollama.com/library/qwen2.5), configured as `qwen2.5:1.5b`

The app has no Python package dependencies. The Google Fonts import is decorative; the app falls back to local system fonts if those fonts are unavailable. The app itself uses no external AI service.

## Quick start: preview mode

Requirements: Python 3.10+.

```bash
git clone https://github.com/YOUR-USERNAME/trailquest-ai.git
cd trailquest-ai
python app.py
```

Open <http://127.0.0.1:8000> in your browser. Without Ollama, the app remains usable and labels missions as **Sample Preview**.

## Enable local AI

1. Install [Ollama](https://ollama.com/download) for your operating system.
2. Start Ollama, then download the model once:

   ```bash
   ollama pull qwen2.5:1.5b
   ```

3. Start/restart TrailQuest:

   ```bash
   python app.py
   ```

4. Open <http://127.0.0.1:8000>. The footer should show `LOCAL MODEL READY` when Ollama and the configured model are available. Select your preferences and choose **Create my nature quest**.

The first model download needs internet. After it is installed, generation runs against your local Ollama server. If local inference fails, the app shows a sample and tells you why it could not confirm AI generation.

### Use another Ollama model

```bash
# macOS / Linux
TRAILQUEST_MODEL=qwen2.5:3b-instruct python app.py
```

```powershell
# Windows PowerShell
$env:TRAILQUEST_MODEL = "qwen2.5:3b-instruct"
python app.py
```

Download that model first with `ollama pull qwen2.5:3b-instruct`. Check the model's licence and resource needs before redistributing or deploying it. The software's MIT licence does not replace the model's separate licence.

If Ollama is running at a non-default local URL, set `OLLAMA_URL`, for example `http://127.0.0.1:11434`.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests cover request validation, sample generation, local-model output normalization, and JSON parsing. They do not download a model or test actual LLM quality.

## Project structure

```text
trailquest-ai/
├── app.py                  # Local HTTP server and Ollama integration
├── index.html              # Main user interface
├── styles.css              # Responsive visual design
├── app.js                  # Form, checklist, timer, and copy actions
├── assets/leaf.svg         # App icon
├── tests/test_app.py       # Unit tests
├── docs/DEMO.md            # Recording and live-demo walkthrough
├── .gitignore
├── LICENSE                 # MIT for this app's source code
└── README.md
```

## Privacy and limitations

- The form asks for a general area, not exact GPS coordinates. Keep the location field broad.
- In AI mode, the prompt is sent to Ollama on the same computer by default; it is not sent to a hosted AI API by this app. A custom Ollama proxy or remote `OLLAMA_URL` would change that privacy boundary.
- Output is generated text, not verified ecological or navigation advice. The app does not identify species, provide directions, check weather, or confirm that a park/trail is open.
- Always follow local rules, stay in permitted and familiar areas, use daylight, and let someone know your plan.
- Assamese is marked experimental because small multilingual models may produce errors. Have a fluent speaker review important translations.
- Model availability, speed, RAM use, and quality depend on the user's computer and the chosen model.

## Next steps

1. Add a short screen recording or GIF to the repository after testing the local AI path.
2. Test the language options with real speakers.
3. Add opt-in, user-reviewed local nature packs for different cities—without claiming species sightings are guaranteed.
4. Consider an installable PWA/offline asset caching if the project grows.

## Credits

- [Ollama](https://ollama.com/) for local model execution.
- [Qwen2.5](https://ollama.com/library/qwen2.5) for the suggested open-weight model. Review the model licence on the model page.

---

Made for the outdoors. Take only memories. 🌿
