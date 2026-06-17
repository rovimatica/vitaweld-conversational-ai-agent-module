# Basic Demo

This demo shows the agent **reasoning and invoking tools**, including the
**parallel, non-blocking** execution of a long-running tool. It runs entirely
without industrial hardware, using two neutral example tools.

> Make sure you have completed
> [`03_installation_and_hello_world.md`](03_installation_and_hello_world.md)
> first (dependencies installed and `config.py` configured).

## 1. The example tools

The demo registers two tools from `examples/example_tool.py`:

| Tool | Behaviour | Purpose |
|---|---|---|
| `get_current_time` | Returns the current date and time instantly | Shows a simple, fast tool call |
| `run_welding_cycle` | **Simulated** long action (`time.sleep`) running in a Ray worker | Shows a slow tool that does **not** block the conversation |

> **Note:** `run_welding_cycle` is a **simulation stub** (a timed sleep), not the
> proprietary welding tool from the demonstrator. It exists only to illustrate
> non-blocking, long-running tool execution.

## 2. Running the demo

From the project root:

```bash
python examples/basic_demo.py
```

## 3. Suggested interaction

**a) Fast tool**

```
User:
What time is it?
```

The agent decides to call `get_current_time`, executes it, and reports the time
in natural language.

**b) Long-running, non-blocking tool**

```
User:
Weld piece A12 for 20 seconds.
```

The agent dispatches `run_welding_cycle` as a background Ray task and immediately
acknowledges that the job has **started** (with a job id), instead of freezing.
You can keep chatting straight away:

```
User:
While that runs, what time is it?
```

The agent answers the new question while the welding cycle is still running.
After ~20 seconds, the finished result is surfaced **asynchronously** as a
follow-up message, and the agent reports the completed cycle in natural language.

<div align="center">

  <img src="media/screenshots/tutorial_basic_demo.png" alt="VITAWELD Conversational AI Agent" width="720" />

</div>

## 4. Expected behaviour summary

- Tool calls are decided by the model (ReAct), not hard-coded.
- A long tool **does not block** new requests (parallel Ray execution).
- Tool results may arrive **as a follow-up message** once the background task
  finishes, rather than inline in the same turn.

## 5. Evidence

- Screenshot: [`../media/screenshots/tutorial.png`](../media/screenshots/tutorial.png)
- Screenshot: [`../media/screenshots/tutorial_basic_demo.png`](../media/screenshots/tutorial_basic_demo.png)
- Full TRL6-7 demonstrator video: see [`../media/video_link.md`](../media/video_link.md)
