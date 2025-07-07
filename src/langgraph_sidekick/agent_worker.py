from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

from langgraph_sidekick.client import AzureAIClient

from langgraph_sidekick.agent_tools import get_agent_tools, get_playwright_tools

from langchain_core.messages import SystemMessage
import asyncio
from langgraph_sidekick.schema import State
from datetime import datetime


load_dotenv(override=True)


class AgentWorker:
    def __init__(self):
        self.llm_with_tools = None
        self.tools = None
        # self.sidekick_id = str(uuid.uuid4())
        self.browser = None
        self.playwright = None

    async def setup(self):
        """Setups the agent worker tools and graph and memory"""

        self.tools = await get_agent_tools()
        # Add playwright tools to the agent tools
        playwright_tools, self.browser, self.playwright = await get_playwright_tools()
        self.tools += playwright_tools

        llm = AzureChatOpenAI(
            api_version="2024-12-01-preview", azure_ad_token_provider=AzureAIClient().token_provider, azure_deployment="gpt-4o"
        )
        self.llm_with_tools = llm.bind_tools(self.tools)

        return self  # So that the instance of the agentworker with tools is available

        # await self.build_graph()

    def run(self, state: State) -> State:
        """Worker execution function - node"""
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
        You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.


        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        This is the success criteria:
        {state.success_criteria}
        You should reply either with a question for the user about this assignment, or with your final response.
        If you have a question for the user, you need to reply by clearly stating your question. 
        An example Quenstion might be: Question: please clarify whether you want a summary or a detailed answer

        If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
        """

        if state.feedback_on_work:
            system_message += f"""
            Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
            Here is the feedback on why this was rejected:
            {state.feedback_on_work}
            With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."""

        # Add in the system message
        found_system_message = False
        # messages = state["messages"]
        messages = state.messages
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with tools
        response = self.llm_with_tools.invoke(messages)
        new_state = state.model_copy(update={"messages": [response]})
        # Return updated state
        return new_state

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
