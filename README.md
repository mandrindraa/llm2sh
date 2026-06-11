<div align="center">

```
 _ _           ____      _     
| | |_ __ ___ |___ \ ___| |__  
| | | '_ ` _ \  __) / __| '_ \ 
| | | | | | | |/ __/\__ \ | | |
|_|_|_| |_| |_|_____|___/_| |_|

```

**Type what you want. Get the command that does it.**

[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![Textual](https://img.shields.io/badge/TUI-Textual-000000?style=flat-square)](https://textual.textualize.io)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-f97316?style=flat-square)](CONTRIBUTING.md)
[![Educational](https://img.shields.io/badge/Purpose-Educational-8b5cf6?style=flat-square)](#-educational-purpose)

</div>

---

##  What Is llm2sh?

**llm2sh** is an **open-source, educational** terminal application that translates plain English into Unix/Linux shell commands — directly inside a rich, interactive TUI.

No more Googling `find` flags at 2am. No more `man` page spelunking. Just describe what you want:

```
> "find all log files larger than 50MB modified in the last 3 days"
```
```bash
$ find / -name "*.log" -size +50M -mtime -3
```

llm2sh shows you the command, explains every part of it, warns you if it's dangerous, and lets you run it — all without leaving your terminal.

---

##  Educational Purpose

**llm2sh** is built as an **educational project** with two goals:

1. **Help people learn Unix/Linux** — every generated command comes with a detailed explanation. llm2sh is not a crutch; it's a teacher. You'll understand *why* a command works, not just copy-paste it blindly.

2. **Learn how to build LLM-powered terminal apps in Python** — the codebase is written to be read. Every module is documented, every architectural decision explained.

> **"The best way to learn the shell is to use it. The best way to use it is to understand it."**

---

##  Demo

```
╔══════════════════════════════════════════════════════════════════╗
║   llm2sh  v0.1.0               [Translate] [Explain] [Script] ║
╠══════════════════╦═══════════════════════════════════════════════╣
║  HISTORY         ║  RESULT                                       ║
║  ─────────────   ║  ─────────────────────────────────────────    ║
║  > list pdfs     ║  $ find . -name "*.log" -size +50M -mtime -3  ║
║  > compress logs ║                                               ║
║  > find big dirs ║   Explanation                               ║
║                  ║  Search the entire filesystem for files       ║
║                  ║  named *.log that are larger than 50MB and    ║
║                  ║  were modified in the last 3 days.            ║
║                  ║                                               ║
║                  ║  🏳 Flags                                     ║
║                  ║  -name   filter by filename pattern           ║
║                  ║  -size   filter by file size (+50M = over 50) ║
║                  ║  -mtime  filter by modification time in days  ║
║                  ║                                               ║
║                  ║  Risk:  SAFE                                ║
║                  ║                                               ║
║                  ║  [▶ Run]  [⎘ Copy]  [✎ Refine]  [ Save]   ║
╠══════════════════╩═══════════════════════════════════════════════╣
║  > find all log files larger than 50MB modified in last 3 days   ║
╚══════════════════════════════════════════════════════════════════╝
```

---

##  Features

| Feature | Description |
|---|---|
|  **NL → Command** | Describe what you want in plain English, get the exact shell command |
|  **Explain Mode** | Every command comes with a breakdown of each flag and what it does |
|  **Reverse Mode** | Paste any command, get a plain-English explanation (`Ctrl+X`) |
|  **Safety Validator** | Dangerous commands (`rm -rf`, `dd`, `mkfs`) are flagged before execution |
|  **Dry Run** | Preview what a command would do without actually executing it |
|  **In-TUI Execution** | Run commands directly from the interface and see live output |
|  **Pipeline Support** | Generate complex multi-command pipelines from a single sentence |
|  **Script Generator** | Describe a multi-step workflow, get a complete Bash script |
|  **Refinement Loop** | Follow up with "but only for .py files" and llm2sh adapts the last command |
|  **Clipboard Copy** | Copy any command to your clipboard instantly (`Ctrl+C`) |

---

##  Installation

### Prerequisites

- Python **3.14+**
- An **OpenAI API key** ([get one here](https://platform.openai.com/api-keys))
- `uv` package manager ([install](https://docs.astral.sh/uv/getting-started/installation/)) — recommended
  - or `pip` if you prefer

### Install with `uv` (recommended)

```bash
# Clone the repository
git clone https://github.com/mandrindraa/llm2sh.git
cd llm2sh

# Install dependencies
uv sync

# Set your API key
cp .env.example .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Run llm2sh
uv run llm2sh
```

### Install with `pip`

```bash
git clone https://github.com/mandrindraa/llm2sh.git
cd llm2sh

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e .

cp .env.example .env
# Add your OPENAI_API_KEY to .env

python -m llm2sh
```

### Install as a global tool with `pipx`

```bash
pipx install git+https://github.com/mandrindraa/llm2sh.git
# Then run from anywhere:
llm2sh
```

---

##  Configuration

llm2sh is configured via a `.env` file at the project root. Copy the example and fill in your values:

```bash
cp .env.example .env
```

```ini
# .env

# Required
OPENAI_API_KEY=sk-your-key-here

# Optional — defaults shown
LLM2SH_MODEL=gpt-4o          # OpenAI model to use
LLM2SH_SHELL=bash             # Your shell (bash, zsh, fish)
LLM2SH_THEME=dark             # TUI theme: dark | light
LLM2SH_DRY_RUN=false          # Always preview, never execute
LLM2SH_HISTORY_SIZE=10        # How many past commands to include as context
```

> **Note:** llm2sh never sends your API key anywhere except directly to OpenAI's API. Your shell history context is only used locally to build better prompts.

---

##  Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` | Submit query |
| `Ctrl+R` | Run the generated command |
| `Ctrl+C` | Copy command to clipboard |
| `Ctrl+E` | Toggle explain mode |
| `Ctrl+X` | Toggle reverse mode (command → explanation) |
| `Ctrl+S` | Save command to a script file |
| `Ctrl+K` | Kill a running process |
| `Ctrl+H` | Toggle history panel |
| `Ctrl+,` | Open settings |
| `Esc` | Clear input / cancel |

---

##  Project Structure

```
llm2sh/
├── llm2sh/
│   ├── core/
│   │   ├── client.py        # OpenAI API wrapper (async, streaming)
│   │   ├── processor.py     # Prompt builder + context collector
│   │   ├── validator.py     # Safety rules + risk classification
│   │   ├── executor.py      # Shell command execution
│   │   └── models.py        # Pydantic data models
│   │
│   ├── tui/
│   │   ├── app.py           # Main Textual app
│   │   ├── screens/         # TUI screens (main, settings, onboarding)
│   │   ├── widgets/         # UI components (panels, modals)
│   │   └── styles/          # Textual CSS themes
│   │
│   ├── config.py            # App configuration (pydantic-settings)
│   └── utils/               # Helpers (history reader, highlighter)
│
├── tests/                   # Unit tests (pytest)
├── pyproject.toml           # Dependencies and project metadata
├── .env.example             # Configuration template
└── README.md
```

Want to understand how it all fits together? Start with [`llm2sh/core/client.py`](llm2sh/core/client.py) — it's the heart of the app.

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14+ |
| LLM | OpenAI API (GPT-4o) |
| TUI | [Textual](https://textual.textualize.io/) |
| Data validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Config | pydantic-settings + python-dotenv |
| Packaging | [uv](https://docs.astral.sh/uv/) + pyproject.toml |
| Testing | pytest + pytest-asyncio |

---

##  Contributing

llm2sh is an open-source educational project and **contributions are warmly welcome** — whether you're fixing a typo, adding a feature, improving the prompts, or writing a tutorial.

### Getting Started

```bash
# Fork and clone the repo
git clone https://github.com/mandrindraa/llm2sh.git
cd llm2sh

# Install with dev dependencies
uv sync --extra dev

# Run the tests
uv run pytest

# Run the linter
uv run ruff check .
```

### Ways to Contribute

-  **Bug reports** — open an issue with steps to reproduce
-  **Feature suggestions** — open a discussion before implementing large features
-  **Documentation** — improve the README, add docstrings, write tutorials
-  **Tests** — add unit or integration tests for untested modules
-  **TUI improvements** — new themes, better layouts, accessibility fixes
-  **Prompt improvements** — better system prompts, edge case handling

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

### Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/). Be kind, be constructive, be excellent to each other.

---

##  Learning Resources

If you're using llm2sh to learn, here are some resources to go deeper:

**Unix/Linux Commands**
- [The Linux Command Line (free book)](https://linuxcommand.org/tlcl.php) — the best free resource for learning the shell
- [explainshell.com](https://explainshell.com) — paste any command and see each part explained
- [tldr-pages](https://tldr.sh/) — simplified man pages with practical examples

**Python & This Codebase**
- [Textual Documentation](https://textual.textualize.io/) — learn the TUI framework used here
- [OpenAI Python SDK](https://github.com/openai/openai-python) — the official client used for API calls
- [Pydantic v2 Docs](https://docs.pydantic.dev/) — understand how data validation works in this project
- [Real Python — Async IO](https://realpython.com/async-io-python/) — async Python patterns used throughout

---

##  Roadmap

- [x] Core NL → command engine
- [x] 3-panel Textual TUI
- [x] Safety validator + execution
- [x] Reverse mode & script generator
- [ ] Shell history learning (personalized suggestions)
- [ ] Project context detection (git, Docker, Node, Python...)
- [ ] Export session as annotated Bash script
- [ ] Agentic mode: multi-step task planning and execution

See [SPEC.md](SPEC.md) for the full project specification and architecture documentation.

---

##  License

llm2sh is released under the **MIT License** — free to use, fork, learn from, and build upon.

See [LICENSE](LICENSE) for the full text.

---

##  Acknowledgements

- [Textual](https://github.com/Textualize/textual) by Will McGugan — the incredible TUI framework powering this app
- [OpenAI](https://openai.com) — the API making the translation magic happen
- The Unix philosophy — for inspiring 50+ years of composable, powerful tools

---

<div align="center">

Built with ❤️ for the terminal lovers and the curious learners.

**[⭐ Star this repo](https://github.com/mandrindraa/llm2sh)** if you find it useful or educational!

</div>