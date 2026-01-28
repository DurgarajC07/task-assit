# Quick Start Guide - Professional Admin Panel

## Starting the Application

### 1. Start the Backend Server

Open PowerShell in the project directory:

```powershell
cd c:\laragon\www\multiagent
```

Activate your Python environment (if using virtual environment):

```powershell
# If using venv
.\venv\Scripts\Activate.ps1

# If using conda
conda activate your_env_name
```

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at: `http://localhost:8000`

### 2. Access the Admin Panel

Open your web browser and navigate to:

```
http://localhost:8000/static/index.html
```

Or simply:

```
http://localhost:8000
```

(If your main.py is configured to serve static files at root)

### 3. Register a New Account

1. Click on "Register Now" on the login page
2. Fill in:
   - Username: `admin`
   - Email: `admin@example.com`
   - Password: `admin123` (minimum 8 characters)
3. Click "Create Account"
4. You'll be redirected to login

### 4. Login

1. Enter your username: `admin`
2. Enter your password: `admin123`
3. Click "Sign In"
4. You'll be redirected to the Dashboard

## Features to Test

### Dashboard

- ✅ View statistics cards (Total, In Progress, Completed, High Priority)
- ✅ Quick actions buttons
- ✅ Connection status indicator (should show "Online" with green pulse)

### Tasks

1. **Create a Task**
   - Click "New Task" button
   - Fill in task details
   - Click "Create Task"
   - Verify task appears in the list

2. **Filter Tasks**
   - Use status dropdown (All, Pending, In Progress, Completed)
   - Use priority dropdown (All, Low, Medium, High, Urgent)
   - Click "Clear Filters" to reset

3. **Search Tasks**
   - Use the search bar in top navigation
   - Type a search query
   - Results will filter in real-time

4. **Edit Task**
   - Click on any task card
   - Modal will open with task details
   - Modify fields
   - Click "Update Task"

5. **Complete Task**
   - Click the checkbox on any task card
   - Task status will toggle between completed/not completed

6. **Delete Task**
   - Click on task to open modal
   - Click "Delete Task" button
   - Confirm deletion

### AI Assistant

1. Click "AI Assistant" in the sidebar
2. Type a message like: "Create a task to review project documentation"
3. Press Enter or click send button
4. Watch for typing indicator (animated dots)
5. Receive AI response

### Analytics

1. Click "Analytics" in sidebar
2. View:
   - Task Status Distribution (Doughnut Chart)
   - Priority Breakdown (Bar Chart)
3. Charts update automatically based on your tasks

## API Endpoints Available

### Authentication

- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - Login user
- GET `/api/auth/me` - Get current user info

### Tasks

- GET `/api/tasks` - List all tasks
- POST `/api/tasks` - Create task
- GET `/api/tasks/{id}` - Get single task
- PUT `/api/tasks/{id}` - Update task
- DELETE `/api/tasks/{id}` - Delete task
- GET `/api/tasks/stats` - Get statistics
- GET `/api/tasks/search?q=query` - Search tasks

### Chat

- POST `/api/chat` - Send chat message
- GET `/api/chat/history?session_id={id}` - Get chat history

### WebSocket

- WS `/api/ws?token={token}` - Real-time communication

## WebSocket Testing

The WebSocket connection is established automatically after login. To test:

1. Open browser DevTools (F12)
2. Go to Console tab
3. You should see: `[WebSocket] Connected`
4. Send a chat message
5. Message will be sent via WebSocket in real-time
6. Response will appear instantly without HTTP request

## Troubleshooting

### "API connection failed" error

- Check if backend server is running
- Verify port 8000 is not blocked
- Check console for errors

### WebSocket not connecting

- Ensure token is valid (check localStorage in DevTools)
- Check if `/api/ws` endpoint is accessible
- Will automatically fall back to HTTP API

### Tasks not loading

- Check browser console for errors
- Verify authentication token is set
- Try logging out and logging in again

### Charts not displaying

- Ensure Chart.js CDN is loaded
- Check browser console for errors
- Try refreshing the analytics view

## Browser DevTools Tips

Press F12 to open DevTools:

**Console Tab:**

- View application logs
- Check for errors
- Monitor WebSocket messages

**Network Tab:**

- Monitor API requests
- Check response times
- Verify status codes

**Application Tab:**

- View localStorage (auth token)
- Check session storage

## Performance Tips

1. **Clear Filters**: Use "Clear Filters" button instead of reloading
2. **Search**: Search is debounced (500ms) for better performance
3. **Auto-refresh**: Tasks refresh automatically on WebSocket updates
4. **Session**: Your session persists across page reloads

## Security Notes

1. Tokens are stored in localStorage
2. All API requests include Authorization header
3. WebSocket uses token-based authentication
4. XSS protection via HTML escaping
5. CORS should be configured in backend

## Production Deployment

Before deploying to production:

1. ✅ Enable HTTPS
2. ✅ Configure CORS properly
3. ✅ Use environment variables for secrets
4. ✅ Set secure WebSocket (wss://)
5. ✅ Enable rate limiting
6. ✅ Add monitoring and logging
7. ✅ Minify JavaScript files
8. ✅ Optimize images
9. ✅ Enable compression
10. ✅ Set up CDN for static assets

## Support

For issues or questions:

- Check console logs
- Review network requests
- Verify backend is running
- Check API documentation

Enjoy your professional Task Assistant Pro admin panel! 🚀
