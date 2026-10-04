import time

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL


client = genai.Client(api_key=GEMINI_API_KEY)


def create_chat(tools):
    return client.chats.create(
        model=GEMINI_MODEL,
        config=types.GenerateContentConfig(
            tools=tools,
        ),
    )


def send_message(chat, message, retries=3):
    for attempt in range(retries):
        try:
            return chat.send_message(message)

        except Exception as e:
            error_text = str(e)

            # Temporary server overload.
            if "503" in error_text:
                if attempt == retries - 1:
                    raise

                wait_time = 2 ** attempt

                print(
                    f"Gemini is temporarily overloaded. "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)
                continue

            # Rate limit / quota exceeded.
            if "429" in error_text:
                print(
                    "\nGemini free-tier rate limit reached."
                    "\nPlease wait about a minute before sending another request."
                )
                return None

            raise