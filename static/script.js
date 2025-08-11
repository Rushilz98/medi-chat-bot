document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    let isProcessing = false;
    let thinkingMessage = null;

    // Auto-resize textarea as user types without scroll
    userInput.addEventListener('input', function () {
        // Reset height to auto to get correct scrollHeight
        this.style.height = 'auto';

        // Calculate new height but cap it at max-height
        const newHeight = Math.min(this.scrollHeight, 100);
        this.style.height = newHeight + 'px';

        // Enable/disable send button based on input
        sendBtn.disabled = this.value.trim().length === 0;
    });

    // Focus input field on load
    setTimeout(() => {
        userInput.focus();
        // Initial height adjustment
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';
    }, 100);

    // Send message function
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message || isProcessing) return;

        isProcessing = true;
        sendBtn.disabled = true;

        // Display user message
        addMessage(message, 'user');
        userInput.value = '';
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';

        // Show thinking indicator as a proper message
        showThinkingIndicator();

        // Send to server
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Hide thinking indicator
                hideThinkingIndicator();

                // Display response with appropriate styling
                if (data.mode === 'medical') {
                    addMedicalResponse(data);
                } else {
                    addMessage(data.response, 'bot');
                }

                // Scroll to bottom
                scrollToBottom();

                // Reset processing state
                isProcessing = false;
                sendBtn.disabled = false;
                userInput.focus();
            })
            .catch(error => {
                // Hide thinking indicator
                hideThinkingIndicator();

                // Show error message
                addMessage("❌ Oops! I couldn't process your request. Please check your internet connection and try again.", 'bot');
                console.error('Error:', error);

                // Reset processing state
                isProcessing = false;
                sendBtn.disabled = false;
                userInput.focus();
            });
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Add message to chat box
    function addMessage(text, type) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', type);

        // Add message header for bot messages
        if (type === 'bot' || type === 'medical') {
            const header = document.createElement('div');
            header.className = 'message-header';

            const icon = document.createElement('div');
            icon.className = 'message-icon';
            icon.innerHTML = '<i class="fas fa-user-md"></i>';

            const title = document.createElement('div');
            title.className = 'message-title';
            title.textContent = 'MediChat Assistant';

            header.appendChild(icon);
            header.appendChild(title);
            msgDiv.appendChild(header);
        }

        // Format markdown-like styling in responses
        if (type === 'medical') {
            // Medical messages are handled by addMedicalResponse
        } else {
            // Basic sanitization to prevent XSS
            const tempDiv = document.createElement('div');
            tempDiv.textContent = text;
            const safeText = tempDiv.innerHTML;

            // Replace markdown with HTML
            let formattedText = safeText
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/^- /gm, '• ')
                .replace(/\n/g, '<br>');

            msgDiv.innerHTML += formattedText;
        }

        // Add to chat
        chatBox.appendChild(msgDiv);

        // Remove suggestion bubbles after first message
        const suggestions = document.querySelector('.suggestion-bubbles');
        if (suggestions && chatBox.children.length > 1) {
            suggestions.remove();
        }

        // Scroll to bottom
        scrollToBottom();
    }

    // Add medical response with enhanced formatting
    function addMedicalResponse(data) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message medical';

        // Message header
        const header = document.createElement('div');
        header.className = 'message-header';

        const icon = document.createElement('div');
        icon.className = 'message-icon';
        icon.innerHTML = '<i class="fas fa-stethoscope"></i>';

        const title = document.createElement('div');
        title.className = 'message-title';
        title.textContent = 'Symptom Analysis';

        header.appendChild(icon);
        header.appendChild(title);
        msgDiv.appendChild(header);

        // Medical category tag
        const category = document.createElement('div');
        category.className = 'medical-category';
        category.innerHTML = '<i class="fas fa-diagnoses"></i> Medical Assessment';
        msgDiv.appendChild(category);

        // Symptoms section
        const symptomsSection = document.createElement('div');
        symptomsSection.innerHTML = `
                    <strong>Reported symptoms:</strong>
                    <div class="symptom-list">
                        ${data.symptoms.map(symptom =>
            `<span class="symptom-tag">${symptom.replace(/_/g, ' ')}</span>`
        ).join('')}
                    </div>
                `;
        msgDiv.appendChild(symptomsSection);

        // Condition section
        const conditionSection = document.createElement('div');
        conditionSection.className = 'medical-content';
        conditionSection.innerHTML = `
                    <strong>Possible condition:</strong> ${data.disease}
                `;
        msgDiv.appendChild(conditionSection);

        // Disclaimer section
        const disclaimer = document.createElement('div');
        disclaimer.className = 'medical-disclaimer';
        disclaimer.innerHTML = `
                    <strong>Important:</strong> This is not a medical diagnosis. 
                    Consult a healthcare professional for accurate assessment.
                `;
        msgDiv.appendChild(disclaimer);

        // Response footer
        const footer = document.createElement('div');
        footer.className = 'response-footer';
        footer.innerHTML = `
                    <span>AI-Powered Analysis</span>
                    <div class="response-source">
                        <i class="fas fa-database"></i> Medical Knowledge Base
                    </div>
                    <div class="chat-stats">
                        <span class="stat-item"><i class="fas fa-symptom"></i> ${data.symptoms.length} symptoms</span>
                    </div>
                `;
        msgDiv.appendChild(footer);

        // Add to chat
        chatBox.appendChild(msgDiv);
    }

    // Add thinking indicator to chat
    function showThinkingIndicator() {
        // Remove any existing thinking indicator
        if (thinkingMessage) {
            thinkingMessage.remove();
            thinkingMessage = null;
        }

        // Create thinking message
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot thinking-message';

        // Message header
        const header = document.createElement('div');
        header.className = 'message-header';

        const icon = document.createElement('div');
        icon.className = 'message-icon';
        icon.innerHTML = '<i class="fas fa-user-md"></i>';

        const title = document.createElement('div');
        title.className = 'message-title';
        title.textContent = 'MediChat Assistant';

        header.appendChild(icon);
        header.appendChild(title);
        msgDiv.appendChild(header);

        // Thinking content
        const thinkingContent = document.createElement('div');
        thinkingContent.className = 'thinking';

        const thinkingText = document.createElement('div');
        thinkingText.className = 'thinking-dots';

        // Add three dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.className = 'thinking-dot';
            thinkingText.appendChild(dot);
        }

        thinkingContent.appendChild(thinkingText);
        msgDiv.appendChild(thinkingContent);

        // Add to chat
        chatBox.appendChild(msgDiv);
        thinkingMessage = msgDiv;

        // Scroll to bottom
        scrollToBottom();

        return msgDiv;
    }

    // Remove thinking indicator
    function hideThinkingIndicator() {
        if (thinkingMessage) {
            thinkingMessage.remove();
            thinkingMessage = null;
        }
    }

    // Suggestion click handler
    function useSuggestion(text) {
        userInput.value = text;
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';
        sendBtn.disabled = false;
        userInput.focus();
        sendMessage();
    }

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-focus input when clicking on chat container
    document.querySelector('.chat-container').addEventListener('click', (e) => {
        if (e.target === chatBox || e.target === document.querySelector('.chat-container')) {
            userInput.focus();
        }
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        scrollToBottom();

        // Adjust input height on resize
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';
    });
});