from flask import Flask, request, abort, render_template_string
import magic
import tempfile
import os
from pydub import AudioSegment
import numpy as np


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
    return samples, sample_rate

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
    '.-': 'A',
    '-...': 'B',
    '-.-.': 'C',
    '-..': 'D',
    '.': 'E',
    '..-.': 'F',
    '--.': 'G',
    '....': 'H',
    '..': 'I',
    '.---': 'J',
    '-.-': 'K',
    '.-..': 'L',
    '--': 'M',
    '-.': 'N',
    '---': 'O',
    '.--.': 'P',
    '--.-': 'Q',
    '.-.': 'R',
    '...': 'S',
    '-': 'T',
    '..-': 'U',
    '...-': 'V',
    '.--': 'W',
    '-..-': 'X',
    '-.--': 'Y',
    '--..': 'Z',
    '.----': '1',
    '..---': '2',
    '...--': '3',
    '....-': '4',
    '.....': '5',
    '-....': '6',
    '--...': '7',
    '---..': '8',
    '----.': '9',
    '-----': '0',
    '.-.-.-': '.',
    '--..--': ',',
    '..--..': '?',
    '· − − − − ·': '\'',
    '− · − · − −': '!',
    '− · · − ·': '/',
    '− · − − ·': '(',
    '− · − − · −': ')',
    '· − · · ·': '&',
    '− − − · · ·': ':',
    '− · − · − ·': ';',
    '− · · · −': '=',
    '· − · − ·': '+',
    '− · · · · −': '-',
    '· · − − · −': '_',
    '· − · · − ·': '"',
    '· · · − · · −': '$',
    '· − − · − ·': '@',
}

def decode_morse(filepath):
    samples, sr = load_audio(filepath)
    tone_map, step_ms = detect_tone_regions(samples, sr)
    segments = tone_map_to_segments(tone_map, step_ms)
    morse = segments_to_morse(segments)
    text = morse_to_text(morse)
    os.remove(filepath)  # Clean up the temporary file
    return text

@app.route('/', methods=['GET'])
def index():
    return render_template_string("""
    <!doctype html>
    <title>Upload an audio file</title>
    <h1>Upload a sound file (wav, mp3, ogg)</h1>
    <form method=post enctype=multipart/form-data action="/upload">
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        abort(400, 'No file part')
    file = request.files['file']

    if file.filename == '':
        abort(400, 'No selected file')
    if not allowed_file(file.filename):
        abort(400, 'Invalid file extension')

    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if mime not in ALLOWED_MIME_TYPES:
        abort(400, f'Invalid MIME type: {mime}')

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=UPLOAD_DIR)
    file.save(tmp.name)

    return decode_morse(tmp.name)
