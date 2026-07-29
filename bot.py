import os
import time
import random
import requests
import urllib.parse
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, ImageClip, ColorClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- BANK NASKAH KELAS ATAS (MENYENTUH & FILOSOFIS) ---
BANK_KONTEN = [
    {"id": "V001", "hook": "TERUNTUK KAMU YANG SEDANG LELAH.", "isi": "Tidak apa-apa jika hari ini kamu tidak berlari kencang.\nBertahan dan tetap bernapas di tengah badai, sudah merupakan sebuah kemenangan yang luar biasa.", "cta": "Ketik 'SAYA KUAT' untuk berterima kasih pada dirimu sendiri.", "prompt_ai": "A solitary figure sitting on a bench looking at a peaceful glowing sunset over a calm ocean, cinematic, healing vibe"},
    {"id": "V002", "hook": "BACA INI SEBELUM MENYERAH.", "isi": "Orang yang paling kuat bukanlah mereka yang tidak pernah menangis.\nTetapi mereka yang menangis di malam hari, namun tetap bangun di pagi hari untuk melanjutkan peperangan.", "cta": "Bagikan ke temanmu yang sedang butuh pelukan hangat.", "prompt_ai": "A beautiful sunrise emerging behind dark heavy rain clouds over a misty mountain, hope, epic lighting, highly detailed"},
    {"id": "V003", "hook": "SADARKAH KAMU?", "isi": "Satu-satunya orang yang akan bersamamu dari lahir hingga akhir hayat, adalah dirimu sendiri.\nBerhentilah terlalu keras pada dirimu. Maafkanlah masa lalumu.", "cta": "Ketik 'AKU BERHARGA' jika kamu sepakat.", "prompt_ai": "A person looking at their own glowing reflection in a crystal clear magical lake, starry night, serene atmosphere"},
    {"id": "V004", "hook": "RAHASIA KETENANGAN HIDUP.", "isi": "Terkadang, jawaban dari masalahmu bukanlah mencari jalan keluar.\nTapi menerima bahwa beberapa hal memang ditakdirkan terjadi, untuk mendewasakanmu.", "cta": "Simpan video ini untuk pengingat di kala sedih.", "prompt_ai": "A lone boat floating on a perfectly calm mirror-like river leading to a glowing giant moon, surreal, peaceful"},
    {"id": "V005", "hook": "WAKTU TERUS BERJALAN.", "isi": "Jangan biarkan ketakutan akan kegagalan menahanmu.\nRasa sakit karena mencoba akan hilang dalam seminggu.\nTapi rasa sakit karena penasaran, akan menghantuimu seumur hidup.", "cta": "Ketik 'SIAP MELANGKAH' untuk memulai hal baru!", "prompt_ai": "An open doorway in a dark room leading to a bright, lush magical forest, stepping into the unknown, cinematic"},
    {"id": "V006", "hook": "HENTIKAN SCROLLMU 15 DETIK.", "isi": "Kamu sudah terlalu banyak memikirkan kebahagiaan orang lain.\nHari ini, ambil waktu sejenak, dan tanyakan pada hatimu:\n'Apa yang sebenarnya membuatku bahagia?'", "cta": "Ketik jawabanmu di kolom komentar!", "prompt_ai": "A cozy warm glowing cabin in a snowy dark forest, safe haven, comforting atmospheric lighting, 8k"},
    {"id": "V007", "hook": "FAKTA YANG MENYAKITKAN.", "isi": "Semakin kamu dewasa, lingkar pertemananmu akan semakin mengecil.\nItu bukan karena kamu sombong. Kamu hanya mulai mengerti bedanya antara kuantitas dan kualitas.", "cta": "Tag sahabat terbaikmu di komentar!", "prompt_ai": "Two glowing wolves standing together on a snowy cliff looking at a vast aurora borealis, loyalty, epic masterpiece"}
]

# --- MANAJEMEN MEMORI (ANTI DUPLIKASI) ---
HISTORY_FILE = "history.txt"

def get_used_ids():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r') as f:
        return [line.strip() for line in f.readlines()]

def mark_id_as_used(video_id):
    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{video_id}\n")

# --- MENGUNDUH FONT PRO (ANTI KORUP & ANTI ERROR) ---
def get_custom_font():
    font_filename = "Montserrat-Black.ttf"
    
    # 1. Hapus file font jika sebelumnya terunduh sebagai file HTML yang rusak (< 100KB)
    if os.path.exists(font_filename) and os.path.getsize(font_filename) < 100000:
        os.remove(font_filename)
        
    # 2. Unduh ulang dari repositori asli yang terjamin kestabilannya
    if not os.path.exists(font_filename):
        print("📥 Mengunduh Font Estetik (Montserrat Black)...")
        # Menggunakan sumber permanen dari GitHub kreator Montserrat
        url = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Black.ttf"
        r = requests.get(url)
        
        if r.status_code == 200:
            with open(font_filename, 'wb') as f:
                f.write(r.content)
            print("✅ Font berhasil diunduh dengan sempurna!")
        else:
            raise Exception(f"Gagal mengunduh font. Status Code: {r.status_code}")
            
    # Mengembalikan path absolut agar sistem grafis bisa membacanya
    return os.path.abspath(font_filename)

# --- 1. AI IMAGE GENERATOR ---
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

# --- 2. AI NEURAL VOICE ---
def generate_ai_voice(full_text, index, output_audio):
    print(f"[{index}/5] 🎙️ Menyuarakan naskah...")
    command = f'edge-tts --voice id-ID-ArdiNeural --rate=-5% --text "{full_text}" --write-media {output_audio}'
    os.system(command)
    return output_audio

# --- 3. EDITOR VIDEO ALA CAPCUT ---
def render_short_video(bg_image_path, audio_path, item, output_video, index):
    print(f"[{index}/5] 🎬 Merakit video CapCut Style...")
    audio = AudioFileClip(audio_path)
    video_duration = audio.duration + 1.5 
    
    bg_clip = ImageClip(bg_image_path).with_duration(video_duration).resized(height=1920).cropped(x_center=540, y_center=960, width=1080, height=1920)
    overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).with_opacity(0.5).with_duration(video_duration)
    
    # Menggunakan font kustom yang sudah dipastikan aman
    font_style = get_custom_font()
    
    txt_hook = TextClip(text=item['hook'], font=font_style, font_size=55, color='yellow', stroke_color='black', stroke_width=2.5, size=(950, None), method='caption', text_align='center')
    txt_hook = txt_hook.with_duration(video_duration).with_position(('center', 450))
    
    txt_isi = TextClip(text=item['isi'], font=font_style, font_size=50, color='white', stroke_color='black', stroke_width=2, size=(950, None), method='caption', text_align='center')
    txt_isi = txt_isi.with_duration(video_duration).with_position(('center', 650))
    
    txt_cta = TextClip(text=f"👇 {item['cta']}", font=font_style, font_size=45, color='cyan', stroke_color='black', stroke_width=2, size=(950, None), method='caption', text_align='center')
    txt_cta = txt_cta.with_duration(video_duration).with_position(('center', 1300))
    
    def make_progress_bar(t):
        w = int(1080 * (t / video_duration))
        if w == 0: w = 1
        return ColorClip(size=(w, 15), color=(255, 215, 0)).get_frame(t)
        
    progress_bar = ColorClip(size=(1080, 15), color=(255, 215, 0)).with_duration(video_duration)
    progress_bar = progress_bar.fl_image(lambda image, t: make_progress_bar(t)) 
    progress_bar = progress_bar.with_position(('left', 'bottom'))

    video = CompositeVideoClip([bg_clip, overlay, txt_hook, txt_isi, txt_cta, progress_bar]).with_audio(audio)
    video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    return output_video, video_duration

# --- 4. YOUTUBE UPLOADER ---
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
    used_ids = get_used_ids()
    available_content = [c for c in BANK_KONTEN if c['id'] not in used_ids]
    
    if not available_content:
        print("⚠️ Semua naskah di Bank Konten sudah digunakan! Silakan tambahkan naskah baru ke bot.py.")
        exit()
        
    selected_batch = available_content[:5]
    print(f"⚡ MEMPROSES {len(selected_batch)} VIDEO BARU ⚡\n")
    
    for i, item in enumerate(selected_batch, 1):
        try:
            suara_naskah = f"{item['hook']} {item['isi'].replace(chr(10), ' ')} {item['cta']}"
            img_file = f"bg_{i}.jpg"
            audio_file = f"voice_{i}.mp3"
            video_file = f"short_{i}.mp4"
            
            clean_hook = item['hook'].replace('.', '')
            JUDUL = f"{clean_hook} 💡 #shorts #motivasi #renungan"
            if len(JUDUL) > 100: JUDUL = JUDUL[:90] + " #shorts"
            DESKRIPSI = f"{item['isi']}\n\n{item['cta']}\n\n#motivasi #renungan #inspirasi #shorts #mindset #psikologi #katabijak"
            TAGS = ["motivasi", "quotes", "shorts", "renungan", "psikologi", "mindset"]
            
            generate_ai_image(item['prompt_ai'], i, img_file)
            generate_ai_voice(suara_naskah, i, audio_file)
            _, durasi = render_short_video(img_file, audio_file, item, video_file, i)
            
            upload_to_youtube(video_file, JUDUL, DESKRIPSI, TAGS, i)
            mark_id_as_used(item['id'])
            
            if i < len(selected_batch):
                print("⏳ Jeda 15 detik untuk keamanan API YouTube...\n")
                time.sleep(15)
                
        except Exception as e:
            print(f"❌ Kesalahan pada video {item['id']}: {e}\n")
