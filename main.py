from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test endpoint
@app.get("/")
async def health_check():
    return {"status": "API is running"}  # ✅ Verify this first

# Ensure downloads directory exists
os.makedirs("downloads", exist_ok=True)
COOKIES_FILE = "youtube_cookies.txt"

class VideoRequest(BaseModel):
    url: str
    format: str
    cookies: str  # Cookies passed as a string from frontend

@app.post("/api/convert")
async def convert_video(request: VideoRequest):
    try:
        # Save cookies to file
        with open(COOKIES_FILE, "w") as f:
            f.write(request.cookies)

        # Generate unique output path
        output_filename = f"{uuid.uuid4()}.{request.format}"
        output_path = os.path.join("downloads", output_filename)

        # Configure yt-dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": request.format
            }],
            "outtmpl": output_path,
            "cookiefile": COOKIES_FILE,  # Key is "cookiefile", not "cookies"
        }

        # Download and convert
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

        # Return the file
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="application/octet-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
