import os
import time
import random
import requests
import urllib.parse
import google.generativeai as genai
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, ImageClip, ColorClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- KONFIGURASI GEMINI AI ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

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

# --- 1. GEMINI AI: GENERATOR NASKAH TANPA BATAS ---
def generate_dynamic_content(num_videos=5):
    print(f"🕊️ Meminta Gemini AI meracik {num_videos} naskah baru yang belum pernah ada...")
    
    # Ambil 25 hook terakhir dari memori untuk memberi tahu AI apa yang harus dihindari
    used_hooks = get_used_hooks()
    history_context = "\n".join(used_hooks[-25:]) if used_hooks else "(Belum ada riwayat, buat topik bebas)"
    
    prompt = f"""
    Bertindaklah sebagai penulis naskah video motivasi, psikologi, dan filosofis tingkat tinggi.
    Buatlah {num_videos} naskah video pendek (YouTube Shorts) yang menyentuh hati, mendalam, dan *relatable*.
    
    ATURAN MUTLAK ANTI-DUPLIKASI: 
    Dilarang keras membuat naskah dengan tema, pesan, atau kalimat pembuka (HOOK) yang mirip dengan daftar naskah yang sudah pernah dibuat ini:
    {history_context}
    
    Gunakan pemisah '---' antar naskah. Format wajib persis seperti ini:
    
    HOOK: [1 kalimat pembuka yang sangat memancing emosi/penasaran]
    ISI: [2-3 kalimat filosofis, mendalam, tentang kehidupan, lelah, penyembuhan luka, mental health, atau kedewasaan]
    CTA: [Ajakan interaksi, misal: Bagikan ke temanmu yang butuh pelukan hangat.]
    PROMPT_AI: [Deskripsi bahasa Inggris untuk AI Gambar. Bebas, kreatif, estetik, cinematic, moody. Contoh: Cinematic portrait of a lone boat on a magical glowing lake, misty, peace, 8k]
    """
    
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    raw_text = ""
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text
            break
        except Exception as e:
            print(f"⚠️ Error Gemini (Percobaan {attempt+1}/3): {e}")
            time.sleep(65)
    else:
        raise Exception("❌ Gagal total menghubungi Gemini AI.")

    batch = []
    for i, chunk in enumerate(raw_text.split("---")):
        if i >= num_videos: break
        lines = [line.strip() for line in chunk.strip().split("\n") if line.strip()]
        if not lines: continue
        
        hook = "TERUNTUK KAMU YANG LELAH."
        isi = "Teruslah bernapas dan bertahan, kamu sudah melakukan yang terbaik hari ini."
        cta = "Ketik Amin jika kamu percaya."
        prompt_ai = "A solitary figure looking at a peaceful glowing sunset, cinematic"
        
        for line in lines:
            if line.startswith("HOOK:"): hook = line.replace("HOOK:", "").strip()
            elif line.startswith("ISI:"): isi = line.replace("ISI:", "").strip()
            elif line.startswith("CTA:"): cta = line.replace("CTA:", "").strip()
            elif line.startswith("PROMPT_AI:"): prompt_ai = line.replace("PROMPT_AI:", "").strip()
                
        batch.append({
            "id": f"VID_{int(time.time())}_{i}",
            "hook": hook,
            "isi": isi,
            "cta": cta,
            "prompt_ai": prompt_ai
        })
        
    print(f"✅ Berhasil meracik {len(batch)} Naskah Filosofis Unik!")
    return batch

# --- MENGUNDUH FONT PRO ---
def get_custom_font():
    font_filename = "Montserrat-Black.ttf"
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

# --- 2. AI IMAGE GENERATOR ---
def generate_ai_image(prompt, index, output_filename):
    print(f"[{index}/5] 🎨 Melukis visual AI...")
    full_prompt = f"{prompt}, dark moody aesthetic, vertical portrait, cinematic lighting, masterpiece"
    encoded_prompt = urllib.parse.quote(full_prompt)
    seed = random.randint(1, 99999)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}"
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return output_filename
    raise Exception("Gagal mengunduh gambar AI.")

# --- 3. AI NEURAL VOICE ---
def generate_ai_voice(full_text, index, output_audio):
    print(f"[{index}/5] 🎙️ Menyuarakan naskah...")
    command = f'edge-tts --voice id-ID-ArdiNeural --rate=-5% --text "{full_text}" --write-media {output_audio}'
    os.system(command)
    return output_audio

# --- 4. EDITOR VIDEO ALA CAPCUT ---
def render_short_video(bg_image_path, audio_path, item, output_video, index):
    print(f"[{index}/5] 🎬 Merakit video CapCut Style...")
    audio = AudioFileClip(audio_path)
    video_duration = audio.duration + 1.5 
    
    bg_clip = ImageClip(bg_image_path).with_duration(video_duration).resized(height=1920).cropped(x_center=540, y_center=960, width=1080, height=1920)
    overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).with_opacity(0.5).with_duration(video_duration)
    
    font_style = get_custom_font()
    
    txt_hook = TextClip(text=item['hook'], font=font_style, font_size=55, color='yellow', stroke_color='black', stroke_width=2.5, size=(950, None), method='caption', text_align='center')
    txt_hook = txt_hook.with_duration(video_duration).with_position(('center', 450))
    
    txt_isi = TextClip(text=item['isi'], font=font_style, font_size=50, color='white', stroke_color='black', stroke_width=2, size=(950, None), method='caption', text_align='center')
    txt_isi = txt_isi.with_duration(video_duration).with_position(('center', 650))
    
    txt_cta = TextClip(text=f"👇 {item['cta']}", font=font_style, font_size=45, color='cyan', stroke_color='black', stroke_width=2, size=(950, None), method='caption', text_align='center')
    txt_cta = txt_cta.with_duration(video_duration).with_position(('center', 1300))
    
    progress_bar = ColorClip(size=(1080, 15), color=(255, 215, 0)).with_duration(video_duration)
    progress_bar = progress_bar.with_position(lambda t: (int(-1080 + (1080 * (t / video_duration))), 'bottom'))

    video = CompositeVideoClip([bg_clip, overlay, txt_hook, txt_isi, txt_cta, progress_bar]).with_audio(audio)
    video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
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
    # Generator dinamis pengganti Bank Konten (Buat 5 video)
    selected_batch = generate_dynamic_content(num_videos=5)
    
    print(f"⚡ MEMPROSES {len(selected_batch)} VIDEO BARU ⚡\n")
    
    for i, item in enumerate(selected_batch, 1):
        try:
            suara_naskah = f"{item['hook']} {item['isi'].replace(chr(10), ' ')} {item['cta']}"
            img_file = f"bg_{i}.jpg"
            audio_file = f"voice_{i}.mp3"
            video_file = f"short_{i}.mp4"
            
            clean_hook = item['hook'].replace('.', '').replace('"', '')
            JUDUL = f"{clean_hook} 💡 #shorts #motivasi #renungan"
            if len(JUDUL) > 100: JUDUL = JUDUL[:90] + " #shorts"
            DESKRIPSI = f"{item['isi']}\n\n{item['cta']}\n\n#motivasi #renungan #inspirasi #shorts #mindset #psikologi #katabijak"
            TAGS = ["motivasi", "quotes", "shorts", "renungan", "psikologi", "mindset"]
            
            generate_ai_image(item['prompt_ai'], i, img_file)
            generate_ai_voice(suara_naskah, i, audio_file)
            _, durasi = render_short_video(img_file, audio_file, item, video_file, i)
            
            upload_to_youtube(video_file, JUDUL, DESKRIPSI, TAGS, i)
            
            # SIMPAN KE MEMORI AGAR BESOK TIDAK DIULANG
            mark_hook_as_used(item['hook'])
            
            if i < len(selected_batch):
                print("⏳ Jeda 15 detik untuk keamanan API YouTube...\n")
                time.sleep(15)
                
        except Exception as e:
            print(f"❌ Kesalahan pada video {i}: {e}\n")
