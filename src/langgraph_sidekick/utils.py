import os
from dotenv import load_dotenv
import requests  # type: ignore
import sendgrid  # type: ignore
from sendgrid.helpers.mail import Mail, Email, To, Content  # type: ignore
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data={"token": pushover_token, "user": pushover_user, "message": text})


def send_email(body: str):
    """Send out an email with the given body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("mohamed.ilyan@boskalis.com")
    # to_email = To("mohamed.ilyan@boskalis.com")
    to_email = To("ilyan146@gmail.com")
    content = Content("text/plain", body)

    mail = Mail(from_email, to_email, "SendGridEmail", content).get()
    response = sg.client.mail.send.post(request_body=mail)  # noqa
    return {"status": "success"}


# database persistant memory
db_path = "memory_db/sqlite_memory.db"


async def setup_async_db():
    async_conn = await aiosqlite.connect(db_path)
    return AsyncSqliteSaver(async_conn)


# # Singleton instantitation of the async connection and memory
# async_conn = asyncio.run(setup_async_db())
# sql_memory = AsyncSqliteSaver(async_conn)


if __name__ == "__main__":
    # Example usage
    # push("This is a test notification from LangGraph Sidekick!")
    send_email("This is a test email from LangGraph Sidekick!")
    print("Notifications sent successfully.")
