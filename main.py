from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import json

app = FastAPI()

# Enable CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Ensure downloads directory exists
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    url: str
    format: str
    cookies: str = None

def parse_cookies(cookies_str: str) -> dict:
    """Parse cookies string into a dictionary"""
    try:
        cookies_dict = {}
        if cookies_str:
            for cookie in cookies_str.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    cookies_dict[name] = value
        return cookies_dict
    except Exception as e:
        print(f"Error parsing cookies: {e}")
        return {}

def create_cookies_file(cookies_dict: dict) -> str:
    """Create a Netscape format cookies file for yt-dlp"""
    cookies_file = os.path.join(DOWNLOADS_DIR, f"cookies_{uuid.uuid4()}.txt")
    try:
        with open(cookies_file, 'w') as f:
            # Write the required header for compatibility
            f.write("# Netscape HTTP Cookie File\n")
            for name, value in cookies_dict.items():
                # Correct format with numeric flags:
                # domain, include_subdomains, path, secure, expiry, name, value
                f.write(
                    f".youtube.com\tTRUE\t/\t1\t{2147483647}\t{name}\t{value}\n"
                )
        return cookies_file
    except Exception as e:
        print(f"Error creating cookies file: {e}")
        return None

@app.post("/convert")
async def convert_video(request: VideoRequest):
    try:
        # Parse and handle cookies
        cookies_dict = parse_cookies(request.cookies)
        cookies_file = create_cookies_file(cookies_dict) if cookies_dict else None

        # Generate unique output path
        output_filename = f"{uuid.uuid4()}.{request.format}"
        output_path = os.path.join(DOWNLOADS_DIR, output_filename)

        # Configure yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": request.format,
                "preferredquality": "192",
            }],
            "outtmpl": output_path,
            "quiet": False,
            "no_warnings": False,
        }

        # Add cookies file if available
        if cookies_file:
            ydl_opts["cookiefile"] = cookies_file

        # Download and convert the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])

        # Clean up cookies file
        if cookies_file and os.path.exists(cookies_file):
            os.remove(cookies_file)

        # Return the converted file
        if os.path.exists(output_path):
            return FileResponse(
                path=output_path,
                filename=f"youtube_{uuid.uuid4()}.{request.format}",
                media_type="application/octet-stream",
                background=None  # Ensures synchronous file deletion
            )
        else:
            raise HTTPException(status_code=404, detail="Converted file not found")

    except Exception as e:
        # Log the error for debugging
        print(f"Error during conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up downloaded files
        if 'output_path' in locals() and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception as e:
                print(f"Error cleaning up file: {e}")
