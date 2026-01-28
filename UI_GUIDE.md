# Task Assistant - Professional UI Guide

## Overview

The Task Assistant now features a professional, modular UI built with **HTML5**, **Tailwind CSS**, and **Vanilla JavaScript**. The UI is fully integrated with all backend APIs and WebSocket support for real-time communication.

## Architecture

### Frontend Structure

The frontend uses a **modular JavaScript architecture** for better maintainability and scalability:

```
app/static/
├── index.html           # Main HTML template
└── js/
    ├── api.js          # HTTP API client
    ├── websocket.js    # Real-time communication
    ├── auth.js         # Authentication module
    ├── tasks.js        # Task management
    ├── chat.js         # Chat functionality
    ├── ui.js           # Shared UI utilities
    └── app.js          # Main app initialization
```

### Module Responsibilities

#### `api.js` - API Client
- Handles all HTTP requests to backend
- Manages authentication tokens
- Error handling and response parsing
- Endpoints for:
  - Authentication (login, register)
  - Task operations (CRUD)
  - Chat messaging
  - Health checks

#### `websocket.js` - Real-time Communication
- WebSocket connection management
- Auto-reconnection with exponential backoff
- Event-driven message handling
- Support for chat and task updates

#### `auth.js` - Authentication
- Login/Register form management
- Form switching (single page)
- Token persistence
- Session restoration
- Logout functionality

#### `tasks.js` - Task Management
- Task CRUD operations
- Task filtering and sorting
- Task modal for detailed editing
- Statistics loading
- Bulk operations

#### `chat.js` - Chat Functionality
- Message sending
- Session management
- WebSocket fallback to HTTP
- Real-time chat updates

#### `ui.js` - Shared Utilities
- Toast notifications
- HTML escaping (XSS prevention)
- Status indicators
- Badge styling (priority, status)

#### `app.js` - Initialization
- Application startup
- Event handler registration
- API health checks

## Features

### ✨ Professional UI/UX
- **Modern Design**: Glass-morphism effects, smooth animations
- **Responsive**: Works on desktop, tablet, and mobile
- **Accessibility**: Semantic HTML, proper ARIA labels
- **Performance**: Lazy loading, efficient rendering

### 🔐 Security
- **Bearer Token Auth**: Secure API authentication
- **XSS Prevention**: HTML escaping on all user input
- **CSRF Protection**: Token-based requests
- **Secure Storage**: localStorage for tokens

### 🚀 Features
- **Real-time Updates**: WebSocket for instant task updates
- **Task Management**: Full CRUD operations
- **AI Chat**: Integrated AI assistant
- **Statistics**: Live dashboard metrics
- **Task Filtering**: By status and other criteria
- **Tag Support**: Organize tasks with tags

### 🔄 API Integration
- **RESTful APIs**: Login, Register, Tasks, Chat
- **WebSocket**: Real-time chat and task updates
- **Error Handling**: Proper error messages and fallbacks
- **Automatic Retry**: WebSocket auto-reconnection

## Getting Started

### 1. Start the Server

```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the startup script:

```bash
bash start_ui.sh
```

### 2. Access the UI

Open your browser and navigate to:
```
http://localhost:8000
```

### 3. Create an Account or Login

**Option 1: Register New Account**
- Click "Register" in the auth form
- Fill in username, email, and password
- Click "Register"

**Option 2: Login with Demo Account**
- Username: `demo_user`
- Password: `demo_password_123`

### 4. Use the Application

Once logged in, you can:
- **View Dashboard**: See task statistics
- **Create Tasks**: Add new tasks with priority, due date, and tags
- **Manage Tasks**: Edit, complete, or delete tasks
- **Chat with AI**: Ask questions and get assistance
- **Real-time Updates**: Get instant notifications

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns token + user info)
- `GET /api/auth/me` - Get current user

### Tasks
- `POST /api/tasks` - Create task
- `GET /api/tasks` - List tasks (with filters)
- `GET /api/tasks/{id}` - Get task details
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `GET /api/tasks/stats` - Get statistics

### Chat
- `POST /api/chat` - Send message
- `GET /api/chat/history` - Get conversation history

### WebSocket
- `WS /api/ws?token={token}` - Real-time connection

## File Structure

### HTML Template (`index.html`)
- Single-page application
- Responsive grid layout
- Modal for task editing
- Toast notification container
- Structured for easy component addition

### Styling
- **Tailwind CSS**: Utility-first CSS framework via CDN
- **Font Awesome**: Icon library via CDN
- **Custom CSS**: Animations, glass effects, transitions

### JavaScript Modules
- **No external dependencies** (except CDNs for CSS/icons)
- Vanilla JavaScript (ES6+)
- Event-driven architecture
- Clean separation of concerns

## Key JavaScript Patterns

### Module Pattern
```javascript
const Module = {
    data: [],
    
    async load() {
        try {
            this.data = await API.endpoint();
        } catch (error) {
            UI.showToast(error.message, 'error');
        }
    },
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupEventListeners();
        });
    }
};
```

### Error Handling
```javascript
try {
    const response = await API.request(method, endpoint, data);
    // Handle success
} catch (error) {
    UI.showToast(error.message, 'error');
    console.error('Error:', error);
}
```

### Event Delegation
```javascript
document.getElementById('form').addEventListener('submit', (e) => {
    e.preventDefault();
    // Handle form submission
});
```

## Authentication Flow

1. **User Registration**
   - Fill registration form
   - Submit to `POST /api/auth/register`
   - Redirected to login

2. **User Login**
   - Fill login form
   - Submit to `POST /api/auth/login`
   - Receive `access_token` and `refresh_token`
   - Store tokens in localStorage
   - Redirect to app dashboard

3. **API Requests**
   - Include `Authorization: Bearer {token}` header
   - Automatic token attachment

4. **Logout**
   - Clear tokens from localStorage
   - Disconnect WebSocket
   - Redirect to login

## State Management

Each module manages its own state:

```javascript
const Module = {
    data: [],
    currentItem: null,
    isLoading: false,
    
    async load() {
        this.isLoading = true;
        try {
            this.data = await API.get();
        } finally {
            this.isLoading = false;
        }
    }
};
```

## WebSocket Real-time Features

### Chat Messages
```javascript
WebSocketManager.on('chat_response', (data) => {
    Chat.addMessage(data.response, 'bot');
});
```

### Task Updates
```javascript
WebSocketManager.on('task_update', (data) => {
    Tasks.loadTasks();
});
```

### Automatic Reconnection
- 5 maximum reconnection attempts
- 3-second delay between attempts
- Exponential backoff supported

## Deployment

### Development
```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or using Gunicorn with Uvicorn:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Optimizations

1. **Lazy Loading**: Tasks loaded on demand
2. **Debouncing**: Chat input debounced
3. **Caching**: User info cached in localStorage
4. **Minimal DOM Updates**: Only changed elements updated
5. **CSS Framework CDN**: Pre-minified, cached globally

## Troubleshooting

### Login Not Working
- Check browser console for errors
- Verify API is running (`http://localhost:8000/api/health`)
- Check network tab in browser dev tools
- Ensure credentials are correct

### WebSocket Connection Failed
- Check if backend is running
- Verify token is present in localStorage
- Check browser console for errors
- App will fallback to HTTP for chat

### Tasks Not Loading
- Ensure you're logged in
- Check API response in network tab
- Verify database has sample data (`python3 seed_database.py`)

### UI Not Responsive
- Clear browser cache (Ctrl+Shift+Del)
- Hard refresh (Ctrl+Shift+R)
- Check Tailwind CSS CDN availability

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Search functionality
- [ ] Advanced filters
- [ ] Task categories
- [ ] Team collaboration
- [ ] File uploads
- [ ] Email notifications
- [ ] Mobile app

## Security Considerations

1. **Tokens**: Stored in localStorage (consider IndexedDB for sensitive apps)
2. **HTTPS**: Use in production
3. **CORS**: Configured for localhost, update for production
4. **CSP**: Implement Content Security Policy headers
5. **Rate Limiting**: Add rate limiting to API

## Support

For issues or questions:
1. Check browser console for errors
2. Review network requests in DevTools
3. Check backend logs
4. Verify all modules are loaded

---

**Version**: 1.0.0  
**Last Updated**: January 27, 2026  
**Created for**: Task Assistant Multi-LLM
