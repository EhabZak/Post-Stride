# Timezone Quick Reference

## Import What You Need

```python
from app.utils.timezone_helpers import (
    parse_iso_to_utc,      # Parse ISO string to naive UTC
    format_utc_with_z,     # Format as "2025-10-04T21:10:00Z"
    format_dual_time,      # Get both UTC and local time
    to_utc_naive,          # Normalize any datetime to naive UTC
    utc_to_user_tz         # Convert UTC to user's timezone
)
```

## Common Use Cases

### 1. Receiving datetime from client

```python
@app.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    data = request.get_json()
    scheduled_time_str = data.get('scheduled_time')
    
    # Parse with user's timezone context
    scheduled_time_utc = parse_iso_to_utc(
        scheduled_time_str, 
        current_user.timezone
    )
    
    post.scheduled_time = scheduled_time_utc
    db.session.commit()
```

### 2. Returning datetime to client (simple)

```python
# In model's to_dict() method
def to_dict(self):
    return {
        'scheduled_time': format_utc_with_z(self.scheduled_time),
        'published_at': format_utc_with_z(self.published_at)
    }
```

### 3. Returning datetime with user's local time

```python
@app.route('/api/posts/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    post = Post.query.get(post_id)
    post_data = post.to_dict()
    
    # Add dual time format
    if post.scheduled_time:
        post_data['scheduled_time_detail'] = format_dual_time(
            post.scheduled_time,
            current_user.timezone
        )
    
    return jsonify(post_data)
```

### 4. Scheduling RQ jobs

```python
from app.scheduler import schedule_post_at

# Parse user input to UTC
when_utc = parse_iso_to_utc(iso_string, current_user.timezone)

# Schedule job (expects naive UTC)
job = schedule_post_at(
    post_id=post.id,
    when=when_utc,
    job_id=f"publish_post-{post.id}"
)
```

### 5. Filtering by date range

```python
from_date_str = request.args.get('from')  # "2025-10-04T00:00:00"
to_date_str = request.args.get('to')      # "2025-10-05T00:00:00"

# Convert to UTC for database query
from_date_utc = parse_iso_to_utc(from_date_str, current_user.timezone)
to_date_utc = parse_iso_to_utc(to_date_str, current_user.timezone)

posts = Post.query.filter(
    Post.scheduled_time >= from_date_utc,
    Post.scheduled_time <= to_date_utc
).all()
```

### 6. Creating timestamps (in worker tasks)

```python
from datetime import datetime

# Always use datetime.utcnow() for timestamps
post.published_at = datetime.utcnow()
db.session.commit()
```

## Input Formats Accepted

All these are valid inputs to `parse_iso_to_utc()`:

```python
# Explicit UTC with 'Z'
"2025-10-04T21:10:00Z"

# With timezone offset
"2025-10-04T17:10:00-04:00"  # Eastern Time
"2025-10-04T19:10:00+02:00"  # Amsterdam

# Naive (interpreted using user_tz parameter)
"2025-10-04T17:10:00"  # Interpreted as user's local time
```

## Output Formats

### Simple UTC (with Z)
```python
format_utc_with_z(datetime(2025, 10, 4, 21, 10, 0))
# Returns: "2025-10-04T21:10:00Z"
```

### Dual Time (UTC + Local)
```python
format_dual_time(datetime(2025, 10, 4, 21, 10, 0), "America/New_York")
# Returns:
# {
#     "utc": "2025-10-04T21:10:00Z",
#     "local": "2025-10-04T17:10:00-04:00",
#     "timezone": "America/New_York"
# }
```

## Common Timezones

```python
"UTC"                   # Universal Coordinated Time
"America/New_York"      # Eastern Time
"America/Los_Angeles"   # Pacific Time
"America/Chicago"       # Central Time
"Europe/Amsterdam"      # Amsterdam
"Europe/London"         # London
"Asia/Tokyo"            # Tokyo
"Australia/Sydney"      # Sydney
```

Full list: `pytz.common_timezones`

## Database Convention

**All DateTime columns store naive UTC:**
- `posts.scheduled_time`
- `posts.created_at`
- `posts.updated_at`
- `post_platforms.published_at`
- All scheduled_jobs datetime fields

**Why naive?** 
- SQLite doesn't support true timezone-aware datetimes
- Simpler to work with consistently
- Convert at API boundary only

## Don't Do This ❌

```python
# DON'T use .isoformat() directly
scheduled_time = post.scheduled_time.isoformat()
# Returns: "2025-10-04T21:10:00" (ambiguous!)

# DON'T mix timezone-aware and naive datetimes
from datetime import timezone
now = datetime.now(timezone.utc)  # timezone-aware
# Store as naive UTC instead:
now = datetime.utcnow()  # naive UTC ✅
```

## Do This Instead ✅

```python
# USE format_utc_with_z() for UTC strings
scheduled_time = format_utc_with_z(post.scheduled_time)
# Returns: "2025-10-04T21:10:00Z" (explicit UTC!)

# USE datetime.utcnow() for timestamps
post.created_at = datetime.utcnow()  # naive UTC ✅

# USE parse_iso_to_utc() for parsing inputs
scheduled_time = parse_iso_to_utc(iso_string, current_user.timezone)
```

## Testing Your Code

```python
from datetime import datetime
from app.utils.timezone_helpers import format_utc_with_z, format_dual_time

# Test UTC formatting
dt = datetime(2025, 10, 4, 21, 10, 0)
print(format_utc_with_z(dt))
# Expected: "2025-10-04T21:10:00Z"

# Test dual time formatting
print(format_dual_time(dt, "America/New_York"))
# Expected: {
#   'utc': '2025-10-04T21:10:00Z',
#   'local': '2025-10-04T17:10:00-04:00',
#   'timezone': 'America/New_York'
# }
```

## Debugging Tips

1. **Check if datetime is naive:**
   ```python
   dt.tzinfo is None  # Should be True for database datetimes
   ```

2. **Verify UTC conversion:**
   ```python
   # Before storing
   print(f"UTC: {to_utc_naive(dt)}")
   ```

3. **Inspect API responses:**
   ```bash
   # Should see "Z" suffix or timezone offset
   curl http://localhost:5000/api/posts/1 | jq '.scheduled_time'
   # Expected: "2025-10-04T21:10:00Z"
   ```

4. **Check user timezone:**
   ```python
   print(f"User timezone: {current_user.timezone}")
   # Should be IANA name like "America/New_York"
   ```

## When in Doubt

1. Store in DB: **Naive UTC** (use `datetime.utcnow()`)
2. Parse input: **Use `parse_iso_to_utc()`**
3. Return output: **Use `format_utc_with_z()` or `format_dual_time()`**
4. Schedule jobs: **Naive UTC datetime**
5. User sees: **Local time from `*_detail.local` field**








