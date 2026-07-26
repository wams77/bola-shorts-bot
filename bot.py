import os
from gtts import gTTS
import yt_dlp
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, VideoFileClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. MENGUNDUH VIDEO TERBARU DARI VK VIDEO ---
def download_vk_video(vk_url, output_filename="bg_video.mp4"):
    print(f"[1/4] Mengambil video terbaru dari VK: '{vk_url}'...")
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_filename,
        'noplaylist': False, 
        'playlist_items': '1', # Ambil video paling atas/terbaru
        'max_filesize': 50000000, # Batas ukuran 50MB
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(vk_url, download=True)
        
        # Mengekstrak judul asli video dari VK
        if 'entries' in info and len(info['entries']) > 0:
            video_title = info['entries'][0].get('title', 'Video Sepak Bola Terbaru')
        else:
            video_title = info.get('title', 'Video Sepak Bola Terbaru')
            
    print(f"[1/4] Berhasil mengunduh video: {video_title}")
    return output_filename, video_title

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
    
    # Load video, potong sesuai durasi suara, matikan suara asli
    bg_video = VideoFileClip(bg_video_path).subclipped(0, duration).without_audio()
    
    # Paksa ubah ukuran (resize) menjadi rasio Shorts vertikal (1080x1920) & crop tengah
    bg_video = bg_video.resized(height=1920)
    bg_video = bg_video.cropped(x_center=bg_video.w/2, y_center=bg_video.h/2, width=1080, height=1920)
    
    txt_clip = TextClip(
        text="KABAR BOLA HARI INI!\n\nTonton sampai habis!", 
        font_size=70, 
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
            "categoryId": "17" # Kategori Olahraga
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print(f"✅ Video berhasil diunggah! Link: https://youtu.be/{response['id']}")

if __name__ == "__main__":
    # 1. SUMBER LINK VK VIDEO
    VK_URL = "https://vksport.vkvideo.ru/sport/football"
    
    # 2. NASKAH DAN METADATA
    NASKAH = "Update berita sepak bola terbaru hari ini! Jangan lupa subscribe channel ini untuk kabar bola terpanas setiap harinya."
    DESKRIPSI = "Kabar sepak bola paling hot hari ini! \n\n#sepakbola #beritabola #shorts #football"
    TAGS = ["sepakbola", "berita bola", "bola terbaru", "shorts", "football highlights"]
    
    try:
        # Mengambil video dari VK
        bg_file, judul_asli = download_vk_video(VK_URL)
        
        # Menyesuaikan judul video
        JUDUL_VIDEO = f"{judul_asli} 🔥 #shorts"
        if len(JUDUL_VIDEO) > 100:
            JUDUL_VIDEO = JUDUL_VIDEO[:90] + " #shorts"
            
        # Proses pembuatan dan pengunggahan
        audio_file = create_voiceover(NASKAH)
        video_final = generate_video(bg_file, audio_file)
        upload_to_youtube(video_final, JUDUL_VIDEO, DESKRIPSI, TAGS)
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
