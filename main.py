import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Local imports
from services import (
    get_assemblyai_transcription,
    get_gemini_response,
    get_murf_audio_url,
    load_chat_history,
    save_chat_history
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app and templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Pydantic models for request and response
class ChatRequest(BaseModel):
    text: str = Field(..., description="The user's spoken transcription.")
    voice_id: str = Field(..., description="The Murf AI voice ID for the response.")

class ChatResponse(BaseModel):
    transcription: str = Field(..., description="The transcribed text from the user.")
    llm_response: str = Field(..., description="The text response from the LLM.")
    murf_audio_url: Optional[str] = Field(None, description="The URL of the generated Murf AI audio file.")

# Route to serve the main HTML page
@app.get("/", response_class=HTMLResponse)
async def serve_root(request: Request):
    """Serve the main VocaLoop UI."""
    return templates.TemplateResponse("index.html", {"request": request})

# Agent chat endpoint
@app.post("/agent/chat/{session_id}")
async def agent_chat_endpoint(session_id: str, voice_id: str, file: UploadFile = File(...)):
    """
    Handles the conversational agent interaction.
    - Transcribes the audio using AssemblyAI.
    - Gets an LLM response from Google Gemini with context.
    - Generates and returns audio from Murf AI.
    """
    logger.info(f"Received request for session_id: {session_id}")
    try:
        # Load chat history for context
        chat_history = load_chat_history(session_id)

        # Transcribe audio using AssemblyAI
        transcription = await get_assemblyai_transcription(file)
        logger.info(f"Transcription from user: {transcription}")

        if not transcription:
            raise HTTPException(status_code=400, detail="Could not transcribe audio.")

        # Get LLM response from Gemini
        llm_response = await get_gemini_response(transcription, chat_history)
        logger.info(f"LLM response: {llm_response}")

        # Save the new chat history
        save_chat_history(session_id, transcription, llm_response)

        # Generate audio from Murf AI
        murf_audio_url = await get_murf_audio_url(llm_response, voice_id)
        logger.info(f"Murf audio URL: {murf_audio_url}")

        return JSONResponse(content={
            "transcription": transcription,
            "llm_response": llm_response,
            "murf_audio_url": murf_audio_url
        })
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={
            "detail": "An unexpected error occurred on the server.",
            "murf_audio_url": None,
            "transcription": "Hello.",
            "llm_response": "I'm having trouble connecting right now. Please try again in a moment."
        })

# Endpoint to retrieve chat history
@app.get("/history/{session_id}")
async def get_chat_history_endpoint(session_id: str):
    """
    Retrieves the chat history for a given session.
    """
    try:
        chat_history = load_chat_history(session_id)
        return JSONResponse(content={"history": chat_history})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat history not found for this session.")
    except Exception as e:
        logger.error(f"Error retrieving history for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)