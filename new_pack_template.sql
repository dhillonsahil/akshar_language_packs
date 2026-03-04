-- ============================================================
--  akshar language pack — new pack template
--
--  Use this to build any language pack from scratch.
--  Replace the example INSERT rows with your actual data.
--
--  Steps:
--  1. Copy this file, rename it e.g. build_fr.sql
--  2. Replace the INSERT rows with your language data
--  3. Run: sqlite3 akshar_fr.db < build_fr.sql
--  4. Upload akshar_fr.db to GitHub releases
--  5. Add entry to manifest.json
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA synchronous  = NORMAL;

-- ── Standard entries table (same for every language) ──────
CREATE TABLE IF NOT EXISTS entries (
    word          TEXT NOT NULL,  -- native script word  (bonjour, 你好, привет)
    word_lower    TEXT NOT NULL,  -- lowercase for lookup
    english_word  TEXT NOT NULL,  -- English equivalent  (hello)
    romanization  TEXT NOT NULL,  -- latin spelling      (pinyin, romaji — empty if not needed)
    pos           TEXT NOT NULL,  -- noun / verb / adjective / adverb / other
    sense_num     INTEGER NOT NULL DEFAULT 0,  -- 0,1,2... for multiple meanings of same word
    ipa           TEXT NOT NULL,  -- IPA pronunciation  (empty if not available)
    definition    TEXT NOT NULL,  -- meaning in native language (empty is fine)
    definition_en TEXT NOT NULL   -- meaning in English
);

-- ── Standard search view (same for every language) ────────
CREATE VIEW IF NOT EXISTS words_search AS
SELECT
    word                AS display_word,
    word_lower          AS search_lower,
    lower(romanization) AS romanization_lower
FROM entries;

-- ── Indexes ───────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_entries_word_lower   ON entries(word_lower);
CREATE INDEX IF NOT EXISTS idx_entries_english_word ON entries(lower(english_word));
CREATE INDEX IF NOT EXISTS idx_entries_romanization ON entries(lower(romanization));

-- ── Insert your data below ────────────────────────────────
--
-- Column order:
--   word, word_lower, english_word, romanization, pos, sense_num, ipa, definition, definition_en
--
-- Rules:
--   - word_lower  = lower(word)         always
--   - romanization = '' if not needed   (French, Spanish, Russian don't need it)
--   - romanization = pinyin             for Chinese
--   - romanization = romaji             for Japanese
--   - romanization = latin transliteration for Hindi, Arabic, etc.
--   - sense_num starts at 0, increment for each extra meaning of the SAME word
--   - definition   can be ''            (English gloss in definition_en is enough)
--   - definition_en must not be ''      (this is what shows on the English entry page)
--   - english_word must not be ''       (this is the cross-language pivot)
--
-- ── French example rows ───────────────────────────────────
INSERT INTO entries VALUES
--  word        word_lower   english_word  roman  pos      sense ipa            definition  definition_en
  ('bonjour',  'bonjour',   'hello',      '',    'interjection', 0, '/bɔ̃ʒuʁ/', '',  'A greeting used during the day'),
  ('bonsoir',  'bonsoir',   'good evening','',   'interjection', 0, '/bɔ̃swaʁ/', '', 'A greeting used in the evening'),
  ('merci',    'merci',     'thank you',  '',    'interjection', 0, '/mɛʁsi/',  '',  'An expression of gratitude'),
  ('chat',     'chat',      'cat',        '',    'noun',         0, '/ʃa/',     '',  'A small domesticated carnivorous mammal'),
  ('chien',    'chien',     'dog',        '',    'noun',         0, '/ʃjɛ̃/',   '',  'A domesticated carnivorous mammal'),
  ('maison',   'maison',    'house',      '',    'noun',         0, '/mɛzɔ̃/',  '',  'A building for human habitation'),
  ('eau',      'eau',       'water',      '',    'noun',         0, '/o/',      '',  'A clear liquid essential for life'),
  ('livre',    'livre',     'book',       '',    'noun',         0, '/livʁ/',   '',  'A written or printed work'),
  ('livre',    'livre',     'pound',      '',    'noun',         1, '/livʁ/',   '',  'A unit of weight or currency'),
  ('manger',   'manger',    'eat',        '',    'verb',         0, '/mɑ̃ʒe/',  '',  'To consume food'),
  ('boire',    'boire',     'drink',      '',    'verb',         0, '/bwaʁ/',   '',  'To consume liquid'),
  ('grand',    'grand',     'big',        '',    'adjective',    0, '/ɡʁɑ̃/',   '',  'Of considerable size or extent'),
  ('petit',    'petit',     'small',      '',    'adjective',    0, '/pəti/',   '',  'Of little size');

-- ── Chinese example rows (with pinyin romanization) ───────
-- INSERT INTO entries VALUES
--  ('你好',  '你好',  'hello',    'nǐ hǎo',   'interjection', 0, '',  '', 'A common greeting'),
--  ('书',    '书',    'book',     'shū',       'noun',         0, '',  '', 'A written or printed work'),
--  ('水',    '水',    'water',    'shuǐ',      'noun',         0, '',  '', 'A clear liquid essential for life'),
--  ('吃',    '吃',    'eat',      'chī',       'verb',         0, '',  '', 'To consume food'),
--  ('猫',    '猫',    'cat',      'māo',       'noun',         0, '',  '', 'A small domesticated carnivorous mammal');

-- ── Verify ────────────────────────────────────────────────
SELECT 'Total entries' AS info, COUNT(*) AS count FROM entries;
SELECT 'Unique words'  AS info, COUNT(DISTINCT word) AS count FROM entries;
SELECT 'Sample' AS info, display_word, romanization_lower FROM words_search LIMIT 5;