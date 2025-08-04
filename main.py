import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf # We only need to import the Murf class

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Pydantic model for the request body
class TextToSpeechRequest(BaseModel):
    text: str = "Hello, world! I am a newly-minted voice agent, ready for my big debut."
    voice_id: str = "en-US-terrell"

@app.post("/generate-audio")
async def generate_audio(request: TextToSpeechRequest):
    api_key = os.getenv("MURF_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="MURF_API_KEY not set in environment variables")
    
    try:
        # Initialize the Murf client with your API key
        murf_client = Murf(api_key=api_key)
        
        # Use the official SDK to generate the audio
        res = murf_client.text_to_speech.generate(
            text=request.text,
            voice_id=request.voice_id
        )
        
        # The response object directly contains the audio URL
        audio_url = res.audio_file
        
        if audio_url:
            return {"audio_url": audio_url}
        else:
            raise HTTPException(status_code=500, detail="Audio URL not found in API response")
            
    except Exception as e:
        # This catch-all exception block is simple and effective.
        # It handles any error that occurs, including API-related ones.
        raise HTTPException(status_code=500, detail=f"An error occurred while generating audio: {e}")

# This is a sample endpoint from Day 1 to ensure the server is working
@app.get("/")
def home():
    return {"message": "Server is running. Navigate to /docs for API details."}