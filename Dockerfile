# Bruger image fra python:3.11
FROM python:3.11

# Sætter environment variable for non-interactive mode
# Dette forhindrer apt-get i at spørge om input under installation
# af packages og sikrer, at installationen kører uden problemer
ENV DEBIAN_FRONTEND=noninteractive

# Opdaterer packageindekset og installerer nødvendige pakker
# ffmpeg bruges til at håndtere video- og lydfiler
# libmagic1 bruges til at identificere filtyper (MIME type)
# file bruges til at identificere filtyper
# Rydder op i apt-cache for at reducere billedstørrelsen
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    file && \
    rm -rf /var/lib/apt/lists/*

# Sætter folderen som containeren udfører kommandoer i til /app
WORKDIR /app

# Kopierer app/ mappen fra host til containerens /app/ mappe
# Dette er rekursivt og inkluderer alle filer og undermapper
COPY app/ /app/

# Kopierer requirements.txt fra host til containerens /app/ mappe
# requirements.txt indeholder en liste over Python-libraries, der skal installeres
COPY requirements.txt .

# Installerer de nødvendige Python-libraries fra requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Sætter environment variable for Flask
# FLASK_APP angiver den fil, der indeholder Flask-applikationen (app.py)
# FLASK_RUN_HOST angiver, at Flask-applikationen skal køre på alle IP-adresser
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Sætter port 5000 (standardport for Flask) til at være tilgængelig udefra (fra host maskinen)
EXPOSE 5000

# Starter Flask-applikationen
CMD ["flask", "run"]
