import boto3
from datetime import datetime, timedelta
import random

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('one-more-day-habits')

# 30-day history window ending today
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Your real account
users = {
    '5408d408-2061-7034-371c-28405909a258': {
        'email': 'tamigaertner@outlook.com',
        'name': 'Tami',
        'time': '07:00',
        'tz': 'EST'
    },
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

def every_day(d): return True
def weekdays_only(d): return d.weekday() < 5
def struggling(d): return d.weekday() in [1, 3] and d.day % 3 != 0
def strong_then_break(d, start): 
    days = (d - start).days
    return days < 20 or (days > 25 and d.weekday() < 5)
def high_compliance(d): return not (d.weekday() == 6 and d.day % 3 == 0)
def weekends_only(d): return d.weekday() >= 5

user_habits = {
    '5408d408-2061-7034-371c-28405909a258': [
        {'id': 'tami001', 'name': 'LeetCode', 'category': 'Learning',
         'fn': lambda d: weekdays_only(d)},
        {'id': 'tami002', 'name': 'Walk 10k steps', 'category': 'Fitness',
         'fn': lambda d: high_compliance(d)},
        {'id': 'tami003', 'name': 'No social media before noon', 'category': 'Mind',
         'fn': lambda d: weekdays_only(d) and d.day % 3 != 0},
        {'id': 'tami004', 'name': 'Review class notes', 'category': 'Learning',
         'fn': lambda d: weekdays_only(d)},
        {'id': 'tami005', 'name': 'No unnecessary spending', 'category': 'Finance',
         'fn': lambda d: struggling(d)},
        {'id': 'tami006', 'name': 'Work on capstone', 'category': 'Productivity',
         'fn': lambda d: every_day(d)},
        {'id': 'tami007', 'name': 'Drink 8 glasses of water', 'category': 'Health',
         'fn': lambda d: high_compliance(d)},
        {'id': 'tami008', 'name': 'Read 20 minutes', 'category': 'Mind',
         'fn': lambda d: d.weekday() < 6},
    ],
}
# Add this to seed_tami.py — real habits with real UUIDs

real_habits = [
    {'id': '343880e2-d401-4998-b8e3-551da632e309', 'name': 'Leetcode in Java', 'category': 'Learning',
     'fn': lambda d: weekdays_only(d)},
    {'id': '4f4b8935-7136-45d6-b40a-e1f4a8126717', 'name': 'Walking', 'category': 'Fitness',
     'fn': lambda d: high_compliance(d)},
    {'id': 'cdc68b93-1b59-423f-9260-917677effe0e', 'name': 'AWS Cloud Study', 'category': 'Learning',
     'fn': lambda d: weekdays_only(d)},
    {'id': 'f9f78b41-1fd2-440c-94ea-b2a9d5402e4a', 'name': 'Morning meditation', 'category': 'Mind',
     'fn': lambda d: struggling(d)},
]
total_checkins = 0
total_habits = 0

for user, prefs in users.items():
    print(f"\nSeeding {prefs['name']} ({user})...")

    table.put_item(Item={
        'userId': user,
        'SK': 'USER#profile',
        'email': prefs['email'],
        'name': prefs['name'],
        'preferredReminderTime': prefs['time'],
        'timezone': prefs['tz'],
        'createdAt': start_date.strftime('%Y-%m-%dT10:00:00Z')
    })

    habits = user_habits[user] + real_habits

    for habit in habits:
        habit_id = habit['id']
        checkin_dates = set()

        current = start_date
        while current <= end_date:
            if habit['fn'](current):
                checkin_dates.add(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        dates_sorted = sorted(list(checkin_dates))

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

        yesterday = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')
        today = end_date.strftime('%Y-%m-%d')
        current_streak = temp_streak if (today in checkin_dates or yesterday in checkin_dates) else 0
        last_completed = dates_sorted[-1] if dates_sorted else None

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
            'createdAt': start_date.strftime('%Y-%m-%dT10:00:00Z'),
            'deletedAt': None
        })

        print(f"  HABIT: {habit['name']} — {len(dates_sorted)} checkins, streak: {current_streak}, longest: {longest_streak}")
        total_habits += 1

print(f"\n✅ Seed complete")
print(f"   1 user: tamigaertner@outlook.com")
print(f"   {total_habits} habits")
print(f"   {total_checkins} check-in records")
print(f"   30 days of history")