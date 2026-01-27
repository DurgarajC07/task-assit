/**
 * API Client Module
 * Handles all HTTP requests to the backend
 */

const API = {
    baseURL: `${window.location.origin}/api`,
    token: null,
    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    },

    /**
     * Get authentication token
     */
    getToken() {
        return this.token || localStorage.getItem('token');
    },

    /**
     * Clear authentication token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
    },

    /**
     * Get authorization headers
     */
    getHeaders() {
        return {
            'Content-Type': 'application/json',
            ...(this.getToken() && { 'Authorization': `Bearer ${this.getToken()}` })
        };
    },

    /**
     * Make HTTP request
     */
    async request(method, endpoint, data = null) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            const options = {
                method,
                headers: this.getHeaders(),
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(url, options);
            
            // Handle non-JSON responses
            const contentType = response.headers.get('content-type');
            let responseData;
            
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            } else {
                responseData = { detail: await response.text() };
            }

            if (!response.ok) {
                const errorMessage = responseData.detail || responseData.error?.message || `Error: ${response.status} ${response.statusText}`;
                throw new Error(errorMessage);
            }

            return responseData;
        } catch (error) {
            console.error(`API Error [${method} ${endpoint}]:`, error);
            throw error;
        }
    },

    /**
     * Auth Endpoints
     */
    auth: {
        register(username, email, password) {
            return API.request('POST', '/auth/register', { username, email, password });
        },

        login(username, password) {
            return API.request('POST', '/auth/login', { username, password });
        },

        getCurrentUser() {
            return API.request('GET', '/auth/me');
        }
    },

    /**
     * Task Endpoints
     */
    tasks: {
        create(taskData) {
            return API.request('POST', '/tasks', taskData);
        },

        list(filters = {}) {
            const params = new URLSearchParams(filters);
            return API.request('GET', `/tasks?${params.toString()}`);
        },

        get(taskId) {
            return API.request('GET', `/tasks/${taskId}`);
        },

        update(taskId, updates) {
            return API.request('PUT', `/tasks/${taskId}`, updates);
        },

        delete(taskId) {
            return API.request('DELETE', `/tasks/${taskId}`);
        },

        complete(taskId) {
            return API.request('PATCH', `/tasks/${taskId}/complete`);
        },

        getStats() {
            return API.request('GET', '/tasks/stats');
        },

        search(query) {
            const params = new URLSearchParams({ q: query });
            return API.request('GET', `/tasks/search?${params.toString()}`);
        }
    },

    /**
     * Chat Endpoints
     */
    chat: {
        sendMessage(message, sessionId = null) {
            return API.request('POST', '/chat', {
                message,
                session_id: sessionId
            });
        },

        getHistory(sessionId, limit = 10) {
            const params = new URLSearchParams({
                session_id: sessionId,
                limit: limit
            });
            return API.request('GET', `/chat/history?${params.toString()}`);
        }
    },

    /**
     * Health Check
     */
    health() {
        return API.request('GET', '/health');
    }
};
