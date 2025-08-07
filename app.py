import os
import shutil
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf
from starlette.middleware.cors import CORSMiddleware
import assemblyai as aai # New Import

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class TextToSpeechRequest(BaseModel):
    text: str = "Hello, world! I am a newly-minted voice agent, ready for my big debut."
    voice_id: str = "en-US-terrell"

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

# NEW ENDPOINT for Day 6: Transcribe Audio
@app.post("/transcribe/file")
async def transcribe_file(file: UploadFile = File(...)):
    assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not assemblyai_api_key:
        raise HTTPException(status_code=500, detail="ASSEMBLYAI_API_KEY not set in environment variables")
    
    aai.settings.api_key = assemblyai_api_key
    transcriber = aai.Transcriber()

    try:
        # Transcribe directly from the file stream
        # Read the file content into memory for direct transcription
        audio_data = await file.read()
        transcript = transcriber.transcribe(audio_data)

        if transcript.text:
            return {"transcription": transcript.text}
        else:
            return {"transcription": "No transcription found."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during transcription: {e}")

# You no longer need the /upload-audio endpoint from Day 5, so it's removed.
# If you wish to keep it for reference, you can uncomment it, but it's not needed for this task.
# @app.post("/upload-audio")
# async def upload_audio(file: UploadFile = File(...)):
#     try:
#         upload_folder = "uploads"
#         if not os.path.exists(upload_folder):
#             os.makedirs(upload_folder)

#         file_path = os.path.join(upload_folder, file.filename)
        
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
            
#         return {
#             "filename": file.filename,
#             "content_type": file.content_type,
#             "size": file.size
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred during upload: {e}")