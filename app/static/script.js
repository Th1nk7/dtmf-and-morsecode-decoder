// Defineres til null for at undgå error med ikke defineret variabel
var activeMode = null;

// Tjekker om DOM content er loaded
document.addEventListener('DOMContentLoaded', () => {

  // Henter URL parametre
  const urlParams = new URLSearchParams(window.location.search);

  // Henter specifikt err parametret fra URL (error)
  const err = urlParams.get('err');

  // Eksisterer err parametret
  if (err) {

    // Hvis ja, så vises en alert med fejlbeskeden
    alert(err);

    // Redirect til forsiden (uden err parameteren)
    window.location.href = '/';
  }
});

// Ændrer status på file upload feltet
function updateFileName() {

  // Henter file input feltet
  const fileInput = document.getElementById('soundUpload');

  // Henter file name status feltet
  const fileNameDisplay = document.getElementById('fileNameField');

  // Opdater file input status feltet til den uploadede fil, hvis den eksisterer
  const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file chosen';
  fileNameDisplay.textContent = fileName;
}

// Ændrer valgt knap (ikke begge knapper kan være aktive)
function toggleButton(selectedButton) {

  // Henter knappernes elementer
  const dtmfButton = document.getElementById('dtmfButton');
  const morseButton = document.getElementById('morseButton');

  // Hvis den valgte knap er DTMF, så tilføj active class til den og fjern fra morse
  // Ellers tilføj active class til morse knappen og fjern fra DTMF
  // Derudover opdateres activeMode variablen til den valgte knap
  if (selectedButton === 'dtmf') {
    dtmfButton.classList.add('active');
    morseButton.classList.remove('active');
    activeMode = 'dtmf';
  } else {
    morseButton.classList.add('active');
    dtmfButton.classList.remove('active');
    activeMode = 'morse';
  }
}


// Bruger event listener på start knappen og lytter efter click event
document.getElementById('startButton').addEventListener('click', async (event) => {

  // Forhindrer yderligere handlinger ved click event (f.eks. et ekstra klik eller lign.)
  // Dette er gjort eftersom handlingen her tager lang tid
  event.preventDefault();

  // Tjekker om der er valgt en mode (DTMF eller Morse)
  if (!activeMode) {

    // Hvis ikke, så vises en alert med besked om at vælge en mode
    alert('Please select a mode (DTMF or Morse) before starting.');
    return;
  }

  // Tjekker om den valgte mode er DTMF
  if (activeMode === 'dtmf') {

    // Uanset hvad, så vises en alert med besked om at DTMF mode ikke er implementeret endnu
    alert('DTMF mode is not yet implemented.');
    return;
  }

  // Tjekker om der er valgt en fil til upload
  else if (document.getElementById('soundUpload').files.length === 0) {

    // Hvis ikke, så vises en alert med besked om at vælge en fil
    alert('Please select a sound file to upload.');
    return;
  }

  // Hvis der er valgt en fil og en mode, så vises loading display
  // Dette indikerer at uploaden er i gang, og brugeren skal vente
  document.getElementById('loadingDisplay').style.display = 'flex';


  // Opretter formData objekt til at håndtere fil upload
  const formData = new FormData();

  // Definerer file input feltet
  const fileInput = document.getElementById('soundUpload');

  // Tilføjer filen og den valgte mode til formData objektet
  formData.append('file', fileInput.files[0]);

  // Tilføjer den valgte mode til formData objektet (DTMF eller Morse)
  formData.append('type', activeMode);

  // Sender POST request til serveren med formData objektet
  fetch('/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json()) // Konverterer svaret til JSON
  .then(data => {

    // Hvis data.redirect eksisterer, så redirectes brugeren til den URL
    if (data.redirect) {
      window.location.href = data.redirect;
    }
  });
});