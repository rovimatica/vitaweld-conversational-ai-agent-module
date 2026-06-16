from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition
from langchain_core.runnables import RunnableConfig
from src.vitaweld_agent.config import Config
from src.vitaweld_agent.init import setup_environment
import ray
import json
import os
import asyncio
import uuid
from pathlib import Path

# Project root (the folder that contains ``src`` and ``examples``). Ray workers
# are separate processes, so they need this on their PYTHONPATH to be able to
# import the tool functions by reference.
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])

def _plain_fn(tool):
    """Return the original undecorated function.

    Tools are ``@ray.remote``-decorated, so the plain Python function lives on
    the wrapper's ``_function`` attribute. Falls back to the object itself for
    an undecorated callable.
    """
    return getattr(tool, "_function", tool)


def _tool_name(tool) -> str:
    """Name the model uses to call the tool (the original function name)."""
    return getattr(_plain_fn(tool), "__name__", None)


def _flatten_tool_args(original_args: dict, tool_call_id: str, thread_id: str, messages) -> dict:
    args = dict(original_args or {})
    if "input_dict" in args and isinstance(args["input_dict"], dict):
        base = dict(args["input_dict"])
    else:
        base = dict(args)
    base["tool_call_id"] = tool_call_id
    base["thread_id"]    = thread_id
    return base

class RayToolNode:
    def __init__(self, tools, on_dispatch=None):
        # Tools are already ``@ray.remote``-decorated, so they are keyed by the
        # original function name and dispatched later via ``.remote(args)``.
        self.tools = {_tool_name(t): t for t in tools}
        # Callback(job_id, name, obj_ref) invoked right after dispatch so the
        # assistant can await the Ray result in the background.
        self.on_dispatch = on_dispatch

    async def __call__(self, state, config):
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage) or not getattr(last_message, "tool_calls", None):
            return {"messages": []}

        thread_id = (config or {}).get("configurable", {}).get("thread_id", "default")

        # Fire-and-forget: dispatch each tool as a Ray task and return control
        # immediately with a "started" acknowledgement. The real result is
        # awaited in the background (see VitaweldAssistant._await_job) and fed
        # back into the conversation when ready, so a running tool never blocks
        # new requests to the LLM.
        tool_messages = []
        for tc in last_message.tool_calls:
            name = tc["name"]
            remote_tool = self.tools.get(name)
            if remote_tool is None:
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: Tool '{name}' not found",
                        tool_call_id=tc["id"],
                        name=name,
                    )
                )
                continue

            args = _flatten_tool_args(tc.get("args"), tc["id"], thread_id, state["messages"])
            obj_ref = remote_tool.remote(args)
            job_id = uuid.uuid4().hex[:8]

            if self.on_dispatch is not None:
                self.on_dispatch(job_id, name, obj_ref)

            tool_messages.append(
                ToolMessage(
                    content=json.dumps({
                        "status": "started",
                        "job_id": job_id,
                        "message": (
                            f"Tarea '{name}' lanzada en segundo plano (job {job_id}). "
                            "Avisaré al usuario en cuanto termine; puede seguir preguntando."
                        ),
                    }),
                    tool_call_id=tc["id"],
                    name=name,
                )
            )

        return {"messages": tool_messages}

class VitaweldAssistant:
    def __init__(self):
        self.config = Config()
        self.model = setup_environment(self.config)
        # Start a local Ray runtime (no-op if one is already running) so the
        # RayToolNode can dispatch tools as remote tasks. The project root is
        # added to the workers' PYTHONPATH so they can import the tool modules.
        if not ray.is_initialized():
            existing = os.environ.get("PYTHONPATH", "")
            pythonpath = PROJECT_ROOT + (os.pathsep + existing if existing else "")
            ray.init(
                ignore_reinit_error=True,
                runtime_env={"env_vars": {"PYTHONPATH": pythonpath}},
            )
        # Background-job machinery: tools are fire-and-forget, so their results
        # are awaited off the main turn and surfaced when ready. The lock
        # serialises graph access between the user's turn and the watcher.
        self._results = asyncio.Queue()
        self._jobs = set()
        self._graph_lock = asyncio.Lock()
        self.tools = [] # List of tools to be used by the assistant
        self.graph = self._create_graph()

    def _create_graph(self):
        """Crea y configura el grafo de conversación."""
        graph = StateGraph(MessagesState)

        graph.add_node("call_model", self._call_model)
        graph.add_node("tools", RayToolNode(self.tools, on_dispatch=self._register_job))
        
        graph.add_edge(START, "call_model")
        graph.add_conditional_edges("call_model", tools_condition)
        graph.add_edge("tools", "call_model")
        
        return graph.compile(checkpointer=Config.MEMORY)

    async def _call_model(self, state: MessagesState, config: RunnableConfig):

        messages = state["messages"]
        system_msg = SystemMessage(content=Config.SYSTEM_PROMPT)

        # Send the full conversation history (persisted by the checkpointer for
        # this thread_id) so the model keeps memory across turns.
        full_messages = [system_msg] + list(messages)

        # Guard: the model needs at least one human/AI message to respond to.
        if not any(isinstance(m, (HumanMessage, AIMessage)) for m in messages):
            full_messages.append(HumanMessage(content=""))

        # bind_tools needs the plain functions to build each tool's schema; the
        # @ray.remote wrappers cannot be introspected.
        plain_tools = [_plain_fn(t) for t in self.tools]
        response = await self.model.bind_tools(plain_tools, tool_choice="auto").ainvoke(full_messages,config)
        return {"messages": [response]}

    def _register_job(self, job_id, name, obj_ref):
        """Schedule a background task to await a dispatched Ray tool result.

        Called synchronously from the tool node right after ``.remote(args)``,
        so it must not block: it only spawns the awaiter task.
        """
        task = asyncio.create_task(self._await_job(job_id, name, obj_ref))
        # Keep a strong reference so the task is not garbage-collected mid-flight.
        self._jobs.add(task)
        task.add_done_callback(self._jobs.discard)

    async def _await_job(self, job_id, name, obj_ref):
        """Await a Ray object ref off the main turn and queue its outcome."""
        try:
            result = await obj_ref
            await self._results.put((job_id, name, result, None))
        except Exception as e:
            await self._results.put((job_id, name, None, str(e)))

    async def _watch_results(self):
        """Feed finished tool results back into the conversation as new turns."""
        while True:
            job_id, name, result, error = await self._results.get()
            if error is not None:
                note = (
                    f"[Aviso del sistema] La tarea en segundo plano '{name}' "
                    f"(job {job_id}) ha fallado: {error}. Informa al usuario."
                )
            else:
                note = (
                    f"[Aviso del sistema] La tarea en segundo plano '{name}' "
                    f"(job {job_id}) ha terminado con resultado: {json.dumps(result)}. "
                    "Informa al usuario del resultado de forma natural."
                )

            # Serialise against the user's turn so both don't write the shared
            # checkpoint concurrently.
            async with self._graph_lock:
                out = await self.graph.ainvoke(
                    {"messages": [HumanMessage(content=note)]}, config=self.config.CONFIG
                )

            print()
            if out.get("messages"):
                out["messages"][-1].pretty_print()
            print("\nUser:")

    async def talk(self):
        """Start the conversation with the assistant."""

        print("\nI am VITAWELD's assistant.. How may I assist you?\n")

        # Background task that surfaces finished tool jobs without blocking input.
        watcher = asyncio.create_task(self._watch_results())

        try:
            while True:
                # ``input`` runs in a thread so the event loop stays free to
                # progress background tool jobs while we wait for the user.
                user_input = await asyncio.to_thread(input, "User:\n")
                exit_keys = ["exit", "quit", "bye"]
                if user_input.lower() in exit_keys:
                    print("Bye!")
                    break

                input_msg = HumanMessage(content=user_input)
                async with self._graph_lock:
                    result = await self.graph.ainvoke(
                        {"messages": [input_msg]}, config=self.config.CONFIG
                    )

                if 'messages' in result and result['messages']:
                    print()
                    result['messages'][-1].pretty_print()
                    print()
        finally:
            watcher.cancel()

