// Floating Chatbot JS Logic with Responsive Interactive Chips

document.addEventListener('DOMContentLoaded', () => {
    const chatbotToggleBtn = document.getElementById('chatbotToggleBtn');
    const chatbotBox = document.getElementById('chatbotBox');
    const chatbotCloseBtn = document.getElementById('chatbotCloseBtn');
    const chatbotForm = document.getElementById('chatbotForm');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotBody = document.getElementById('chatbotBody');

    if (!chatbotToggleBtn || !chatbotBox) return;

    // Toggle Visibility
    chatbotToggleBtn.addEventListener('click', () => {
        chatbotBox.classList.toggle('hidden');
        if (!chatbotBox.classList.contains('hidden')) {
            loadChatHistory();
            chatbotInput.focus();
        }
    });

    if (chatbotCloseBtn) {
        chatbotCloseBtn.addEventListener('click', () => {
            chatbotBox.classList.add('hidden');
        });
    }

    // Load conversation history
    async function loadChatHistory() {
        const res = await fetchAPI('/api/chatbot/history');
        if (res.success && Array.isArray(res.data) && res.data.length > 0) {
            chatbotBody.innerHTML = '';
            res.data.forEach(msg => {
                appendChatMessage(msg.sender_type, msg.message);
            });
            scrollToBottom();
        } else {
            chatbotBody.innerHTML = `
                <div class="chat-msg bot">
                    Hello! I'm your Insurance Assistant. 🛡️<br>How can I help you today? Select an option below or ask me a question:
                    <div class="chat-chips-container">
                        <button class="chat-chip-btn" onclick="sendQuickChat('my claim status')">📋 Claim Status</button>
                        <button class="chat-chip-btn" onclick="sendQuickChat('my policies')">🛡️ My Policies</button>
                        <button class="chat-chip-btn" onclick="sendQuickChat('how to submit claim')">❓ How to Claim</button>
                        <button class="chat-chip-btn" onclick="sendQuickChat('raise a ticket')">🎫 Raise Ticket</button>
                    </div>
                </div>
            `;
        }
    }

    function appendChatMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${sender}`;
        
        // Format markdown bold & linebreaks simple
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        msgDiv.innerHTML = formattedText;

        // If bot welcome message, append chips if not present
        if (sender === 'bot' && (text.includes("I am your AI Insurance Assistant") || text.includes("How can I help you"))) {
            const chipsDiv = document.createElement('div');
            chipsDiv.className = 'chat-chips-container';
            chipsDiv.innerHTML = `
                <button class="chat-chip-btn" onclick="sendQuickChat('my claim status')">📋 Claim Status</button>
                <button class="chat-chip-btn" onclick="sendQuickChat('my policies')">🛡️ My Policies</button>
                <button class="chat-chip-btn" onclick="sendQuickChat('how to submit claim')">❓ How to Claim</button>
                <button class="chat-chip-btn" onclick="sendQuickChat('raise a ticket')">🎫 Raise Ticket</button>
            `;
            msgDiv.appendChild(chipsDiv);
        }

        chatbotBody.appendChild(msgDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatbotBody.scrollTop = chatbotBody.scrollHeight;
    }

    // Handle user input
    if (chatbotForm) {
        chatbotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = chatbotInput.value.trim();
            if (!text) return;

            // Display user message
            appendChatMessage('user', text);
            chatbotInput.value = '';

            // Loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'chat-msg bot fst-italic text-muted';
            loadingDiv.id = 'chatLoading';
            loadingDiv.textContent = 'Thinking...';
            chatbotBody.appendChild(loadingDiv);
            scrollToBottom();

            // Send to API
            const res = await fetchAPI('/api/chatbot/message', {
                method: 'POST',
                body: { message: text }
            });

            // Remove loading
            const lEl = document.getElementById('chatLoading');
            if (lEl) lEl.remove();

            if (res.success && res.data && res.data.reply) {
                appendChatMessage('bot', res.data.reply);
            } else {
                appendChatMessage('bot', 'Sorry, I encountered an issue processing your request. Please try again.');
            }
        });
    }

    // Quick chip buttons inside chatbot window
    window.sendQuickChat = function(text) {
        if (chatbotInput) {
            chatbotInput.value = text;
            chatbotForm.dispatchEvent(new Event('submit'));
        }
    };
});
