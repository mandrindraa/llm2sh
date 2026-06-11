# llm2sh — Natural Language to Unix Command Translator
### Project Specification Document

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Perimeter](#2-project-perimeter)
3. [Technology Stack](#3-technology-stack)
4. [Libraries & Dependencies](#4-libraries--dependencies)
5. [Architecture](#5-architecture)
6. [Implementation Plan](#6-implementation-plan)
7. [TUI Design & UX](#7-tui-design--ux)
8. [OpenAI Integration](#8-openai-integration)
9. [Safety & Error Handling](#9-safety--error-handling)
10. [File Structure](#10-file-structure)
11. [Future Roadmap](#11-future-roadmap)

---

## 1. Project Overview

**llm2sh** is a terminal-based application that allows users to describe what they want to do in plain English and receive accurate, ready-to-execute Unix/Linux shell commands. Powered by the OpenAI API and built with a rich TUI (Text User Interface), it bridges the gap between human intent and shell syntax — serving both beginners learning the terminal and experts who want to move faster.

### Key Value Propositions

- Translate natural language into precise Unix commands instantly
- Explain what each generated command does, flag by flag
- Detect and warn about potentially destructive commands before execution
- Support iterative refinement through natural follow-up queries
- Work entirely inside the terminal — no browser, no context switching

---

## 2. Project Perimeter

### In Scope

| Feature | Description |
|---|---|
| NL → Command translation | Convert plain English descriptions into Unix/Linux shell commands |
| Command explanation | Break down each command and its flags in human-readable language |
| Reverse mode | Paste a command, get a plain-English explanation |
| Safety validation | Detect dangerous commands and require explicit user confirmation |
| Dry-run preview | Show what a command would do without executing it |
| Command execution | Optionally run the generated command directly from the TUI |
| Shell history context | Use recent command history to produce more relevant suggestions |
| Session memory | Remember previous queries within the same session |
| Pipeline support | Generate complex multi-command pipelines from a single query |
| Script generation | Generate full Bash scripts from multi-step descriptions |

### Out of Scope (v1)

- GUI or web interface
- Support for Windows (PowerShell / CMD)
- Cloud sync or persistent history across machines
- Multi-user or collaborative features
- Plugin marketplace

### Target Platforms

- Linux (Debian, Ubuntu, Arch, Fedora)
- macOS (via Terminal or iTerm2)
- Any POSIX-compliant shell: `bash`, `zsh`, `fish`

---

## 3. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.14+ | Rich ecosystem, excellent TUI and AI libraries |
| LLM Backend | OpenAI API (GPT-4o) | Best-in-class instruction following and code generation |
| TUI Framework | Textual | Modern, async-native, CSS-styled TUI for Python |
| Shell Execution | Python `subprocess` | Safe, cross-platform command execution |
| Configuration | `pydantic-settings` + `.env` | Typed config management with env var support |
| Packaging | `uv` + `pyproject.toml` | Fast, modern Python packaging and dependency management |

---

## 4. Libraries & Dependencies

### Core Dependencies

```toml
[project]
name = "llm2sh"
version = "0.1.0"
requires-python = ">=3.14"

dependencies = [
    "aiofiles>=25.1.0", # async I/O file
    "openai>=2.40.0",
    "pydantic>=2.13.4",
    "pydantic-settings>=2.14.1",
    "pyperclip>=1.11.0",
    "python-dotenv>=1.2.2",
    "rich>=15.0.0",
    "textual>=8.2.7",
]
```

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-textual-snapshot>=0.4.0",  # TUI snapshot testing
    "ruff>=0.4.0",                     # Linting and formatting
    "mypy>=1.10.0",                    # Static type checking
]
```

### Library Roles

**Textual** — The TUI engine. Handles layout, widgets, keyboard events, async rendering, and CSS-based styling. Chosen over alternatives (`curses`, `urwid`, `blessed`) for its modern async-first design and rich component library.

**OpenAI SDK** — Official Python client for the OpenAI API. Used for streaming completions, managing conversation history, and function calling where structured outputs are needed.

**Pydantic + pydantic-settings** — Validates all structured data: the API response schema, configuration values, and user settings. Prevents runtime crashes from malformed responses.

**Rich** — Powers syntax highlighting, panels, and tables inside the TUI (Textual uses it internally; direct use is available for fine-grained control).

**pyperclip** — One-keystroke copy of generated commands to the clipboard without leaving the TUI.

---

## 5. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     llm2sh TUI                        │
│  (Textual App — async event loop)                        │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Input Panel │  │ Result Panel │  │  History Panel │  │
│  │  (query box) │  │ (command +   │  │  (session log) │  │
│  │             │  │  explanation)│  │                │  │
│  └──────┬──────┘  └──────────────┘  └────────────────┘  │
│         │                                                │
└─────────┼────────────────────────────────────────────────┘
          │ user query
          ▼
┌─────────────────────┐
│   QueryProcessor    │  ← builds prompt with context
│                     │    (OS, cwd, shell, history)
└─────────┬───────────┘
          │ enriched prompt
          ▼
┌─────────────────────┐
│   OpenAIClient      │  ← streaming call to GPT-4o
│   (async wrapper)   │    structured JSON response
└─────────┬───────────┘
          │ CommandResult (pydantic model)
          ▼
┌─────────────────────┐
│   SafetyValidator   │  ← flags: rm -rf, dd, mkfs, chmod 777...
│                     │    categorizes risk level
└─────────┬───────────┘
          │ validated result
          ▼
┌─────────────────────┐
│   ResultRenderer    │  ← formats command + explanation for TUI
│                     │    syntax highlights, adds action buttons
└─────────────────────┘
          │ user confirms execution
          ▼
┌─────────────────────┐
│   ShellExecutor     │  ← subprocess.run / dry-run mode
│                     │    captures stdout/stderr
└─────────────────────┘
```

### Core Data Models

```python
from pydantic import BaseModel
from enum import Enum

class RiskLevel(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"    # irreversible but scoped
    DANGER = "danger"      # destructive, wide-scope

class CommandResult(BaseModel):
    command: str                  # the generated shell command
    explanation: str              # plain-English breakdown
    flag_explanations: dict[str, str]  # per-flag explanations
    risk_level: RiskLevel
    risk_reason: str | None       # why it's flagged, if applicable
    is_pipeline: bool
    estimated_effect: str         # what it would do on the system
```

---

## 6. Implementation Plan

The project is divided into **4 milestones**, each producing a working, testable increment.

---

### Milestone 1 — Core Engine

**Goal:** Working NL → command translation in the terminal, no TUI yet.

#### Tasks

- [✔️] Set up project structure with `uv` and `pyproject.toml`
- [✔️] Implement `Config` class using `pydantic-settings` (API key, model, shell type, theme)
- [✔️] Write `OpenAIClient` — async wrapper around the OpenAI SDK with streaming support
- [✔️] Design the **system prompt**: instruct the model to always return JSON matching `CommandResult`
- [✔️] Implement `QueryProcessor` — collects OS info, current shell, `$CWD`, last 10 history entries
- [✔️] Implement `SafetyValidator` — rule-based + LLM-assisted risk classification
- [✔️] Write unit tests for the engine components
- [✔️] CLI smoke test: `python -m llm2sh "list all files larger than 10MB"`

#### Deliverable

A Python script that accepts a string and prints a formatted command + explanation to stdout.

---

### Milestone 2 — TUI Shell

**Goal:** Full Textual TUI with the core three-panel layout.

#### Tasks

- [✔️] Scaffold `Textual` app with CSS layout
- [✔️] Build **InputPanel**: query input box, mode toggle (Translate / Explain / Script), submit button
- [✔️] Build **ResultPanel**: syntax-highlighted command display, explanation section, action buttons (Run / Copy / Refine / Save)
- [✔️] Build **HistoryPanel**: scrollable session log with clickable past queries
- [✔️] Wire TUI to the core engine (async message passing)
- [✔️] Implement streaming response — tokens stream into the ResultPanel in real time
- [✔️] Add keyboard shortcuts: `Ctrl+Enter` submit, `Ctrl+C` copy, `Ctrl+R` run, `Ctrl+E` explain, `Esc` clear
- [✔️] Implement `pyperclip` clipboard integration

#### Deliverable

A functional TUI that accepts queries and displays results with streaming.

---

### Milestone 3 — Execution & Safety

**Goal:** Safe command execution and all safety UX flows.

#### Tasks

- [✔️] Implement `ShellExecutor` with dry-run and live modes
- [✔️] Build **ConfirmationModal** for CAUTION and DANGER commands
- [✔️] Display execution output (stdout/stderr) inside the TUI in a dedicated output pane
- [✔️] Implement `--dry-run` global flag: show effect without executing
- [✔️] Add execution result to session history
- [✔️] Handle long-running commands: show spinner, allow `Ctrl+K` to kill process

#### Deliverable

Users can safely run commands from within the TUI, with risk warnings and confirmation dialogs.

---

### Milestone 4 — Advanced Features & Polish

**Goal:** Script generation, reverse mode, refinement loop, final UX polish.

#### Tasks

- [ ] **Reverse mode**: paste a command → get explanation (toggle with `Ctrl+X`)
- [ ] **Script generator**: multi-step NL → full bash script with shebang, comments, error handling
- [ ] **Iterative refinement**: follow-up queries that build on the previous command
- [ ] **Context awareness**: auto-detect distro, shell version, available tools (`which fzf`, etc.)
- [ ] Settings screen: theme, default shell, model selection, API key management
- [ ] First-run onboarding: API key prompt, quick tutorial
- [ ] Full README with install instructions, demo GIF
- [ ] Package as `pipx`-installable tool

#### Deliverable

Feature-complete v1.0 ready for public release.

---

## 7. TUI Design & UX

### Layout (3-Panel)

```
╔══════════════════════════════════════════════════════════════╗
║  llm2sh  v0.1.0          [Translate] [Explain] [Script]  ║
╠══════════════════════╦═══════════════════════════════════════╣
║                      ║                                       ║
║   HISTORY            ║   RESULT                              ║
║   ─────────          ║   ──────                              ║
║   > list pdfs...     ║   $ find . -name "*.pdf" -mtime -7   ║
║   > compress logs    ║                                       ║
║   > find big dirs    ║   Explanation:                        ║
║                      ║   Find all .pdf files modified in     ║
║                      ║   the last 7 days in the current dir  ║
║                      ║                                       ║
║                      ║   Risk: ✅ SAFE                       ║
║                      ║                                       ║
║                      ║   [▶ Run] [⎘ Copy] [✎ Refine] [💾]  ║
╠══════════════════════╩═══════════════════════════════════════╣
║  > Describe what you want...                    [Ctrl+Enter] ║
╚══════════════════════════════════════════════════════════════╝
```

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` | Submit query |
| `Ctrl+R` | Run the generated command |
| `Ctrl+C` | Copy command to clipboard |
| `Ctrl+E` | Toggle explain mode |
| `Ctrl+X` | Toggle reverse mode (command → explanation) |
| `Ctrl+S` | Save command to a script file |
| `Ctrl+K` | Kill running process |
| `Ctrl+H` | Toggle history panel |
| `Ctrl+,` | Open settings |
| `Esc` | Clear / cancel |

### Risk Level Visual Design

| Level | Color | Icon | Behavior |
|---|---|---|---|
| SAFE | Green | 🟢 | Run button active immediately |
| CAUTION | Yellow | 🟡 | Single confirmation dialog |
| DANGER | Red | 🔴 | Double confirmation + forced 3s wait |

---

## 8. OpenAI Integration

### System Prompt Design

```python
SYSTEM_PROMPT = """
You are llm2sh, an expert Unix/Linux shell assistant.
Your job is to convert natural language requests into precise shell commands.

Rules:
- Always respond with a valid JSON object matching the schema provided.
- Prefer POSIX-compliant commands unless the user's shell is specified.
- Never guess — if a request is ambiguous, include a clarifying_question field.
- Flag any command that is irreversible, destructive, or affects system-wide state.
- Keep explanations concise but complete. Explain each flag used.

Context you will receive:
- User's operating system and distro
- Current working directory
- Shell type and version
- Last 10 commands from shell history
- Previous queries in this session (for refinement)

Response schema:
{
  "command": "string",
  "explanation": "string",
  "flag_explanations": {"flag": "explanation"},
  "risk_level": "safe | caution | danger",
  "risk_reason": "string | null",
  "is_pipeline": boolean,
  "estimated_effect": "string",
  "clarifying_question": "string | null"
}
"""
```

### Context Injection

```python
def build_context() -> dict:
    return {
        "os": platform.system(),
        "distro": distro.name() if platform.system() == "Linux" else None,
        "shell": os.environ.get("SHELL", "bash"),
        "cwd": os.getcwd(),
        "history": get_recent_history(n=10),
    }
```

### Streaming

The OpenAI response streams token by token into the TUI's ResultPanel, giving the user immediate visual feedback rather than a blank wait screen.

---

## 9. Safety & Error Handling

### Dangerous Pattern Detection

In addition to the LLM's own risk classification, a local rule-based validator runs as a secondary check:

```python
DANGER_PATTERNS = [
    r"rm\s+-rf\s+/",          # rm -rf /
    r"dd\s+.*of=/dev/[sh]d",  # dd to raw disk
    r"mkfs\.",                 # format filesystem
    r"chmod\s+-R\s+777\s+/",  # recursive 777 on root
    r">\s*/dev/[sh]d",        # redirect to raw disk
    r"fork\s*bomb",            # :(){ :|: & };:
    r"wget.*\|\s*sh",          # remote script piped to shell
    r"curl.*\|\s*(ba)?sh",     # remote script piped to shell
]
```

### Error Handling Strategy

| Error Type | Handling |
|---|---|
| OpenAI API error | Retry with exponential backoff (3 attempts), then show user-friendly message |
| Invalid JSON response | Re-prompt model once with stricter instructions; fall back to raw text |
| Command execution error | Display stderr in output pane, offer "explain this error" shortcut |
| Network timeout | Cache last response; notify user; allow retry |
| Missing API key | Redirect to settings/onboarding screen on first run |

---

## 10. File Structure

```
llm2sh/
├── pyproject.toml
├── README.md
├── .env.example
│
├── llm2sh/
│   ├── __init__.py
│   ├── __main__.py              # Entry point: python -m llm2sh
│   │
│   ├── core/
│   │   ├── client.py            # OpenAIClient (async)
│   │   ├── processor.py         # QueryProcessor + context builder
│   │   ├── validator.py         # SafetyValidator
│   │   ├── executor.py          # ShellExecutor
│   │   └── models.py            # Pydantic models (CommandResult, etc.)
│   │
│   ├── tui/
│   │   ├── app.py               # Main Textual App
│   │   ├── screens/
│   │   │   ├── main.py          # Main 3-panel screen
│   │   │   ├── settings.py      # Settings screen
│   │   │   └── onboarding.py    # First-run screen
│   │   ├── widgets/
│   │   │   ├── input_panel.py
│   │   │   ├── result_panel.py
│   │   │   ├── history_panel.py
│   │   │   ├── output_pane.py
│   │   │   └── confirm_modal.py
│   │   └── styles/
│   │       ├── main.tcss        # Textual CSS (dark theme)
│   │       └── light.tcss       # Light theme
│   │
│   ├── config.py                # pydantic-settings Config
│   └── utils/
│       ├── history.py           # Shell history reader
│       └── highlight.py         # Syntax highlighting helpers
│
└── tests/
    ├── test_client.py
    ├── test_validator.py
    ├── test_processor.py
    └── test_executor.py
```

---

## 11. Future Roadmap

### v1.1 — Intelligence Upgrades
- Shell history learning: personalize suggestions based on your own past commands
- Project detection: recognize git repos, Docker projects, Node/Python projects and adapt suggestions
- Alias awareness: read `~/.bashrc` / `~/.zshrc` and respect custom aliases

### v1.2 — Collaboration & Export
- Export session as annotated Bash script
- Share a query + result as a Gist with one keystroke
- `llm2sh explain <command>` as a standalone CLI alias

### v2.0 — Agentic Mode
- Multi-step task execution: "Set up a new Python project with venv, install requests, and create a Hello World script"
- llm2sh plans and executes a sequence of commands, pausing for confirmation at each step
- Full undo stack for executed commands (where possible)

---

*Document version: 1.0 — last updated June 2026*