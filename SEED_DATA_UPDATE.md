# Seed Data Update - Timezone Support

## Changes Made

Updated `app/seeds/users.py` to include timezone information for all seeded users.

### Updated Code

```python
def seed_users():
    demo = User(
        username='Demo', 
        email='demo@aa.io', 
        password='password',
        timezone='America/New_York'  # Eastern Time (UTC-5/-4)
    )
    marnie = User(
        username='marnie', 
        email='marnie@aa.io', 
        password='password',
        timezone='America/Los_Angeles'  # Pacific Time (UTC-8/-7)
    )
    bobbie = User(
        username='bobbie', 
        email='bobbie@aa.io', 
        password='password',
        timezone='Europe/Amsterdam'  # Central European Time (UTC+1/+2)
    )

    db.session.add(demo)
    db.session.add(marnie)
    db.session.add(bobbie)
    db.session.commit()
```

## Seeded Users

| Username | Email            | Timezone              | UTC Offset       |
|----------|------------------|-----------------------|------------------|
| Demo     | demo@aa.io       | America/New_York      | UTC-5/-4 (DST)   |
| marnie   | marnie@aa.io     | America/Los_Angeles   | UTC-8/-7 (DST)   |
| bobbie   | bobbie@aa.io     | Europe/Amsterdam      | UTC+1/+2 (DST)   |

## Why Different Timezones?

Seeding users with different timezones allows you to test the timezone functionality:

1. **Demo (New York)** - Eastern Time
   - When Demo schedules a post for "5:00 PM", it's stored as "21:00 UTC" (or "22:00 UTC" in winter)
   - Perfect for testing US East Coast users

2. **marnie (Los Angeles)** - Pacific Time
   - When marnie schedules a post for "5:00 PM", it's stored as "01:00 UTC" next day (or "02:00 UTC" in winter)
   - Tests US West Coast timezone handling

3. **bobbie (Amsterdam)** - Central European Time
   - When bobbie schedules a post for "5:00 PM", it's stored as "15:00 UTC" (or "16:00 UTC" in winter)
   - Tests European timezone handling

## Testing Example

### Scenario: All users schedule for "5:00 PM local time on Oct 7, 2025"

**Demo (New York - EDT, UTC-4):**
- Input: `"2025-10-07T17:00:00"` (naive)
- Stored: `"2025-10-07T21:00:00"` (UTC)
- API returns:
  ```json
  {
    "scheduled_time": "2025-10-07T21:00:00Z",
    "scheduled_time_detail": {
      "utc": "2025-10-07T21:00:00Z",
      "local": "2025-10-07T17:00:00-04:00",
      "timezone": "America/New_York"
    }
  }
  ```

**marnie (Los Angeles - PDT, UTC-7):**
- Input: `"2025-10-07T17:00:00"` (naive)
- Stored: `"2025-10-08T00:00:00"` (UTC - next day!)
- API returns:
  ```json
  {
    "scheduled_time": "2025-10-08T00:00:00Z",
    "scheduled_time_detail": {
      "utc": "2025-10-08T00:00:00Z",
      "local": "2025-10-07T17:00:00-07:00",
      "timezone": "America/Los_Angeles"
    }
  }
  ```

**bobbie (Amsterdam - CEST, UTC+2):**
- Input: `"2025-10-07T17:00:00"` (naive)
- Stored: `"2025-10-07T15:00:00"` (UTC - earlier!)
- API returns:
  ```json
  {
    "scheduled_time": "2025-10-07T15:00:00Z",
    "scheduled_time_detail": {
      "utc": "2025-10-07T15:00:00Z",
      "local": "2025-10-07T17:00:00+02:00",
      "timezone": "Europe/Amsterdam"
    }
  }
  ```

### All posts execute at their local 5:00 PM

- **Demo's post** runs at 21:00 UTC = 5:00 PM EDT
- **marnie's post** runs at 00:00 UTC = 5:00 PM PDT (previous day)
- **bobbie's post** runs at 15:00 UTC = 5:00 PM CEST

## Running the Seeds

```bash
# Undo existing seeds
flask seed undo

# Seed with new timezone data
flask seed all
```

## Verification

After seeding, you can verify the timezones are set correctly:

```bash
sqlite3 dev.db "SELECT username, email, timezone FROM users;"
```

Expected output:
```
Demo|demo@aa.io|America/New_York
marnie|marnie@aa.io|America/Los_Angeles
bobbie|bobbie@aa.io|Europe/Amsterdam
```

## API Testing

### Login as Demo
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@aa.io","password":"password"}'
```

### Check User Info (includes timezone)
```bash
curl http://localhost:5000/api/users/me \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

Expected response includes:
```json
{
  "id": 1,
  "username": "Demo",
  "email": "demo@aa.io",
  "timezone": "America/New_York"
}
```

### Create a Post with Naive Time
```bash
curl -X POST http://localhost:5000/api/posts \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "caption": "Test post",
    "scheduled_time": "2025-10-07T17:00:00"
  }'
```

The naive time "17:00:00" will be interpreted as Eastern Time and stored as UTC "21:00:00".

## Important Notes

1. **Existing Users**: If you already have users in your database, they will default to `timezone='UTC'` until they update their profile.

2. **User Settings**: In production, you should add an API endpoint for users to update their timezone:
   ```python
   @app.route('/api/users/me', methods=['PATCH'])
   @login_required
   def update_user_profile():
       data = request.get_json()
       if 'timezone' in data:
           from app.utils.timezone_helpers import validate_timezone
           if validate_timezone(data['timezone']):
               current_user.timezone = data['timezone']
               db.session.commit()
   ```

3. **Frontend Detection**: The frontend should detect the user's timezone and suggest it:
   ```javascript
   const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
   // "America/New_York", "Europe/Amsterdam", etc.
   ```

## Benefits of Diverse Seed Data

- ✅ Tests timezone conversion edge cases
- ✅ Verifies date boundary handling (LA post scheduled for 5 PM becomes next day in UTC)
- ✅ Ensures proper handling of positive and negative UTC offsets
- ✅ Validates API responses show correct local times
- ✅ Demonstrates the system works globally

## Summary

All seed data has been updated to include realistic timezone information. This allows comprehensive testing of the timezone feature without needing to manually update user records.









