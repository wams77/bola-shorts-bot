import os
import requests
from gtts import gTTS
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, VideoFileClip

def download_background_video(video_url, output_filename="bg_video.mp4"):
    print("[1/4] Mengunduh video latar belakang stok...")
    # Menambahkan User-Agent agar tidak diblokir (Error 403 Forbidden)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(video_url, headers=headers, stream=True)
    
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("[1/4] Unduhan video berhasil.")
    else:
        raise Exception(f"Gagal mengunduh video, status code: {response.status_code}")
    return output_filename

def create_voiceover(text, output_audio="voiceover.mp3"):
    print("[2/4] Membuat suara (Voiceover)...")
    tts = gTTS(text=text, lang="id", slow=False)
    tts.save(output_audio)
    return output_audio

def generate_video(bg_video_path, audio_path, output_video="output.mp4"):
    print("[3/4] Merakit video Shorts dengan background...")
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    bg_video = VideoFileClip(bg_video_path).subclipped(0, duration)
    bg_video = bg_video.resized(height=1920)
    
    txt_content = "BOLA SHORTS\n\nTahukah Kamu?\nReal Madrid adalah rajanya Liga Champions dengan 15 trofi!"
    
    txt_clip = TextClip(
        text=txt_content, 
        font_size=55, 
        color='white', 
        size=(900, None),
        method='caption',
        text_align='center'
    ).with_duration(duration).with_position('center')
    
    video = CompositeVideoClip([bg_video, txt_clip]).with_audio(audio)
    video.write_videofile(
        output_video, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        preset="ultrafast"
    )
    print(f"[4/4] Video berhasil dibuat: {output_video}")

if __name__ == "__main__":
    BG_VIDEO_URL = "https://assets.mixkit.co/videos/preview/mixkit-feet-of-a-soccer-player-controlling-a-ball-41584-large.mp4"
    script = "Tahukah kamu? Real Madrid dijuluki sebagai rajanya Liga Champions karena telah mengoleksi lima belas trofi bergengsi di Eropa. Luar biasa!"
    
    bg_file = download_background_video(BG_VIDEO_URL)
    audio_file = create_voiceover(script)
    generate_video(bg_file, audio_file)
    print("Selesai! File video 'output.mp4' siap.")
