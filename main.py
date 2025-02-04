from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
from pathlib import Path
import uuid

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,  # Allow credentials (cookies)
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create downloads folder
if not os.path.exists("downloads"):
    os.makedirs("downloads")

class VideoURL(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"status": "alive"}

@app.post("/convert")
async def convert_video(video: VideoURL, request: Request):
    try:
        # Extract cookies from the request
        cookies = request.cookies
        if not cookies.get("session_cookie"):
            raise HTTPException(status_code=400, detail="Cookies are required")

        # Check if the cookies are valid (e.g., simulate a YouTube request)
        ydl_opts = {
            'cookies': cookies,  # Use cookies for YouTube request
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': "downloads/%(id)s.%(ext)s",
        }

        # Test the YouTube video URL with the provided cookies
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video.url])

        # Create unique filename
        filename = f"{uuid.uuid4()}.wav"
        output_path = f"downloads/{filename}"

        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="audio/wav"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
