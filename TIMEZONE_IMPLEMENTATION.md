# Timezone Implementation Guide

## Overview

This application follows a comprehensive timezone strategy to handle scheduling and publishing of social media posts across different user timezones.

## Golden Rules

1. **Store ALL datetimes in DB as naive UTC** (no tzinfo)
2. **Remember each user's timezone** (IANA name in `users.timezone` column)
3. **Interpret naive timestamps using user's timezone**, then convert to UTC
4. **Return both UTC and user-local time** in API responses

## Implementation Details

### 1. Database Storage

All `DateTime` columns store **naive UTC** timestamps:
- `posts.scheduled_time`
- `posts.created_at`
- `posts.updated_at`
- `post_platforms.published_at`
- `scheduled_jobs.*` (all datetime fields)

**Why naive?** SQLite and many databases don't have true timezone-aware datetime types. By convention, we store all times as naive UTC and handle timezone conversion in the application layer.

### 2. User Timezone Storage

Each user has a `timezone` field storing an IANA timezone name (e.g., "America/New_York", "Europe/Amsterdam", "UTC").

**Default:** UTC

**To update a user's timezone:**
```python
user.timezone = "America/New_York"
db.session.commit()
```

### 3. Parsing Input Datetimes

When receiving datetime strings from the client, use `parse_iso_to_utc()`:

```python
from app.utils.timezone_helpers import parse_iso_to_utc

# Parses ISO 8601 string, interprets naive times using user timezone
utc_dt = parse_iso_to_utc("2025-10-04T21:10:00", current_user.timezone)
# or with explicit UTC marker
utc_dt = parse_iso_to_utc("2025-10-04T21:10:00Z", current_user.timezone)
```

**Behavior:**
- `"2025-10-04T21:10:00Z"` → interpreted as UTC
- `"2025-10-04T21:10:00-04:00"` → interpreted as Eastern Time
- `"2025-10-04T21:10:00"` (naive) → interpreted using `user_tz` parameter

### 4. Serializing Output Datetimes

#### Simple UTC Format (with 'Z')

All model `to_dict()` methods use `format_utc_with_z()`:

```python
from app.utils.timezone_helpers import format_utc_with_z

# Returns: "2025-10-04T21:10:00Z"
iso_string = format_utc_with_z(post.scheduled_time)
```

#### Dual Time Format (UTC + Local)

For detailed views, provide both UTC and user's local time:

```python
from app.utils.timezone_helpers import format_dual_time

time_detail = format_dual_time(post.scheduled_time, current_user.timezone)
# Returns:
# {
#     "utc": "2025-10-04T21:10:00Z",
#     "local": "2025-10-04T17:10:00-04:00",
#     "timezone": "America/New_York"
# }
```

### 5. API Response Format

All API responses now include timezone-aware datetime fields:

**Simple format (UTC with Z):**
```json
{
  "scheduled_time": "2025-10-04T21:10:00Z",
  "published_at": "2025-10-04T21:15:30Z"
}
```

**Detailed format (UTC + local):**
```json
{
  "scheduled_time": "2025-10-04T21:10:00Z",
  "scheduled_time_detail": {
    "utc": "2025-10-04T21:10:00Z",
    "local": "2025-10-04T17:10:00-04:00",
    "timezone": "America/New_York"
  }
}
```

### 6. Scheduling Jobs

When scheduling RQ jobs, always pass naive UTC datetimes:

```python
from app.scheduler import schedule_post_at
from app.utils.timezone_helpers import parse_iso_to_utc

# Parse user input to UTC
when_utc = parse_iso_to_utc(iso_string, current_user.timezone)

# Schedule job (expects naive UTC)
job = schedule_post_at(
    post_id=post.id,
    when=when_utc,
    job_id=f"publish_post-{post.id}-{int(when_utc.timestamp())}"
)
```

## File Structure

### Core Files

1. **`app/utils/timezone_helpers.py`** - All timezone conversion utilities
2. **`app/models/user.py`** - User model with `timezone` field
3. **`app/api/posts_routes.py`** - Routes with timezone-aware parsing and formatting
4. **`app/tasks.py`** - Worker tasks (uses `datetime.utcnow()` consistently)
5. **`app/scheduler.py`** - Job scheduling helpers

### Model Updates

All models now use `format_utc_with_z()` in their `to_dict()` methods:
- `Post`
- `PostPlatform`
- `ScheduledJob`

## Common Patterns

### Accepting datetime from client

```python
from app.utils.timezone_helpers import parse_iso_to_utc

scheduled_time_str = request.json.get('scheduled_time')
scheduled_time_utc = parse_iso_to_utc(scheduled_time_str, current_user.timezone)
post.scheduled_time = scheduled_time_utc
db.session.commit()
```

### Returning datetime to client

```python
from app.utils.timezone_helpers import format_dual_time, format_utc_with_z

# Simple UTC format
response = {
    'scheduled_time': format_utc_with_z(post.scheduled_time)
}

# Detailed format with user's local time
response = {
    'scheduled_time': format_utc_with_z(post.scheduled_time),
    'scheduled_time_detail': format_dual_time(post.scheduled_time, current_user.timezone)
}
```

### Filtering by datetime range

```python
from app.utils.timezone_helpers import parse_iso_to_utc

from_date_str = request.args.get('from')
to_date_str = request.args.get('to')

# Convert to UTC for database query
from_date_utc = parse_iso_to_utc(from_date_str, current_user.timezone)
to_date_utc = parse_iso_to_utc(to_date_str, current_user.timezone)

posts = Post.query.filter(
    Post.scheduled_time >= from_date_utc,
    Post.scheduled_time <= to_date_utc
).all()
```

## Migration Applied

The `users` table now has a `timezone` column:

```sql
ALTER TABLE users ADD COLUMN timezone VARCHAR(64) DEFAULT 'UTC' NOT NULL;
```

Existing users will have `timezone='UTC'` by default.

## Testing Timezone Handling

### Example User Scenarios

**User in New York (UTC-4 during DST):**
- User sets schedule: "2025-10-04T17:10:00" (naive, no timezone)
- System interprets as: "2025-10-04T17:10:00-04:00" (Eastern)
- Stored in DB as: "2025-10-04T21:10:00" (naive UTC)
- Returned to user: 
  - `scheduled_time`: "2025-10-04T21:10:00Z"
  - `scheduled_time_detail.local`: "2025-10-04T17:10:00-04:00"

**User in Amsterdam (UTC+2 during DST):**
- User sets schedule: "2025-10-04T19:10:00" (naive)
- System interprets as: "2025-10-04T19:10:00+02:00" (Amsterdam)
- Stored in DB as: "2025-10-04T17:10:00" (naive UTC)
- Returned to user:
  - `scheduled_time`: "2025-10-04T17:10:00Z"
  - `scheduled_time_detail.local`: "2025-10-04T19:10:00+02:00"

### Test with curl

```bash
# Create a post with explicit UTC time
curl -X POST http://localhost:5000/api/posts \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Test post",
    "scheduled_time": "2025-10-04T21:10:00Z"
  }'

# Create a post with timezone offset
curl -X POST http://localhost:5000/api/posts \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Test post",
    "scheduled_time": "2025-10-04T17:10:00-04:00"
  }'

# Create a post with naive time (interpreted using user's timezone)
curl -X POST http://localhost:5000/api/posts \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Test post",
    "scheduled_time": "2025-10-04T17:10:00"
  }'
```

## Frontend Integration

The frontend should:

1. **Detect user's timezone** and allow them to update it in settings
2. **Display times in user's local timezone** using `scheduled_time_detail.local`
3. **Send times with timezone offset** when possible (e.g., `"2025-10-04T17:10:00-04:00"`)
4. **Show both UTC and local time** for clarity in detailed views

### Recommended Frontend Approach

```javascript
// Get user's timezone
const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
// e.g., "America/New_York"

// Update user's timezone on backend
fetch('/api/users/me', {
  method: 'PATCH',
  body: JSON.stringify({ timezone: userTimezone })
});

// When creating/editing posts, send ISO with offset
const scheduledTime = new Date('2025-10-04T17:10:00');
const isoWithOffset = scheduledTime.toISOString(); // Includes timezone
// e.g., "2025-10-04T21:10:00.000Z"

// Display times using the local field
const localTime = response.scheduled_time_detail.local;
// "2025-10-04T17:10:00-04:00"
```

## Benefits

✅ **No timezone ambiguity** - All times are explicitly UTC in DB  
✅ **User-friendly** - Users see times in their local timezone  
✅ **Accurate scheduling** - RQ jobs run at correct UTC time  
✅ **Flexible** - Supports naive inputs (interpreted with user TZ) and explicit TZ  
✅ **Clear API** - Returns both UTC and local representations  
✅ **Standardized** - All datetimes follow ISO 8601 with 'Z' or offset

## Dependencies Added

- `pytz==2024.1` - For IANA timezone conversions

Install with:
```bash
pip install -r requirements.txt
```

