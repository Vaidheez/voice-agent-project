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
        loadingSpinner.style.display = 'block'; // Show the spinner
        
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
            loadingSpinner.style.display = 'none'; // Hide the spinner
        }
    });
});