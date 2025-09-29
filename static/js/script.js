// DOM Elements
const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const btnText = sendBtn.querySelector('.btn-text');
const btnSpinner = document.getElementById('btn-spinner');

// Template variables
const userId = window.templateVars?.userId || '';
const chatId = window.templateVars?.chatId || '';
const sessionId = window.templateVars?.sessionId || '';

// Loading state management
let isLoading = false;
let loadingMessage = null;

// Form submission handler
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query || isLoading) return;

    // Add user message
    appendMessage('user', query);
    
    // Clear input and show loading state
    userInput.value = '';
    setLoadingState(true);
    
    // Show loading message with animated dots
    showLoadingMessage();

    const payload = {
        user_query: query,
        user_id: String(userId),
        chat_id: Number(chatId),
        session_id: String(sessionId)
    };

    try {
        console.log('Sending payload:', JSON.stringify(payload));

        const res = await fetch('/api/v1/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        console.log('Response data:', data);

        // Hide loading message and show response
        hideLoadingMessage();
        appendMessage('assistant', data.message || '[No message]');

        // Add mindmap if present
        if (data.mindmap && Object.keys(data.mindmap).length > 0) {
            addMindmap(data.mindmap);
        }

    } catch (err) {
        console.error('❌ API error:', err);
        hideLoadingMessage();
        appendMessage('assistant', `Error: ${err.message || 'Something went wrong.'}`);
    } finally {
        setLoadingState(false);
    }
});

// Set loading state for button
function setLoadingState(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    userInput.disabled = loading;
    
    if (loading) {
        btnText.classList.add('d-none');
        btnSpinner.classList.remove('d-none');
    } else {
        btnText.classList.remove('d-none');
        btnSpinner.classList.add('d-none');
    }
}

// Show loading message with Bootstrap spinner
function showLoadingMessage() {
    const div = document.createElement('div');
    div.className = 'loading-msg';
    div.innerHTML = `
        <strong>Assistant:</strong> 
        Thinking...
        <div class="spinner-border spinner-border-sm text-secondary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    
    loadingMessage = div;
    chatBox.appendChild(div);
    scrollToBottom();
}

// Hide loading message
function hideLoadingMessage() {
    if (loadingMessage) {
        loadingMessage.remove();
        loadingMessage = null;
    }
}

// Append message to chat
function appendMessage(role, content) {
    const div = document.createElement('div');
    div.className = role === 'user' ? 'user-msg' : 'bot-msg';
    
    // Sanitize content to prevent XSS
    const sanitizedContent = escapeHtml(content);
    div.innerHTML = `<strong>${capitalize(role)}:</strong> ${sanitizedContent}`;
    
    chatBox.appendChild(div);
    scrollToBottom();
}

// Add mindmap to chat
function addMindmap(mindmapData) {
    const id = 'mindmap_' + Date.now();

    const div = document.createElement('div');
    div.innerHTML = `
        <div class="bot-msg" style="margin-bottom: 0; border-radius: 12px 12px 0 0;">
            <strong>Assistant:</strong> Here's a mindmap visualization:
        </div>
        <div id="${id}" class="mindmap-container"></div>
    `;
    
    chatBox.appendChild(div);
    scrollToBottom();

    // Initialize jsMind with error handling
    try {
        const jm = new jsMind({
            container: id,
            theme: 'greensea',
            editable: true
        });
        
        jm.show(mindmapData);
        
        // Apply scaling to mindmap elements
        const container = document.getElementById(id);
        const canvas = container.querySelector('canvas');
        const nodes = container.querySelector('jmnodes');

        if (canvas) {
            canvas.style.transform = 'scale(0.8)';
            canvas.style.transformOrigin = 'top left';
        }

        if (nodes) {
            nodes.style.transform = 'scale(0.8)';
            nodes.style.transformOrigin = 'top left';
        }
        
    } catch (error) {
        console.error('Error creating mindmap:', error);
        appendMessage('assistant', 'Error: Could not display mindmap visualization.');
    }
}

// Utility functions
function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle Enter key for sending messages
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Auto-focus input when page loads
document.addEventListener('DOMContentLoaded', () => {
    userInput.focus();
});