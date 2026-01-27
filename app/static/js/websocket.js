/**
 * WebSocket Manager Module
 * Handles real-time communication with the backend
 */

const WebSocketManager = {
    ws: null,
    url: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectDelay: 3000,
    messageHandlers: {},
    isConnecting: false,

    /**
     * Connect to WebSocket
     */
    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            console.log('[WebSocket] Already connected or connecting');
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            try {
                const token = API.getToken();
                if (!token) {
                    console.error('[WebSocket] No authentication token available');
                    reject(new Error('No authentication token available'));
                    return;
                }

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                this.url = `${protocol}//${window.location.host}/api/ws?token=${token}`;
                
                console.log('[WebSocket] Connecting to:', this.url.replace(token, '***'));
                this.isConnecting = true;
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    console.log('[WebSocket] ✓ Connected successfully');
                    this.isConnecting = false;
                    this.reconnectAttempts = 0;
                    this.emit('connected');
                    
                    // Test bidirectional communication with a ping
                    this.sendPing();
                    
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('[WebSocket] Error parsing message:', error);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('[WebSocket] Error:', error);
                    this.emit('error', error);
                    this.isConnecting = false;
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('[WebSocket] Disconnected');
                    this.isConnecting = false;
                    this.emit('disconnected');
                    this.attemptReconnect();
                };

                // Timeout for connection
                setTimeout(() => {
                    if (this.isConnecting) {
                        reject(new Error('WebSocket connection timeout'));
                    }
                }, 10000);

            } catch (error) {
                this.isConnecting = false;
                reject(error);
            }
        });
    },

    /**
     * Attempt to reconnect
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[WebSocket] Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => {
                this.connect().catch(() => {
                    // Reconnection attempt failed, will retry
                });
            }, this.reconnectDelay);
        } else {
            console.error('[WebSocket] Max reconnection attempts reached');
            this.emit('reconnect_failed');
        }
    },

    /**
     * Send message via WebSocket
     */
    send(type, data = {}) {
        return new Promise((resolve, reject) => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                reject(new Error('WebSocket is not connected'));
                return;
            }

            try {
                const message = {
                    type,
                    ...data,
                    timestamp: new Date().toISOString()
                };

                this.ws.send(JSON.stringify(message));
                resolve();
            } catch (error) {
                reject(error);
            }
        });
    },

    /**
     * Send chat message
     */
    sendChatMessage(message, sessionId = null) {
        return this.send('chat', {
            message,
            session_id: sessionId
        });
    },

    /**
     * Send ping to test connection
     */
    sendPing() {
        if (this.isConnected()) {
            console.log('[WebSocket] Sending ping...');
            this.send('ping', {}).catch(() => {
                console.log('[WebSocket] Ping failed');
            });
        }
    },

    /**
     * Handle incoming messages
     */
    handleMessage(message) {
        console.log('[WebSocket] Received message:', message);
        const { type, data, error } = message;

        if (error) {
            console.error('[WebSocket] Server error:', error);
            this.emit('server_error', error);
            return;
        }

        // Handle pong response
        if (type === 'pong') {
            console.log('[WebSocket] ✓ Bidirectional communication verified');
            return;
        }

        if (type === 'chat_response') {
            this.emit('chat_response', message);
        } else if (type === 'task_update') {
            this.emit('task_update', data);
        } else if (type === 'notification') {
            this.emit('notification', data);
        } else {
            this.emit(type, data);
        }
    },

    /**
     * Register event handler
     */
    on(event, handler) {
        if (!this.messageHandlers[event]) {
            this.messageHandlers[event] = [];
        }
        this.messageHandlers[event].push(handler);
    },

    /**
     * Unregister event handler
     */
    off(event, handler) {
        if (!this.messageHandlers[event]) return;
        this.messageHandlers[event] = this.messageHandlers[event].filter(h => h !== handler);
    },

    /**
     * Emit event
     */
    emit(event, data) {
        if (!this.messageHandlers[event]) return;
        this.messageHandlers[event].forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`[WebSocket] Error in event handler for ${event}:`, error);
            }
        });
    },

    /**
     * Check if connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    },

    /**
     * Disconnect
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
};
