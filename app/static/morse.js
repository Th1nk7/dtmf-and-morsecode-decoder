document.addEventListener("DOMContentLoaded", () => {
    const morseVideo = document.getElementById("morseBarDisplay");
    morseVideo.oncanplay = function() {
      document.getElementById('loadingDisplay').hidden = true;
    };
  });
