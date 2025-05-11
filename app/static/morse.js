const vid = document.getElementById('morseBarDisplay');

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