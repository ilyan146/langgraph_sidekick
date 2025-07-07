from pydantic import BaseModel, Field
from typing import Any
from databricks_langchain import ChatDatabricks  # type: ignore
from langgraph_sidekick.schema import State
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarification is required, or the assistant is stuck"
    )


class AgentEvaluator:
    def __init__(self):
        self.evaluator_llm = None

    async def setup(self):
        llm = ChatDatabricks(endpoint="databricks-claude-3-7-sonnet", max_tokens=1000)
        self.evaluator_llm = llm.with_structured_output(EvaluatorOutput)
        return self  # To make the agent class instance available

    def format_conversation(self, messages: list[Any]) -> str:
        convo = "Conversation history:\n\n"
        for msg in messages:
            if isinstance(msg, HumanMessage):
                convo += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                text = msg.content or "[Tools used]"
                convo += f"Assistant: {text}\n"
        return convo

    def run(self, state: State) -> State:
        last_response = state.messages[-1].content

        system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
        Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
        and whether more input is needed from the user."""

        user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.
        Here is the conversation history:
        {self.format_conversation(state.messages)}

        The success criteria for this assignment is:
        {state.success_criteria}

        The final response from the Assistant is:
        {last_response}

        Respond with your feedback, and decide if the success criteria is met by this response.
        Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.

        The Assistant has access to a number of tools such for sending push notifications, sending emails, writing to file/
        If the Assistant says they have used a tool you should give the Assistant the benefit of the doubt that it did do so. But you should reject if you feel that more work should go into this.
        """

        if state.feedback_on_work:
            user_message += (
                f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state.feedback_on_work}\n"
            )
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."

        evaluator_messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]

        evaluator_response = self.evaluator_llm.invoke(evaluator_messages)

        new_state = State(
            messages=[{"role": "assistant", "content": f"Evaluator Feedback on this answer: {evaluator_response.feedback}"}],
            feedback_on_work=evaluator_response.feedback,
            success_criteria_met=evaluator_response.success_criteria_met,
            user_input_needed=evaluator_response.user_input_needed,
            success_criteria=state.success_criteria,
        )

        return new_state
