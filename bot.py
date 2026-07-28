import os
import time
import random
import requests
import urllib.parse
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, ImageClip, ColorClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- KOLEKSI NASKAH MOTIVASI VIRAL (DURASI > 15 DETIK) ---
KONTEN_BATCH = [
    {
        "hook": "HENTIKAN SCROLLMU SEJENAK.",
        "isi": "Jangan pernah takut berjalan lambat,\ntakutlah jika kamu hanya diam di tempat.\nLangkah kecil hari ini adalah awal dari kemenangan besar.",
        "cta": "Ketik 'SAYA BISA' di komentar jika kamu siap berubah!",
        "prompt_ai": "A lonely wanderer standing on a cliff edge looking at a surreal glowing galaxy, epic cinematic sunset, hyperrealistic 8k"
    },
    {
        "hook": "BACA INI SAAT KAMU LELAH.",
        "isi": "Pohon yang paling kuat tumbuh dari angin yang paling kencang.\nUjian yang kamu hadapi saat ini sedang membentuk dirimu menjadi sosok yang tak terkalahkan.",
        "cta": "Simpan video ini agar kamu ingat saat sedang turun!",
        "prompt_ai": "A giant ancient resilient tree on top of a mountain during a thunder storm, dramatic lighting, masterpiece"
    },
    {
        "hook": "RAHASIA ORANG SUKSES.",
        "isi": "Rasa sakit karena kedisiplinan hanya menekanmu sebentar.\nNamun rasa sakit karena penyesalan akan menghantuimu seumur hidup.\nPilihlah perjuanganmu sekarang.",
        "cta": "Ketik 'SIAP' untuk berkomitmen pada dirimu sendiri!",
        "prompt_ai": "A dark moody gym or temple at dawn, golden sunlight piercing through smoke, inspiring cinematic aesthetic"
    },
    {
        "hook": "INGATLAH SATU HAL INI.",
        "isi": "Kamu tidak bisa mengubah masa lalu yang telah berlalu.\nTapi kamu memegang kendali penuh atas cerita yang ingin kamu tuliskan esok hari.",
        "cta": "Bagikan video ini ke orang yang sedang butuh semangat!",
        "prompt_ai": "An open glowing magical book in an old mysterious library, floating dust particles, atmospheric lighting"
    },
    {
        "hook": "PESAN UNTUK MASA DEPANMU.",
        "isi": "Banyak orang gagal bukan karena kurang berpotensi,\ntetapi karena mereka berhenti tepat satu langkah sebelum berhasil.\nTeruslah melangkah.",
        "cta": "Ketik 'PANTANG MENYERAH' jika kamu percaya pada prosesmu!",
        "prompt_ai": "A futuristic glowing path towards a bright horizon, endless road in a scenic valley at twilight, hyperrealistic"
    }
]

# --- 1. AI IMAGE GENERATOR (Pollinations AI) ---
def generate_ai_image(prompt, index, output_filename):
    print(f"[{index}/5] 🎨 Meminta AI melukis gambar: '{prompt[:30]}...'")
    full_prompt = f"{prompt}, dark moody aesthetic, vertical 9:16 portrait, cinematic lighting, ultra detailed, 8k"
    encoded_prompt = urllib.parse.quote(full_prompt)
    seed = random.randint(1, 99999)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(image_url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return output_filename
    else:
        raise Exception(f"Gagal mengunduh gambar AI (Status: {response.status_code})")

# --- 2. AI NEURAL VOICE GENERATOR (Edge-TTS) ---
def generate_ai_voice(full_text, index, output_audio):
    print(f"[{index}/5] 🎙️ Menyuarakan naskah dengan Suara AI Neural...")
    # Kecepatan dinaikkan sedikit (-5%) agar intonasi tegas dan tidak bosan
    command = f'edge-tts --voice id-ID-ArdiNeural --rate=-5% --text "{full_text}" --write-media {output_audio}'
    os.system(command)
    if os.path.exists(output_audio):
        return output_audio
    else:
        raise Exception("Gagal membuat suara AI.")

# --- 3. EDITOR VIDEO DENGAN LAYOUT TEKS PRESISI (SAFE ZONE) ---
def render_short_video(bg_image_path, audio_path, hook_text, isi_text, cta_text, output_video, index):
    print(f"[{index}/5] 🎬 Merakit video Shorts durasi monetisasi...")
    
    audio = AudioFileClip(audio_path)
    audio_duration = audio.duration
    # Durasi video disesuaikan dengan suara + 1 detik jeda nyaman
    video_duration = audio_duration + 1.0 
    
    # 1. Background Gambar AI
    bg_clip = ImageClip(bg_image_path).with_duration(video_duration)
    bg_clip = bg_clip.resized(height=1920)
    bg_clip = bg_clip.cropped(x_center=bg_clip.w/2, y_center=bg_clip.h/2, width=1080, height=1920)
    
    # 2. Dark Overlay Transparan (Agar Teks Mudah Dibaca)
    overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).with_opacity(0.45).with_duration(video_duration)
    
    # Combined Text untuk Tampilan Utama
    full_display_text = f"🔥 {hook_text} 🔥\n\n{isi_text}\n\n👇 {cta_text}"
    
    # 3. Teks Utama dengan Layout Safe Zone
    txt_clip = TextClip(
        text=full_display_text, 
        font_size=48, 
        color='white', 
        size=(920, None),
        method='caption',
        text_align='center'
    ).with_duration(video_duration).with_position('center')
    
    # 4. Kotak Latar Teks (Text Card Overlay) agar Teks Terbaca Jelas di HP Mana Pun
    box_width = 980
    box_height = txt_clip.h + 80
    text_bg_box = ColorClip(size=(box_width, box_height), color=(15, 15, 20)).with_opacity(0.70).with_duration(video_duration).with_position('center')
    
    # Merakit Seluruh Layer
    video = CompositeVideoClip([bg_clip, overlay, text_bg_box, txt_clip]).with_audio(audio)
    
    # Render Video
    video.write_videofile(
        output_video, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        preset="ultrafast"
    )
    print(f"[{index}/5] ✅ Video #{index} selesai dirender! Durasi: {video_duration:.1f} detik")
    return output_video, video_duration

# --- 4. AUTO-UPLOAD KE YOUTUBE ---
def upload_to_youtube(video_path, title, description, tags, index):
    print(f"[{index}/5] 🚀 Mengunggah video #{index} ke YouTube...")
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
            "categoryId": "27" # Category: Education / Motivation
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print(f"[{index}/5] 🎉 BERHASIL UNGGAH! Link Video: https://youtu.be/{response['id']}\n")

# --- EXECUTION MAIN LOOP (BATCH 5 VIDEOS) ---
if __name__ == "__main__":
    print("==================================================")
    print("⚡ MEMULAI PRODUKSI MASAL 5 VIDEO SHORTS MOTIVASI ⚡")
    print("==================================================\n")
    
    # Mengambil 5 item dari koleksi konten
    selected_batch = KONTEN_BATCH[:5]
    
    for i, item in enumerate(selected_batch, 1):
        try:
            print(f"--- MENGERJAKAN VIDEO {i} DARI 5 ---")
            
            # Penggabungan Teks Suara
            suara_naskah = f"{item['hook']} {item['isi'].replace(chr(10), ' ')} {item['cta']}"
            
            # Nama File Output Sementara
            img_file = f"bg_{i}.jpg"
            audio_file = f"voice_{i}.mp3"
            video_file = f"short_output_{i}.mp4"
            
            # SEO Title & Description
            clean_hook = item['hook'].replace('.', '')
            JUDUL = f"{clean_hook} 💡 #shorts #motivasi #quotes"
            if len(JUDUL) > 100:
                JUDUL = JUDUL[:90] + " #shorts"
                
            DESKRIPSI = f"{item['isi']}\n\n{item['cta']}\n\n#motivasi #quotes #inspirasi #shorts #mindset #katabijak"
            TAGS = ["motivasi", "quotes", "shorts", "inspirasi", "katabijak", "mindset"]
            
            # TAHAP 1: Gambar AI
            generate_ai_image(item['prompt_ai'], i, img_file)
            
            # TAHAP 2: Suara AI
            generate_ai_voice(suara_naskah, i, audio_file)
            
            # TAHAP 3: Render Video
            _, durasi = render_short_video(img_file, audio_file, item['hook'], item['isi'], item['cta'], video_file, i)
            
            # Validasi Durasi Minimal 15 Detik
            if durasi < 15.0:
                print(f"⚠️ Peringatan: Durasi video ({durasi:.1f}s) di bawah 15 detik. Menyesuaikan jeda...")
            
            # TAHAP 4: Upload YouTube
            upload_to_youtube(video_file, JUDUL, DESKRIPSI, TAGS, i)
            
            # Anti-Spam Delay antara setiap upload (15 detik)
            if i < 5:
                print("⏳ Jeda 15 detik sebelum memproses video berikutnya untuk keamanan API...\n")
                time.sleep(15)
                
        except Exception as e:
            print(f"❌ Terjadi kesalahan pada video #{i}: {e}\n")
            
    print("==================================================")
    print("✨ SELURUH BATCH 5 VIDEO SELESAI DIPRODUKSI DAN DIUNGGAH ✨")
    print("==================================================")
