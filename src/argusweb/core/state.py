
from pydantic import BaseModel, Field, HttpUrl
from typing import Annotated, Literal, Union
from operator import add
from langchain_core.messages import BaseMessage



# Graph states schema
class AgentState(BaseModel):
    user_goal : str  = Field(description="The prompt given by the user")   
    plan : list[str] = Field (description="List of string about the sequntial planning of the task , that how to do.")

    screenshot : str | None = Field(default=None, description="Base64 encoded screenshot of the screen")
    snapshot : str | None = Field(default=None, description="The aria snapshot of the page that is reterived after the hybrid reterival")   

    current_step : int = Field(default=0, description="Current index of the plan that is going to be executed")    
    current_attempts : int = Field(default=0, description="Number of attempts done for a particular task") 
    goto : str | None = Field(default=None, title="Goto another node", description="Can be used when need to go to any other node")
    reasons : list[str] | None = Field(default=None, title="Reasons of task performed", description="Temprory storage for nodes to store their current steps for a particular task")
    messages : Annotated[list[BaseMessage], add] = Field(default=[], description="Every message that is produced and given during the task") 


class InputState(BaseModel):
    user_goal: str  = Field(description="The prompt given by the user.")



# Tool schema
class MouseClickArgs(BaseModel):
    x : int = Field(title="X - Coordinate", description="x coordinate for where to click.")
    y : int = Field(title="Y - Coordinate",description="y coordinate for where to click.")


class NavigateURLArgs(BaseModel):
    url : HttpUrl = Field(description="url of the page that you want to navigate on.") 


class MouseActionArgs(BaseModel):
    action : Literal["click", "type"] = Field(description="Name of the action want to perfrom of webpage. 'click' for clicking a element and 'type' for typing something on the webpage")
    element_id : str = Field(title="Reference Id", description="Reference id (e.g.f3e51) of the element on which you want to perform this action on.")
    text : str | None = Field(default=None, title="text", description="If the action if write, then the text that you want to write")



#Using disctiminator
class NavigateToCall(BaseModel):
    tool_name: Literal["navigate_to"] = Field(description="use to navigate on a webpage")
    tool_args: NavigateURLArgs

class MouseActionCall(BaseModel):
    tool_name: Literal["mouse_action"] = Field(description="use to do any either write or click on the webpage using refernce id")
    tool_args: MouseActionArgs

class MouseClickCall(BaseModel):
    tool_name: Literal["mouse_click"] = Field(description="use to click on specific coordinate on the screen using x and y coordinate")
    tool_args: MouseClickArgs  # Replace with your actual click args class

ToolCallAction = Annotated[
    Union[NavigateToCall, MouseActionCall, MouseClickCall],
    Field(discriminator="tool_name")
]

# LLM output schema
class RecoveryOutput(BaseModel):
    execution_done : bool = Field(description="True if the current action is completed , False otherwise.") 
    tool_call: ToolCallAction | None = Field(
            description="The exact tool and its matching arguments to execute."
        )
    reason : str | None = Field(default=None, description="One-sentence explanation of why this step.")
    name:str = Field(default="Recovery Node", description="Name of the node that made this output" )


class PlannerOuptut(BaseModel):
    plan : list[str] = Field(title="Plan for the task", description="Single step, seuquential task in python list to execute the whole plan.")
    name:str = Field(default="Planner Node", description="Name of the node that made this output" )



class ExecutorOutput(BaseModel):
    tool_call: ToolCallAction = Field(
        description="The exact tool and its matching arguments to execute."
    )
    name: str = Field(
        default="Executor Node",
        description="Name of the node that made this output"
    )