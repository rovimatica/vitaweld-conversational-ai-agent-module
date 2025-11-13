from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition
from langchain_core.runnables import RunnableConfig
from config import Config
from init import setup_environment
import ray

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
    def __init__(self, tools):
        self.tools = {getattr(t, "__name__", None): t for t in tools}

    async def __call__(self, state, config):
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage) or not getattr(last_message, "tool_calls", None):
            return {"messages": []}

        thread_id = (config or {}).get("configurable", {}).get("thread_id", "default")
        tool_messages = []

        for tc in last_message.tool_calls:
            name = tc["name"]
            tool = self.tools.get(name)
           
            if tool is None:
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: Tool '{tc['name']}' not found",
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    )
                )
                continue

            args = _flatten_tool_args(tc.get("args"), tc["id"], thread_id, state["messages"])

            try:
                running = tool(args)
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps(running),
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    )
                )
            except Exception as e:
                tool_messages.append(
                    ToolMessage(
                        content=f"Error ejecutando tool {tc['name']}: {e}",
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    )
                )

        return {"messages": tool_messages}

class VitaweldAssistant:
    def __init__(self):
        self.config = Config()
        self.model = setup_environment(self.config)
        self.tools = [] # List of tools to be used by the assistant
        self.graph = self._create_graph()

    def _create_graph(self):
        """Crea y configura el grafo de conversación."""
        graph = StateGraph(MessagesState)

        graph.add_node("call_model", self._call_model)
        graph.add_node("tools", RayToolNode(self.tools))
        
        graph.add_edge(START, "call_model")
        graph.add_conditional_edges("call_model", tools_condition)
        graph.add_edge("tools", "call_model")
        
        return graph.compile(checkpointer=Config.MEMORY)

    async def _call_model(self, state: MessagesState, config: RunnableConfig):

        messages = state["messages"]
        system_msg = SystemMessage(content=Config.SYSTEM_PROMPT)

        last_human_index = None
        for i in reversed(range(len(messages))):
            if isinstance(messages[i], HumanMessage):
                last_human_index = i
                break

        if last_human_index is None:
            relevant_msgs = [msg for msg in messages if isinstance(msg, (HumanMessage, AIMessage, ToolMessage))]
        else:
            relevant_msgs = [messages[last_human_index]]
            for j in range(last_human_index + 1, len(messages)):
                msg = messages[j]       
                if isinstance(msg, AIMessage) or isinstance(msg, ToolMessage):
                    relevant_msgs.append(msg)
                else:
                    break

        if len(relevant_msgs) == 0:
            relevant_msgs.append(HumanMessage(content=""))

        sanitized_messages = []
        for msg in relevant_msgs:
            if isinstance(msg, (HumanMessage, AIMessage, ToolMessage)):
                sanitized_messages.append(msg)

        full_messages = [system_msg] + sanitized_messages

        has_valid_message = any(isinstance(m, (HumanMessage, AIMessage)) for m in full_messages)
        if not has_valid_message:
            full_messages.append(HumanMessage(content=""))

        response = await self.model.bind_tools(self.tools, tool_choice="auto").ainvoke(full_messages,config)
        return {"messages": [response]}

    async def talk(self):
        """Start the conversation with the assistant."""

        print("\nI am VITAWELD's assistant.. How may I assist you?\n")
        
        while True:
            user_input = input("User:\n")
            exit_keys = ["exit", "quit", "bye"]
            if user_input.lower() in exit_keys:
                print("Bye!")
                break

                
            input_msg = HumanMessage(content=user_input)
            result = await self.graph.ainvoke({"messages": [input_msg]}, config=self.config.CONFIG)
            
            if 'messages' in result and result['messages']:
                print()
                result['messages'][-1].pretty_print()
                print()

