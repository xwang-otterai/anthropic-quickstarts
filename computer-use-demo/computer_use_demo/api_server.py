import logging
import sys

import uvicorn
from anthropic.types.beta import BetaMessageParam, BetaTextBlockParam
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from computer_use_demo.loop import APIProvider, sampling_loop_generator

app = FastAPI()
# Configure the root logger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,  # This ensures logs go to container stdout
)

logger = logging.getLogger(__name__)


class ComputerUseMessage(BaseModel):
    text: str


class Sender:
    USER = "user"


@app.post("/send_message")
async def send_message(message: ComputerUseMessage):
    logger.info(f"Received message: {message}")

    msg: BetaMessageParam = {
        "role": Sender.USER,
        "content": [BetaTextBlockParam(type="text", text=message.text)],
    }

    return StreamingResponse(
        sampling_loop_generator(
            system_prompt_suffix="""
        You are demonstrating the Otter.ai web application. You have access to a logged-in test account for demo purposes, so it's safe to perform any actions within the app.

When performing computer actions, please:
1. Narrate each step in a clear, demo-style format ("Now I'm clicking...", "You'll see...")
2. Use everyday language that non-technical users can understand
3. Break down complex actions into small, clear steps
4. Describe what users should expect to see after each action
5. Keep descriptions brief and clear for text-to-speech conversion

Please close any popup banners to keep the interface clean.
""",
            model="claude-3-5-sonnet-20241022",
            provider=APIProvider.ANTHROPIC,
            messages=[msg],
            output_callback=lambda x: None,
            tool_output_callback=lambda x, y: None,
            api_response_callback=lambda x, y, z: None,
            api_key="sk-ant-lzYHF2_R2RPOupp0lrFJm_Amtqqz9AaclaeS99CttE-PlR92PRE0pqW6ENQQAUtBddx_KCHyxgfESYBnKrOhqA",
            only_n_most_recent_images=10,
        ),
        media_type="text/plain",
    )


async def run_server():
    """Run FastAPI server"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8111, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
    logger.info("FastAPI server started")
