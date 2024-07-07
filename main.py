import asyncio
import logging
from flask import Flask, render_template

from livekit.agents import JobContext, JobRequest, WorkerOptions, cli
from livekit.agents.llm import ChatContext, ChatMessage, ChatRole
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, elevenlabs, openai, silero

app = Flask(__name__)

# This function is the entrypoint for the agent.
async def entrypoint(ctx: JobContext):
    # Create an initial chat context with a system prompt
    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role=ChatRole.SYSTEM,
                text="You are a voice assistant created by LiveKit. Your interface with users will be voice. Pretend we're having a conversation, no special formatting or headings, just natural speech.",
            )
        ]
    )

    # VoiceAssistant is a class that creates a full conversational AI agent.
    assistant = VoiceAssistant(
        vad=silero.VAD(), # Voice Activity Detection
        stt=deepgram.STT(), # Speech-to-Text
        llm=openai.LLM(), # Language Model
        tts=elevenlabs.TTS(), # Text-to-Speech
        chat_ctx=initial_ctx, # Chat history context
    )

    # Start the voice assistant with the LiveKit room
    assistant.start(ctx.room)

    await asyncio.sleep(3)

    # Greets the user with an initial message
    await assistant.say("Hey, how can I help you today?", allow_interruptions=True)


# This function is called when the worker receives a job request
# from a LiveKit server.
async def request_fnc(req: JobRequest) -> None:
    logging.info("received request %s", req)
    # Accept the job tells the LiveKit server that this worker
    # wants the job. After the LiveKit server acknowledges that job is accepted,
    # the entrypoint function is called.
    await req.accept(entrypoint)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    # Initialize the worker with the request function
    cli.run_app(WorkerOptions(request_fnc))
    # Run the Flask app
    app.run(port=5000)
