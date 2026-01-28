# Bulk Operations Guide

## Overview

The Task Assistant now supports powerful bulk operations through natural language conversation. You can manage multiple tasks at once using simple commands.

## Available Bulk Operations

### 1. Bulk Delete

Delete multiple tasks based on criteria.

**Examples:**

```
✅ "delete all completed tasks"
✅ "remove all high priority tasks"
✅ "delete all tasks for today"
✅ "remove all pending tasks"
```

**Supported Criteria:**

- **Status**: pending, in_progress, completed, cancelled
- **Priority**: low, medium, high, urgent
- **Date Filter**: today, this_week, this_month, overdue

### 2. Bulk Update

Update multiple tasks with new values.

**Examples:**

```
✅ "mark all today's tasks as high priority"
✅ "change all pending tasks to medium priority"
✅ "update all overdue tasks to urgent"
✅ "set all in_progress tasks to high priority"
```

**Supported Updates:**

- **Priority**: low, medium, high, urgent
- **Status**: pending, in_progress, completed
- **Tags**: Add or update tags

### 3. Bulk Complete

Mark multiple tasks as complete at once.

**Examples:**

```
✅ "complete all today's tasks"
✅ "mark all pending tasks as done"
✅ "finish all high priority tasks"
✅ "complete all tasks for this week"
```

## How It Works

### Multi-Agent Reasoning & Action

The system uses advanced multi-agent coordination:

1. **Intent Agent** analyzes your request
   - Detects bulk operation keywords ("all", "multiple", "every")
   - Extracts criteria (status, priority, date filters)
   - Identifies action (delete, update, complete)

2. **Task Agent** executes the operation
   - Queries tasks matching criteria
   - Applies bulk changes
   - Logs audit trail for each task
   - Returns results with count

3. **Conversation Agent** provides feedback
   - Confirms operation
   - Reports count of affected tasks
   - Suggests next actions

## Real-World Usage

### Scenario 1: End of Day Cleanup

```
User: "complete all today's tasks"
AI: "I've marked 5 tasks as complete for today! Great progress!"

User: "delete all completed tasks from last week"
AI: "Successfully removed 12 completed tasks from last week."
```

### Scenario 2: Priority Management

```
User: "mark all overdue tasks as urgent"
AI: "Updated 3 overdue tasks to urgent priority."

User: "change all pending tasks to high priority"
AI: "Set 7 pending tasks to high priority."
```

### Scenario 3: Bulk Organization

```
User: "delete all cancelled tasks"
AI: "Deleted 4 cancelled tasks from your list."

User: "complete all tasks with low priority"
AI: "Marked 6 low priority tasks as complete!"
```

## Smart Features

### Context-Aware Processing

The system understands context from conversation:

```
User: "show me all high priority tasks"
AI: "You have 8 high priority tasks..."

User: "mark them all as complete"
AI: [Understands "them" refers to high priority tasks]
    "Completed 8 high priority tasks! Excellent work!"
```

### Safety Confirmations

For large bulk operations, the system provides details:

```
User: "delete all tasks"
AI: "Are you sure? This will delete 45 tasks. Please specify criteria like 'delete all completed tasks' for safety."
```

### Reasoning Transparency

The system explains its actions:

```
User: "finish everything for today"
AI: "I'll mark all tasks due today as complete.
     Found 4 tasks due today - marking them as done..."
```

## API Structure

### Bulk Delete

**Intent**: `BULK_DELETE`
**Entities**:

```json
{
  "bulk_criteria": {
    "status": "completed",
    "priority": "low",
    "due_date_filter": "today"
  }
}
```

### Bulk Update

**Intent**: `BULK_UPDATE`
**Entities**:

```json
{
  "bulk_criteria": {
    "status": "pending",
    "due_date_filter": "overdue"
  },
  "bulk_updates": {
    "priority": "urgent"
  }
}
```

### Bulk Complete

**Intent**: `BULK_COMPLETE`
**Entities**:

```json
{
  "bulk_criteria": {
    "due_date_filter": "today",
    "priority": "high"
  }
}
```

## Examples by Use Case

### Daily Review

```
"show my tasks for today"
"complete all done tasks"
"mark remaining as high priority"
```

### Weekly Cleanup

```
"delete all completed tasks from this week"
"mark all overdue as urgent"
"complete all low priority tasks"
```

### Project Management

```
"show all high priority tasks"
"update all to in_progress status"
"complete all finished tasks"
```

### Quick Triage

```
"mark all today's tasks as urgent"
"complete all easy tasks"
"delete all cancelled tasks"
```

## Best Practices

1. **Be Specific**: Use clear criteria
   - ✅ "delete all completed tasks"
   - ❌ "delete some tasks"

2. **Use Filters**: Combine multiple criteria
   - ✅ "complete all high priority tasks for today"
   - ✅ "delete all completed low priority tasks"

3. **Review Before Bulk Delete**: Check tasks first

   ```
   "show completed tasks"
   [Review list]
   "delete all completed tasks"
   ```

4. **Audit Trail**: All changes are logged
   - View audit logs for accountability
   - Track who changed what and when

## Limitations

- Maximum 100 tasks per bulk operation (safety limit)
- Cannot bulk delete all tasks without criteria
- Cannot undo bulk operations (deleted tasks are soft-deleted)
- Bulk operations respect user permissions

## Technical Details

### Database Queries

Bulk operations use optimized queries:

- Single transaction for all changes
- Efficient filtering with indexes
- Atomic operations (all or nothing)

### Audit Logging

Every task change is logged:

- Task ID and user ID
- Action performed
- Old and new values
- Timestamp

### Performance

- Handles up to 1000 tasks efficiently
- Async processing for speed
- Minimal database round trips

## Troubleshooting

### "No tasks match criteria"

- Check your criteria are correct
- Verify tasks exist with those properties
- Try listing tasks first

### Bulk operation didn't work

- Check intent detection in logs
- Verify API key is set correctly
- Ensure you have permissions

### Too many tasks affected

- Be more specific with criteria
- Use date filters to narrow scope
- Review tasks before bulk operations

## Future Enhancements

Coming soon:

- Undo bulk operations
- Scheduled bulk operations
- Bulk export/import
- Custom bulk actions
- Templates for common operations

---

**Remember**: Bulk operations are powerful! Always verify your criteria before executing large changes.
