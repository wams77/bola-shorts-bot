import os
import time
import random
import requests
import urllib.parse
from groq import Groq
from moviepy import AudioFileClip, VideoFileClip, TextClip, CompositeVideoClip, ColorClip, ImageClip, concatenate_videoclips
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Mengunci direktori kerja agar file tidak "nyasar"
BASE_DIR = os.path.abspath(os.getcwd())

# --- KONFIGURASI GROQ AI ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# --- MANAJEMEN MEMORI (ANTI DUPLIKASI KONTEN) ---
HISTORY_FILE = "history_hooks.txt"

def get_used_hooks():
    """Mengambil riwayat naskah yang sudah pernah dibuat agar AI tidak mengulanginya"""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def mark_hook_as_used(hook_text):
    """Menyimpan hook baru ke dalam memori bot"""
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{hook_text}\n")

# --- 1. GROQ AI: GENERATOR NASKAH + QUERY PEXELS ---
def generate_dynamic_content(num_videos=5):
    print(f"🕊️ Meminta Groq Llama-3.3 meracik {num_videos} naskah & kueri video Pexels...")
    
    used_hooks = get_used_hooks()
    history_context = "\n".join(used_hooks[-25:]) if used_hooks else "(Belum ada riwayat, buat topik bebas)"
    
    prompt = f"""
    Bertindaklah sebagai penulis naskah video motivasi, psikologi, dan filosofis tingkat tinggi.
    Buatlah {num_videos} naskah video pendek (YouTube Shorts) yang menyentuh hati, mendalam, dan relatable.
    
    ATURAN MUTLAK ANTI-DUPLIKASI: 
    Dilarang keras membuat naskah dengan tema, pesan, atau kalimat pembuka (HOOK) yang mirip dengan daftar naskah yang sudah pernah dibuat ini:
    {history_context}
    
    Gunakan pemisah '---' antar naskah. Format wajib persis seperti ini:
    
    HOOK: [1 kalimat pembuka yang sangat memancing emosi/penasaran]
    ISI: [2-3 kalimat filosofis, mendalam, tentang kehidupan, lelah, penyembuhan luka, mental health, atau kedewasaan]
    CTA: [Ajakan interaksi, misal: Bagikan ke temanmu yang butuh pelukan hangat.]
    PEXELS_QUERY: [Kata kunci bahasa Inggris untuk mencari video background di Pexels yang SANGAT RELEVAN dengan isi naskah, contoh: "dark moody ocean waves crashing cliff", "foggy pine forest drone shot", "lonely person walking in rain cinematic"]
    """
    
    raw_text = ""
    for attempt in range(3):
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Anda adalah asisten AI penulis naskah yang patuh pada format instruksi."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=2048,
            )
            raw_text = chat_completion.choices[0].message.content
            break
        except Exception as e:
            print(f"⚠️ Error Groq (Percobaan {attempt+1}/3): {e}")
            time.sleep(15)
    else:
        raise Exception("❌ Gagal total menghubungi Groq AI.")

    batch = []
    for i, chunk in enumerate(raw_text.split("---")):
        if i >= num_videos: break
        lines = [line.strip() for line in chunk.strip().split("\n") if line.strip()]
        if not lines: continue
        
        hook = "TERUNTUK KAMU YANG LELAH."
        isi = "Teruslah bernapas dan bertahan, kamu sudah melakukan yang terbaik hari ini."
        cta = "Ketik Amin jika kamu percaya."
        pexels_query = "dark moody nature cinematic drone shot"
        
        for line in lines:
            if line.startswith("HOOK:"): hook = line.replace("HOOK:", "").strip()
            elif line.startswith("ISI:"): isi = line.replace("ISI:", "").strip()
            elif line.startswith("CTA:"): cta = line.replace("CTA:", "").strip()
            elif line.startswith("PEXELS_QUERY:"): pexels_query = line.replace("PEXELS_QUERY:", "").strip()
                
        batch.append({
            "id": f"VID_{int(time.time())}_{i}",
            "hook": hook,
            "isi": isi,
            "cta": cta,
            "pexels_query": pexels_query
        })
        
    print(f"✅ Berhasil meracik {len(batch)} Naskah & Kueri Pexels Unik!")
    return batch

# --- MENGUNDUH FONT PRO ---
def get_custom_font():
    font_filename = os.path.join(BASE_DIR, "Montserrat-Black.ttf")
    if os.path.exists(font_filename) and os.path.getsize(font_filename) < 100000:
        os.remove(font_filename)
        
    if not os.path.exists(font_filename):
        print("📥 Mengunduh Font Estetik (Montserrat Black)...")
        url = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Black.ttf"
        r = requests.get(url)
        if r.status_code == 200:
            with open(font_filename, 'wb') as f:
                f.write(r.content)
            print("✅ Font berhasil diunduh dengan sempurna!")
        else:
            raise Exception(f"Gagal mengunduh font. Status Code: {r.status_code}")
    return os.path.abspath(font_filename)

# --- 2. PEXELS VIDEO BACKGROUND DOWNLOADER DENGAN VALIDASI ---
def download_pexels_video(query, output_filename):
    print(f"🎬 Mencari video latar relevan di Pexels untuk: '{query}'...")
    api_key = os.environ.get("PEXELS_API_KEY")
    headers = {"Authorization": api_key}
    
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=5"
    
    try:
        response = requests.get(url, headers=headers, timeout=15).json()
        if "videos" in response and len(response["videos"]) > 0:
            video_obj = random.choice(response["videos"])
            video_files = video_obj["video_files"]
            hd_file = next((v for v in video_files if v["quality"] == "hd"), video_files[0])
            video_url = hd_file["link"]
            
            vid_data = requests.get(video_url, timeout=30).content
            with open(output_filename, 'wb') as f:
                f.write(vid_data)
                
            if os.path.exists(output_filename) and os.path.getsize(output_filename) > 50000:
                print("✅ Stok video Pexels berhasil diunduh dan divalidasi!")
                return output_filename
    except Exception as e:
        print(f"⚠️ Peringatan unduhan Pexels: {e}")

    # Fallback aman jika gagal/korup
    print("⚠️ Menggunakan video latar cadangan universal yang aman...")
    fallback_url = "https://api.pexels.com/videos/search?query=nature+landscape+drone&orientation=portrait&per_page=1"
    fallback_res = requests.get(fallback_url, headers=headers).json()
    
    if "videos" in fallback_res and len(fallback_res["videos"]) > 0:
        video_obj = fallback_res["videos"][0]
        hd_file = video_obj["video_files"][0]
        vid_data = requests.get(hd_file["link"], timeout=30).content
        with open(output_filename, 'wb') as f:
            f.write(vid_data)
        return output_filename
        
    raise Exception("Gagal total mengunduh video dari Pexels API.")

# --- 3. AI NEURAL VOICE ---
def generate_ai_voice(full_text, index, output_audio):
    print(f"[{index}/5] 🎙️ Menyuarakan naskah...")
    command = f'edge-tts --voice id-ID-ArdiNeural --rate=-5% --text "{full_text}" --write-media "{output_audio}"'
    os.system(command)
    return output_audio

# --- 4. EDITOR VIDEO CAPCUT STYLE (ANTI-ERROR TEXTCLIP SHAPE) ---
def render_short_video(bg_video_path, audio_path, item, output_video, index):
    print(f"[{index}/5] 🎬 Merakit video latar Pexels & Teks...")
    audio = AudioFileClip(audio_path)
    video_duration = audio.duration + 1.5 
    
    video_clip = VideoFileClip(bg_video_path)
    
    # Algoritma Looping Video jika durasinya kurang dari suara narator
    if video_clip.duration < video_duration:
        n_loops = int(video_duration // video_clip.duration) + 1
        video_clip = concatenate_videoclips([video_clip] * n_loops)
        
    video_clip = video_clip.subclipped(0, video_duration)
    video_clip = video_clip.resized(height=1920).cropped(x_center=video_clip.w/2, y_center=video_clip.h/2, width=1080, height=1920)
    
    overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).with_opacity(0.45).with_duration(video_duration)
    
    font_style = get_custom_font()
    
    # Menggunakan metode aman untuk TextClip agar terhindar dari error broadcasting shape (376,0)
    txt_hook = TextClip(text=item['hook'], font=font_style, font_size=55, color='yellow', stroke_color='black', stroke_width=2.5, method='caption', size=(950, None))
    txt_hook = txt_hook.with_duration(video_duration).with_position(('center', 450))
    
    txt_isi = TextClip(text=item['isi'], font=font_style, font_size=50, color='white', stroke_color='black', stroke_width=2, method='caption', size=(950, None))
    txt_isi = txt_isi.with_duration(video_duration).with_position(('center', 650))
    
    txt_cta = TextClip(text=f"👇 {item['cta']}", font=font_style, font_size=45, color='cyan', stroke_color='black', stroke_width=2, method='caption', size=(950, None))
    txt_cta = txt_cta.with_duration(video_duration).with_position(('center', 1300))
    
    progress_bar = ColorClip(size=(1080, 15), color=(255, 215, 0)).with_duration(video_duration)
    progress_bar = progress_bar.with_position(lambda t: (int(-1080 + (1080 * (t / video_duration))), 'bottom'))

    video = CompositeVideoClip([video_clip, overlay, txt_hook, txt_isi, txt_cta, progress_bar]).with_audio(audio)
    video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    # Melepaskan file handle sistem
    try:
        video.close()
        audio.close()
        video_clip.close()
    except Exception:
        pass
        
    time.sleep(2) # Mencegah error disk-latency GitHub Actions
    if not os.path.exists(output_video):
        raise Exception(f"File {output_video} gagal dibuat oleh MoviePy!")
        
    return output_video, video_duration

# --- 5. YOUTUBE UPLOADER ---
def upload_to_youtube(video_path, title, description, tags, index):
    print(f"[{index}/5] 🚀 Mengunggah ke YouTube...")
    creds = Credentials(token=None, refresh_token=os.environ.get("YOUTUBE_REFRESH_TOKEN"), token_uri="https://oauth2.googleapis.com/token", client_id=os.environ.get("YOUTUBE_CLIENT_ID"), client_secret=os.environ.get("YOUTUBE_CLIENT_SECRET"))
    youtube = build('youtube', 'v3', credentials=creds)
    body = {"snippet": {"title": title, "description": description, "tags": tags, "categoryId": "27"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    print(f"[{index}/5] 🎉 BERHASIL! Link: https://youtu.be/{response['id']}\n")

# --- MAIN LOOP ---
if __name__ == "__main__":
    selected_batch = generate_dynamic_content(num_videos=5)
    
    print(f"⚡ MEMPROSES {len(selected_batch)} VIDEO BARU ⚡\n")
    
    for i, item in enumerate(selected_batch, 1):
        try:
            suara_naskah = f"{item['hook']} {item['isi'].replace(chr(10), ' ')} {item['cta']}"
            video_bg_file = os.path.join(BASE_DIR, f"stock_bg_{i}.mp4")
            audio_file = os.path.join(BASE_DIR, f"voice_{i}.mp3")
            video_file = os.path.join(BASE_DIR, f"short_{i}.mp4")
            
            clean_hook = item['hook'].replace('.', '').replace('"', '')
            JUDUL = f"{clean_hook} 💡 #shorts #motivasi #renungan"
            if len(JUDUL) > 100: JUDUL = JUDUL[:90] + " #shorts"
            DESKRIPSI = f"{item['isi']}\n\n{item['cta']}\n\n#motivasi #renungan #inspirasi #shorts #mindset #psikologi #katabijak"
            TAGS = ["motivasi", "quotes", "shorts", "renungan", "psikologi", "mindset"]
            
            download_pexels_video(item['pexels_query'], video_bg_file)
            generate_ai_voice(suara_naskah, i, audio_file)
            _, durasi = render_short_video(video_bg_file, audio_file, item, video_file, i)
            
            upload_to_youtube(video_file, JUDUL, DESKRIPSI, TAGS, i)
            
            # SIMPAN KE MEMORI AGAR BESOK TIDAK DIULANG
            mark_hook_as_used(item['hook'])
            
            if i < len(selected_batch):
                print("⏳ Jeda 15 detik untuk keamanan API YouTube...\n")
                time.sleep(15)
                
        except Exception as e:
            print(f"❌ Kesalahan pada video {i}: {e}\n")
