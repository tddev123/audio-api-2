from fastapi import FastAPI, HTTPException, Request
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
    allow_origins=["http://localhost:3001"],  # Update this with your actual frontend URL
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

# Pydantic model for video conversion request
class VideoRequest(BaseModel):
    url: str
    format: str
    cookies: str  # Cookies passed as a string from frontend

@app.post("/convert")  # Ensure you're using the correct API endpoint
async def convert_video(request: VideoRequest, cookies: Request):
    try:
        # Get cookies from the request object (using cookies passed from frontend)
        frontend_cookies = cookies.cookies.get("session_cookie")

        if frontend_cookies:
            # If the frontend sends cookies, save them to a file for yt-dlp
            with open(COOKIES_FILE, "w") as f:
                f.write(frontend_cookies)
        
        # Alternatively, if cookies are passed directly in the request (fallback)
        elif request.cookies:
            with open(COOKIES_FILE, "w") as f:
                f.write(request.cookies)

        # Generate unique output path
        output_filename = f"{uuid.uuid4()}.{request.format}"
        output_path = os.path.join("downloads", output_filename)

        # Configure yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": request.format
            }],
            "outtmpl": output_path,
            "cookiefile": COOKIES_FILE,  # Using the cookiefile in yt-dlp
        }

        # Download and convert the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

        # Return the downloaded file as response
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="application/octet-stream"
        )

    except Exception as e:
        # Handle any errors
        raise HTTPException(status_code=500, detail=str(e))
