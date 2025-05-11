from flask import Flask, request, abort, render_template, send_from_directory, redirect, url_for, jsonify # Importer flask og andre nødvendige biblioteker som hører under flask
import magic # Importer python-magic for at bestemme filernes MIME-type
import tempfile # Importer tempfile for at oprette midlertidige filer med tilfældige navne
import os # Importer os for at håndtere filsystemet
from pydub import AudioSegment # Importer pydub for at håndtere lydfiler
import numpy as np # Importer numpy for at håndtere lydfilernes samples
from PIL import Image, ImageDraw # Importer PIL for at oprette billeder til video
import imageio # Importer imageio for at gemme video
import subprocess # Importer subprocess for at køre ffmpeg
import uuid # Importer uuid for at generere unikke ID'er (bruges kun til at generere en hemmelig nøgle her)
import shutil # Importer shutil for at håndtere filsystemet (specifikt til at slette gamle uploads)
from mutagen.mp4 import MP4 # Importer mutagen for at håndtere MP4 metadata (bruges til at gemme timestamps)
import json # Importer json for at håndtere JSON data (bruges til at gemme timestamps i MP4 metadata)

app = Flask(__name__) # Opretter en Flask-applikation
app.secret_key = str(uuid.uuid4())  # Replace with a strong, unique key
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024  # Limiter upload størrelse: 3MB

ALLOWED_MIME_TYPES = {'audio/wav', 'audio/x-wav'} # MIME-typer der er tilladt
ALLOWED_EXTENSIONS = {'wav'} # Filtyper der er tilladt

app.config['UPLOAD_DIR'] = os.path.join(app.root_path, 'uploads') # Opretter en mappe til uploads
shutil.rmtree(app.config['UPLOAD_DIR'], ignore_errors=True)  # Rydder gamle uploads
os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True) # Opretter upload-mappen hvis den ikke findes

# Mapping af morsekode til tekst
MORSE_TO_CHARS_MAPPING = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z', '.----': '1', '..---': '2', '...--': '3',
    '....-': '4', '.....': '5', '-....': '6', '--...': '7', '---..': '8',
    '----.': '9', '-----': '0', '.-.-.-': '.', '--..--': ',', '..--..': '?',
    '-.-.--': '!',
    '-..-.': '/', '-.--.': '(', '-.--.-': ')', '.-...': '&',
    '---...': ':', '-.-.-.': ';', '-...-': '=', '.-.-.': '+',
    '-....-': '-', '..--.-': '_', '.-..-.': '"', '...-..-': '$',
    '.--.-.': '@', '/': ' '
}

# Funktion til at kontrollere om filen har en tilladt filtype
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Funktion til at læse lydfilen og konvertere den til mono
def load_audio(filepath):
    audio = AudioSegment.from_file(filepath).set_channels(1) # Konverterer til mono
    samples = np.array(audio.get_array_of_samples()) # Konverterer til numpy array
    sample_rate = audio.frame_rate # Henter sample rate
    return samples, sample_rate, len(audio)  # Returnerer samples, sample rate og længden af lyden i ms

def detect_tone_regions(samples, sample_rate, threshold=60, window_ms=10):
    window_size = int(sample_rate * (window_ms / 1000)) # Beregner vinduesstørrelse i samples
    tone_map = [] # Liste til at gemme tone information

    # Loop gennem samples i vinduer
    for i in range(0, len(samples), window_size):
        window = samples[i:i+window_size] # Henter vinduet
        amplitude = np.max(np.abs(window)) # Beregner amplitude
        is_tone = amplitude > threshold # Tjekker om amplitude er over threshold
        tone_map.append(is_tone) # Tilføjer til tone_map

    return tone_map, window_ms # Returnerer tone_map og vinduesstørrelse


# Funktion til at konvertere tone_map til segmenter
# Segmenter er en liste af tuples (is_tone, duration)
def tone_map_to_segments(tone_map, window_ms):
    segments = [] # Liste til at gemme segmenter
    current = tone_map[0] # Starter med den første tone
    duration = window_ms # Starter med vinduesstørrelsen

    # Loop gennem tone_map og grupperer segmenter
    for val in tone_map[1:]:
        if val == current: # Hvis den samme tone fortsætter
            duration += window_ms # Tilføjer vinduesstørrelsen til varigheden
        else:
            # Ellers tilføj segmentet og variabler indstilles
            segments.append((current, duration))
            current = val
            duration = window_ms

    # Tilføj det sidste segment, som ellers ville blive glemt
    segments.append((current, duration))
    return segments # Returnerer segmenter som en liste af tuples (is_tone, duration)

# Funktion til at konvertere segmenter til morsekode
def segments_to_morse(segments):
    dot_len = 100  # dot længde i ms, juster efter behov (wpm, nuværende hastighed er 20 wpm)
    morse = "" # Start med en tom morse-streng

    # Loop gennem segmenter og konverter til morsekode
    for is_tone, duration in segments:
        if is_tone:
            if duration < dot_len * 1.5:
                morse += "."  # Kort tone er et punktum
            else:
                morse += "-"  # Lang tone er en streg
        else:
            if duration < dot_len * 1.5:
                morse += ""  # Kort pause mellem dele af samme bogstav/tegn
            elif duration < dot_len * 3.5:
                morse += " "  # Længere pause er næste bogstav
            else:
                morse += " / "  # Lang pause er mellemrum (white space)
    return morse  # Returnerer morsekoden som streng

# Konverterer hver morsekode til ASCII værdi ved hjælp af mapping table
def morse_to_text(morse):
    # Returnerer den som tekst
    return ''.join(
        MORSE_TO_CHARS_MAPPING.get(char, ' ') for char in morse.split() 
    )


# Funktion til at afkode morsekoden til tekst, morsekode, segmenter og tone_map
# Den returnerer også varigheden af lydfilen i ms (skulle have været brugt. Se README'en)
def decode_morse(filepath):
    samples, sr, duration_ms = load_audio(filepath)  # Angiver samples, sample rate og varighed
    tone_map, step_ms = detect_tone_regions(samples, sr)  # Angiver tone_map og step_ms
    segments = tone_map_to_segments(tone_map, step_ms)  # Angiver segmenter
    morse = segments_to_morse(segments)  # Konverterer segmenter til morsekode og opbevarer i morse variabel
    text = morse_to_text(morse)  # Konverterer morsekode til tekst og opbevarer i text variabel
    return tone_map, segments, morse, text, duration_ms  # Returnerer alt data (tone_map, segments, morse, text og varighed i ms)

# Genererer timestamps for morsekoden baseret på segmenterne
def generate_morse_timestamps(segments, morse):
    timestamps = [] # Liste til at gemme timestamps
    morse_parts = [] # Liste til at gemme morse dele
    current_symbol = "" # Start med en tom streng
    
    # Iterér gennem morsekoden og opdel den i dele
    for char in morse:
        if char == " ": # Hvis der er et mellemrum
            if current_symbol: # Hvis der er en aktuel symbol
                morse_parts.append(current_symbol) # Tilføj det til morse_parts
                current_symbol = "" # Nulstil den aktuelle symbol
            else:
                # Hvis der er et mellemrum, tilføj en separator
                morse_parts.append("/")
        else:
            current_symbol += char # Tilføj karakteren til den aktuelle symbol
    
    # Tilføj den sidste symbol hvis der er nogen
    if current_symbol:
        morse_parts.append(current_symbol)
    
    # Definerer variabler til at holde styr på segmenter og tid
    segment_index = 0
    time_acc = 0
    
    # Iterér gennem morse_parts og opret timestamps
    for morse_part in morse_parts:
        if morse_part == "/": # Hvis det er en separator
            # Tilføj et mellemrum i timestamps
            timestamps.append([time_acc, " "])
            continue
            
        # Start med at oprette en liste til at holde styr på segmenter for denne symbol
        symbol_segments = []
        
        # Iterér gennem morse_part og opret symbolsegmenter 
        for char in morse_part:
            if char == ".":
                symbol_segments.append(1)  # Dot
            elif char == "-":
                symbol_segments.append(2)  # Dash
        
        # Iterér gennem segmenterne og opret timestamps
        while segment_index < len(segments) and len(symbol_segments) > 0:
            is_tone, duration = segments[segment_index]
            time_acc += duration
            
            if is_tone:
                # Hvis det er en tone, tjekker vi om det er en dot eller dash
                if symbol_segments[0] == 1 and duration < 150:  # Dot
                    symbol_segments.pop(0)
                elif symbol_segments[0] == 2 and duration >= 150:  # Dash
                    symbol_segments.pop(0)
            
            segment_index += 1
            
            # Hvis segmentet er en pause, tjekker vi om det er en kort pause
            # mellem dele af samme bogstav/tegn
            if len(symbol_segments) > 0 and segment_index < len(segments):
                is_next_tone, next_duration = segments[segment_index]
                if not is_next_tone and next_duration < 150:
                    time_acc += next_duration
                    segment_index += 1
        
        # Tilføj timestamp for den aktuelle morse del
        char = morse_to_text(morse_part)
        timestamps.append([time_acc, char])
        
        # Spring den næste pause mellem bogstaver
        if segment_index < len(segments):
            is_tone, duration = segments[segment_index]
            if not is_tone and duration >= 150 and duration < 350:
                time_acc += duration
                segment_index += 1
    
    # Returner timestamps som en liste af tuples (tid, karakter)
    return timestamps

# Funktion til at generere en video med en bar der viser tone information
# Det er her alt magien sker
def generate_bar_video(tone_map, window_ms, output_path, bar_width=512, height=96, fps=60):
    frames = [] # Liste til at gemme frames

    # Beregn total frames baseret på tone_map længde og vinduesstørrelse
    total_frames = int(len(tone_map) * (1000 / window_ms)) // (1000 // fps)

    tone_cache = [255 for _ in range(bar_width)] # Opret en liste til at gemme tone information

    # Loop gennem alle frames og opret billeder
    for frame_idx in range(total_frames):
        # Opret et billede med hvid baggrund
        img = Image.new('RGB', (bar_width, height), color='white')
        draw = ImageDraw.Draw(img)

        progress = frame_idx % bar_width # Beregn hvor langt vi er i billedet
        tone_index = int(frame_idx * (1000 / fps) / window_ms) # Beregn tone_index (hvilken tone vi er på)

        # Opdater tone_cache baseret på tone_index så vi husker hvornår der skal være toner i de efterfølgende frames
        if tone_index < len(tone_map):
            tone_cache[progress] = 255 if not tone_map[tone_index] else 0

        # Tegn en lodret linje for hver tone i tone_cache
        for i in range(bar_width):
            draw.line([(i, 0), (i, height)], fill=(255, tone_cache[i], tone_cache[i]))

        # Tegn en lodret linje for den aktuelle tone (den blå linje der indikerer hvor vi er i videoen)
        draw.line([(progress, 0), (progress, height)], fill=(0, 0, 255))

        frames.append(np.array(img)) # Tilføj billedet til frames listen

    imageio.mimsave(output_path, frames, fps=fps) # Gem videoen med de oprettede frames


# Funktion til at slette gamle uploads
# Den sletter den ældste fil hvis der er mere end 10 filer i upload-mappen
def removeOldFiles():
    # Finder alle filer i upload-mappen
    files = [os.path.join(app.config['UPLOAD_DIR'], f) for f in os.listdir(app.config['UPLOAD_DIR'])]

    # Sorterer filerne efter oprettelsesdato og fjerner den ældste fil hvis der er mere end 10 filer
    if len(files) > 10:
        oldest_file = min(files, key=os.path.getctime)
        os.remove(oldest_file)

# Flask route til index-siden (tilgåes via "/" med GET request)
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Flask route til upload-siden (tilgåes via "/upload" med POST request)
@app.route('/upload', methods=['POST'])
def upload_file():

    # Tjekker om der er en fil i request
    # hvis ikke, returner til index-siden med error
    if 'file' not in request.files:
        return redirect(url_for('index', err='No file part'))

    file = request.files['file'] # Henter filen fra request og gemmer den i variablen file

    # Tjekker om filnavnet er tomt
    # Hvis ja, returner til index-siden med error
    if file.filename == '':
        return redirect(url_for('index', err='No selected file'))

    # Tjekker om filen har en tilladt filtype
    # Hvis ikke, returner til index-siden med error
    if not allowed_file(file.filename):
        return redirect(url_for('index', err='File type not allowed'))

    mime = magic.from_buffer(file.read(2048), mime=True) # Tjekker MIME-type af filen
    file.seek(0) # Går tilbage til starten af filen

    # Tjekker om MIME-typen er i de tilladte typer
    # Hvis ikke, returner til index-siden med error
    if mime not in ALLOWED_MIME_TYPES:
        return redirect(url_for('index', err='Invalid file type'))

    # Opretter en midlertidig fil til at gemme den uploadede lydfil
    # Filen gemmes i upload-mappen med et tilfældigt navn (af sikkerhedsmæssige årsager)
    # og med filtypenavn ".wav"
    tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=app.config['UPLOAD_DIR'])
    file.save(tmp_audio.name)

    # Tjekker om filen er en morse-fil ved at se på type parameteren i request
    # Den er angivet i JS fra script.js som værende lig med "mode"
    if request.form.get('type') == 'morse':
        tone_map, segments, morse, decoded_text, duration_ms = decode_morse(tmp_audio.name)
        
        # Use the existing functions to generate timestamps
        timestamps = generate_morse_timestamps(segments, morse)

        # Opretter en midlertidig fil til at gemme videoen
        tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=app.config['UPLOAD_DIR'])

        # Generer midlertidig video med bar der viser morsekodens tone information (afspilning eller ej)
        tmp_bar = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=app.config['UPLOAD_DIR'])
        generate_bar_video(tone_map, window_ms=10, output_path=tmp_bar.name)

        # Konverterer den midlertidige video til MP4 format
        # og tilføjer den uploadede lydfil som baggrundslyd
        # og gemmer den i upload-mappen med det tilfældige navn
        # Der gøres brug af ffmpeg til at konvertere videoen og tilføje lyden
        # ffmpeg skal være installeret og tilgængeligt i PATH
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "quiet",
            "-i", tmp_bar.name, "-i", tmp_audio.name,
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            "-shortest", tmp_video.name
        ])

        # Tilføj timestamps til videoens metadata
        # Dette gøres ved at bruge mutagen til at tilføje metadata til MP4 filen
        video = MP4(tmp_video.name)
        video["----:com.apple.iTunes:timestampArray"] = [json.dumps(timestamps).encode("utf-8")]
        video.save()

        # Sletter de midlertidige filer
        os.remove(tmp_audio.name)
        os.remove(tmp_bar.name)

        # Sletter gamle uploads hvis der er mere end 10 filer i upload-mappen
        removeOldFiles()

        # Returner til morse-siden med video-id
        return jsonify({'redirect': url_for('morse', v_id=os.path.basename(tmp_video.name).split('.')[0])})
    else:
        # Hvis filen ikke er en morse-fil, returner til index-siden med error
        # DTMF findes ikke, da det ikke er implementeret endnu (desværre)
        return redirect(url_for('index', err='Invalid file type'))


# Flask route til morse-siden (tilgåes via "/morse" med GET request)
# Denne route kræver en v_id (video_id) parameter i URL'en
# Ellers returner til index-siden med error
@app.route('/morse', methods=['GET'])
def morse():
    # Henter video_id fra URL'en
    video_id = request.args.get('v_id')

    # Tjekker om video_id er angivet
    if not video_id:
        return redirect(url_for('index', err='Missing video ID'))

    # Henter videoens path
    video_path = os.path.join(app.config['UPLOAD_DIR'], f"{video_id}.mp4")

    # Tjekker om videoen findes i upload-mappen
    # Hvis ikke, returner til index-siden med error
    if not os.path.exists(video_path):
        return redirect(url_for('index', err='Video not found'))

    # Retunnerer morse-siden med videoens path og timestamps
    # Timestamps hentes fra videoens metadata
    return render_template('morse.html', video_path=f"uploads/{video_id}.mp4", timestamps=MP4(video_path).tags.get('----:com.apple.iTunes:timestampArray')[0].decode("utf-8"))


# Flask route til at sende videoen til browseren
# Denne route bruges kun med GET request og er tilgået via "/uploads/<filename>"
# Den sender videoen fra upload-mappen til browseren
@app.route('/uploads/<path:filename>', methods=['GET'])
def send_video(filename):
    # Returner videoen fra upload-mappen som en ikke-vedhæftet fil med MIME-type "video/mp4"
    return send_from_directory(app.config['UPLOAD_DIR'], filename, as_attachment=False, mimetype='video/mp4')

# Flask route til at sende favicon.ico til browseren
# Denne route bruges kun med GET request og er tilgået via "/favicon.ico"
# Den sender favicon.ico fra static-mappen
@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')