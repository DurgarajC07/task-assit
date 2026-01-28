# Testing Real-time Dashboard & Analytics

## Quick Test Steps

### 1. Start the Server

```bash
cd c:\laragon\www\task-assit
python -m uvicorn app.main:app --reload
```

### 2. Open Browser

Navigate to: `http://localhost:8000`

### 3. Login/Register

- Create an account or login with existing credentials

---

## Test 1: Dashboard Stats & Recent Activity

### Steps:

1. **Go to Dashboard view**
   - Click "Dashboard" in sidebar
   - View the 6 stats cards at top

2. **Check stats are showing real data**:
   - Total Tasks
   - Pending Tasks
   - In Progress Tasks
   - Completed Tasks
   - High Priority Tasks
   - Overdue Tasks

3. **Verify Recent Activity**:
   - Look at "Recent Activity" section
   - Should show 5 most recent tasks
   - Verify tasks are sorted newest first (check creation dates)

4. **Create a new task via chat**:
   - Type: "create a meeting for tomorrow at 2pm"
   - Press Enter
   - Watch Dashboard auto-update with new task
   - New task should appear at top of Recent Activity

✅ **Expected**: Stats update immediately, new task appears first in Recent Activity

---

## Test 2: Analytics Charts

### Steps:

1. **Go to Analytics view**
   - Click "Analytics" in sidebar

2. **Verify Status Chart (Doughnut)**:
   - Should show 3 segments:
     - Pending (Gray)
     - In Progress (Blue)
     - Completed (Green)
   - Hover to see counts

3. **Verify Priority Chart (Bar)**:
   - Should show 4 bars:
     - Low (Gray)
     - Medium (Blue)
     - High (Orange)
     - Urgent (Red)
   - Check Y-axis shows correct counts

4. **Test real-time updates**:
   - Keep Analytics view open
   - Open a new browser tab
   - Go to same app, login
   - Create/complete a task in new tab
   - Go back to Analytics tab
   - Wait up to 10 seconds
   - Charts should update automatically

✅ **Expected**: Charts display current data and update automatically

---

## Test 3: WebSocket Real-time Updates

### Steps:

1. **Open Dashboard in Browser 1**
   - Note current stats

2. **Open Tasks view in Browser 2**
   - Create a new task
   - Complete an existing task

3. **Check Browser 1 Dashboard**:
   - Should update within 1 second
   - Stats cards should reflect new counts
   - Recent Activity should show new task

4. **Switch to Analytics in Browser 1**:
   - Charts should show updated data
   - Wait 10 seconds, should auto-refresh

✅ **Expected**: All views update in real-time via WebSocket

---

## Test 4: Sorting Verification

### Steps:

1. **Create multiple tasks quickly**:
   - "create task 1"
   - "create task 2"
   - "create task 3"

2. **Go to Dashboard**
   - Check Recent Activity
   - Task 3 should be at top
   - Task 2 should be second
   - Task 1 should be third

3. **Verify dates**:
   - Look at creation dates
   - Should be in descending order (newest first)

✅ **Expected**: Recent Activity sorted newest to oldest

---

## Test 5: Auto-refresh Cleanup

### Steps:

1. **Go to Analytics view**
   - Charts load and start auto-refreshing

2. **Switch to Tasks view**
   - Wait 15 seconds

3. **Open browser DevTools Console**
   - Should NOT see repeated API calls to `/api/tasks/stats`

4. **Go back to Analytics**
   - Should see API calls resume

✅ **Expected**: Auto-refresh stops when leaving Analytics, resumes when returning

---

## Test 6: API Parameters

### Steps:

1. **Open browser DevTools Network tab**

2. **Go to Dashboard**
   - Look for request to `/api/tasks`
   - Check query parameters: `?sort_by=created_at&sort_order=desc`

3. **Go to Analytics**
   - Look for request to `/api/tasks/stats`
   - Check response has all stats fields

✅ **Expected**: API calls include correct parameters

---

## Debugging Tips

### If stats don't show:

1. Check browser console for errors
2. Verify backend is running: `http://localhost:8000/docs`
3. Check API response: `/api/tasks/stats`

### If charts don't appear:

1. Verify Chart.js is loaded in HTML
2. Check for canvas elements: `#statusChart`, `#priorityChart`
3. Look for JavaScript errors in console

### If WebSocket doesn't update:

1. Check WebSocket connection in DevTools Network tab
2. Look for "connected" message in console
3. Verify token is valid (try logout/login)

### If sorting is wrong:

1. Check API response includes `created_at` field
2. Verify tasks are in correct order in API response
3. Check browser console for errors in `renderRecentActivity()`

---

## Success Criteria

✅ Dashboard stats show real numbers
✅ Recent Activity sorted newest first
✅ Status chart displays pending/in-progress/completed
✅ Priority chart displays low/medium/high/urgent
✅ Charts auto-refresh every 10 seconds
✅ WebSocket updates all views instantly
✅ No memory leaks (auto-refresh stops when leaving view)
✅ All API calls use correct parameters

---

## Performance Checks

- Dashboard loads in < 1 second
- Analytics charts render in < 2 seconds
- WebSocket updates appear in < 1 second
- Auto-refresh happens every 10 seconds
- No duplicate API calls
- No console errors

---

## Common Issues

### Issue: Stats showing 0 for all values

**Fix**: Create some tasks first

### Issue: Charts not updating

**Fix**: Check auto-refresh is working (should refresh every 10 seconds)

### Issue: Recent Activity empty

**Fix**: Create tasks, they should appear immediately

### Issue: WebSocket not connecting

**Fix**: Check backend is running, verify token is valid

### Issue: Dates not showing in Recent Activity

**Fix**: Check task has `created_at` field in API response

---

## API Testing (Optional)

### Test sort_by parameter:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/tasks?sort_by=created_at&sort_order=desc"
```

### Test stats endpoint:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/tasks/stats"
```

Expected stats response:

```json
{
  "success": true,
  "data": {
    "statistics": {
      "total_tasks": 10,
      "pending": 3,
      "in_progress": 2,
      "completed": 5,
      "low_priority": 2,
      "medium_priority": 5,
      "high_priority": 2,
      "urgent_priority": 1
    }
  }
}
```
