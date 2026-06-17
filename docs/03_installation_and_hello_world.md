# Installation and Hello World

This guide installs the **VITAWELD Conversational AI Agent** and runs a minimal
hello world **without any industrial hardware** — only Python and an LLM API key
are required.

## 1. Prerequisites

- **Python 3.11**
- An **Anthropic (Claude) API key**
- Internet access (the agent calls the LLM API; the local Ray runtime is started
  automatically on first use)

No robot, welding cell, ROS 2 or simulator is required.

## 2. Installation

Run all commands from the **project root** (the folder that contains `src/` and
`examples/`).

```bash
# 1. (Recommended) Create and activate a virtual environment
conda create -n vitaweld_conversational_agent python=3.11
conda activate vitaweld_conversational_agent 

# 2. Install the dependencies
pip install -r requirements.txt
```

Dependencies installed: `langchain-anthropic`, `langchain-core`, `langgraph`
and `ray` (pinned versions in `requirements.txt`).

## 3. Configuration

Copy the configuration template and fill in your model and API key:

```bash
cp config/config.example.py src/vitaweld_agent/config.py
```

Then edit `src/vitaweld_agent/config.py` and set at least:

```python
MODEL   = "claude-..."   # your model name/version
API_KEY = "sk-ant-..."   # your Anthropic API key
```

Optional parameters (`TEMPERATURE`, `MAX_TOKENS`, `SYSTEM_PROMPT`, `thread_id`,
memory) can be left at their defaults.

## 4. Hello World (no tools)

The simplest run starts the agent with **no tools registered**, so it performs
pure conversational reasoning. This verifies that the installation and the LLM
connection work.

```bash
python src/main.py
```

**Expected output:**

```
I am VITAWELD's assistant.. How may I assist you?

User:
```

Type a message (e.g. *"Hello, what can you do?"*). If you get a coherent reply,
the installation is correct. Exit with `exit`, `quit` or `bye`.

<div align="center">

  <img src="media/screenshots/tutorial.png" alt="VITAWELD Conversational AI Agent" width="720" />

</div>

## 5. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Authentication / 401 error | Empty or invalid `API_KEY` | Set a valid Anthropic API key in `config.py` |
| Model-not-found error | Empty or wrong `MODEL` | Set a valid model name in `config.py` |
| `ModuleNotFoundError` | Not run from the project root | Run `python src/main.py` from the folder containing `src/` |
| Hangs on first run | Local Ray runtime starting | Wait a few seconds; this only happens once per session |

To see tool execution in action, continue with
[`04_basic_demo_how_to_use.md`](04_basic_demo_how_to_use.md).
