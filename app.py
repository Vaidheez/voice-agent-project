import os
import shutil
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf
from starlette.middleware.cors import CORSMiddleware
import assemblyai as aai
from murf import Murf

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

# NEW Echo Bot endpoint: Transcribes audio and generates a Murf response
@app.post("/tts/echo")
async def tts_echo(file: UploadFile = File(...)):
    assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
    murf_api_key = os.getenv("MURF_API_KEY")
    if not assemblyai_api_key or not murf_api_key:
        raise HTTPException(status_code=500, detail="API keys not set in environment variables")
    
    upload_folder = "uploads"
    unique_filename = f"{os.urandom(16).hex()}_{file.filename}"
    file_path = os.path.join(upload_folder, unique_filename)
    
    transcription = "No transcription found."
    murf_audio_url = None
    
    try:
        # 1. Save the uploaded file locally for transcription
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Transcribe the audio file using AssemblyAI
        aai.settings.api_key = assemblyai_api_key
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(file_path)
        
        transcription = transcript.text if transcript.text else "No transcription found."

        if transcription:
            # 3. Use Murf API to generate new audio from the transcription
            murf_client = Murf(api_key=murf_api_key)
            murf_voice_id = "en-US-terrell" # You can choose any Murf voice here
            
            murf_res = murf_client.text_to_speech.generate(
                text=transcription,
                voice_id=murf_voice_id
            )
            murf_audio_url = murf_res.audio_file

        return {
            "transcription": transcription,
            "murf_audio_url": murf_audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during audio processing: {e}")
    finally:
        # 4. Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)