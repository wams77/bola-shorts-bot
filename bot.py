import os
import random
import requests
import urllib.parse
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, ImageClip, ColorClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- KOLEKSI KEBIJAKSANAAN (FILSAFAT & MOTIVASI) ---
KUOTES = [
    {
        "teks": "Jangan menunggu cahaya di ujung terowongan.\nJadilah cahaya itu sendiri.",
        "prompt_gambar": "A glowing mystical lantern in a dark moody forest, cinematic lighting, epic fantasy, extremely detailed"
    },
    {
        "teks": "Kesulitan yang kamu hadapi hari ini,\nadalah kekuatan yang kamu butuhkan untuk hari esok.",
        "prompt_gambar": "A lone warrior standing on a mountain peak looking at a stormy sky, dark clouds, epic cinematic landscape"
    },
    {
        "teks": "Bukan beban yang menghancurkanmu,\ntetapi cara kamu memikulnya.",
        "prompt_gambar": "A beautiful serene lake reflecting giant towering mountains at twilight, deep blue and purple hues, peaceful"
    },
    {
        "teks": "Waktu adalah kanvas.\nDan tindakanmu adalah lukisannya.\nJangan biarkan kanvasmu kosong.",
        "prompt_gambar": "An ancient giant hourglass standing in a vast desert under a starry galaxy sky, surreal, highly detailed"
    },
    {
        "teks": "Pohon yang besar tumbuh dari angin yang kencang.\nTeruslah berdiri kokoh.",
        "prompt_gambar": "A massive ancient glowing tree in the middle of a dark stormy landscape, resilient, cinematic composition"
    }
]

# --- 1. AI IMAGE GENERATOR ---
def generate_ai_image(prompt, output_filename="bg_image.jpg"):
    print(f"[1/4] Meminta AI melukis gambar: '{prompt}'...")
    # Menambahkan instruksi agar gambar berformat vertikal dan gelap (agar teks putih terbaca)
    full_prompt = f"{prompt}, dark moody atmosphere, vertical portrait, 8k resolution, masterpiece"
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # Menggunakan Pollinations AI (Gratis, tanpa API Key)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"
    
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print("[1/4] Lukisan AI berhasil diciptakan.")
        return output_filename
    else:
        raise Exception("Gagal menghasilkan gambar AI.")

# --- 2. AI NEURAL VOICE GENERATOR ---
def generate_ai_voice(text, output_audio="voiceover.mp3"):
    print("[2/4] Menyuarakan kebijaksanaan dengan AI Neural...")
    # Menggunakan Edge-TTS (Suara Pria Indonesia: id-ID-ArdiNeural)
    # Suara ini sangat natural, tenang, dan bijaksana.
    command = f'edge-tts --voice id-ID-ArdiNeural --rate=-10% --text "{text}" --write-media {output_audio}'
    os.system(command)
    
    if os.path.exists(output_audio):
        print("[2/4] Suara berhasil direkam.")
        return output_audio
    else:
        raise Exception("Gagal menghasilkan suara AI.")

# --- 3. EDITOR VIDEO OTOMATIS ---
def generate_video(bg_image_path, audio_path, text, output_video="output.mp4"):
    print("[3/4] Merakit visual dan audio menjadi mahakarya Shorts...")
    audio = AudioFileClip(audio_path)
    # Tambahkan sedikit jeda di akhir agar tidak terpotong tiba-tiba
    duration = audio.duration + 1.5 
    
    # Memuat gambar AI
    bg_image = ImageClip(bg_image_path).with_duration(duration)
    
    # Membuat filter gelap transparan agar teks semakin menonjol
    dark_overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).with_opacity(0.4).with_duration(duration)
    
    # Membuat Teks (Subtitle/Quotes)
    txt_clip = TextClip(
        text=text, 
        font_size=65, 
        color='white', 
        size=(900, None),
        method='caption',
        text_align='center'
    ).with_duration(duration).with_position('center')
    
    # Menggabungkan semuanya: Gambar Asli -> Lapisan Gelap -> Teks -> Audio
    video = CompositeVideoClip([bg_image, dark_overlay, txt_clip]).with_audio(audio)
    
    # Render akhir
    video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    print(f"[3/4] Video mahakarya berhasil diselesaikan: {output_video}")
    return output_video

# --- 4. AUTO-UPLOAD KE YOUTUBE ---
def upload_to_youtube(video_path, title, description, tags):
    print("[4/4] Mengunggah kebijaksanaan ke YouTube...")
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
            "categoryId": "27" # Kategori: Education / Motivasi
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print(f"✅ Mahakarya berhasil dipublikasikan! Link: https://youtu.be/{response['id']}")

if __name__ == "__main__":
    try:
        # 1. Memilih kebijaksanaan hari ini secara acak
        konten = random.choice(KUOTES)
        naskah = konten["teks"]
        prompt_gambar = konten["prompt_gambar"]
        
        # Metadata YouTube
        JUDUL_VIDEO = "Renungan Hari Ini 💡 #shorts #motivasi"
        DESKRIPSI = f"{naskah}\n\nTeruslah melangkah ke depan. Jangan lupa subscribe untuk asupan motivasi setiap hari.\n\n#motivasi #inspirasi #quotes #filsafat #pengembangandiri #shorts"
        TAGS = ["motivasi", "inspirasi", "quotes bijak", "filsafat", "pengembangan diri", "kata mutiara", "shorts"]
        
        # 2. Proses Penciptaan
        bg_file = generate_ai_image(prompt_gambar)
        audio_file = generate_ai_voice(naskah)
        video_final = generate_video(bg_file, audio_file, naskah)
        
        # 3. Publikasi
        upload_to_youtube(video_final, JUDUL_VIDEO, DESKRIPSI, TAGS)
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan dalam meditasi bot: {e}")
