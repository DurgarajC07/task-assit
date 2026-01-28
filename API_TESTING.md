# API Testing Guide

## Using cURL

### 1. Register User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "secure_password_123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "secure_password_123"
  }'
```

Save the `access_token` from the response.

### 3. Create Task via API

```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy milk",
    "description": "Get milk from the store",
    "priority": "high",
    "due_date": "2025-01-30T10:00:00Z",
    "tags": ["shopping"]
  }'
```

### 4. Create Task via Natural Language

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a task to buy milk tomorrow morning"
  }'
```

### 5. List Tasks

```bash
curl -X GET "http://localhost:8000/api/tasks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

With filters:
```bash
curl -X GET "http://localhost:8000/api/tasks?filter_type=today&priority=high" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Search Tasks

```bash
curl -X GET "http://localhost:8000/api/tasks/search?q=milk" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 7. Get Task Statistics

```bash
curl -X GET "http://localhost:8000/api/tasks/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8. Natural Language Commands

#### Mark task complete
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mark the milk task as complete"
  }'
```

#### Get task summary
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many tasks do I have pending?"
  }'
```

#### Update task
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Change the milk task priority to low"
  }'
```

## Using Postman

1. **Create Collection**: "Task Assistant API"

2. **Authentication Requests**:
   - POST `/api/auth/register`
   - POST `/api/auth/login`
   - GET `/api/auth/me` (with Bearer token)

3. **Task Requests**:
   - POST `/api/tasks`
   - GET `/api/tasks`
   - GET `/api/tasks/{id}`
   - PUT `/api/tasks/{id}`
   - DELETE `/api/tasks/{id}`

4. **Chat Requests**:
   - POST `/api/chat`
   - GET `/api/chat/history`

5. **Environment Variables**:
   - Set `base_url` = `http://localhost:8000`
   - Set `access_token` from login response
   - Use `{{base_url}}` and `Authorization: Bearer {{access_token}}`

## Natural Language Test Cases

### Task Creation
- "Add a task to call mom tomorrow at 3pm"
- "Create a high priority task to finish the report by Friday"
- "Remind me to schedule a dentist appointment next week"
- "Add task: submit project by end of month"

### Task Listing
- "Show me my tasks"
- "What do I have to do today?"
- "List my high priority tasks"
- "What's due this week?"
- "Show tasks from the last 7 days"

### Task Completion
- "Mark the report task as done"
- "Complete the meeting tomorrow"
- "I finished buying groceries"
- "Check off the dentist appointment"

### Task Searching
- "Find all tasks related to work"
- "Show me tasks tagged with personal"
- "Search for tasks with 'meeting' in them"

### Task Updates
- "Change the report task to high priority"
- "Move the meeting from Tuesday to Wednesday"
- "Add 'urgent' tag to the grocery task"
- "Update the project deadline to next Friday"

### Task Deletion
- "Delete the old grocery task"
- "Remove the completed tasks"

### Statistics
- "How many tasks do I have?"
- "What's my completion rate?"
- "Show me overdue tasks"
- "How many tasks are pending?"

## Expected Responses

### Successful Task Creation
```json
{
  "success": true,
  "message": "✓ Task 'Buy milk' created successfully!",
  "data": {
    "id": "uuid",
    "title": "Buy milk",
    "status": "pending",
    "priority": "high",
    "due_date": "2025-01-30T10:00:00",
    "tags": ["shopping"]
  }
}
```

### Task List
```json
{
  "success": true,
  "message": "Retrieved 5 task(s)",
  "data": {
    "tasks": [
      {
        "id": "uuid",
        "title": "Buy milk",
        "status": "pending",
        "priority": "high",
        ...
      }
    ],
    "total_count": 5,
    "filters_applied": ["today"]
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task not found",
    "details": "No tasks found matching your criteria"
  }
}
```

## Troubleshooting

### 401 Unauthorized
- Token has expired - use refresh token endpoint
- Token format is incorrect
- Check Authorization header format: `Bearer TOKEN`

### 404 Not Found
- Task/resource doesn't exist
- User ID mismatch

### 422 Validation Error
- Invalid request body format
- Missing required fields
- Check Swagger UI (/docs) for request schema

### 500 Internal Server Error
- Check server logs
- Verify database connection
- Check API key configuration

## Performance Testing

### Load Testing with Apache Bench
```bash
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" http://localhost:8000/api/tasks
```

### WebSocket Connection Test
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws?token=YOUR_TOKEN');
ws.onmessage = (event) => {
  console.log('Message:', JSON.parse(event.data));
};
ws.send(JSON.stringify({
  message: "Add a task to buy milk",
  session_id: "uuid"
}));
```
