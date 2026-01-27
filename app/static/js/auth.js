/**
 * Authentication Module
 * Handles login, register, and auth state
 */

const Auth = {
    currentUser: null,
    refreshToken: null,
    isLoading: false,

    init() {
        this.setupEventListeners();
        this.restoreAuthState();
    },

    setupEventListeners() {
        // Form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));

        // Form switching
        document.getElementById('switchToRegisterBtn').addEventListener('click', () => this.showRegisterForm());
        document.getElementById('switchToLoginBtn').addEventListener('click', () => this.showLoginForm());
        document.getElementById('registerNavBtn').addEventListener('click', () => this.showRegisterForm());
        document.getElementById('loginNavBtn').addEventListener('click', () => this.showLoginForm());

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());
    },

    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        try {
            this.setLoading(true);
            const response = await API.auth.login(username, password);
            
            // Store tokens and user info
            API.setToken(response.access_token);
            this.refreshToken = response.refresh_token;
            this.currentUser = response.user;

            localStorage.setItem('user', JSON.stringify(this.currentUser));
            localStorage.setItem('refreshToken', this.refreshToken);

            // Show app
            this.showApp();
            UI.showToast('Login successful!', 'success');
            
            // Connect WebSocket with delay to ensure app is ready
            setTimeout(() => {
                WebSocketManager.connect()
                    .then(() => {
                        console.log('[Auth] WebSocket connected');
                        UI.updateStatus('online');
                    })
                    .catch((error) => {
                        console.log('[Auth] WebSocket failed:', error);
                        UI.updateStatus('offline');
                    });
            }, 500);

            // Load data
            await Tasks.loadTasks();
            await Tasks.loadStats();
        } catch (error) {
            UI.showToast(error.message || 'Login failed', 'error');
            console.error('Login error:', error);
        } finally {
            this.setLoading(false);
        }
    },

    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;

        try {
            this.setLoading(true);
            await API.auth.register(username, email, password);
            UI.showToast('Registration successful! Please login.', 'success');
            
            // Clear form and switch to login
            document.getElementById('registerForm').reset();
            this.showLoginForm();
        } catch (error) {
            UI.showToast(error.message || 'Registration failed', 'error');
            console.error('Register error:', error);
        } finally {
            this.setLoading(false);
        }
    },

    async handleLogout() {
        try {
            this.setLoading(true);
            WebSocketManager.disconnect();
            
            API.clearToken();
            this.currentUser = null;
            this.refreshToken = null;
            localStorage.removeItem('user');
            localStorage.removeItem('refreshToken');
            
            // Show auth form
            this.showAuth();
            UI.showToast('Logged out successfully', 'success');
        } catch (error) {
            console.error('Logout error:', error);
            this.showAuth();
        } finally {
            this.setLoading(false);
        }
    },

    showLoginForm() {
        document.getElementById('loginFormContainer').classList.remove('hidden');
        document.getElementById('registerFormContainer').classList.add('hidden');
        document.getElementById('loginUsername').focus();
    },

    showRegisterForm() {
        document.getElementById('loginFormContainer').classList.add('hidden');
        document.getElementById('registerFormContainer').classList.remove('hidden');
        document.getElementById('registerUsername').focus();
    },

    showAuth() {
        document.getElementById('authContainer').classList.remove('hidden');
        document.getElementById('appContainer').classList.add('hidden');
        this.showLoginForm();
    },

    showApp() {
        document.getElementById('authContainer').classList.add('hidden');
        document.getElementById('appContainer').classList.remove('hidden');

        // Update user display
        if (this.currentUser) {
            document.getElementById('userDisplay').textContent = this.currentUser.username;
        }

        // Switch to dashboard view
        if (window.switchView) {
            window.switchView('dashboard');
        }
    },

    setLoading(loading) {
        this.isLoading = loading;
    },

    restoreAuthState() {
        const token = localStorage.getItem('token');
        const userStr = localStorage.getItem('user');
        const refreshToken = localStorage.getItem('refreshToken');

        if (token && userStr) {
            try {
                API.setToken(token);
                this.currentUser = JSON.parse(userStr);
                this.refreshToken = refreshToken;
                this.showApp();
                
                console.log('[Auth] Restoring session for user:', this.currentUser.username);
                
                // Load initial data
                Tasks.loadTasks();
                Tasks.loadStats();
                
                // Try to connect WebSocket for real-time updates
                setTimeout(() => {
                    WebSocketManager.connect()
                        .then(() => {
                            console.log('[Auth] WebSocket connected successfully');
                            UI.updateStatus('online');
                        })
                        .catch((error) => {
                            console.log('[Auth] WebSocket connection failed:', error);
                            UI.updateStatus('offline');
                        });
                }, 500);
            } catch (error) {
                console.error('Error restoring auth state:', error);
                // Clear invalid data and show login
                API.clearToken();
                localStorage.removeItem('user');
                localStorage.removeItem('refreshToken');
                this.showAuth();
            }
        } else {
            this.showAuth();
        }
    }
};

// Initialize auth when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});
