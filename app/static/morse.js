const vid = document.getElementById('morseBarDisplay');
let triggeredIndexes = new Set();
let lastTime = 0;
const secondTimestamps = timestamps.map(([ms, char]) => [(ms-55) / 1000, char]);

function checkTimestamps() {
  if (vid.paused || vid.ended) {
    return;
  }

  const currentTime = vid.currentTime;

  for (let i = 0; i < secondTimestamps.length; i++) {
    const [ts, char] = secondTimestamps[i];
    if (!triggeredIndexes.has(i) && lastTime < ts && currentTime >= ts) {
      triggeredIndexes.add(i);
      document.getElementById('morseOutput').value += char;
    }
  }

  lastTime = currentTime;
}

function copyToClipboard() {
  navigator.clipboard.writeText(document.getElementById('morseOutput').value ).then(function() {
    console.log('Text copied to clipboard');
  }, function(err) {
    console.error('Could not copy text: ', err);
  });
}

function togglePlay() {
  vid.paused ? vid.play() : vid.pause();
}

function toggleMute() {
  if (vid.muted) {
    vid.muted = false;
    document.getElementById('volumeButton').innerText = 'volume_up';
  } else {
    vid.muted = true;
    document.getElementById('volumeButton').innerText = 'volume_off';
  }
}

function setVolume(value) {
  vid.volume = value; // Set the video volume
  if (value == 0) {
    document.getElementById('volumeButton').innerText = 'volume_off';
  } else {
    document.getElementById('volumeButton').innerText = 'volume_up';
  }
}

function stopVideo() {
  vid.currentTime = 0;
  vid.pause()
}

setInterval(checkTimestamps, 50);