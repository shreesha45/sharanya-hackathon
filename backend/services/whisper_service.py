import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

async def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )

    return transcript["text"] 