import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('one-more-day-habits')

# ─── Test users ───
users = ['aksana-dev', 'melody-dev', 'nilu-dev', 'tami-dev']

for user in users:

    # ─── USER profile item ───
    table.put_item(Item={
        'userId': user,
        'SK': 'USER#profile',
        'email': f'{user.split("-")[0]}@example.com',
        'name': user.split('-')[0].capitalize(),
        'createdAt': '2026-06-01T10:00:00Z'
    })

    # ─── HABIT items ───
    table.put_item(Item={
        'userId': user,
        'SK': 'HABIT#seed001',
        'habitId': 'seed001',
        'habitName': 'Drink water',
        'category': 'Health',
        'active': True,
        'streakCount': 5,
        'longestStreak': 7,
        'lastCompletedDate': '2026-06-09',
        'createdAt': '2026-06-01T10:00:00Z',
        'deletedAt': None
    })

    table.put_item(Item={
        'userId': user,
        'SK': 'HABIT#seed002',
        'habitId': 'seed002',
        'habitName': 'LeetCode',
        'category': 'Learning',
        'active': True,
        'streakCount': 1,
        'longestStreak': 5,
        'lastCompletedDate': '2026-06-08',
        'createdAt': '2026-06-01T10:00:00Z',
        'deletedAt': None
    })

    table.put_item(Item={
        'userId': user,
        'SK': 'HABIT#seed003',
        'habitId': 'seed003',
        'habitName': 'Meditate',
        'category': 'Mind',
        'active': True,
        'streakCount': 14,
        'longestStreak': 14,
        'lastCompletedDate': '2026-06-09',
        'createdAt': '2026-06-01T10:00:00Z',
        'deletedAt': None
    })

    # ─── CHECKIN items ───
    checkins = [
        ('seed001', '2026-06-05', 'Drank 8 cups today'),
        ('seed001', '2026-06-06', None),
        ('seed001', '2026-06-07', None),
        ('seed001', '2026-06-08', None),
        ('seed001', '2026-06-09', 'Staying hydrated'),
        ('seed002', '2026-06-08', 'Completed two problems'),
        ('seed002', '2026-06-09', None),
        ('seed003', '2026-06-01', None),
        ('seed003', '2026-06-02', None),
        ('seed003', '2026-06-03', None),
        ('seed003', '2026-06-04', None),
        ('seed003', '2026-06-05', None),
        ('seed003', '2026-06-06', None),
        ('seed003', '2026-06-07', None),
        ('seed003', '2026-06-08', None),
        ('seed003', '2026-06-09', 'Feeling calm'),
    ]

    for habitId, date, notes in checkins:
        table.put_item(Item={
            'userId': user,
            'SK': f'CHECKIN#{habitId}#{date}',
            'habitId': habitId,
            'date': date,
            'completed': True,
            'notes': notes,
            'timestamp': f'{date}T20:00:00Z'
        })

print("Seed data loaded successfully")