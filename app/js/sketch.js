let sound
let isPlaying = false

function setup() {
  noCanvas()
  document.getElementById("soundFile").addEventListener("change", handleFile)
}

function handleFile(event){
  let file = event.target.files[0]
  if(file) {
    let reader = new FileReader()
    reader.onload = function (e) {
      let data = e.target.result
      sound = loadSound(data, () => console.log("Sound loaded"))
    }
    reader.readAsDataURL(file)
  }
}

function togglePlay() {
  if (sound.isLoaded()) {
    if (!isPlaying){
      sound.play()
      isPlaying = true
    }
    else {
      sound.pause()
      isPlaying = false
    }
  }
  else {
    alert("No sound loaded yet!")
  }
}