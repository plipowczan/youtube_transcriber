// DOM Elements
const urlInput = document.getElementById('youtube-url');
const transcribeBtn = document.getElementById('transcribe-btn');
const errorMessage = document.getElementById('error-message');
const resultSection = document.getElementById('result-section');
const transcriptText = document.getElementById('transcript-text');
const copyBtn = document.getElementById('copy-btn');
const downloadBtn = document.getElementById('download-btn');

let currentVideoId = '';

// Event Listeners
transcribeBtn.addEventListener('click', handleTranscribe);
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleTranscribe();
    }
});
copyBtn.addEventListener('click', handleCopy);
downloadBtn.addEventListener('click', handleDownload);

// Main transcribe function
async function handleTranscribe() {
    const url = urlInput.value.trim();
    
    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }

    // Hide previous results and errors
    hideError();
    hideResult();
    
    // Show loading state
    setLoading(true);

    try {
        const response = await fetch('/api/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to transcribe video');
        }

        // Success
        currentVideoId = data.video_id;
        transcriptText.textContent = data.transcript;
        showResult();
        
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

// Copy transcript to clipboard
async function handleCopy() {
    try {
        await navigator.clipboard.writeText(transcriptText.textContent);
        
        // Visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Copied!
        `;
        copyBtn.style.color = 'var(--success-color)';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.color = '';
        }, 2000);
        
    } catch (error) {
        showError('Failed to copy to clipboard');
    }
}

// Download transcript as text file
function handleDownload() {
    const transcript = transcriptText.textContent;
    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript_${currentVideoId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// UI Helper Functions
function setLoading(loading) {
    if (loading) {
        transcribeBtn.classList.add('loading');
        transcribeBtn.disabled = true;
        urlInput.disabled = true;
    } else {
        transcribeBtn.classList.remove('loading');
        transcribeBtn.disabled = false;
        urlInput.disabled = false;
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

function showResult() {
    resultSection.classList.remove('hidden');
}

function hideResult() {
    resultSection.classList.add('hidden');
}

// Add smooth scroll to result when it appears
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.target === resultSection && 
            !resultSection.classList.contains('hidden')) {
            setTimeout(() => {
                resultSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'nearest' 
                });
            }, 100);
        }
    });
});

observer.observe(resultSection, { 
    attributes: true, 
    attributeFilter: ['class'] 
});
