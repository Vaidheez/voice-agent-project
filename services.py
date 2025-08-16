import os
import json
import logging
import shutil
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import assemblyai as aai
from murf import Murf
from google.generativeai import GenerativeModel
from fastapi import UploadFile

# Load environment variables
load_dotenv()
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
murf = Murf(api_key=os.getenv("MURF_API_KEY"))
gemini_model = GenerativeModel("gemini-1.5-flash")

# Configure logging
logger = logging.getLogger(__name__)

# File path for chat history
HISTORY_DIR = "chat_history"
os.makedirs(HISTORY_DIR, exist_ok=True)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Function to load chat history from a JSON file
def load_chat_history(session_id: str) -> List[Dict[str, Any]]:
    """Loads chat history from a JSON file for a given session ID."""
    history_file = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from history file: {history_file}. Starting new history.")
            return []
    return []

# Function to save chat history to a JSON file
def save_chat_history(session_id: str, user_text: str, llm_response: str):
    """Appends new user and AI messages to the chat history file."""
    chat_history = load_chat_history(session_id)
    chat_history.append({"role": "user", "parts": [user_text]})
    chat_history.append({"role": "model", "parts": [llm_response]})

    history_file = os.path.join(HISTORY_DIR, f"{session_id}.json")
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(chat_history, f, indent=4)
    logger.info(f"Saved chat history for session: {session_id}")

# Function to get transcription from AssemblyAI
async def get_assemblyai_transcription(file: UploadFile) -> str:
    """Sends an audio file to AssemblyAI for transcription."""
    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        config = aai.TranscriptionConfig(language_code="en_us")
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(temp_path, config=config)
        
        if transcript.status == aai.TranscriptionStatus.completed:
            return transcript.text
        else:
            logger.error(f"AssemblyAI transcription failed with status: {transcript.status}")
            return ""
    except Exception as e:
        logger.error(f"Error during AssemblyAI transcription: {e}", exc_info=True)
        return ""
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Function to get response from Google Gemini
async def get_gemini_response(transcription: str, chat_history: List[Dict[str, Any]]) -> str:
    """Gets a contextual response from Google Gemini."""
    try:
        chat = gemini_model.start_chat(history=chat_history)
        response = await chat.send_message_async(transcription)
        return response.text
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {e}", exc_info=True)
        return "I'm having trouble connecting right now. Please try again in a moment."

# Function to get audio URL from Murf AI
async def get_murf_audio_url(text: str, voice_id: str) -> Optional[str]:
    """Generates an audio file from Murf AI and returns its URL."""
    try:
        response = murf.gen_audio(text, voice_id=voice_id)
        return response.get("audio_file_url")
    except Exception as e:
        logger.error(f"Error generating audio with Murf AI: {e}", exc_info=True)
        return None