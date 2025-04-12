let activeMode = null; // Default mode

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

  const formData = new FormData();
  const fileInput = document.getElementById('soundUpload');
  const activeMode = document.querySelector('.button.active')?.id.replace('Button', '');

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
    const error = await response.text();
    alert(error);
  }
});
