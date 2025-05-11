var activeMode = null; // Default mode

document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const err = urlParams.get('err');
  if (err) {
    alert(err);
    window.location.href = '/';
  }
});

function updateFileName() {
  const fileInput = document.getElementById('soundUpload');
  const fileNameDisplay = document.getElementById('fileNameField');
  const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file chosen';
  fileNameDisplay.textContent = fileName;
}

function toggleButton(selectedButton) {
  const dtmfButton = document.getElementById('dtmfButton');
  const morseButton = document.getElementById('morseButton');

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

document.getElementById('startButton').addEventListener('click', async (event) => {
  event.preventDefault();

  if (!activeMode) {
    alert('Please select a mode (DTMF or Morse) before starting.');
    return;
  }

  if (activeMode === 'dtmf') {
    alert('DTMF mode is not yet implemented.');
    return;
  }

  else if (document.getElementById('soundUpload').files.length === 0) {
    alert('Please select a sound file to upload.');
    return;
  }

  document.getElementById('loadingDisplay').style.display = 'flex';

  const formData = new FormData();
  const fileInput = document.getElementById('soundUpload');


  formData.append('file', fileInput.files[0]);
  formData.append('type', activeMode);

  fetch('/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.redirect) {
      window.location.href = data.redirect;
    }
  });
});