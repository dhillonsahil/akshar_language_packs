-- ============================================================
--  akshar language pack — standard schema migration
--  Run this against any DB built with the old 'hindi' table.
--
--  Works for Hindi. Use the same CREATE TABLE block for any
--  new language — just populate 'entries' with your data.
--
--  Usage (command line):
--    sqlite3 akshar_hi.db < migrate_to_standard_schema.sql
--
--  After running, the DB will have:
--    - original 'hindi' table still intact (safe, untouched)
--    - new 'entries' table  (standard schema)
--    - new 'words_search' view (standard schema)
--    - indexes for fast lookup
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA synchronous  = NORMAL;

-- ── Step 1: Create the standard entries table ─────────────
CREATE TABLE IF NOT EXISTS entries (
    word          TEXT NOT NULL,  -- display word in native script
    word_lower    TEXT NOT NULL,  -- lowercase, used for lookup
    english_word  TEXT NOT NULL,  -- primary English equivalent
    romanization  TEXT NOT NULL,  -- latin transliteration (empty if N/A)
    pos           TEXT NOT NULL,  -- part of speech
    sense_num     INTEGER NOT NULL DEFAULT 0,
    ipa           TEXT NOT NULL,  -- IPA pronunciation (empty if N/A)
    definition    TEXT NOT NULL,  -- meaning in native language (can be empty)
    definition_en TEXT NOT NULL   -- meaning in English
);

-- ── Step 2: Populate entries from old hindi table ─────────
--  Maps every column from the old schema to the new one.
--  'definition' (native language) didn't exist before → empty string.
--  'sense_num' didn't exist before → 0 for all rows.
INSERT INTO entries (
    word,
    word_lower,
    english_word,
    romanization,
    pos,
    sense_num,
    ipa,
    definition,
    definition_en
)
SELECT
    hindi_word,                          -- word
    lower(hindi_word),                   -- word_lower
    COALESCE(english_word, ''),          -- english_word
    COALESCE(romanization, ''),          -- romanization
    COALESCE(pos, ''),                   -- pos
    0,                                   -- sense_num
    COALESCE(ipa, ''),                   -- ipa
    '',                                  -- definition (didn't exist before)
    COALESCE(definition_en, '')          -- definition_en
FROM hindi;

-- ── Step 3: Create the standard search view ───────────────
--  The app always queries this view, never the raw table.
--  This is what makes every language pack work the same way.
CREATE VIEW IF NOT EXISTS words_search AS
SELECT
    word                 AS display_word,
    word_lower           AS search_lower,
    lower(romanization)  AS romanization_lower
FROM entries;

-- ── Step 4: Indexes for fast search ──────────────────────
CREATE INDEX IF NOT EXISTS idx_entries_word_lower   ON entries(word_lower);
CREATE INDEX IF NOT EXISTS idx_entries_english_word ON entries(lower(english_word));
CREATE INDEX IF NOT EXISTS idx_entries_romanization ON entries(lower(romanization));

-- ── Step 5: Verify ────────────────────────────────────────
SELECT
    'entries rows'     AS check_name,
    COUNT(*)           AS result
FROM entries
UNION ALL
SELECT
    'words_search rows',
    COUNT(*)
FROM words_search
UNION ALL
SELECT
    'hindi rows (original)',
    COUNT(*)
FROM hindi;