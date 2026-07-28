import os
import requests
from gtts import gTTS
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, ImageClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. MENGUNDUH GAMBAR SEBAGAI LATAR BELAKANG ---
def download_image(image_url, output_filename="bg_image.jpg"):
    print("[1/4] Mengunduh gambar latar belakang...")
    # Menggunakan User-Agent dan Accept header lengkap layaknya browser asli
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
    }
    response = requests.get(image_url, headers=headers, stream=True)
    
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print("[1/4] Berhasil mengunduh gambar.")
        return output_filename
    else:
        raise Exception(f"Gagal mengunduh gambar, status: {response.status_code}")

# --- 2. MEMBUAT SUARA (TTS) ---
def create_voiceover(text, output_audio="voiceover.mp3"):
    print("[2/4] Membuat suara (Voiceover)...")
    tts = gTTS(text=text, lang="id", slow=False)
    tts.save(output_audio)
    return output_audio

# --- 3. MERAKIT VIDEO SHORTS DARI GAMBAR ---
def generate_video(bg_image_path, audio_path, output_video="output.mp4"):
    print("[3/4] Merakit video Shorts...")
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    # Load gambar sebagai klip video dan sesuaikan durasinya dengan panjang suara
    bg_image = ImageClip(bg_image_path).with_duration(duration)
    
    # Paksa ubah ukuran (resize) menjadi rasio Shorts vertikal (1080x1920) & crop tengah
    bg_image = bg_image.resized(height=1920)
    bg_image = bg_image.cropped(x_center=bg_image.w/2, y_center=bg_image.h/2, width=1080, height=1920)
    
    txt_clip = TextClip(
        text="KABAR BOLA HARI INI!\n\nTonton sampai habis!", 
        font_size=70, 
        color='white', 
        size=(900, None),
        method='caption',
        text_align='center'
    ).with_duration(duration).with_position('center')
    
    # Gabungkan gambar, teks, dan audio
    video = CompositeVideoClip([bg_image, txt_clip]).with_audio(audio)
    
    # Render video akhir dengan frame rate standar
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
    # 1. SUMBER GAMBAR SEPAK BOLA (Menggunakan Unsplash - Cepat, stabil, resolusi tinggi)
    IMAGE_URL = "https://images.unsplash.com/photo-1574629810360-7efbb1925536?q=80&w=1080&auto=format&fit=crop"
    
    # 2. NASKAH DAN METADATA
    NASKAH = "Update berita sepak bola terbaru hari ini! Jangan lupa subscribe channel ini untuk kabar bola terpanas setiap harinya."
    JUDUL_VIDEO = "Highlight Sepak Bola 🔥 #shorts"
    DESKRIPSI = "Kabar sepak bola paling hot hari ini! \n\n#sepakbola #beritabola #shorts #football"
    TAGS = ["sepakbola", "berita bola", "bola terbaru", "shorts", "football highlights"]
    
    try:
        # Mengunduh gambar
        bg_file = download_image(IMAGE_URL)
        
        # Membuat suara dan merakit video
        audio_file = create_voiceover(NASKAH)
        video_final = generate_video(bg_file, audio_file)
        
        # Unggah ke YouTube
        upload_to_youtube(video_final, JUDUL_VIDEO, DESKRIPSI, TAGS)
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
