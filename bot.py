import os
import time
from gtts import gTTS
import yt_dlp
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, VideoFileClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. MENGUNDUH SUMBER VIDEO (Dengan Cookies Anti-Blokir) ---
def download_background_video(youtube_url, output_filename="bg_video.mp4"):
    print("[1/4] Mengunduh video latar belakang dari YouTube...")
    ydl_opts = {
        'format': 'bestvideo[height<=1920][ext=mp4]+bestaudio[ext=m4a]/best[height<=1920][ext=mp4]',
        'outtmpl': output_filename,
        'cookiefile': 'cookies.txt', # Menggunakan cookies dari GitHub Secrets
        'noplaylist': True,
        'max_filesize': 50000000,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    return output_filename

# --- 2. MEMBUAT SUARA (TTS) ---
def create_voiceover(text, output_audio="voiceover.mp3"):
    print("[2/4] Membuat suara (Voiceover)...")
    tts = gTTS(text=text, lang="id", slow=False)
    tts.save(output_audio)
    return output_audio

# --- 3. MERAKIT VIDEO SHORTS ---
def generate_video(bg_video_path, audio_path, output_video="output.mp4"):
    print("[3/4] Merakit video Shorts...")
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    bg_video = VideoFileClip(bg_video_path).subclipped(0, duration)
    bg_video = bg_video.resized(height=1920)
    
    txt_clip = TextClip(
        text="FAKTA SEPAK BOLA!\n\nReal Madrid adalah rajanya\nLiga Champions dengan 15 trofi!", 
        font_size=60, 
        color='white', 
        size=(900, None),
        method='caption',
        text_align='center'
    ).with_duration(duration).with_position('center')
    
    video = CompositeVideoClip([bg_video, txt_clip]).with_audio(audio)
    video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    return output_video

# --- 4. AUTO-UPLOAD KE YOUTUBE ---
def upload_to_youtube(video_path, title, description, tags):
    print("[4/4] Mengunggah ke YouTube...")
    
    # Membangun kredensial dari GitHub Secrets
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("YOUTUBE_CLIENT_ID"),
        client_secret=os.environ.get("YOUTUBE_CLIENT_SECRET")
    )
    
    youtube = build('youtube', 'v3', credentials=creds)
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "17" # Kategori: Olahraga
        },
        "status": {
            "privacyStatus": "public", # Ubah ke 'private' jika ingin ditinjau dulu
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print(f"✅ Video berhasil diunggah! Link: https://youtu.be/{response['id']}")

if __name__ == "__main__":
    # Pengaturan Meta Data Konten
    YOUTUBE_BG_URL = "https://www.youtube.com/watch?v=2Vv-BfVoq4g" # Ganti dengan video sumber Anda
    NASKAH = "Tahukah kamu? Real Madrid dijuluki sebagai rajanya Liga Champions karena telah mengoleksi lima belas trofi bergengsi di Eropa. Luar biasa!"
    JUDUL_VIDEO = "Fakta Gila Real Madrid di UCL 🏆 #shorts #sepakbola"
    DESKRIPSI = "Fakta menarik seputar Real Madrid dan dominasinya di Liga Champions. \n\n#realmadrid #championsleague #sepakbola #football #shorts"
    TAGS = ["sepakbola", "football", "real madrid", "champions league", "shorts", "berita bola"]
    
    try:
        bg_file = download_background_video(YOUTUBE_BG_URL)
        audio_file = create_voiceover(NASKAH)
        video_final = generate_video(bg_file, audio_file)
        
        # Eksekusi unggah otomatis ke channel Anda
        upload_to_youtube(video_final, JUDUL_VIDEO, DESKRIPSI, TAGS)
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
