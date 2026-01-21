# Session to Project Migration Guide

## Overview

TokenDance is migrating from a Session-centric to Project-First architecture. This guide helps you migrate your code and understand the changes.

## Timeline

- **Now**: Both Session and Project APIs work. Session API shows deprecation warnings.
- **v2.0** (planned): Session API will be removed.

## Key Concepts

### Before (Session-centric)
```
Workspace → Session → Messages
                   → Artifacts
```

### After (Project-First)
```
Workspace → Project → Conversations → Messages
                   → Artifacts
                   → Context (decisions, failures, findings)
                   → Versions
```

## API Migration

### Creating a task

**Old (deprecated)**:
```http
POST /api/v1/sessions
{
  "workspace_id": "...",
  "title": "My Task"
}
```

**New**:
```http
POST /api/v1/projects
{
  "workspace_id": "...",
  "intent": "Analyze competitor market share",
  "project_type": "research"  // optional
}
```

### Listing tasks

**Old (deprecated)**:
```http
GET /api/v1/sessions?workspace_id=...
```

**New**:
```http
GET /api/v1/projects?workspace_id=...&status=in_progress
```

### Getting messages

**Old (deprecated)**:
```http
GET /api/v1/sessions/{session_id}/messages
```

**New**:
```http
GET /api/v1/projects/{project_id}/conversations
# Then get messages from a specific conversation
```

### Chat/Execute

**Old**:
SSE endpoint with session_id

**New**:
```http
POST /api/v1/projects/{project_id}/chat
{
  "message": "...",
  "conversation_id": "...",  // optional, auto-creates if not provided
  "selection": {             // optional, for in-place editing
    "artifact_id": "...",
    "selected_text": "...",
    "selection_range": {"start": 0, "end": 50}
  }
}
```

## Frontend Migration

### Store Changes

**Old**:
```typescript
import { useSessionStore } from '@/stores/session'
const sessionStore = useSessionStore()
await sessionStore.createSession({ workspace_id, title })
```

**New**:
```typescript
import { useProjectStore } from '@/stores/project'
const projectStore = useProjectStore()
await projectStore.createProject({ workspace_id, intent })
```

### Route Changes

**Old**:
```
/execution/:sessionId
```

**New**:
```
/project/:projectId
```

## Data Migration

### Running the Migration Script

```bash
cd backend

# Preview changes (recommended first)
uv run python scripts/migrate_session_to_project.py --dry-run

# Run actual migration
uv run python scripts/migrate_session_to_project.py
```

### What Gets Migrated

| Session Field | Project Field |
|--------------|---------------|
| id | (new UUID) |
| workspace_id | workspace_id |
| title | title |
| status | status (mapped) |
| skill_id | settings.skill_id |
| first user message | intent |
| tool call errors | context.failures |

### Status Mapping

| Session Status | Project Status |
|---------------|----------------|
| pending | draft |
| active/running | in_progress |
| completed | completed |
| failed | in_progress |
| cancelled/archived | archived |

## Benefits of Project-First

1. **Persistent Context**: Decisions and failures are preserved across conversations
2. **Version Control**: Artifacts have version history
3. **In-place Editing**: Select text → Ask AI → Replace
4. **Better Organization**: Projects group related work together

## FAQ

**Q: Will my old data be lost?**
A: No. The migration creates new Project records and links existing data. Session records are preserved for reference.

**Q: Can I still use the old API?**
A: Yes, until v2.0. But it will return deprecation warnings.

**Q: What if migration fails?**
A: The script is idempotent - you can run it multiple times. Failed sessions are logged and can be retried.

## Support

For issues with migration, please open a GitHub issue with the `migration` label.
