#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Downloader - تطبيق تحميل فيديوهات يوتيوب

المطور: عبد الحليم
Instagram: https://www.instagram.com/abdelhalim.officiel/
Telegram: https://t.me/CiH99x

تطبيق مجاني لتحميل الفيديوهات والصوتيات من يوتيوب
"""

import customtkinter as ctk
import subprocess
import os
import re
import glob
import threading
import yt_dlp
import shutil
import webbrowser
from PIL import Image
import requests
import json
from packaging import version

# معلومات الإصدار
CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "Abdelhalimx5/youtube-downloader"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def extract_video_url(playlist_url):
    match = re.search(r"v=([a-zA-Z0-9_-]+)", playlist_url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return playlist_url

def convert_video(input_file, target_format):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(os.path.dirname(input_file), f"{base_name}.{target_format}")
    if target_format == "mp4":
        command = [ "ffmpeg", "-i", input_file, "-vcodec", "libx264", "-acodec", "aac", "-b:v", "1000k", "-b:a", "128k", "-preset", "fast", "-crf", "23", "-movflags", "+faststart", output_file ]
    elif target_format == "mkv":
        command = [ "ffmpeg", "-i", input_file, "-c:v", "libx264", "-c:a", "aac", "-b:v", "1000k", "-b:a", "128k", output_file ]
    else:
        return None
    subprocess.run(command)
    return output_file

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            if 'total_bytes' in d:
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d:
                progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                return
            app.after(100, lambda: progress_bar.set(progress / 100))
            app.after(100, lambda: status_label.configure(text=f"⏳ جاري التحميل... {progress:.1f}%"))
        except:
            pass
    elif d['status'] == 'finished':
        app.after(100, lambda: progress_bar.set(1))
        app.after(100, lambda: status_label.configure(text="✅ تم التحميل بنجاح!"))

def download_media():
    url = url_entry.get().strip()
    file_type = file_type_option.get()
    quality = quality_option.get().lower()
    is_playlist = playlist_var.get()
    if not url:
        status_label.configure(text="❌ يرجى إدخال رابط YouTube", text_color="red")
        return
    if "list=" in url and not is_playlist:
        url = extract_video_url(url)
    status_label.configure(text="⏳ جاري التحميل...", text_color="yellow")
    download_btn.configure(state="disabled")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    audio_quality_map = {"low": "50K", "medium": "128K", "high": "192K"}
    video_quality_map = {"low": "360", "medium": "720", "high": "1080"}
    filename = os.path.join(output_dir, "%(title)s.%(ext)s")
    ydl_opts = { 'progress_hooks': [progress_hook], 'outtmpl': filename }
    if file_type == "mp3":
        ydl_opts.update({ 'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': audio_quality_map.get(quality, '128'),}],})
    elif file_type == "mp4":
        ydl_opts.update({ 'format': f'bv*[height<={video_quality_map.get(quality, "720")}]+ba/best', 'merge_output_format': 'mp4' })
    if not is_playlist:
        ydl_opts['noplaylist'] = True
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        app.after(100, lambda: status_label.configure(text=f"❌ خطأ في التحميل: {str(e)}", text_color="red"))
        app.after(100, lambda: download_btn.configure(state="normal"))
        return
    if file_type == "mp4":
        downloaded_files = sorted(glob.glob(os.path.join(output_dir, "*.mp4")), key=os.path.getmtime, reverse=True)
        if downloaded_files:
            input_file = downloaded_files[0]
            if convert_var.get():
                target_format = convert_format_option.get()
                status_label.configure(text="⏳ جاري التحويل...", text_color="yellow")
                output_file = convert_video(input_file, target_format)
                if output_file:
                    status_label.configure(text=f"✅ تم التحويل إلى {target_format}", text_color="green")
                    download_btn.configure(state="normal")
                    return
        else:
            status_label.configure(text="❌ لم يتم العثور على ملف MP4 للتحويل", text_color="red")
            download_btn.configure(state="normal")
            return
    status_label.configure(text="✅ تم التحميل بنجاح!", text_color="green")
    download_btn.configure(state="normal")

def threaded_download():
    threading.Thread(target=download_media, daemon=True).start()

def open_output_folder():
    output_dir = os.path.abspath("output")
    os.startfile(output_dir)

def check_ffmpeg():
    if shutil.which("ffmpeg"):
        ffmpeg_status_label.configure(text="✅ FFmpeg: مثبت", text_color="green")
    else:
        ffmpeg_status_label.configure(text="⚠️ FFmpeg: غير مثبت", text_color="orange")

def open_instagram():
    webbrowser.open("https://www.instagram.com/abdelhalim.officiel/")

def open_telegram():
    webbrowser.open("https://t.me/CiH99x")

def check_for_updates():
    """فحص وجود تحديثات جديدة"""
    try:
        response = requests.get(GITHUB_API_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data["tag_name"].replace("v", "")

            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                show_update_notification(latest_version, data.get("body", ""))
    except Exception as e:
        print(f"خطأ في فحص التحديثات: {e}")

def show_update_notification(new_version, release_notes):
    """إظهار إشعار التحديث"""
    update_window = ctk.CTkToplevel(app)
    update_window.title("🆕 تحديث متاح")
    update_window.geometry("500x350")
    update_window.resizable(False, False)

    # توسيط النافذة
    update_window.transient(app)
    update_window.grab_set()

    # محتوى الإشعار
    main_frame = ctk.CTkFrame(update_window, corner_radius=15)
    main_frame.pack(pady=20, padx=20, fill="both", expand=True)

    title_label = ctk.CTkLabel(main_frame, text="🆕 تحديث جديد متاح!",
                              font=("Calibri", 18, "bold"), text_color="#4CAF50")
    title_label.pack(pady=(20, 10))

    version_label = ctk.CTkLabel(main_frame,
                                text=f"الإصدار الحالي: {CURRENT_VERSION}\nالإصدار الجديد: {new_version}",
                                font=("Calibri", 14))
    version_label.pack(pady=10)

    # ملاحظات التحديث
    if release_notes:
        notes_frame = ctk.CTkFrame(main_frame)
        notes_frame.pack(pady=10, padx=20, fill="both", expand=True)

        notes_label = ctk.CTkLabel(notes_frame, text="ما الجديد:",
                                  font=("Calibri", 12, "bold"))
        notes_label.pack(pady=(10, 5))

        notes_text = ctk.CTkTextbox(notes_frame, height=80, font=("Calibri", 10))
        notes_text.pack(pady=(0, 10), padx=10, fill="both", expand=True)
        notes_text.insert("1.0", release_notes[:200] + "..." if len(release_notes) > 200 else release_notes)
        notes_text.configure(state="disabled")

    # أزرار الإجراء
    buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    buttons_frame.pack(pady=20)

    download_btn = ctk.CTkButton(buttons_frame, text="💾 تحميل التحديث",
                                command=lambda: [webbrowser.open(GITHUB_RELEASES_URL), update_window.destroy()],
                                width=150, height=40, font=("Calibri", 12, "bold"),
                                fg_color="#4CAF50", hover_color="#45a049")
    download_btn.pack(side="left", padx=10)

    later_btn = ctk.CTkButton(buttons_frame, text="⏰ لاحقاً",
                             command=update_window.destroy,
                             width=100, height=40, font=("Calibri", 12, "bold"),
                             fg_color="gray", hover_color="#666666")
    later_btn.pack(side="left", padx=10)

if __name__ == "__main__":
    app = ctk.CTk()

    # Center the window on screen
    window_width = 600
    window_height = 650
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    app.geometry(f"{window_width}x{window_height}+{x}+{y}")
    app.title(f"YouTube Downloader v{CURRENT_VERSION} ")
    app.resizable(False, False)

    font = ("Calibri", 14, "bold")
    title_font = ("Calibri", 18, "bold")

    main_frame = ctk.CTkFrame(app, corner_radius=15)
    main_frame.pack(pady=20, padx=20, fill="both", expand=True)

    title_label = ctk.CTkLabel(main_frame, text="🎬 YouTube Downloader", font=title_font)
    title_label.pack(pady=(20, 30))
    ctk.CTkLabel(main_frame, text="رابط YouTube:", font=font).pack(pady=(0, 5))
    url_entry = ctk.CTkEntry(main_frame, width=500, height=35, font=font, placeholder_text="أدخل رابط الفيديو أو قائمة التشغيل هنا...")
    url_entry.pack(pady=(0, 20))
    options_frame1 = ctk.CTkFrame(main_frame, fg_color="transparent")
    options_frame1.pack(pady=10, fill="x", padx=20)
    ctk.CTkLabel(options_frame1, text="نوع الملف:", font=font).pack(side="left", padx=(0, 10))
    file_type_option = ctk.CTkOptionMenu(options_frame1, values=["mp4", "mp3"], width=120, font=font)
    file_type_option.pack(side="left", padx=(0, 30))
    file_type_option.set("mp4")
    ctk.CTkLabel(options_frame1, text="الجودة:", font=font).pack(side="left", padx=(0, 10))
    quality_option = ctk.CTkOptionMenu(options_frame1, values=["Low", "Medium", "High"], width=120, font=font)
    quality_option.pack(side="left")
    quality_option.set("Medium")
    options_frame2 = ctk.CTkFrame(main_frame, fg_color="transparent")
    options_frame2.pack(pady=20, fill="x", padx=20)
    playlist_var = ctk.BooleanVar(value=False)
    playlist_checkbox = ctk.CTkCheckBox(options_frame2, text="تحميل قائمة التشغيل كاملة", variable=playlist_var, font=font)
    playlist_checkbox.pack(side="left", padx=(0, 30))
    convert_var = ctk.BooleanVar(value=False)
    convert_checkbox = ctk.CTkCheckBox(options_frame2, text="تحويل بعد التحميل", variable=convert_var, font=font)
    convert_checkbox.pack(side="left")
    convert_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    convert_frame.pack(pady=10, fill="x", padx=20)
    ctk.CTkLabel(convert_frame, text="صيغة التحويل:", font=font).pack(side="left", padx=(0, 10))
    convert_format_option = ctk.CTkOptionMenu(convert_frame, values=["mp4", "mkv"], width=120, font=font)
    convert_format_option.pack(side="left")
    convert_format_option.set("mkv")
    buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    buttons_frame.pack(pady=30)
    download_btn = ctk.CTkButton(buttons_frame, text="⬇️ بدء التحميل", command=threaded_download, width=200, height=45, font=("Calibri", 16, "bold"))
    download_btn.pack(side="left", padx=10)
    open_folder_btn = ctk.CTkButton(buttons_frame, text="📂 فتح المجلد", command=open_output_folder, width=200, height=45, font=("Calibri", 16, "bold"))
    open_folder_btn.pack(side="left", padx=10)
    progress_bar = ctk.CTkProgressBar(main_frame, width=400)
    progress_bar.pack(pady=(10, 5))
    progress_bar.set(0)
    status_label = ctk.CTkLabel(main_frame, text="جاهز للتحميل", font=font)
    status_label.pack(pady=(0, 20))

    # Social media buttons
    social_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    social_frame.pack(pady=(15, 10))

    # Load and resize icons
    try:
        instagram_image = ctk.CTkImage(Image.open("instagram_icon.png"), size=(24, 24))
        telegram_image = ctk.CTkImage(Image.open("telegram_icon.png"), size=(24, 24))

        instagram_btn = ctk.CTkButton(social_frame, text="Instagram", image=instagram_image,
                                     command=open_instagram, width=140, height=40,
                                     font=("Calibri", 12, "bold"), fg_color="#E4405F",
                                     hover_color="#C13584", corner_radius=20,
                                     compound="left", anchor="center")
        instagram_btn.pack(side="left", padx=15)

        telegram_btn = ctk.CTkButton(social_frame, text="Telegram", image=telegram_image,
                                    command=open_telegram, width=140, height=40,
                                    font=("Calibri", 12, "bold"), fg_color="#0088CC",
                                    hover_color="#006699", corner_radius=20,
                                    compound="left", anchor="center")
        telegram_btn.pack(side="left", padx=15)

    except Exception as e:
        # Fallback to text-only buttons if icons fail to load
        instagram_btn = ctk.CTkButton(social_frame, text="Instagram", command=open_instagram,
                                     width=140, height=40, font=("Calibri", 12, "bold"),
                                     fg_color="#E4405F", hover_color="#C13584",
                                     corner_radius=20)
        instagram_btn.pack(side="left", padx=15)

        telegram_btn = ctk.CTkButton(social_frame, text="Telegram", command=open_telegram,
                                    width=140, height=40, font=("Calibri", 12, "bold"),
                                    fg_color="#0088CC", hover_color="#006699",
                                    corner_radius=20)
        telegram_btn.pack(side="left", padx=15)

    # FFmpeg status directly under social media buttons
    ffmpeg_status_label = ctk.CTkLabel(main_frame, text="", font=("Calibri", 11))
    ffmpeg_status_label.pack(pady=(5, 10))

    check_ffmpeg()

    # فحص التحديثات في خيط منفصل
    threading.Thread(target=check_for_updates, daemon=True).start()

    app.mainloop()