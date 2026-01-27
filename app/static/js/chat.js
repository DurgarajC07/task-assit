/**
 * Chat Module
 * Handles chat functionality
 */

const Chat = {
    currentSessionId: null,

    async sendMessage(message) {
        if (!message.trim()) return;

        try {
            // Add user message to UI
            this.addMessage(message, 'user');
            document.getElementById('chatInput').value = '';

            // Generate session ID if needed
            if (!this.currentSessionId) {
                this.currentSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            }

            // Show typing indicator
            this.showTypingIndicator();

            // Send via WebSocket if connected, otherwise HTTP
            if (WebSocketManager.isConnected()) {
                console.log('[Chat] Sending via WebSocket:', message);
                await WebSocketManager.sendChatMessage(message, this.currentSessionId);
            } else {
                console.log('[Chat] WebSocket not connected, using HTTP fallback');
                try {
                    const response = await API.chat.sendMessage(message, this.currentSessionId);
                    this.hideTypingIndicator();
                    if (response.data?.response || response.message) {
                        this.addMessage(response.data?.response || response.message, 'bot');
                    }
                    // Reload tasks if task was created
                    if (response.intent || response.data) {
                        setTimeout(() => {
                            Tasks.loadTasks();
                            Tasks.loadStats();
                        }, 500);
                    }
                } catch (error) {
                    this.hideTypingIndicator();
                    this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
                }
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            UI.showToast(error.message || 'Failed to send message', 'error');
        }
    },

    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const indicator = document.createElement('div');
        indicator.id = 'typingIndicator';
        indicator.className = 'flex justify-start fade-in';
        indicator.innerHTML = `
            <div class="bg-gray-200 text-gray-900 rounded-xl px-4 py-3">
                <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    },

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    },

    addMessage(message, sender) {
        const chatMessages = document.getElementById('chatMessages');
        
        // Clear placeholder if exists
        const placeholder = chatMessages.querySelector('.text-center');
        if (placeholder && placeholder.parentElement.classList.contains('h-full')) {
            placeholder.parentElement.remove();
        }

        // Remove typing indicator if exists
        this.hideTypingIndicator();

        const messageEl = document.createElement('div');
        messageEl.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} fade-in`;
        
        const bgColor = sender === 'user' ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' : 'bg-gray-200 text-gray-900';
        const alignment = sender === 'user' ? 'items-end' : 'items-start';
        
        messageEl.innerHTML = `
            <div class="max-w-xs lg:max-w-md ${bgColor} rounded-xl px-4 py-3 shadow-md">
                ${sender === 'bot' ? `<div class="flex items-center gap-2 mb-1"><i class="fas fa-robot text-sm"></i><span class="text-xs font-semibold">AI Assistant</span></div>` : ''}
                <p class="text-sm break-words whitespace-pre-wrap">${UI.escapeHtml(message)}</p>
                <span class="text-xs opacity-70 mt-1 block">${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
        `;
        
        chatMessages.appendChild(messageEl);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    },

    init() {
        document.getElementById('chatForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const message = document.getElementById('chatInput').value;
            this.sendMessage(message);
        });

        // Listen to WebSocket messages
        WebSocketManager.on('chat_response', (data) => {
            this.hideTypingIndicator();
            console.log('[Chat] Received response:', data);
            const message = data?.data?.response || data?.response || data?.data?.message || data?.message;
            if (message) {
                this.addMessage(message, 'bot');
                // Reload tasks if task was created/updated
                if (data?.data?.data || data?.intent) {
                    setTimeout(() => {
                        Tasks.loadTasks();
                        Tasks.loadStats();
                    }, 500);
                }
            }
        });
    }
};

// Initialize chat when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Chat.init();
});
