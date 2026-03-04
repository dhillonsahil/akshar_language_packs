import sqlite3
import os
import sys

DB_PATH = "akshar_th.db"

# ── Check file exists ─────────────────────────────────────
if not os.path.exists(DB_PATH):
    print(f"Error: {DB_PATH} not found in current directory.")
    print(f"Run this script from the same folder as {DB_PATH}")
    sys.exit(1)

print(f"Opening {DB_PATH}...")
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── Check old schema exists ───────────────────────────────
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hindi'")
if not cur.fetchone():
    print("Error: 'hindi' table not found. Is this the right DB?")
    conn.close()
    sys.exit(1)

old_count = cur.execute("SELECT COUNT(*) FROM hindi").fetchone()[0]
print(f"Found {old_count:,} rows in hindi table.")

# ── Check if already migrated ─────────────────────────────
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entries'")
if cur.fetchone():
    existing = cur.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    print(f"'entries' table already exists with {existing:,} rows.")
    ans = input("Re-run migration and replace it? (y/n): ").strip().lower()
    if ans != 'y':
        print("Aborted.")
        conn.close()
        sys.exit(0)
    print("Dropping existing entries table and words_search view...")
    cur.execute("DROP VIEW  IF EXISTS words_search")
    cur.execute("DROP TABLE IF EXISTS entries")
    conn.commit()

# ── Step 1: Create entries table ──────────────────────────
print("Creating entries table...")
cur.execute("""
    CREATE TABLE entries (
        word          TEXT NOT NULL,
        word_lower    TEXT NOT NULL,
        english_word  TEXT NOT NULL,
        romanization  TEXT NOT NULL,
        pos           TEXT NOT NULL,
        sense_num     INTEGER NOT NULL DEFAULT 0,
        ipa           TEXT NOT NULL,
        definition    TEXT NOT NULL,
        definition_en TEXT NOT NULL
    )
""")

# ── Step 2: Migrate data ──────────────────────────────────
print("Migrating data from hindi → entries...")
cur.execute("""
    INSERT INTO entries (
        word, word_lower, english_word, romanization,
        pos, sense_num, ipa, definition, definition_en
    )
    SELECT
        hindi_word,
        lower(hindi_word),
        COALESCE(english_word, ''),
        COALESCE(romanization, ''),
        COALESCE(pos, ''),
        0,
        COALESCE(ipa, ''),
        '',
        COALESCE(definition_en, '')
    FROM hindi
""")
conn.commit()

new_count = cur.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
print(f"Inserted {new_count:,} rows into entries.")

# ── Step 3: Create words_search view ─────────────────────
print("Creating words_search view...")
cur.execute("""
    CREATE VIEW words_search AS
    SELECT
        word                AS display_word,
        word_lower          AS search_lower,
        lower(romanization) AS romanization_lower
    FROM entries
""")
conn.commit()

# ── Step 4: Create indexes ────────────────────────────────
print("Creating indexes...")
cur.execute("CREATE INDEX idx_entries_word_lower   ON entries(word_lower)")
cur.execute("CREATE INDEX idx_entries_english_word ON entries(lower(english_word))")
cur.execute("CREATE INDEX idx_entries_romanization ON entries(lower(romanization))")
conn.commit()

# ── Step 5: Verify ────────────────────────────────────────
print()
print("── Verification ─────────────────────────────────────")
hindi_rows   = cur.execute("SELECT COUNT(*) FROM hindi").fetchone()[0]
entries_rows = cur.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
view_rows    = cur.execute("SELECT COUNT(*) FROM words_search").fetchone()[0]
print(f"  hindi table (original) : {hindi_rows:,}")
print(f"  entries table (new)    : {entries_rows:,}")
print(f"  words_search view      : {view_rows:,}")

if hindi_rows == entries_rows == view_rows:
    print()
    print("✓ Migration successful. All row counts match.")
    print(f"✓ {DB_PATH} is ready to upload to GitHub.")
else:
    print()
    print("✗ Row count mismatch — something went wrong.")

# ── Sample check ──────────────────────────────────────────
print()
print("── Sample rows from entries ─────────────────────────")
rows = cur.execute("""
    SELECT word, english_word, romanization, pos, ipa
    FROM entries LIMIT 5
""").fetchall()
for r in rows:
    print(f"  {r[0]:<20} | {r[1]:<15} | {r[2]:<15} | {r[3]:<10} | {r[4]}")

print("Dropping old hindi table...")
cur.execute("DROP TABLE hindi")
conn.commit()
print("✓ hindi table removed.")

conn.close()
print()
print("Done.")