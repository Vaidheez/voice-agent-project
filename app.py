import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf
from starlette.middleware.cors import CORSMiddleware # New Import

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# New: Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Mount the static directory to serve CSS and JS files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 for HTML templating
templates = Jinja2Templates(directory="templates")

# Pydantic model for the request body
class TextToSpeechRequest(BaseModel):
    text: str = "Hello, world! I am a newly-minted voice agent, ready for my big debut."
    voice_id: str = "en-US-terrell"
    
# The root endpoint to serve the HTML page
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-audio")
async def generate_audio(request: TextToSpeechRequest):
    api_key = os.getenv("MURF_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="MURF_API_KEY not set in environment variables")
    
    try:
        murf_client = Murf(api_key=api_key)
        
        res = murf_client.text_to_speech.generate(
            text=request.text,
            voice_id=request.voice_id
        )
        
        audio_url = res.audio_file
        
        if audio_url:
            return {"audio_url": audio_url}
        else:
            raise HTTPException(status_code=500, detail="Audio URL not found in API response")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while generating audio: {e}")