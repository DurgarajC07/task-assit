# 🚀 Quick Start - Task Assistant UI

## 60-Second Setup

### Step 1: Start Server
```bash
cd /home/anvex/workspace/multiagent
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Open Browser
```
http://localhost:8000
```

### Step 3: Login or Register

**Quick Login** (Demo Account)
```
Username: demo_user
Password: demo_password_123
```

**Or Create New Account**
- Click "Register"
- Enter username, email, password
- Click "Register"
- Login with new credentials

## 🎯 Main Features

### 📊 Dashboard
- View task statistics
- See all your tasks
- Monitor progress

### ✏️ Create Task
1. Fill task title
2. Select priority (Low/Medium/High/Urgent)
3. Add description (optional)
4. Set due date (optional)
5. Add tags (optional)
6. Click "Create Task"

### ✅ Manage Tasks
- **Click task** to open details
- **Checkbox** to mark complete
- **Edit** in modal
- **Delete** with confirmation

### 🤖 Chat with AI
- Type message in chat box
- Press Enter or click send
- AI Assistant responds in real-time
- Keep asking questions

### 🔍 Filter Tasks
- Select filter dropdown
- Choose: All, Pending, In Progress, Completed
- List updates instantly

## 💡 Tips & Tricks

### Task Priority Colors
- 🔴 Red: Urgent
- 🟠 Orange: High
- 🔵 Blue: Medium
- ⚪ Gray: Low

### Task Status
- ⏳ Pending: Not started
- ▶️ In Progress: Working on it
- ✅ Completed: Done

### Keyboard Shortcuts
- `Enter` in chat = Send message
- `Ctrl+Shift+R` = Hard refresh
- `F12` = Developer tools

## 🔧 Troubleshooting

### Can't Login?
1. Check username is correct
2. Verify password
3. Try demo account first
4. Check server is running
5. Hard refresh browser (Ctrl+Shift+R)

### Chat Not Working?
- Try typing shorter message
- Check internet connection
- Hard refresh page
- App falls back to HTTP if WebSocket fails

### Tasks Not Showing?
- Create a task first
- Check filter isn't set to "Completed"
- Refresh page
- Check browser console (F12)

### Server Won't Start?
```bash
# Check if port is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Try different port
python3 -m uvicorn app.main:app --port 8001
```

## 📱 Browser Compatibility

✅ Chrome 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Edge 90+  

## 🎨 UI Layout

```
┌─────────────────────────────────────┐
│  Task Assistant      Status  👤User │  ← Navbar
├──────────────────────────────────────┤
│                                      │
│ ┌────────────┬─────────────────────┐ │
│ │            │    📊 STATS         │ │
│ │   💬 CHAT  ├─────────────────────┤ │
│ │            │                     │ │
│ │            │  ➕ CREATE TASK    │ │
│ │            │                     │ │
│ │            │  📋 TASKS LIST     │ │
│ │            │  - Task 1         │ │
│ │            │  - Task 2         │ │
│ └────────────┴─────────────────────┘ │
└──────────────────────────────────────┘
```

## 📚 Full Documentation

For detailed information, see:
- `UI_GUIDE.md` - Complete UI documentation
- `UI_IMPLEMENTATION.md` - Implementation details
- `README.md` - Project overview

## 🆘 Getting Help

### Check Logs
```bash
# Terminal where server is running will show errors
```

### Browser DevTools
1. Open DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for API calls
4. Check Application tab for stored data

### Common Log Messages
```
✓ API health check passed      → Server working
[WebSocket] Connected          → Real-time working
401 Unauthorized              → Token expired, login again
Network Error                 → Server not running
```

## 🎓 Learning Path

1. **Basics**: Login → Create Task → View Stats
2. **Intermediate**: Edit Task → Filter → Tag
3. **Advanced**: Chat → Real-time Updates → WebSocket

## ⚙️ System Requirements

- Python 3.8+
- Modern web browser
- 4GB RAM (minimum)
- 500MB disk space
- Internet connection (for CDN resources)

## 📦 What's Included

✅ Professional UI  
✅ Real-time WebSocket  
✅ Task Management  
✅ AI Chat  
✅ Authentication  
✅ Responsive Design  
✅ Dark mode ready  
✅ Mobile friendly  

## 🚀 Next Steps

1. ✅ Start server and login
2. ✅ Create some tasks
3. ✅ Try different priorities
4. ✅ Chat with AI assistant
5. ✅ Test on mobile

## 📞 Support Info

- **Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/api/ws

---

**Enjoy using Task Assistant!** 🎉

For detailed documentation, see `UI_GUIDE.md`
