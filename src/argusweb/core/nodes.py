from pathlib import Path
from dotenv import load_dotenv
import uuid

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenAIClassifier

from langchain_core.messages import (HumanMessage, SystemMessage, AIMessage)
from argusweb.core.state import (AgentState, InputState,PlannerOuptut, RecoveryOutput, ExecutorOutput)
from argusweb.core.prompts import (PLANNER_PROMPT, EXECUTOR_PROMPT, SELF_RECOVERY_PROMPT)
from argusweb.tools import (get_screenshot, get_snapshot)


dotenv_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=dotenv_path)


planner = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
) # Using this model to plan the task of the user in a sequential manner.


recovery = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
) # Using the model if we get into any kind of loop or not be able to execute some task, it will take over.

executor = ChatOllama(
    model="frob/qwen3.5-instruct:9b",
    base_url="http://localhost:11434",
    temperature=0.0,
    keep_alive=-1,
    num_ctx=32768,
) # Using a small low cost model to execute the single task that is in the plan.

evaluator = GoogleGenAIClassifier(model="gemini-decision-1")  #Using a decision model to check wheather the last action was enough or not to complete the task

planner = planner.with_structured_output(
    PlannerOuptut, 
    method="json_schema",
    strict=True)

recovery_with_tools = recovery.with_structured_output(
    RecoveryOutput, 
    method="json_schema",
    strict=True
    )

executor_with_tools = executor.with_structured_output(
    ExecutorOutput, 
    method="json_schema",
    strict=True
    )



async def planner_node(state: InputState) -> AgentState:
    """
    Takes user goal and plans sequential target steps.
    """


    try:
        system_message = SystemMessage(content=PLANNER_PROMPT)
        human_message = HumanMessage(content=state.user_goal, name="User")
        message = [system_message, human_message]
        response : PlannerOuptut = await planner.ainvoke(message)
        # Will produce the sequntial task to complete the complex task given by the user
        plan = response.plan
        response.name = "Planner Node"
        response = AIMessage(
            content=response.plan, 
            name = response.name)
        
        chat_history = [human_message, response]
        # Human prompt and the response by the llm

        print(response.pretty_repr()) ##PRINTING
        return {
            "plan": plan,
            "messages": chat_history,
        }

    except Exception as e:
        raise e



async def executor_node(state: AgentState) -> AgentState :
    """
        A dumb node that takes only the current plan and execute it.
    """
    
    try:
        current_attempts = state.current_attempts
        current_step = state.current_step
        
        
        if state.messages and state.messages[-1].type == "tool" and state.messages[-1].status != "error": #Checking if the last message and its a Tool Message then make the current step be +1.
            current_step += 1 
            current_attempts = 0
        if(current_step >= len(state.plan)):
            return {
                "current_step" : current_step + 1
            }
        current_action = state.plan[current_step]
        number_of_retry = 1 # give the retry for tool call for a same task even if no error and execption happened
        
        if (current_attempts - 1)  >= number_of_retry  : # - 1 because the first attemp will not be counted as a retry.
            system_message = SystemMessage(content="Rerouting to recovery node as the executor has failed on tool calls.")
            return {"messages" : [system_message],
                    "current_attempts" : 0,
                    "goto" : "recovery"}

        system_message = SystemMessage(content= EXECUTOR_PROMPT)
        snapshot_data = await get_snapshot()
        text = f"Aria snapshot of the current page : {snapshot_data} \n\n Using this execute the current task : {current_action}"
        human_message = HumanMessage(content=[
                    {
                        "type" : "text",
                        "text" : text
                    }, 
                ], name="User")
        message = [system_message, human_message]


        response : ExecutorOutput = await executor_with_tools.ainvoke(message)
        response.name = "Executor Node"

        response = AIMessage(
            content = "",
            tool_calls = [
                {
                    "name" : response.tool_call.tool_name,
                    "args" : response.tool_call.tool_args.model_dump(exclude_none=True) if response.tool_call.tool_args is not None else {},
                    "id" : f"call_{str(uuid.uuid4().hex[:8])}",
                    "type" : "tool_call"
                }
            ],
            name = response.name,
        )

        print(response.pretty_repr()) ## PRINITING

        chat_history = [human_message, response]

        return {
            "messages" : chat_history,
            "current_attempts" : current_attempts + 1,
            "current_step" : current_step

        }

    except Exception as e:
        raise e
    



async def recovery_node(state: AgentState) -> dict:
    """
    If the executor fails to complete a step, this node will reason about the failure and provide a solution for it.
    """

    try:
        screenshot_data = await get_screenshot()
        current_step = state.current_step
        current_action = state.plan[current_step]
        current_attempts = state.current_attempts
        reasons = state.reasons
        system_message = SystemMessage(content=SELF_RECOVERY_PROMPT)
        text = f"""Action taken by you for this task till now : {"\n -".join(reasons)}
                             Failed to execute step: {current_action}""" if reasons is not None else f"""Failed to execute step: {current_action}"""
        human_message = HumanMessage(content=[
            {
                "type" : "text",
                "text" : text
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{screenshot_data}"},
            },
        ])

        #Do not know how to solve this issue right know that how will I stop the llm even if it tries to task that is completed , so just using the hardcoded number of attempt loop
        if current_attempts > 3:
            response = RecoveryOutput(
                execution_done=True,
                reason = "Number of tries are exceeded for a particular task.")
        else:
            message = [system_message, human_message]
            response : RecoveryOutput = await recovery_with_tools.ainvoke(message)
            response.name = "Recovery Node"

        if not response.execution_done and response.tool_name != None and response.tool_args is not None:
            reasons = state.reasons + [response.reason] if state.reasons is not None else [response.reason]
            response = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": response.tool_call.tool_name,
                        "args": response.tool_call.tool_args.model_dump(exclude_none=True) if response.tool_call.tool_args is not None else {},
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "type": "tool_call",
                    }
                ],
                name = response.name,
            )
            print(response.pretty_repr) ##PRINITNG
            return {"messages": [response],
                    "current_attempts" : current_attempts + 1,
                    "reasons" : reasons,
                    "goto" : None,
                    }

        if response.execution_done :
            return {
                "messages": [AIMessage(content=f"No blocker found. {response.reason}", name="Recovery Node")],
                "current_attempts": 0,
                "current_step": current_step + 1,
                "reasons" : None,
                "goto" : None,
            }


    except Exception as e:
        raise e


