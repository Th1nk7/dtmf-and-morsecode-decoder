
const vid = document.getElementById('morseBarDisplay');
const volControl = document.getElementById('vol-control');
const pauseBtn = document.getElementById('pauseBtn');

volControl.oninput = () => vid.volume = volControl.value / 100;
pauseBtn.onclick = () => {
  if (vid.paused) {
    vid.play();
    pauseBtn.textContent = 'Pause';
  } else {
    vid.pause();
    pauseBtn.textContent = 'Play';
  }
};
