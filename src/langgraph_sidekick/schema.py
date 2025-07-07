from pydantic import BaseModel
from typing import Annotated, Optional
from langgraph.graph.message import add_messages  # A reducer function


class State(BaseModel):
    messages: Annotated[list, add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
