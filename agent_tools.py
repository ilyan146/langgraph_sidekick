from utils import push, send_email
from playwright.async_api import async_playwright, Browser, Playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper


load_dotenv(override=True)


async def get_playwright_tools() -> tuple[list, Browser, Playwright]:
    """Generate playwright tools"""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    playwright_tools = toolkit.get_tools()
    # For proper clean up
    return playwright_tools, browser, playwright


async def get_agent_tools():
    """Get a bunch of tools that the agent can use"""

    # Google tool
    tool_search = Tool(
        name="google_serper_search_tool",
        func=GoogleSerperAPIWrapper().run,
        description="Useful for when you need more information from an online search",
    )

    # Push notification tool
    tool_push = Tool(name="push_notification_tool", func=push, description="Useful for sending push notifications to the user")

    # Email tool
    tool_email = Tool(name="send_email_tool", func=send_email, description="Useful for sending emails to the user")

    return [tool_search, tool_push, tool_email]
