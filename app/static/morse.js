// Morse bar display videoen
const vid = document.getElementById('morseBarDisplay');

// Set der lagrer indekserne der er blevet trigget
let triggeredIndexes = new Set();

// Variabel der holder styr på den sidste tid videoen blev set på
let lastTime = 0;

// Importerer timestamps fra serveren og konverterer dem til sekunder
// 55ms er trukket fra, da det sidste timestamp ellers havde risiko for at blive skippet
const secondTimestamps = timestamps.map(([ms, char]) => [(ms-55) / 1000, char]);

// Tjekker om tidsrummet mellem nu og sidste tjek har et timestamp i sig
function checkTimestamps() {

  // Hvis videoen er paused eller ended, så gør intet
  if (vid.paused || vid.ended) {
    return;
  }

  // Henter den nuværende tid fra videoen
  const currentTime = vid.currentTime;

  // Itererer over alle timestamp/char set
  for (let i = 0; i < secondTimestamps.length; i++) {

    // Henter timestamp og char fra secondTimestamps arrayet
    const [ts, char] = secondTimestamps[i];

    // Hvis timestampet er blevet trigget, så spring det over
    // ligeledes hvis timestampet ikke passer til tidsrummet
    if (!triggeredIndexes.has(i) && lastTime < ts && currentTime >= ts) {

      // Marker timestamp som trigget
      triggeredIndexes.add(i);

      // Tilføj char fra timstamps til output feltet
      document.getElementById('morseOutput').value += char;
    }
  }

  // Opdater sidste tjekket tid
  lastTime = currentTime;
}

// Mute/unmute videoen
function toggleMute() {
  if (vid.muted) {
    vid.muted = false;

    // 'volume_up' icon er fra Google Material Icons
    document.getElementById('volumeButton').innerText = 'volume_up';
  } else {
    vid.muted = true;

    // 'volume_off' icon er fra Google Material Icons
    document.getElementById('volumeButton').innerText = 'volume_off';
  }
}

// Sætter lydstyrken på videoen som en værdi mellem 0 og 1 (almen procentregning)
function setVolume(value) {
  vid.volume = value;
  if (value == 0) {

    // 'volume_off' icon er fra Google Material Icons
    document.getElementById('volumeButton').innerText = 'volume_off';
  } else {

    // 'volume_up' icon er fra Google Material Icons
    document.getElementById('volumeButton').innerText = 'volume_up';
  }
}

// Stopper videoen og starter forfra samt pauser den
function stopVideo() {
  vid.currentTime = 0;
  vid.pause()
}

// Sætter interval til at tjekke timestamps hvert 50ms
setInterval(checkTimestamps, 50);