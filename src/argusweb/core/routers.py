
from argusweb.core.state import AgentState
from langgraph.types import Command
from langchain_core.messages import SystemMessage


def executor_router(state: AgentState) -> str:
    if state.goto is not None:
        return state.goto
    if state.messages and getattr(state.messages[-1], "tool_calls", None) is not None:
        return "tools"
    
    if state.current_step >= len(state.plan):
        return "__end__"

    return "executor"



def tool_router(state: AgentState)  -> str | Command:
    node_map = {
            "Executor Node" : "executor",
            "Recovery Node" : "recovery"
        }
    for msg in reversed(state.messages):
        if msg.type == "ai" and getattr(msg, "tool_calls", None):
            if msg.name in node_map:
                return node_map[msg.name]
    system_msg = SystemMessage(content="Tool was called non - deterministically, no reason found.")
    return Command(
        update={"messages" : [system_msg]},
        goto="__end__"
    )


    
def recovery_router(state: AgentState) -> str :
    if state.messages :
        last_msg = state.messages[-1]
        if getattr(last_msg, "tool_calls", None):
            return "tools"
        if isinstance(last_msg.content, str) and last_msg.content.startswith("No blocker found."):
            return "executor"


    return "recovery"