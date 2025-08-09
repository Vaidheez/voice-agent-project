// --- Text-to-Speech Logic ---
document.addEventListener('DOMContentLoaded', function() {
    const textInput = document.getElementById('text-input');
    const voiceSelector = document.getElementById('voice-selector');
    const speakButton = document.getElementById('speak-button');
    const audioPlayer = document.getElementById('audio-player');
    const statusMessage = document.getElementById('status-message');
    const loadingSpinner = document.getElementById('loading-spinner');

    speakButton.addEventListener('click', async () => {
        const text = textInput.value;
        const voiceId = voiceSelector.value;

        if (!text) {
            statusMessage.textContent = "Please enter some text.";
            return;
        }

        statusMessage.textContent = "";
        speakButton.disabled = true;
        audioPlayer.style.display = 'none';
        loadingSpinner.style.display = 'block';

        const payload = {
            text: text,
            voice_id: voiceId
        };

        try {
            const response = await fetch('http://localhost:8000/generate-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const audioUrl = data.audio_url;

            if (audioUrl) {
                audioPlayer.src = audioUrl;
                audioPlayer.style.display = 'block';
                audioPlayer.play();
                statusMessage.textContent = "Audio ready and playing!";
            } else {
                throw new Error("Audio URL not found in response.");
            }

        } catch (error) {
            console.error('Error generating audio:', error);
            statusMessage.textContent = `Error: ${error.message}`;
        } finally {
            speakButton.disabled = false;
            loadingSpinner.style.display = 'none';
        }
    });
});

// --- Echo Bot & Transcription Logic ---
const startRecordingButton = document.getElementById('start-recording-button');
const stopRecordingButton = document.getElementById('stop-recording-button');
const echoAudioPlayer = document.getElementById('echo-audio-player');
const echoStatusMessage = document.getElementById('echo-status-message');
const waveformContainer = document.getElementById('waveform-container');
const transcriptionResult = document.getElementById('transcription-result');

let mediaRecorder;
let audioChunks = [];

// Request microphone access and start recording
startRecordingButton.addEventListener('click', async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            echoStatusMessage.textContent = "Transcribing and generating Murf audio...";
            echoStatusMessage.classList.remove('success', 'error');
            waveformContainer.style.display = 'none';
            transcriptionResult.textContent = '';

            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

            const filename = `echo-recording-${new Date().toISOString().replace(/:/g, '-').replace(/\./g, '-')}.webm`;
            const formData = new FormData();
            formData.append('file', audioBlob, filename);

            try {
                // Fetch the NEW /tts/echo endpoint
                const response = await fetch('http://localhost:8000/tts/echo', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `Processing failed with status: ${response.status}`);
                }

                const data = await response.json();
                
                // Use the Murf audio URL from the response
                const murfAudioUrl = data.murf_audio_url;

                echoStatusMessage.innerHTML = `<span style="color: green;">Processing successful!</span>`;
                echoStatusMessage.classList.add('success');
                transcriptionResult.textContent = `Transcript: "${data.transcription}"`;
                
                if (murfAudioUrl) {
                    echoAudioPlayer.src = murfAudioUrl;
                    echoAudioPlayer.style.display = 'block';
                    echoAudioPlayer.play();
                } else {
                    echoStatusMessage.innerHTML = `<span style="color: red;">Error: Murf audio URL not found.</span>`;
                }

            } catch (error) {
                console.error('Error during processing:', error);
                echoStatusMessage.innerHTML = `<span style="color: red;">Error: ${error.message}</span>`;
                echoStatusMessage.classList.add('error');
            } finally {
                startRecordingButton.disabled = false;
                stopRecordingButton.disabled = true;
            }
        };

        mediaRecorder.start();
        echoStatusMessage.textContent = "Recording...";
        echoStatusMessage.classList.remove('success', 'error');
        startRecordingButton.disabled = true;
        stopRecordingButton.disabled = false;
        echoAudioPlayer.style.display = 'none';
        waveformContainer.style.display = 'flex';

    } catch (err) {
        echoStatusMessage.textContent = `Error: ${err.message}. Please allow microphone access.`;
        echoStatusMessage.classList.add('error');
        console.error('Error accessing microphone:', err);
    }
});

// Stop recording and trigger processing/playback
stopRecordingButton.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        echoStatusMessage.textContent = "Processing audio...";
        startRecordingButton.disabled = true;
        stopRecordingButton.disabled = true;
    }
});