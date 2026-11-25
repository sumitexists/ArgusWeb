from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from argusweb.core.state import (InputState, AgentState)
from argusweb.core.routers import (tool_router, executor_router, recovery_router)
from argusweb.core.nodes import (planner_node, executor_node, recovery_node)
from argusweb.tools import (mouse_action,close_browser, navigate_to, mouse_click)
tools = [ mouse_action,  close_browser,  navigate_to, mouse_click]

workflow = StateGraph(
    state_schema=AgentState, 
    input_schema=InputState)

#Adding nodes to the graph
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("recovery", recovery_node)
workflow.add_node("tools", ToolNode(tools=tools, handle_tool_errors=True))

#Adding edges
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")

#Adding condtional edges
workflow.add_conditional_edges("executor", 
                               executor_router,
                               {
                                   "recovery" : "recovery",
                                   "tools" : "tools",
                                   "executor" : "executor",
                                   "__end__" : END
                               }
                               )
workflow.add_conditional_edges("tools", 
                               tool_router,
                               {
                                   "executor" : "executor",
                                   "recovery" : "recovery",
                                   "__end__" : END
                               })
workflow.add_conditional_edges("recovery", 
                               recovery_router,
                               {
                                   "tools" : "tools",
                                   "executor" : "executor",
                                   "recovery" : "recovery"
                               }
                               )

app = workflow.compile()


async def main():
    user_input = InputState(user_goal="Go on the steam website and serach me for cs2")

    messages = await app.ainvoke(user_input)
    for message in messages:
        if hasattr(message, "pretty_print"):
            message.pretty_print()
        else:
            print(message)


if __name__ == "__main__":
    from IPython.display import Image
    img = Image(app.get_graph().draw_mermaid_png())
    with open("graph.png", "wb") as f:
        f.write(img.data)  # Saves to disk
    import asyncio
    asyncio.run(main())