import boto3
from datetime import datetime, timedelta
import random

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('one-more-day-habits')

# 60-day history window
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# ─── User profiles ───
# Keys are real Cognito `sub` values — pulled via:
# aws cognito-idp list-users --user-pool-id $COGNITO_USER_POOL_ID \
#   --query "Users[].{email:Attributes[?Name=='email']|[0].Value,sub:Attributes[?Name=='sub']|[0].Value}"
users = {
    'f458b498-e0c1-7019-2c53-f757e908294a': {'email': 'aksana@example.com', 'name': 'Aksana', 'time': '08:00', 'tz': 'EST'},
    '2458b438-1041-70a1-b2d3-15c83f530be1': {'email': 'melody@example.com', 'name': 'Melody', 'time': '20:00', 'tz': 'PST'},
    'e4e8a428-f021-701f-d94c-dad182f1144b': {'email': 'nilu@example.com',   'name': 'Nilu',   'time': '07:30', 'tz': 'GMT'},
    '94b87438-7001-701f-bfc8-d433f4b4442d': {'email': 'tami@example.com',   'name': 'Tami',   'time': '18:00', 'tz': 'EST'},
}

sample_notes = [
    "Feeling great today!",
    "Completed right before lunch.",
    "Hard to get through it, but pushed through.",
    "Done early in the morning.",
    "Routine is feeling solid.",
    "Proud of myself today.",
    "Needed this.",
    "Tough day but did it.",
]

# ─────────────────────────────────────────
# HABIT CONFIGS PER USER
# Each user has 6 habits — different categories, different patterns
# Pattern key: function(date) -> bool (True = completed that day)
# ─────────────────────────────────────────

def every_day(d): return True
def weekdays_only(d): return d.weekday() < 5
def high_compliance_breaks_sundays(d): return not (d.weekday() == 6 and d.day % 2 == 0)
def eleven_on_three_off(d, start): return (d - start).days % 14 < 11 and d.weekday() < 5
def struggling(d): return d.weekday() in [1, 3] and d.day % 3 != 0
def weekends_only(d): return d.weekday() >= 5
def declining(d, start): days = (d - start).days; return days < 30 and d.weekday() < 5
def strong_then_break(d, start): days = (d - start).days; return days < 20 or (days > 35 and d.weekday() < 5)

user_habits = {
    'f458b498-e0c1-7019-2c53-f757e908294a': [  # Aksana
        # Health dominant — crushing water and sleep, struggling with fitness
        {'id': 'aksana001', 'name': 'Drink 8 glasses of water', 'category': 'Health',
         'fn': lambda d: high_compliance_breaks_sundays(d)},
        {'id': 'aksana002', 'name': 'Sleep 8 hours', 'category': 'Health',
         'fn': lambda d: d.weekday() < 6},
        {'id': 'aksana003', 'name': 'Run 3 miles', 'category': 'Fitness',
         'fn': lambda d: struggling(d)},
        {'id': 'aksana004', 'name': 'Take vitamins', 'category': 'Health',
         'fn': lambda d: every_day(d)},
        {'id': 'aksana005', 'name': 'Stretch 10 minutes', 'category': 'Fitness',
         'fn': lambda d: d.weekday() in [0, 2, 4]},
        {'id': 'aksana006', 'name': 'No alcohol', 'category': 'Health',
         'fn': lambda d: every_day(d)},
    ],
    '2458b438-1041-70a1-b2d3-15c83f530be1': [  # Melody
        # Learning + Mind dominant — strong LeetCode, inconsistent meditation
        {'id': 'melody001', 'name': 'LeetCode', 'category': 'Learning',
         'fn': lambda d: weekdays_only(d)},
        {'id': 'melody002', 'name': 'Read 20 minutes', 'category': 'Mind',
         'fn': lambda d: d.weekday() < 6},
        {'id': 'melody003', 'name': 'Meditate', 'category': 'Mind',
         'fn': lambda d, s=start_date: eleven_on_three_off(d, s)},
        {'id': 'melody004', 'name': 'Study flashcards', 'category': 'Learning',
         'fn': lambda d: weekdays_only(d) and d.day % 2 == 0},
        {'id': 'melody005', 'name': 'Journal', 'category': 'Mind',
         'fn': lambda d: struggling(d)},
        {'id': 'melody006', 'name': 'Watch a tutorial', 'category': 'Learning',
         'fn': lambda d: d.weekday() in [1, 3, 5]},
    ],
    'e4e8a428-f021-701f-d94c-dad182f1144b': [  # Nilu
        # Productivity dominant — perfect on planning, weak on finance
        {'id': 'nilu001', 'name': 'Plan tomorrow', 'category': 'Productivity',
         'fn': lambda d: every_day(d)},
        {'id': 'nilu002', 'name': 'Deep work block', 'category': 'Productivity',
         'fn': lambda d: weekdays_only(d)},
        {'id': 'nilu003', 'name': 'Log expenses', 'category': 'Finance',
         'fn': lambda d: struggling(d)},
        {'id': 'nilu004', 'name': 'Clear inbox', 'category': 'Productivity',
         'fn': lambda d: d.weekday() < 6},
        {'id': 'nilu005', 'name': 'Check budget', 'category': 'Finance',
         'fn': lambda d: d.weekday() == 0},
        {'id': 'nilu006', 'name': 'Work on capstone', 'category': 'Productivity',
         'fn': lambda d: every_day(d)},
    ],
    '94b87438-7001-701f-bfc8-d433f4b4442d': [  # Tami
        # Mixed — strong Learning, inconsistent Mind and Finance
        {'id': 'tami001', 'name': 'LeetCode', 'category': 'Learning',
         'fn': lambda d, s=start_date: strong_then_break(d, s)},
        {'id': 'tami002', 'name': 'Walk 10k steps', 'category': 'Fitness',
         'fn': lambda d: d.weekday() < 6},
        {'id': 'tami003', 'name': 'No social media before noon', 'category': 'Mind',
         'fn': lambda d: weekdays_only(d) and d.day % 3 != 0},
        {'id': 'tami004', 'name': 'Review class notes', 'category': 'Learning',
         'fn': lambda d: weekdays_only(d)},
        {'id': 'tami005', 'name': 'No unnecessary spending', 'category': 'Finance',
         'fn': lambda d: struggling(d)},
        {'id': 'tami006', 'name': 'Work on capstone', 'category': 'Productivity',
         'fn': lambda d: every_day(d)},
    ],
}

# ─────────────────────────────────────────
# WRITE ALL DATA
# ─────────────────────────────────────────

total_checkins = 0
total_habits = 0

for user, prefs in users.items():
    print(f"\nSeeding {prefs['name']} ({user})...")

    # USER profile
    table.put_item(Item={
        'userId': user,
        'SK': 'USER#profile',
        'email': prefs['email'],
        'name': prefs['name'],
        'preferredReminderTime': prefs['time'],
        'timezone': prefs['tz'],
        'createdAt': '2026-04-13T10:00:00Z'
    })

    habits = user_habits[user]

    for habit in habits:
        habit_id = habit['id']
        checkin_dates = set()

        # Generate checkin dates using the habit's pattern function
        current = start_date
        while current <= end_date:
            if habit['fn'](current):
                checkin_dates.add(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        dates_sorted = sorted(list(checkin_dates))

        # Write CHECKIN items
        for i, date_str in enumerate(dates_sorted):
            has_note = (i % 3 == 0)
            table.put_item(Item={
                'userId': user,
                'SK': f'CHECKIN#{habit_id}#{date_str}',
                'habitId': habit_id,
                'date': date_str,
                'completed': True,
                'notes': sample_notes[i % len(sample_notes)] if has_note else None,
                'timestamp': f'{date_str}T20:00:00Z'
            })
            total_checkins += 1

        # Calculate streaks mathematically
        longest_streak = 0
        temp_streak = 0
        current = start_date
        while current <= end_date:
            if current.strftime('%Y-%m-%d') in checkin_dates:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
            current += timedelta(days=1)

        # Current streak — check if active as of today or yesterday
        yesterday = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')
        today = end_date.strftime('%Y-%m-%d')
        current_streak = temp_streak if (today in checkin_dates or yesterday in checkin_dates) else 0
        last_completed = dates_sorted[-1] if dates_sorted else None

        # Write HABIT item
        table.put_item(Item={
            'userId': user,
            'SK': f'HABIT#{habit_id}',
            'habitId': habit_id,
            'habitName': habit['name'],
            'category': habit['category'],
            'active': True,
            'streakCount': current_streak,
            'longestStreak': longest_streak,
            'lastCompletedDate': last_completed,
            'createdAt': '2026-04-13T10:00:00Z',
            'deletedAt': None
        })

        print(f"  HABIT: {habit['name']} — {len(dates_sorted)} checkins, streak: {current_streak}, longest: {longest_streak}")
        total_habits += 1

print(f"\n✅ Seed data loaded successfully")
print(f"   4 users (real Cognito sub values)")
print(f"   {total_habits} habits (6 per user)")
print(f"   {total_checkins} check-in records")
print(f"   60 days of history (2026-04-13 to 2026-06-12)")