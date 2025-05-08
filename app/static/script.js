document.addEventListener("DOMContentLoaded", () => {
  const dtmfBtn = document.getElementById('dtmfButton');
  const morseBtn = document.getElementById('morseButton');
  const typeInput = document.getElementById('uploadType');
  const soundUpload = document.getElementById('soundUpload');
  const fileNameField = document.getElementById('fileNameField');

  function toggleButton(type) {
    typeInput.value = type;
    dtmfBtn.classList.remove('active');
    morseBtn.classList.remove('active');
    if (type === 'dtmf') dtmfBtn.classList.add('active');
    if (type === 'morse') morseBtn.classList.add('active');
  }

  dtmfBtn.addEventListener('click', () => toggleButton('dtmf'));
  morseBtn.addEventListener('click', () => toggleButton('morse'));

  soundUpload.addEventListener('change', () => {
    fileNameField.textContent = soundUpload.files[0]
      ? soundUpload.files[0].name
      : 'No file uploaded yet';
  });
});
