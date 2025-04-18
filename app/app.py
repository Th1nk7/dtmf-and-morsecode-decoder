from flask import Flask, request, abort, render_template, send_file, redirect, url_for
import re
import magic
import tempfile
import os
from pydub import AudioSegment
import numpy as np
from PIL import Image, ImageDraw
import io
import imageio
import subprocess

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Limit: 5MB

ALLOWED_MIME_TYPES = {'audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/x-wav', 'audio/x-mpeg', 'audio/x-ogg'}
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_audio(filepath):
    audio = AudioSegment.from_file(filepath).set_channels(1)
    samples = np.array(audio.get_array_of_samples())
    sample_rate = audio.frame_rate
    return samples, sample_rate, len(audio)  # return duration in ms

def detect_tone_regions(samples, sample_rate, threshold=60, window_ms=10):
    window_size = int(sample_rate * (window_ms / 1000))
    tone_map = []

    for i in range(0, len(samples), window_size):
        window = samples[i:i+window_size]
        amplitude = np.max(np.abs(window))
        is_tone = amplitude > threshold
        tone_map.append(is_tone)

    return tone_map, window_ms

def tone_map_to_segments(tone_map, window_ms):
    segments = []
    current = tone_map[0]
    duration = window_ms

    for val in tone_map[1:]:
        if val == current:
            duration += window_ms
        else:
            segments.append((current, duration))
            current = val
            duration = window_ms

    segments.append((current, duration))
    return segments  

def segments_to_morse(segments):
    dot_len = 100  # ms, adjust for your setup
    morse = ""
    for is_tone, duration in segments:
        if is_tone:
            if duration < dot_len * 1.5:
                morse += "."
            else:
                morse += "-"
        else:
            if duration < dot_len * 1.5:
                morse += ""  # intra-char gap
            elif duration < dot_len * 3.5:
                morse += " "  # char gap
            else:
                morse += " / "  # word gap
    return morse

def morse_to_text(morse):
    return ''.join(
        MORSE_TO_CHARS_MAPPING.get(char, ' ') for char in morse.split()
    )

MORSE_TO_CHARS_MAPPING = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z', '.----': '1', '..---': '2', '...--': '3',
    '....-': '4', '.....': '5', '-....': '6', '--...': '7', '---..': '8',
    '----.': '9', '-----': '0', '.-.-.-': '.', '--..--': ',', '..--..': '?',
    '· − − − − ·': '\'', '− · − · − −': '!', '− · · − ·': '/',
    '− · − − ·': '(', '− · − − · −': ')', '· − · · ·': '&',
    '− − − · · ·': ':', '− · − · − ·': ';', '− · · · −': '=',
    '· − · − ·': '+', '− · · · · −': '-', '· · − − · −': '_',
    '· − · · − ·': '"', '· · · − · · −': '$', '· − − · − ·': '@'
}

def decode_morse(filepath):
    samples, sr, duration_ms = load_audio(filepath)
    tone_map, step_ms = detect_tone_regions(samples, sr)
    segments = tone_map_to_segments(tone_map, step_ms)
    morse = segments_to_morse(segments)
    text = morse_to_text(morse)
    return tone_map, text, duration_ms

def generate_bar_video(tone_map, window_ms, output_path, bar_width=512, height=96, fps=60):
    frames = []
    total_frames = int(len(tone_map) * (1000 / window_ms)) // (1000 // fps)
    tone_cache = [255 for _ in range(bar_width)]

    for frame_idx in range(total_frames):
        img = Image.new('RGB', (bar_width, height), color='white')
        draw = ImageDraw.Draw(img)

        progress = frame_idx % bar_width
        tone_index = int(frame_idx * (1000 / fps) / window_ms)
        if tone_index < len(tone_map):
            tone_cache[progress] = 255 if not tone_map[tone_index] else 0

        for i in range(bar_width):
            draw.line([(i, 0), (i, height)], fill=(255, tone_cache[i], tone_cache[i]))

        draw.line([(progress, 0), (progress, height)], fill=(0, 0, 255))
        frames.append(np.array(img))

    imageio.mimsave(output_path, frames, fps=fps)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', err=None)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        abort(400, render_template('index.html', err='No file part'))
    file = request.files['file']
    if file.filename == '':
        abort(400, render_template('index.html', err='No selected file'))
    if not allowed_file(file.filename):
        abort(400, render_template('index.html', err='Invalid file extension'))

    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if mime not in ALLOWED_MIME_TYPES:
        abort(400, render_template('index.html', err=f'Invalid MIME type: {mime}'))

    tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=UPLOAD_DIR)
    file.save(tmp_audio.name)
    print(request.form)
    if request.form.get('type') == 'morse':
        tone_map, decoded_text, duration_ms = decode_morse(tmp_audio.name)

        tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=UPLOAD_DIR)
        tmp_bar = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=UPLOAD_DIR)
        generate_bar_video(tone_map, window_ms=10, output_path=tmp_bar.name)

        # Combine audio and video with ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "quiet",
            "-i", tmp_bar.name, "-i", tmp_audio.name,
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            "-shortest", tmp_video.name
        ])

    os.remove(tmp_audio.name)
    os.remove(tmp_bar.name)

    # Render the video path directly into the template
    return render_template('morse.html', video_path=f"uploads/{os.path.basename(tmp_video.name)}")

@app.route('/uploads/<path:filename>', methods=['GET'])
def send_video(filename):
    return send_file(f'./uploads/{filename}', as_attachment=False, mimetype='video/mp4')