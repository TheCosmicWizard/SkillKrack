// Global variables
let stream = null;
let mediaRecorder = null;
let recordedChunks = [];
let isRecording = false;
let recordedVideoUrl = null;
let isMicEnabled = true;
let recordingTime = 0;
let timerInterval = null;
let isPreviewMode = true;
let currentQuestion = 0;

const questions = [
  "Tell me about yourself and your background.",
  "What are your greatest strengths and how do they apply to this role?",
  "Describe a challenging situation you faced and how you overcame it.",
  "Where do you see yourself in 5 years?",
  "Why are you interested in this position and our company?",
];

// Initialize Lucide icons
lucide.createIcons();

// Initialize camera on page load
window.addEventListener("load", () => {
  initializeCamera();
});

// Clean up on page unload
window.addEventListener("beforeunload", () => {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
  if (timerInterval) {
    clearInterval(timerInterval);
  }
});

function showPage(pageId) {
  // Hide all pages
  document.querySelectorAll(".page").forEach((page) => {
    page.classList.remove("active");
  });

  // Remove active class from all tabs
  document.querySelectorAll(".nav-tab").forEach((tab) => {
    tab.classList.remove("active");
  });

  // Show selected page
  document.getElementById(pageId + "-page").classList.add("active");

  // Add active class to clicked tab
  event.target.classList.add("active");
}

async function initializeCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720 },
      audio: isMicEnabled,
    });

    const video = document.getElementById("cameraVideo");
    video.srcObject = stream;

    // Enable record button
    document.getElementById("recordButton").disabled = false;
  } catch (error) {
    console.error("Error accessing camera:", error);
    alert(
      "Unable to access camera. Please check permissions and reload the page."
    );
  }
}

function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

function startRecording() {
  if (!stream) return;

  recordedChunks = [];
  mediaRecorder = new MediaRecorder(stream, {
    mimeType: "video/webm;codecs=vp9",
  });

  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      recordedChunks.push(event.data);
    }
  };

  mediaRecorder.onstop = () => {
    const blob = new Blob(recordedChunks, { type: "video/webm" });
    recordedVideoUrl = URL.createObjectURL(blob);

    // Switch to playback mode
    switchToPlaybackMode();
  };

  mediaRecorder.start();
  isRecording = true;
  recordingTime = 0;

  // Update UI
  updateRecordingUI();

  // Start timer
  timerInterval = setInterval(() => {
    recordingTime++;
    updateRecordingTime();
  }, 1000);
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    clearInterval(timerInterval);
    updateRecordingUI();
  }
}

function resetRecording() {
  if (recordedVideoUrl) {
    URL.revokeObjectURL(recordedVideoUrl);
    recordedVideoUrl = null;
  }

  recordedChunks = [];
  recordingTime = 0;
  isPreviewMode = true;

  // Reset UI
  switchToPreviewMode();
  initializeCamera();
}

function downloadVideo() {
  if (recordedVideoUrl) {
    const a = document.createElement("a");
    a.href = recordedVideoUrl;
    a.download = `interview-recording-${new Date()
      .toISOString()
      .slice(0, 19)
      .replace(/:/g, "-")}.webm`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
}

function toggleMicrophone() {
  isMicEnabled = !isMicEnabled;

  if (stream) {
    stream.getAudioTracks().forEach((track) => {
      track.enabled = isMicEnabled;
    });
  }

  updateMicrophoneUI();
}

function nextQuestion() {
  currentQuestion = (currentQuestion + 1) % questions.length;
  updateQuestionDisplay();
}

function switchToPreviewMode() {
  isPreviewMode = true;
  document.getElementById("cameraVideo").classList.remove("hidden");
  document.getElementById("playbackVideo").classList.add("hidden");
  document.getElementById("recordButton").classList.remove("hidden");
  document.getElementById("resetButton").classList.add("hidden");
  document.getElementById("downloadButton").classList.add("hidden");
}

function switchToPlaybackMode() {
  isPreviewMode = false;
  document.getElementById("cameraVideo").classList.add("hidden");
  document.getElementById("playbackVideo").classList.remove("hidden");
  document.getElementById("playbackVideo").src = recordedVideoUrl;
  document.getElementById("recordButton").classList.add("hidden");
  document.getElementById("resetButton").classList.remove("hidden");
  document.getElementById("downloadButton").classList.remove("hidden");
}

function updateRecordingUI() {
  const recordButton = document.getElementById("recordButton");
  const recordingIndicator = document.getElementById("recordingIndicator");

  if (isRecording) {
    recordButton.innerHTML =
      '<i data-lucide="square"></i><span>Stop Recording</span>';
    recordButton.className = "btn btn-danger";
    recordingIndicator.classList.remove("hidden");
  } else {
    recordButton.innerHTML =
      '<i data-lucide="camera"></i><span>Start Recording</span>';
    recordButton.className = "btn btn-primary";
    recordingIndicator.classList.add("hidden");
  }

  lucide.createIcons();
}

function updateMicrophoneUI() {
  const micButton = document.getElementById("micButton");

  if (isMicEnabled) {
    micButton.className = "mic-button mic-enabled";
    micButton.innerHTML = '<i data-lucide="mic"></i>';
  } else {
    micButton.className = "mic-button mic-disabled";
    micButton.innerHTML = '<i data-lucide="mic-off"></i>';
  }

  lucide.createIcons();
}

function updateRecordingTime() {
  const mins = Math.floor(recordingTime / 60);
  const secs = recordingTime % 60;
  const timeString = `${mins.toString().padStart(2, "0")}:${secs
    .toString()
    .padStart(2, "0")}`;
  document.getElementById("recordingTime").textContent = `REC ${timeString}`;
}

function updateQuestionDisplay() {
  document.getElementById("questionNumber").textContent = `Question ${
    currentQuestion + 1
  } of ${questions.length}`;
  document.getElementById("questionText").textContent =
    questions[currentQuestion];
}

// Initialize question display
updateQuestionDisplay();
