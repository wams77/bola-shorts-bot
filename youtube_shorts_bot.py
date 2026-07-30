import os
import time
import random
import requests
import urllib.parse
import asyncio
import edge_tts
import google.generativeai as genai
from moviepy import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ColorClip, ImageClip, VideoFileClip, concatenate_audioclips, concatenate_videoclips
from moviepy.audio.fx import MultiplyVolume

BASE_DIR = os.path.abspath(os.getcwd())

# Konfigurasi Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# PEXELS API KEY (Untuk mengambil video latar belakang sepak bola gratis)
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# ==========================================
# 1. GEMINI AI: GENERATOR NASKAH SEPAK BOLA
# ==========================================
def generate_football_script(num_videos=3):
    print(f"⚽ Meminta Gemini AI meracik {num_videos} naskah YouTube Shorts Sepak Bola...")
    
    prompt = f"""
    Bertindaklah sebagai konten kreator YouTube Shorts sepak bola profesional yang antusias dan paham statistik bola.
    Buatlah {num_videos} naskah video pendek (durasi 30-40 detik) tentang fakta menarik, sejarah, atau rivalitas epik di dunia sepak bola.
    Gunakan pemisah '---' antar naskah. Format persis seperti ini:
    
    JUDUL: [Judul video yang clickbait dan menarik, max 60 karakter]
    NASKAH: [Naskah suara yang seru, dinamis, dan padat. Tanpa jeda waktu, langsung isi naskah narasi]
    PENCARIAN_VIDEO: [Kata kunci bahasa Inggris untuk mencari video Pexels, misal: "football skills match stadium", "soccer player celebration", atau "stadium crowd cheering"]
    """
    
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    raw_text = ""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text
            break 
        except Exception as e:
            print(f"⚠️ Error Gemini (Percobaan {attempt+1}): {e}")
            time.sleep(65)
    else:
        raise Exception("❌ Gagal terhubung ke Gemini AI.")

    batch = []
    for i, chunk in enumerate(raw_text.split("---")):
        if i >= num_videos: break
        lines = [line.strip() for line in chunk.strip().split("\n") if line.strip()]
        if not lines: continue
        
        judul, naskah, keyword = "Fakta Unik Sepak Bola Dunia", "Tahukah kamu fakta menarik tentang sepak bola?", "football match stadium"
        for line in lines:
            if line.startswith("JUDUL:"): judul = line.replace("JUDUL:", "").strip()
            if line.startswith("NASKAH:"): naskah = line.replace("NASKAH:", "").strip()
            if line.startswith("PENCARIAN_VIDEO:"): keyword = line.replace("PENCARIAN_VIDEO:", "").strip()
                
        batch.append({
            "id": f"FB_{int(time.time())}_{i}",
            "judul": judul,
            "naskah": naskah,
            "keyword": keyword
        })
    print(f"✅ Berhasil meracik {len(batch)} Naskah Sepak Bola!")
    return batch

# ==========================================
# 2. PEXELS API: MENGUNDUH VIDEO SEPAK BOLA
# ==========================================
def download_pexels_video(keyword, output_filename):
    print(f"📥 Mencari video latar belakang dengan kata kunci: '{keyword}'...")
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(keyword)}&per_page=5&orientation=portrait"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        videos = data.get("videos", [])
        if videos:
            # Pilih video acak dari hasil pencarian
            selected_video = random.choice(videos)
            video_files = selected_video.get("video_files", [])
            
            # Cari kualitas HD atau SD vertikal
            hd_files = [v for v in video_files if v.get("width") and v.get("width") <= 1080]
            if hd_files:
                download_url = hd_files[0]["link"]
            else:
                download_url = video_files[0]["link"]
                
            print(f"   -> Mengunduh video Pexels...")
            v_data = requests.get(download_url)
            with open(output_filename, 'wb') as f:
                f.write(v_data.content)
            return output_filename
            
    raise Exception("Gagal mengunduh video dari Pexels API.")

# ==========================================
# 3. EDGE-TTS NATIVE (SUARA NARATOR BERSEMANGAT)
# ==========================================
async def _generate_audio_async(text, output_audio):
    # Menggunakan suara Indonesia 'ArdiNeural' dengan kecepatan +5% agar bersemangat
    communicate = edge_tts.Communicate(text, "id-ID-ArdiNeural", rate="+5%")
    await communicate.save(output_audio)

def generate_voiceover(text, output_audio):
    print("🎙️ Merekam suara narator sepak bola...")
    asyncio.run(_generate_audio_async(text, output_audio))
    return output_audio

# ==========================================
# 4. EDITOR VIDEO (MOVIEPY)
# ==========================================
def render_shorts_video(video_bg_path, voice_path, output_video):
    print("🎬 Merakit video YouTube Shorts...")
    voice_clip = AudioFileClip(voice_path)
    target_duration = voice_clip.duration + 1.5
    
    # Muat video latar belakang
    video_clip = VideoFileClip(video_bg_path)
    
    # Loop video jika durasinya lebih pendek dari suara narator
    if video_clip.duration < target_duration:
        n_loops = int(target_duration // video_clip.duration) + 1
        video_clip = concatenate_videoclips([video_clip] * n_loops)
        
    video_clip = video_clip.subclipped(0, target_duration)
    
    # Resize & crop ke format vertikal Shorts (1080x1920)
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
    
    # Tambahkan background musik (opsional, jika ada file bgm.mp3)
    final_audio = voice_clip
    bgm_file = os.path.join(BASE_DIR, "bgm.mp3")
    if os.path.exists(bgm_file):
        bgm_clip = AudioFileClip(bgm_file).with_effects([MultiplyVolume(0.1)])
        if bgm_clip.duration < target_duration:
            n_loops = int(target_duration // bgm_clip.duration) + 1
            bgm_clip = concatenate_audioclips([bgm_clip] * n_loops)
        bgm_clip = bgm_clip.subclipped(0, target_duration)
        final_audio = CompositeAudioClip([bgm_clip, voice_clip.with_start(0)])
        
    final_video = video_clip.with_audio(final_audio)
    final_video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    try:
        final_video.close(); voice_clip.close(); video_clip.close()
    except: pass
    
    return output_video

# ==========================================
# EKSEKUTOR UTAMA
# ==========================================
if __name__ == "__main__":
    JUMLAH_VIDEO = 3
    print(f"⚽ MEMULAI BOT YOUTUBE SHORTS SEPAK BOLA ({JUMLAH_VIDEO} VIDEO) ⚽\n")
    
    batch = generate_football_script(JUMLAH_VIDEO)
    
    for i, item in enumerate(batch, 1):
        try:
            print(f"--- MENGERJAKAN VIDEO {i} DARI {len(batch)}: {item['judul']} ---")
            
            video_bg = os.path.join(BASE_DIR, f"football_bg_{i}.mp4")
            audio_file = os.path.join(BASE_DIR, f"football_voice_{i}.mp3")
            output_file = os.path.join(BASE_DIR, f"youtube_shorts_{i}.mp4")
            
            download_pexels_video(item['keyword'], video_bg)
            generate_voiceover(item['naskah'], audio_file)
            render_shorts_video(video_bg, audio_file, output_file)
            
            print(f"✅ Video {i} Berhasil Dirender: {output_file}\n")
            
            if i < len(batch):
                time.sleep(10)
                
        except Exception as e:
            print(f"❌ Kesalahan pada video {i}: {e}\n")
            
    print("🎉 SEMUA VIDEO SHORTS SEPAK BOLA SELESAI DIBUAT! 🎉")
