# Morsekode og DTMF dekoder
### Af Th1nk7 (Tobias Øfjord Ransborg 3.T 2024/2025 Københavns Mediegymnasium)

# Morsecode and DTMF decoder
This is an exam project for programming.
The synopsis below is made according to the requirements for this exam. (Written in Danish)


## Indledning
Jeg skal udvikle en webapp, der kan afkode morsekode og DTMF (Dual-Tone Multi-Frequency) fra en lydfil. Formålet med projektet er at gøre det muligt for brugere at uploade en lydfil med enten morsekode eller DTMF og få den dekodede tekst vist til brugeren.

Denne webapp kan være meget brugbar i flere sammenhæng. F.eks. vil den være god til CTF-konkurrencer, hvor der ofte er brug for netop disse funktioner.

Projektet vil gøre brug af lydanalyse, og til dette vil jeg benytte Python og de libraries, som er nødvendige. Analysen skal finde mønstre i lyden og dermed bestemme frekvenser for DTMF, eller længden af tonen for morsekode.


## Problemformulering
Hvordan kan jeg udvikle en webapp, hvor brugeren kan uploade en lydfil med enten morsekode eller DTMF, hvorefter lyden afkodes og den dekodede tekst vises til brugeren?

 - Hvordan kan man gøre det muligt at upload lydfiler?

 - Hvordan kan jeg finde forskellen mellem korte og lange signaler i morsekode?

 - Hvordan kan man finde frekvenserne, som skal bruges til DTMF?

 - Hvordan kan man afkode dataene og vise den korrekt.


## Flowchart på brugerniveau
![image](https://github.com/user-attachments/assets/7534bd2f-8929-4e87-81aa-8222c2b7f1eb)


## Disposition over koncepter der tages i brug

### 1. Webapplikation
- **Backend**: Python (til server-side)
- **Framework**: Flask (Python web framework)
- **Frontend**: HTML, CSS, JavaScript
- **Templating**: Jinja2 (til dynamisk indhold)
- **Brugerinteraktion**: Filupload, knapper til valg af dekodningstype, video-kontrollering

### 2. Morsekode-dekodning
- **Lydstyrkedetektion**: Identificering af tone/stille i lydfilen
- **Morsekode tone afkodning**: Afkodning af toner til korte (dots) og lange (dashes) signaler
- **Morsekode-oversættelse**: Oversættelse af dots og dashes til bogstaver/tal/symboler
- **Analyse baseret på tid**: Beregning af længden på toner for at skelne mellem dots og dashes
- **Tidsintervaller**: Identificering af pauser mellem toner og ord

### 3. Datavisualisering
- **Video-generering**: Omdannelse af lydsignal til video til visuel feedback
- **Blok-rendering baseret på lyd og tid**: Grafisk repræsentation af om der er lyd eller ej over tid
- **Interaktiv afspilning**: Kontrolelementer til afspilning, pause, lydstyrke
- **Visuel feedback**: Dynamisk opdatering af dekodet tekst i takt med afspilning

### 4. Filvalidering og upload
- **Filupload gjort sikkert**: Sikker modtagelse og behandling af uploadede filer
- **MIME-type validering**: Sikring af at kun lydfiltyper accepteres (i dette tilfælde kun .wav)
- **Midlertidige filer**: Brug af midlertidige filer til behandling
- **Oprydning**: Automatisk sletning af uploadede og genererede filer

### 5. Containerisering og deployment
- **Docker**: Applikation i en container for let deployment og stærk sikkerhed
- **Environment konfiguration**: Opsætning af nødvendige libraries og andre requirements
- **Dockerfile**: Opsætning af Dockerfile til at bygge containeren
- **Port-mapping**: Mapping af port 5000 til containeren


## Funktionsbeskrivelse
Her vil jeg henvise til koden selv, da jeg har taget min tid til at kommentere hver enkelt funktion og derudover næsten alle enkelte linjer i koden. Det er derfor ikke nødvendigt at skrive det hele her, da det vil være redundant og unødvendigt at gentage sig selv.

I stedet vil jeg forklare hvordan man selv kan insatallere og køre applikationen i en docker container.

### Installation og kørsel
1. **Installer Docker**: Sørg for at have Docker installeret på din computer.
2. **Download koden**: Klon eller download dette repository til din lokale maskine. (`git clone https://github.com/Th1nk7/dtmf-and-morsecode-decoder.git`)
3. **Skift folder til projektmappen**: Åbn en terminal og cd til den mappe, hvor du har downloadet dette repository.
4. **Byg Docker-containeren**: Kør følgende kommandoer i command prompt:
```
docker build -t flask-morse .
docker create --name morse-container -p 5000:5000 flask-morse
docker start -a morse-container
```
5. **Åbn hjemmesiden**: Åbn din webbrowser og gå til `http://localhost:5000` for at få adgang til applikationen.
6. **Upload en lydfil**: Klik på "Upload" knappen og vælg en .wav fil med morsekode
7. **Tryk på play**: Tryk på play knappen for at afspille filen og se den dekodede tekst blive vist i realtid.


## Hvad gør koden?
Koden kan beskrives ved følgende handlinger. (Der tages udgangspunkt i en fungerende og kørende docker container. Derudover er dette også en meget simplficeret version af hvad der sker, da der er mange flere ting der sker i baggrunden, som ikke er beskrevet her.):
1. **Flask starter**: Flask serveren starter, og rydder først 'uploads/' folderen, og lytter derefter på port 5000.
2. **Brugeren besøger hjemmesiden**: Brugeren besøger hjemmesiden på endpoint '/' og Flask serveren sender template filen 'index.html' til brugeren med CSS og JS filernes paths inkluderet.
3. **Brugeren efterspørger JS og CSS**: Flask serveren modtager GET requestene for JS og CSS filerne og sender dem til brugeren.
4. **Brugeren uploader en fil**: Brugeren uploader en .wav fil, som hjemmesiden først opbevarer lokalt.
5. **Brugeren vælger dekodningstype**: Brugeren vælger dekodningstype (Morsekode eller DTMF).
6. **Brugeren starter dekodning**: Brugeren trykker på "Start decoding" knappen, og Flask serveren modtager POST requesten med lydfilen og dekodningstypen.
7. **Flask serveren tjekker filen**: Flask serveren tjekker om filen er en .wav fil og om den er tom. Hvis det ikke er tilfældet, så fortsætter den med at dekode filen. Derudover tjekker den om MIME type er korrekt.
8. **Flask serveren gemmer filen**: Flask serveren gemmer filen i 'uploads/' folderen med tilfældigt navn og som midlertidig fil.
9. **Flask serveren dekoder filen**: Flask serveren dekoder filen og finder relevante data for senere brug.
10. **Flask serveren genererer video (1/3)**: Flask serveren genererer en video af en hvid firkant, som har en blå cursor, der bevæger sig henover firkanten og farver firkanten rød, når der er lyd og hvid når der ikke er lyd. Cursoren looper tilbage til start når den når enden af firkanten.
11. **Flask serveren genererer video (2/3)**: Flask serveren genererer en lydfil med relevant data til den endelige video.
12. **Flask serveren genererer video (3/3)**: Flask serveren genererer den endelige video ved at kombinere den første video og den anden lydfil. Den endelige video gemmes i en tidligere oprettet fil, som også opbevares i 'uploads/' folderen. De midlerertidige filer slettes efterfølgende samt de endelige videoer, der er ældst, hvis der er mere end 10 videoer i 'uploads/' folderen.
13. **Flask serveren sender 200 OK**: Flask serveren sender en 200 OK response tilbage til brugeren med den midlertidige fils navn.
14. **Brugeren omdirigeres**: Brugeren omdirigeres til '/morse' endpointet, hvor der i URL'en er inkluderet den midlertidige fils navn som parameteren 'v_id' for video id. Der gives også timestamps variablen som indeholder timestamps for morse koden samt den dekodede tekst.
15. **Flask serveren sender morse template**: Flask serveren sender template filen 'morse.html' til brugeren med CSS og JS filernes paths inkluderet.
16. **Step 3 gentages**: Brugeren efterspørger JS og CSS filerne og Flask serveren sender dem til brugeren.
17. **Brugeren henter videoen**: Brugeren henter videoen ved brug af 'v_id' parameteren i URL'en.
18. **Flask serveren sender videoen**: Flask serveren sender videoen til brugeren.
19. **Brugeren har fuld styring**: Brugeren har hermed fuld kontrol over hvad der sker, men et godt bud er:
- Brugeren trykker på play knappen og videoen starter.
- JS sørger for at der indsættes dekodet tekst i textarea'en ud fra de timestamps der er givet med morse.html template filen.
- Brugeren kan trykke på pause/play knappen og videoen pauser/fortsætter.
- Brugeren kan trykke på stop knappen og sættes tilbage til start og stoppes.
- Brugeren kan justere lydstyrken for videoen.
- Brugeren kan kopiere den dekodede tekst til udklipsholderen.
- Brugeren kan slette den dekodede tekst.
20. **Brugeren afslutter**: Brugeren afslutter sessionen og lukker browseren.

## Hvad kan der gøres bedre?
Der er mange ting der kan gøres bedre.
- **Setup**: Der bruges kun Flask til at køre serveren, men det kunne være en god idé at bruge en server som Gunicorn eller uWSGI, da de er lavet til produktionssetup.
- **DTMF**: DTMF er ikke færdiggjort og virker derfor ikke. Det er dog ikke langt fra at være klar til implementering. Alle de basale funktioner og templates er sat op, da de skulle bruges til morsekoden. Det er virkeligt dårligt at det ikke er færdigt, da det var en del af projektet og jeg havde håbet på at få det færdigt. Det er dog ikke muligt at få det færdigt i denne omgang, da jeg har brugt for meget tid på morsekoden og videoen.
- **Morsekode**: Morse koden er færdiggjort og virker, men der er stadig nogle ting der kan gøres bedre. F.eks. havde jeg nævnt at jeg ville gøre det muligt at analysere lyden, så den selv vil kunne finde ud af WPM (Words Per Minute) og dermed finde ud af hvor lang tid der skal være mellem hvert signal. Derudover havde jeg nævnt at jeg ville gøre det muligt at finde frekvensen automatisk, og dermed kunne filtrere støjen fra.
- **Client-side**: Jeg havde håbet på at kunne lave det hele client-side, men fandt hurtigt ud af at den frame-rate der bruges i browser ikke er hurtig nok til at kunne følge med.
- **Dårlig CSS**: CSS'en er ikke særlig pæn og skal ryddes op. Det er svært at finde rundt i den.
- **Opdeling af Python kode**: Python koden er svær at finde rundt i, da det hele er i en fil. Det er ikke lige til at finde ud af hvad der er afkodning og hvad der er Flask server relateret.
- **Error håndtering efter dårlig upload**: Client-side bliver bare efterladt hængende, hvis der er fejl internal server error. Det vil være nemt at lave om, men mangel af tid gør at det ikke er muligt.
- **Kun wav**: Det er kun muligt at benytte .wav filer, da jeg pga. mangel på tid ikke har fået implementeret bare så meget som en converter fra andre filtyper til .wav. Det er dog muligt at lave en converter eller lave native support for andre filtyper.
- **"button" class**: Der er lavet en "button" class, og jeg fortryder at lave den. Jeg har dog prøvet at fjerne den, men så virker det ikke. Har ikke nok tid til at finde ud af hvorfor det ikke virker.
- **UUID**: UUID er ikke nødvendigt. Selv secret key er ikke nødvendigt, da det ikke bruges, så ved ikke hvorfor den endte der.
- **"seeking" af video**: Det er ikke muligt at "seek" i videoen, men der er alligevel event listeners, som lytter efter det.
- **Ineffektiv detektion af morsekode**: For at finde morsekoden bliver der tjekket ikke bare én, heller ikke to, men tre gange for hver lydfil. Dette bør skrives om, men det er ikke muligt at gøre det nu pga. mangel på tid.
- **Afvis lange lydfiler**: Ville gerne have afvist lange lydfiler, da de tager lang tid at dekode. Med dette menes der ikke størrelsen, men afspilningstiden.


## Yderligere information
- **morse.wav**: Det er bare en test fil, som kan bruges til test af applikationen.


## Konklusion
Jeg er tilfreds med det færdige resultat, også selvom det ikke er helt færdigt. Det er dog ikke muligt at få det færdigt, da jeg har brugt for meget tid på morsekoden og videoen. Det er dog muligt at få det færdigt i fremtiden, hvis der er tid til det. Jeg vil lave en fork af projektet, som fortsættes engang når eksamerne er færdige. Der er meget der skal gøres, og jeg tager glædeligt imod hjælp. Alt er kommenteret, hvis der mangler noget info, så kan det med garanti findes i koden. Jeg kan desværre ikke besvare min problemformulering helt, da DTMF ikke er færdiggjort, men morsekodens spørgsmål kan man finde svaret på ovenfor. Skulle jeg gentage svaret her, så ville det blive for langt og ville ikke give mening. En ting er dog sikkert, jeg har lært meget - og det er ikke kun om morsekode, men også om container setup med flask og deployment. Det har været en sjov og lærerig oplevelse, og jeg glæder mig til at fortsætte arbejdet med projektet i fremtiden.