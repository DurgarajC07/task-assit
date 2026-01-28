# UI Testing Instructions

## Quick Test Steps

### 1. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Open Browser

Navigate to: `http://localhost:8000`

### 3. Login with Demo Account

- **Username**: `demo_user`
- **Password**: `demo_password_123`

### 4. Verify Online Status

After login, check:

- ✅ Top right corner should show green dot with "Online"
- ✅ Console logs should show: `[WebSocket] ✓ Connected successfully`
- ✅ Console logs should show: `[WebSocket] ✓ Bidirectional communication verified`

### 5. Test Dashboard

- ✅ Dashboard should show real-time stats (Total, In Progress, Completed, High Priority)
- ✅ Recent Activity should display last 5 tasks
- ✅ Stats update every 30 seconds

### 6. Test AI Assistant Chat

1. Click "AI Assistant" in sidebar
2. Send message: "create a high priority task to test the system"
3. Verify:
   - ✅ Message appears immediately
   - ✅ Typing indicator shows
   - ✅ Bot responds within seconds
   - ✅ Task appears in Tasks view
   - ✅ Console shows: `[Chat] Sending via WebSocket`

### 7. Test WebSocket Bidirectionality

Check browser console for:

```
[WebSocket] Connecting to: ws://localhost:8000/api/ws?token=***
[WebSocket] ✓ Connected successfully
[WebSocket] Sending ping...
[WebSocket] ✓ Bidirectional communication verified
```

### 8. Test Page Refresh

1. Refresh the page (F5)
2. Verify:
   - ✅ You remain logged in (no redirect to login)
   - ✅ Dashboard loads automatically
   - ✅ Online status shows "Online"
   - ✅ Tasks and stats load

### 9. Test Tasks CRUD

- ✅ Create task with date picker
- ✅ Update task status (click checkbox)
- ✅ Edit task (click task card)
- ✅ Delete task
- ✅ Search tasks (global search)

### 10. Test Analytics

- Click "Analytics" in sidebar
- ✅ Status chart (doughnut) displays
- ✅ Priority chart (bar) displays
- ✅ Data matches dashboard stats

## Expected Console Logs

### On Login:

```
[Auth] Restoring session for user: demo_user
[WebSocket] Connecting to: ws://localhost:8000/api/ws?token=***
[WebSocket] ✓ Connected successfully
[WebSocket] Sending ping...
[WebSocket] Received message: {type: "pong", data: {...}}
[WebSocket] ✓ Bidirectional communication verified
```

### On Chat Message:

```
[Chat] Sending via WebSocket: create a task
[WebSocket] Received message: {type: "chat_response", data: {...}}
[Chat] Received response: {data: {response: "Task created..."}}
```

### Backend Logs:

```
INFO: WebSocket connection established for user ...
INFO: Received WebSocket message: {'type': 'ping', ...}
INFO: Received ping, sending pong
INFO: Processing message for user ...: create a task
INFO: Processing chat for user ...: create a task
INFO: Intent: CREATE_TASK, Confidence: 0.95
INFO: Executing task operation: CREATE_TASK
INFO: Task operation result: {'success': True, ...}
INFO: Sent WebSocket response to user ...
```

## Troubleshooting

### Online Status Not Showing:

1. Check browser console for WebSocket errors
2. Verify token is saved: `localStorage.getItem('token')`
3. Check backend logs for connection rejection
4. Try logout and login again

### Chat Not Working:

1. Verify online status is "Online"
2. Check console for WebSocket send errors
3. If offline, HTTP fallback should work
4. Check backend logs for orchestrator errors

### Page Refresh Logs Out:

1. Check if token exists: `localStorage.getItem('token')`
2. Verify token is not expired
3. Check console for auth restoration errors

## Success Criteria

✅ All 10 tests pass
✅ No console errors
✅ WebSocket bidirectional verified
✅ Chat creates tasks through orchestrator
✅ Page refresh maintains session
✅ Dashboard shows real-time data
