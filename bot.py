import os
import time
import random
import requests
import urllib.parse
import asyncio
import edge_tts
import textwrap
from groq import Groq
from moviepy import (
    AudioFileClip, 
    CompositeAudioClip, 
    CompositeVideoClip, 
    ColorClip, 
    ImageClip, 
    VideoFileClip, 
    concatenate_audioclips, 
    concatenate_videoclips
)
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# KONFIGURASI DIREKTORI & API
# ==========================================
BASE_DIR = os.path.abspath(os.getcwd())

# Konfigurasi Groq API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    print("⚠️ PERINGATAN: GROQ_API_KEY belum dipasang!")
    groq_client = None

# Konfigurasi Pexels API
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# ==========================================
# 1. GROQ AI: GENERATOR NASKAH STOICISME
# ==========================================
def generate_stoic_script(num_videos=3):
    print(f"🏛️ Meminta Groq Llama-3 meracik {num_videos} naskah YouTube Shorts Stoicisme...")
    
    prompt = f"""
    Bertindaklah sebagai konten kreator YouTube Shorts yang fokus pada filsafat Stoicisme (Stoa) dan kebijaksanaan hidup.
    Buatlah {num_videos} naskah video pendek (durasi 30-40 detik) yang berisi ketenangan batin, pengendalian diri, dan kebijaksanaan dari para filsuf Stoic (seperti Marcus Aurelius, Seneca, atau Epictetus).
    Gunakan pemisah '---' antar naskah. Format persis seperti ini:
    
    JUDUL: [Judul video yang tenang dan memancing rasa penasaran, max 60 karakter]
    QUOTE: [Satu kalimat kutipan asli dari filsuf Stoic yang paling kuat dan mendalam]
    NASKAH: [Naskah suara narator yang menenangkan, bijak, dan mendalam. Tanpa jeda waktu, langsung isi naskah narasi]
    PENCARIAN_VIDEO: [Kata kunci bahasa Inggris untuk video Pexels bertema stoic, misal: "ancient statue", "calm ocean waves", "man thinking nature", "roman ruins", "cinematic fog calm"]
    """
    
    raw_text = ""
    for attempt in range(3):
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Anda adalah asisten AI filsuf Stoic. Jangan gunakan format markdown (seperti tanda bintang). Selalu ikuti struktur yang diminta persis."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=1500,
            )
            raw_text = chat_completion.choices[0].message.content
            print(f"📄 Naskah mentah dari AI:\n{raw_text[:200]}...\n")
            break 
        except Exception as e:
            print(f"⚠️ Error Groq (Percobaan {attempt+1}/3): {e}")
            time.sleep(15)
    else:
        raise Exception("❌ Gagal total menghubungi Groq AI.")

    batch = []
    chunks = raw_text.split("---")
    
    for chunk in chunks:
        if len(batch) >= num_videos: break
        
        ref_judul = "Kebijaksanaan Stoic"
        quote = "Kamu memiliki kendali atas pikiranmu, bukan kejadian di luar sana."
        naskah = "Sadarilah hal ini, dan kamu akan menemukan kekuatan sejati. Stoicisme mengajarkan kita untuk fokus pada apa yang bisa kita kendalikan."
        keyword = "ancient statue cinematic"
        
        # PARSER MEMBERSIHKAN FORMAT ASTERISK (*) JIKA ADA
        lines = chunk.strip().split("\n")
        has_content = False
        for line in lines:
            line_clean = line.replace("**", "").replace("*", "").strip()
            if not line_clean: continue
            has_content = True
            
            if line_clean.upper().startswith("JUDUL:"):
                ref_judul = line_clean[6:].strip()
            elif line_clean.upper().startswith("QUOTE:"):
                quote = line_clean[6:].strip()
            elif line_clean.upper().startswith("NASKAH:"):
                naskah = line_clean[7:].strip()
            elif line_clean.upper().startswith("PENCARIAN_VIDEO:"):
                keyword = line_clean[16:].strip()
                
        if not has_content: continue
                
        batch.append({
            "id": f"STOIC_{int(time.time())}_{len(batch)}",
            "judul": ref_judul,
            "quote": quote,
            "naskah": naskah,
            "keyword": keyword
        })
        
    print(f"✅ Berhasil meracik {len(batch)} Naskah Stoicisme!")
    return batch

# ==========================================
# 2. PEXELS API: MENGUNDUH VIDEO ESTETIK
# ==========================================
def download_pexels_video(keyword, output_filename):
    print(f"📥 Mencari video estetik Stoic di Pexels untuk: '{keyword}'...")
    headers = {"Authorization": PEXELS_API_KEY} if PEXELS_API_KEY else {}
    safe_query = urllib.parse.quote(keyword)
    url = f"https://api.pexels.com/videos/search?query={safe_query}&per_page=5&orientation=portrait"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            videos = data.get("videos", [])
            if videos:
                selected_video = random.choice(videos)
                video_files = selected_video.get("video_files", [])
                
                hd_files = [v for v in video_files if v.get("width") and v.get("width") <= 1080]
                download_url = hd_files[0]["link"] if hd_files else video_files[0]["link"]
                    
                print(f"   -> Mengunduh video...")
                dl_headers = {"User-Agent": "Mozilla/5.0"}
                v_data = requests.get(download_url, headers=dl_headers, stream=True, timeout=30)
                
                with open(output_filename, 'wb') as f:
                    for chunk in v_data.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if os.path.exists(output_filename) and os.path.getsize(output_filename) > 50000:
                    return output_filename
    except Exception as e:
        print(f"⚠️ Peringatan unduhan Pexels: {e}")

    # FALLBACK STOIC: Video patung atau alam yang tenang
    print("⚠️ Menggunakan video cadangan (calm cinematic)...")
    fallback_url = "https://api.pexels.com/videos/search?query=calm+nature+fog+vertical&orientation=portrait&per_page=1"
    try:
        fallback_res = requests.get(fallback_url, headers=headers, timeout=15).json()
        if "videos" in fallback_res and fallback_res["videos"]:
            download_url = fallback_res["videos"][0]["video_files"][0]["link"]
            v_data = requests.get(download_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            with open(output_filename, 'wb') as f:
                f.write(v_data.content)
            return output_filename
    except Exception as ex:
        raise Exception(f"Gagal total mengunduh video: {ex}")

# ==========================================
# 3. MENGHASILKAN GAMBAR TEKS (OVERLAY)
# ==========================================
def get_custom_font():
    font_filename = os.path.join(BASE_DIR, "Montserrat-Bold.ttf")
    if not os.path.exists(font_filename) or os.path.getsize(font_filename) < 10000:
        print("📥 Mengunduh Font Estetik...")
        url = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Bold.ttf"
        r = requests.get(url)
        with open(font_filename, 'wb') as f:
            f.write(r.content)
    return os.path.abspath(font_filename)

def create_text_overlay(item, output_path, img_size=(1080, 1920)):
    img = Image.new("RGBA", img_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_path = get_custom_font()
    font_title = ImageFont.truetype(font_path, 55)
    font_quote = ImageFont.truetype(font_path, 75)
    font_footer = ImageFont.truetype(font_path, 45)
    
    # 1. Judul Atas
    title_text = "🏛️ KUTIPAN STOIC 🏛️"
    try: w_title = draw.textlength(title_text, font=font_title)
    except: w_title = draw.textbbox((0, 0), title_text, font=font_title)[2]
    draw.text(((img_size[0] - w_title) // 2, 280), title_text, font=font_title, fill="#E0E0E0", stroke_width=2, stroke_fill="black")

    # 2. Quote Utama (Tengah Layar)
    lines_quote = textwrap.wrap(f'"{item["quote"]}"', width=24)
    y_quote = 800
    for line in lines_quote:
        try: w_quote = draw.textlength(line, font=font_quote)
        except: w_quote = draw.textbbox((0, 0), line, font=font_quote)[2]
        x_quote = (img_size[0] - w_quote) // 2
        draw.text((x_quote, y_quote), line, font=font_quote, fill="white", stroke_width=4, stroke_fill="black")
        y_quote += 95

    # 3. Footer Bawah
    footer_text = "Fokus pada apa yang bisa kamu kendalikan."
    try: w_foot = draw.textlength(footer_text, font=font_footer)
    except: w_foot = draw.textbbox((0, 0), footer_text, font=font_footer)[2]
    draw.text(((img_size[0] - w_foot) // 2, 1600), footer_text, font=font_footer, fill="#A9A9A9", stroke_width=3, stroke_fill="black")

    img.save(output_path)
    return output_path

# ==========================================
# 4. EDGE-TTS (SUARA NARATOR TENANG/BIJAK)
# ==========================================
async def _generate_audio_async(text, output_audio):
    # Menggunakan rate -5% agar suara terdengar lebih lambat, tenang, dan berwibawa
    communicate = edge_tts.Communicate(text, "id-ID-ArdiNeural", rate="-5%")
    await communicate.save(output_audio)

def generate_voiceover(text, output_audio):
    print("🎙️ Merekam suara narator Stoic...")
    asyncio.run(_generate_audio_async(text, output_audio))
    
    if not os.path.exists(output_audio) or os.path.getsize(output_audio) < 1000:
        raise Exception("File audio gagal dibuat atau kosong!")
    return output_audio

# ==========================================
# 5. EDITOR VIDEO (MOVIEPY)
# ==========================================
def render_shorts_video(video_bg_path, voice_path, item, output_video, index):
    print(f"[{index}] 🎬 Merakit video YouTube Shorts Stoicisme...")
    
    if not os.path.exists(video_bg_path) or os.path.getsize(video_bg_path) == 0:
        raise Exception("Video latar belakang hilang atau korup.")

    voice_clip = AudioFileClip(voice_path)
    target_duration = voice_clip.duration + 2.0  # Tambahan waktu jeda untuk peresapan makna
    
    video_clip = VideoFileClip(video_bg_path)
    
    if video_clip.duration < target_duration:
        n_loops = int(target_duration // video_clip.duration) + 1
        video_clip = concatenate_videoclips([video_clip] * n_loops)
        
    video_clip = video_clip.subclipped(0, target_duration)
    
    # Resize & Crop Vertikal 1080x1920
    w, h = video_clip.size
    target_ratio = 9 / 16
    current_ratio = w / h
    
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x_center = (w - new_w) / 2
        video_clip = video_clip.cropped(x1=x_center, y1=0, x2=x_center + new_w, y2=h)
    else:
        new_h = int(w / target_ratio)
        y_center = (h - new_h) / 2
        video_clip = video_clip.cropped(x1=0, y1=y_center, x2=w, y2=y_center + new_h)
        
    video_clip = video_clip.resized((1080, 1920))
    
    # Tambahkan filter gelap agar video terkesan lebih sinematik dan tulisan mudah dibaca
    dark_overlay = ColorClip(size=(1080, 1920), color=(0,0,0)).with_opacity(0.5).with_duration(target_duration)
    
    # Teks Overlay Gambar
    txt_img_path = os.path.join(BASE_DIR, f"overlay_temp_{index}.png")
    create_text_overlay(item, txt_img_path)
    txt_clip = ImageClip(txt_img_path).with_duration(target_duration)
    
    # Menggabungkan Visual dan Audio
    final_video = CompositeVideoClip([video_clip, dark_overlay, txt_clip], size=(1080, 1920)).with_audio(voice_clip)
    
    try:
        final_video.write_videofile(
            output_video, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac", 
            preset="ultrafast",
            threads=4
        )
    except Exception as e:
        print(f"⚠️ Terjadi error FFmpeg: {e}")
        
    # Pembersihan Memori
    try:
        final_video.close(); voice_clip.close(); video_clip.close()
        if os.path.exists(txt_img_path): os.remove(txt_img_path)
    except Exception: pass
    
    time.sleep(3) 
    
    file_size = os.path.getsize(output_video) if os.path.exists(output_video) else 0
    if file_size < 50000:
        if os.path.exists(output_video): os.remove(output_video)
        raise Exception(f"File {output_video} korup/0 byte!")
        
    return output_video

# ==========================================
# EKSEKUTOR UTAMA
# ==========================================
if __name__ == "__main__":
    JUMLAH_VIDEO = 3
    print(f"🏛️ MEMULAI BOT YOUTUBE SHORTS STOICISME ({JUMLAH_VIDEO} VIDEO) 🏛️\n")
    
    batch = generate_stoic_script(JUMLAH_VIDEO)
    
    for i, item in enumerate(batch, 1):
        try:
            print(f"--- MENGERJAKAN VIDEO {i}/{len(batch)}: {item['judul']} ---")
            
            video_bg = os.path.join(BASE_DIR, f"stoic_bg_{i}.mp4")
            audio_file = os.path.join(BASE_DIR, f"stoic_voice_{i}.mp3")
            output_file = os.path.join(BASE_DIR, f"youtube_shorts_stoic_{i}.mp4")
            
            download_pexels_video(item['keyword'], video_bg)
            generate_voiceover(item['naskah'], audio_file)
            render_shorts_video(video_bg, audio_file, item, output_file, i)
            
            print(f"✅ Video {i} Siap Diunggah ke YouTube: {output_file}\n")
            
            if i < len(batch):
                time.sleep(10)
                
        except Exception as e:
            print(f"❌ Kesalahan pada video {i}: {e}\n")
            
    print("🎉 SEMUA VIDEO SHORTS STOICISME SELESAI DIBUAT! 🎉")
