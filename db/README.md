# Jarvis Database

This directory contains the SQLite database for conversation memory.

## Setup

Run the init script to create the database:

```bash
python db/init.py
```

## Files

- `init.py` - Database initialization script (creates schema)
- `jarvis.db` - SQLite database (gitignored, created by init.py)

## Schema

### messages

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| role | TEXT | 'user' or 'assistant' |
| content | TEXT | Message content |
| created_at | TIMESTAMP | When message was stored |
