var activeMode = null; // Default mode

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

  else if (document.getElementById('soundUpload').files.length === 0) {
    alert('Please select a sound file to upload.');
    return;
  }

  document.getElementById('loadingDisplay').style.display = 'flex';

  const formData = new FormData();
  const fileInput = document.getElementById('soundUpload');


  formData.append('file', fileInput.files[0]);
  formData.append('type', activeMode);

  const response = await fetch('/upload', {
    method: 'POST',
    body: formData,
  });

  if (response.ok) {
    const html = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    document.body.replaceWith(doc.body);
  } else {
    try {
      const error = await response.json();
      let lost = alert(error.error);
      lost.ok = function() {
      window.location.reload()
      }
    }
    catch (e) {
      let lost = alert("Internal Server Error. Please try again later.");
      lost.ok = function() {
        window.location.reload()
      }
    }
  }
});
