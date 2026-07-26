import os
from gtts import gTTS
import yt_dlp
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, VideoFileClip

def download_background_video(youtube_url, output_filename="bg_video.mp4"):
    print("[1/4] Mengunduh video latar belakang dari YouTube...")
    ydl_opts = {
        'format': 'bestvideo[height<=1920][ext=mp4]+bestaudio[ext=m4a]/best[height<=1920][ext=mp4]',
        'outtmpl': output_filename,
        'noplaylist': True,
        'max_filesize': 50000000,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
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
    # Menggunakan link video stok/latar belakang sepak bola yang aktif
    YOUTUBE_BG_URL = "https://www.youtube.com/watch?v=2Vv-BfVoq4g"
    script = "Tahukah kamu? Real Madrid dijuluki sebagai rajanya Liga Champions karena telah mengoleksi lima belas trofi bergengsi di Eropa. Luar biasa!"
    
    bg_file = download_background_video(YOUTUBE_BG_URL)
    audio_file = create_voiceover(script)
    generate_video(bg_file, audio_file)
    print("Selesai! File video 'output.mp4' siap.")
