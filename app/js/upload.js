document.getElementById('uploadForm').addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData();
  const fileInput = document.getElementById('soundFile');
  const decodeType = document.getElementById('decodeType').value;

  formData.append('file', fileInput.files[0]);
  formData.append('type', decodeType);

  const response = await fetch('/upload', {
    method: 'POST',
    body: formData,
  });

  if (response.ok) {
    const data = await response.json();
    displayDecodedData(data);
  } else {
    const error = await response.json();
    alert(error.error);
  }
});

function displayDecodedData(data) {
  const decodedText = document.getElementById('decodedText');
  const timelineBar = document.getElementById('timelineBar');

  decodedText.textContent = '';
  timelineBar.style.display = 'none';

  if (data.type === 'morse') {
    decodedText.textContent = data.decoded;
    drawTimeline(data.timeline);
  } else if (data.type === 'dtmf') {
    decodedText.textContent = data.decoded;
  }
}

function drawTimeline(timeline) {
  const canvas = document.getElementById('timelineBar');
  const ctx = canvas.getContext('2d');
  canvas.style.display = 'block';
  canvas.width = 500;
  canvas.height = 50;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  timeline.forEach((state, index) => {
    ctx.fillStyle = state ? 'green' : 'red';
    ctx.fillRect(index * 50, 0, 50, canvas.height);
  });
}
