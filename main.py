from fastapi import FastAPI, HTTPException
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
    allow_origins=["*"],
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
async def convert_video(video: VideoURL):
    try:
        # Create unique filename
        filename = f"{uuid.uuid4()}.wav"
        output_path = f"downloads/{filename}"
        
        # Download and convert
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': output_path.replace('.wav', ''),
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video.url])
        
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="audio/wav"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))