from flask import Flask, request, abort, render_template, send_from_directory, redirect, url_for, jsonify
import re
import magic
import tempfile
import os
from pydub import AudioSegment
import numpy as np
from PIL import Image, ImageDraw
import imageio
import subprocess
import uuid
import shutil
from mutagen.mp4 import MP4
import json

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())  # Replace with a strong, unique key
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024  # Limit: 3MB

ALLOWED_MIME_TYPES = {'audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/x-wav', 'audio/x-mpeg', 'audio/x-ogg'}
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}

UPLOAD_DIR = "uploads"
shutil.rmtree(UPLOAD_DIR, ignore_errors=True)  # Clean up old uploads
os.makedirs(UPLOAD_DIR, exist_ok=True)

MORSE_TO_CHARS_MAPPING = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z', '.----': '1', '..---': '2', '...--': '3',
    '....-': '4', '.....': '5', '-....': '6', '--...': '7', '---..': '8',
    '----.': '9', '-----': '0', '.-.-.-': '.', '--..--': ',', '..--..': '?',
    '-.-.--': '!',  # Corrected Morse code for "!"
    '-..-.': '/', '-.--.': '(', '-.--.-': ')', '.-...': '&',
    '---...': ':', '-.-.-.': ';', '-...-': '=', '.-.-.': '+',
    '-....-': '-', '..--.-': '_', '.-..-.': '"', '...-..-': '$',
    '.--.-.': '@', '/': ' '  # Added '/' for word separator
}

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

def decode_morse(filepath):
    samples, sr, duration_ms = load_audio(filepath)
    tone_map, step_ms = detect_tone_regions(samples, sr)
    segments = tone_map_to_segments(tone_map, step_ms)
    morse = segments_to_morse(segments)
    text = morse_to_text(morse)
    return tone_map, segments, morse, text, duration_ms

def generate_morse_timestamps(segments, morse):
    """
    Generate timestamps for each decoded morse character
    
    Args:
        segments: List of (is_tone, duration) pairs
        morse: Morse code string with spaces and slashes
        
    Returns:
        List of [timestamp_ms, character] pairs
    """
    timestamps = []
    current_time = 0
    morse_parts = []
    current_symbol = ""
    
    # Process morse code to separate symbols by spaces and words by slashes
    for char in morse:
        if char == " ":
            if current_symbol:
                morse_parts.append(current_symbol)
                current_symbol = ""
            else:
                # Double space (word separator)
                morse_parts.append("/")
        else:
            current_symbol += char
    
    # Add the last symbol if there is one
    if current_symbol:
        morse_parts.append(current_symbol)
    
    # Find the timestamp for each morse part
    segment_index = 0
    time_acc = 0
    
    for morse_part in morse_parts:
        if morse_part == "/":
            # Word separator
            timestamps.append([time_acc, " "])
            continue
            
        # Find when this symbol ends
        symbol_duration = 0
        symbol_segments = []
        
        # Calculate how many segments this symbol uses
        for char in morse_part:
            if char == ".":
                symbol_segments.append(1)  # Dot
            elif char == "-":
                symbol_segments.append(2)  # Dash
        
        # Skip segments until we find the end of this symbol
        while segment_index < len(segments) and len(symbol_segments) > 0:
            is_tone, duration = segments[segment_index]
            time_acc += duration
            
            if is_tone:
                # Tone segment corresponds to a dot or dash
                if symbol_segments[0] == 1 and duration < 150:  # Dot
                    symbol_segments.pop(0)
                elif symbol_segments[0] == 2 and duration >= 150:  # Dash
                    symbol_segments.pop(0)
            
            segment_index += 1
            
            # Move past the silence between parts of the same character
            if len(symbol_segments) > 0 and segment_index < len(segments):
                is_next_tone, next_duration = segments[segment_index]
                if not is_next_tone and next_duration < 150:
                    time_acc += next_duration
                    segment_index += 1
        
        # Add the character at the accumulated time
        char = morse_to_text(morse_part)
        timestamps.append([time_acc, char])
        
        # Skip the silence between characters
        if segment_index < len(segments):
            is_tone, duration = segments[segment_index]
            if not is_tone and duration >= 150 and duration < 350:
                time_acc += duration
                segment_index += 1
    
    return timestamps

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

def removeOldFiles():
    # Check and delete the oldest file if there are more than 10 files
    files = [os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR)]
    if len(files) > 10:
        oldest_file = min(files, key=os.path.getctime)
        os.remove(oldest_file)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index', err='No file part'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index', err='No selected file'))

    if not allowed_file(file.filename):
        return redirect(url_for('index', err='File type not allowed'))

    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if mime not in ALLOWED_MIME_TYPES:
        return redirect(url_for('index', err='Invalid file type'))

    tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=UPLOAD_DIR)
    file.save(tmp_audio.name)

    if request.form.get('type') == 'morse':
        tone_map, segments, morse, decoded_text, duration_ms = decode_morse(tmp_audio.name)
        
        # Use the existing functions to generate timestamps
        timestamps = generate_morse_timestamps(segments, morse)

        tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=UPLOAD_DIR)
        tmp_bar = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=UPLOAD_DIR)
        generate_bar_video(tone_map, window_ms=10, output_path=tmp_bar.name)

        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "quiet",
            "-i", tmp_bar.name, "-i", tmp_audio.name,
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            "-shortest", tmp_video.name
        ])

        video = MP4(tmp_video.name)
        video["----:com.apple.iTunes:timestampArray"] = [json.dumps(timestamps).encode("utf-8")]
        video.save()

    os.remove(tmp_audio.name)
    os.remove(tmp_bar.name)
    removeOldFiles()

    return jsonify({'redirect': url_for('morse', v_id=os.path.basename(tmp_video.name).split('.')[0])})

@app.route('/morse', methods=['GET'])
def morse():
    video_id = request.args.get('v_id')
    if not video_id:
        return redirect(url_for('index', err='Missing video ID'))

    video_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
    if not os.path.exists(video_path):
        return redirect(url_for('index', err='Video not found'))

    return render_template('morse.html', video_path=f"uploads/{video_id}.mp4", timestamps=MP4(video_path).tags.get('----:com.apple.iTunes:timestampArray')[0].decode("utf-8"))

@app.route('/uploads/<path:filename>', methods=['GET'])
def send_video(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False, mimetype='video/mp4')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')