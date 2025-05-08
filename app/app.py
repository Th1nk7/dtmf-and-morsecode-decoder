import os
import re
import shutil
import uuid
import magic
import tempfile
import subprocess
import numpy as np
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, abort
from pydub import AudioSegment
from PIL import Image, ImageDraw
import imageio

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}
ALLOWED_MIME_TYPES = {'audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/x-wav', 'audio/x-mpeg', 'audio/x-ogg'}

# Reset upload directory
if os.path.exists(UPLOAD_DIR):
    shutil.rmtree(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def manage_upload_dir():
    files = sorted([os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR)], key=os.path.getctime)
    while len(files) > 10:
        os.remove(files.pop(0))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)

def load_audio(filepath):
    audio = AudioSegment.from_file(filepath).set_channels(1)
    samples = np.array(audio.get_array_of_samples())
    return samples, audio.frame_rate, len(audio)  # ms

def detect_tone_regions(samples, sr, threshold=60, window_ms=10):
    ws = int(sr * (window_ms / 1000))
    tone_map = [np.max(np.abs(samples[i:i+ws])) > threshold for i in range(0, len(samples), ws)]
    return tone_map, window_ms

def tone_map_to_segments(tone_map, window_ms):
    segments = []
    current = tone_map[0]
    dur = window_ms
    for val in tone_map[1:]:
        if val == current:
            dur += window_ms
        else:
            segments.append((current, dur))
            current, dur = val, window_ms
    segments.append((current, dur))
    return segments

def segments_to_morse(segments):
    dot_len = 100
    morse = ""
    for tone, dur in segments:
        if tone:
            morse += '.' if dur < dot_len * 1.5 else '-'
        else:
            morse += '' if dur < dot_len * 1.5 else (' ' if dur < dot_len * 3.5 else ' / ')
    return morse

MORSE_TO_CHARS = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z', '.----': '1', '..---': '2', '...--': '3',
    '....-': '4', '.....': '5', '-....': '6', '--...': '7', '---..': '8',
    '----.': '9', '-----': '0'
}

def morse_to_text(morse):
    return ''.join(MORSE_TO_CHARS.get(c, ' ') for c in morse.split())

def decode_morse(path):
    samples, sr, dur = load_audio(path)
    if dur > 30000:
        raise ValueError("Audio too long (max 30 seconds)")
    tone_map, step = detect_tone_regions(samples, sr)
    segments = tone_map_to_segments(tone_map, step)
    return tone_map, morse_to_text(segments_to_morse(segments)), dur

def generate_bar_video(tone_map, window_ms, out, width=512, height=96, fps=60):
    frames = []
    tone_cache = [255] * width
    total_frames = len(tone_map)
    for i in range(total_frames):
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        progress = i % width
        tone_cache[progress] = 0 if tone_map[i] else 255
        for x in range(width):
            draw.line([(x, 0), (x, height)], fill=(255, tone_cache[x], tone_cache[x]))
        draw.line([(progress, 0), (progress, height)], fill=(0, 0, 255))
        frames.append(np.array(img))
    imageio.mimsave(out, frames, fps=fps)

@app.route('/')
def index():
    err = request.args.get('err')
    return render_template('index.html', err=err)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index', err='No file provided'))

    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return redirect(url_for('index', err='Invalid file type'))

    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if mime not in ALLOWED_MIME_TYPES:
        return redirect(url_for('index', err='Bad MIME: ' + mime))

    unique_id = uuid.uuid4().hex[:16]
    tmp_path = os.path.join(UPLOAD_DIR, f"{unique_id}.wav")
    file.save(tmp_path)

    try:
        tone_map, decoded, dur = decode_morse(tmp_path)
        bar_path = os.path.join(UPLOAD_DIR, f"{unique_id}_bar.mp4")
        final_path = os.path.join(UPLOAD_DIR, f"{unique_id}.mp4")
        generate_bar_video(tone_map, 10, bar_path)

        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "quiet",
            "-i", bar_path, "-i", tmp_path,
            "-c:v", "libx264", "-c:a", "aac",
            "-strict", "experimental", "-shortest", final_path
        ])

        os.remove(tmp_path)
        os.remove(bar_path)
        manage_upload_dir()
        return redirect(url_for('morse', id=unique_id))

    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return redirect(url_for('index', err=str(e)))

@app.route('/morse')
def morse():
    video_id = request.args.get('id')
    if not video_id:
        return redirect(url_for('index', err='Missing ID'))

    video_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
    if not os.path.isfile(video_path):
        return redirect(url_for('index', err='Invalid or expired ID'))

    return render_template('morse.html', video_path=f"uploads/{video_id}.mp4")

@app.route('/uploads/<filename>')
def serve_upload(filename):
    safe_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(safe_path):
        abort(404, description="File not found")
    return send_from_directory(UPLOAD_DIR, filename, mimetype='video/mp4', as_attachment=False)
