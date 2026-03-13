import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

def analyze_transcript(transcript: str) -> dict:
    """
    Analyze transcript using Gemini AI.
    Returns summary, decisions, tasks.
    """
    prompt = f"""
    Analyze the following meeting transcript and return a JSON with keys:
    1. meeting_summary: string
    2. decisions: list of strings
    3. tasks: list of objects with 'task', 'owner', 'priority'

    Transcript:
    {transcript}
    """
    response = model.generate_content(prompt)
    # Attempt to parse JSON from response
    try:
        data = response.as_dict.get("candidates")[0]["content"]["text"]
        return json.loads(data)
    except Exception:
        # fallback if Gemini returns text only
        return {"meeting_summary": response.text, "decisions": [], "tasks": []}