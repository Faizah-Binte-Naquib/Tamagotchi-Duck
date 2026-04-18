# DuckMind — your desktop duck remembers everything (in a cozy way)

**A tiny life-sim meets cozy desktop pet** — feed them, tuck them in, drop a pond on your screen, and watch them waddle through your day. Under the cute pixels lives a serious ML stack: **semantic memory (RAG)**, **embeddings + ChromaDB**, and **local LLM personality** so your duck does not just *look* alive — they **learn how you play**.

> Portfolio angle: **ML / AI for interactive games** — NPC-style memory, evolving traits, and chat grounded in what actually happened in your session.

### Main menu (the cozy HQ)

This is where you peek at personality text, watch the little stat bars, grab pond/grass/house for the desktop, and **drag the duck out** onto your screen when they are hatched.

![DuckMind main menu — personality, health, item menu, hatch / rename / sound](images/main_menu.png)

*Tip:* click and drag the duck sprite **outside** this window to release them onto the desktop (Windows reports that as a “non-Qt” drop, which the game now handles on purpose).

---

## Why this repo exists (the fun version)

You are not “running a demo.” You are **onboarding a duck**.

- They get hungry, sleepy, silly, and sometimes dramatic (same).
- You place **ponds, grass, houses** — little set-dressing on your desktop.
- They **remember** the vibe of your care style and bring it back in chat.
- The whole thing is wrapped in a **Stardew-flavored** PySide6 UI because comfort is a feature.

If you are here for **game-feel + ML engineering**, you are in the right pond.

---

## ML in games: what this project actually proves

Hiring managers for **ML roles in game dev** often want to see *systems*, not slides. DuckMind is a small, end-to-end slice of “**character AI with memory**”:

| Game-adjacent idea | How it shows up here |
| ------------------ | -------------------- |
| **Believable companion / NPC** | Desktop pet with moods, stats, and time-based decay |
| **Long-term memory** | ChromaDB + embeddings store interaction text as **retrievable** context |
| **Grounded dialogue** | **RAG** pulls relevant memories before the LLM answers |
| **Evolving persona** | Personality traits drift from observed play patterns (LLM-assisted) |
| **Safety / focus** | Topic filtering keeps chat roughly on-theme |

**Stack (high level):** Python · PySide6 · **ChromaDB** · **sentence-transformers** (`all-MiniLM-L6-v2`) · **Ollama** (local LLM, e.g. `llama3.1:8b`)

For a recruiter-ready writeup, see **[PROJECT_DESCRIPTION.md](PROJECT_DESCRIPTION.md)**.

---

## Architecture (one glance)

```
You care for the duck → Observer logs events → Memories + embeddings (ChromaDB)
                                    ↓
              RAG retrieves “what kind of player is this?” context
                                    ↓
           Personality + chat use LLM with that context (Ollama)
```

Deep dive: **[ARCHITECTURE.md](ARCHITECTURE.md)** · Vector notes: **[memory/README.md](memory/README.md)**

---

## Quick start (get the duck on screen)

**You need:** Python 3.8+ · [Ollama](https://ollama.ai) for the AI bits (the pet still runs without it — just quieter upstairs).

```bash
git clone <your-repo-url>
cd tamagachi
python -m venv venv
```

**Activate**

- Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
- Windows (cmd): `venv\Scripts\activate.bat`
- macOS / Linux: `source venv/bin/activate`

```bash
pip install -r requirements.txt
ollama pull llama3.1:8b
python main.py
```

LLM details: **[SETUP_LLM.md](SETUP_LLM.md)** · Config: `config/llm_config.py`

---

## How to play (controls with personality)

**Care loop:** feed, play, sleep, clean, medicine — classic tamagotchi brain, modern desktop hands.

**Get them on your desktop:** once hatched, **drag the duck from the left box** and release on the desktop (not on the menu window).
**Cozy sandbox:** drag **ponds / grass / houses** from the item row the same way; the duck can wander and vibe with them.

**The brainy part:** click the duck to **chat**. Replies lean on **retrieved memories**, so the banter tracks your actual history together.

Auto-save is friendly (about every 30 seconds). Your duck appreciates consistency.

---

## Repo layout (where the magic files live)

```
tamagachi/
├── main.py              # Run this
├── duck_tamagotchi.py   # Core sim logic
├── desktop_duck.py      # Desktop window + duck presence
├── desktop_items.py     # Draggable world bits
├── llm/                 # Ollama client + RAG glue
├── memory/              # ChromaDB + embeddings
├── personality/         # Observer + personality engine + UI bits
├── chat/                # Chat + topic filter
├── config/              # LLM / paths
└── prompts/             # Prompts that teach the duck how to think
```

---

## Performance (honest numbers)

Rough ballparks on a normal laptop: embeddings **~10–50 ms** per memory; semantic search **~50–200 ms** at ~1k memories; LLM replies **~1–5 s** depending on model and hardware. Plan for **8 GB+ RAM** if you want the LLM comfortable.

---

## License & credits

**License:** [LICENSE](LICENSE) (MIT)

**Built with:** [PySide6](https://www.qt.io/qt-for-python) · [Ollama](https://ollama.ai) · [ChromaDB](https://www.trychroma.com/) · [sentence-transformers](https://www.sbert.net/)

---

## One-line pitch for your portfolio

**DuckMind** — a cozy desktop pet sim where **RAG-backed memory** and a **local LLM** turn care gameplay into an evolving character: *game loop in the front, ML systems in the back, duck in the middle.*

If you open an issue saying hi, the duck cannot read GitHub — but the human author will, and they will be happy you visited.
