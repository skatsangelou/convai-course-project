document.addEventListener("DOMContentLoaded", () => {
  const recordButton = document.getElementById("record");
  const stopButton = document.getElementById("stop");
  const timerDisplay = document.getElementById("timer");
  const uploadForm = document.getElementById("uploadForm");

  let mediaRecorder;
  let mediaStream;           // to store mic stream
  let audioChunks = [];
  let audioBlob;
  let timerInterval;

  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }

  recordButton.addEventListener("click", () => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      mediaStream = stream;
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mediaRecorder.start();

      mediaRecorder.startTime = Date.now();
      timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - mediaRecorder.startTime) / 1000);
        timerDisplay.textContent = formatTime(elapsed);
      }, 1000);

      mediaRecorder.addEventListener("dataavailable", event => {
        audioChunks.push(event.data);
      });

      mediaRecorder.addEventListener("stop", () => {
        clearInterval(timerInterval);
        timerDisplay.textContent = "00:00";
        audioBlob = new Blob(audioChunks, { type: "audio/wav" });

        // Fully stop microphone stream to release it
        if (mediaStream) {
          mediaStream.getTracks().forEach(track => track.stop());
          mediaStream = null;
        }
      });

      recordButton.disabled = true;
      stopButton.disabled = false;
    }).catch(error => {
      alert("Microphone permission denied or error occurred.");
      console.error(error);
    });
  });

  stopButton.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    recordButton.disabled = false;
    stopButton.disabled = true;
  });

  uploadForm.addEventListener("submit", (e) => {
    e.preventDefault();
  
    if (!audioBlob) {
      alert("Please record your question before sending.");
      return;
    }
  
    const formData = new FormData();
    const bookFile = document.getElementById("bookFile").files[0];
    if (bookFile) {
      formData.append("book", bookFile);
    }
    formData.append("audio_data", audioBlob, "question.wav");
  
    // Show awaiting response text
    const awaitingText = document.getElementById("awaitingText");
    awaitingText.style.display = "block";
  
    fetch("/upload", {
      method: "POST",
      body: formData
    })
      .then(res => {
        if (!res.ok) throw new Error("Upload failed");
        location.reload();
      })
      .catch(err => console.error("Error:", err));
  });
});
