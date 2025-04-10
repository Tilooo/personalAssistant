// Update the status display
function updateStatus(status) {
    const statusBar = document.getElementById('status');
    statusBar.textContent = status;
    
    // Change status bar color when listening
    if (status.includes('Listening')) {
        statusBar.classList.add('listening');
        document.getElementById('waveform').classList.add('active');
    } else {
        statusBar.classList.remove('listening');
        document.getElementById('waveform').classList.remove('active');
    }
}

// Add a message from the assistant
function updateAssistantMessage(message) {
    const conversation = document.getElementById('conversation');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    
    // Message content
    const messageContent = document.createElement('div');
    messageContent.textContent = message;
    messageDiv.appendChild(messageContent);
    
    // Time stamp
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';
    timeElement.textContent = getCurrentTime();
    messageDiv.appendChild(timeElement);
    
    conversation.appendChild(messageDiv);
    scrollToBottom();
}

// Add a message from the user
function updateUserMessage(message) {
    const conversation = document.getElementById('conversation');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    
    // Message content
    const messageContent = document.createElement('div');
    messageContent.textContent = message;
    messageDiv.appendChild(messageContent);
    
    // Time stamp
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';
    timeElement.textContent = getCurrentTime();
    messageDiv.appendChild(timeElement);
    
    conversation.appendChild(messageDiv);
    scrollToBottom();
}

// Get current time in HH:MM format
function getCurrentTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    minutes = minutes < 10 ? '0' + minutes : minutes;
    
    return `${hours}:${minutes} ${ampm}`;
}

// Scroll to the bottom of the conversation
function scrollToBottom() {
    const conversation = document.getElementById('conversation');
    conversation.scrollTop = conversation.scrollHeight;
}

// Start the assistant
async function startAssistant() {
    document.getElementById('startBtn').disabled = true;
    document.getElementById('stopBtn').disabled = false;
    updateStatus('Starting...');
    const result = await eel.start_assistant()();
    console.log(result);
}

// Stop the assistant
async function stopAssistant() {
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
    updateStatus('Stopping...');
    const result = await eel.stop_assistant()();
    updateStatus('Ready');
    console.log(result);
}

// Expose functions to Python
eel.expose(updateStatus);
eel.expose(updateAssistantMessage);
eel.expose(updateUserMessage);

// Initial greeting when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateAssistantMessage("Hello! I'm your voice assistant. Click 'Start Listening' when you're ready to talk.");
});