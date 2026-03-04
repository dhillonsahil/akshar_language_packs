#!/usr/bin/env python3
"""
Akshar Language Pack Builder
=============================
Builds an akshar_<code>.db from a kaikki.org JSONL (or .jsonl.gz) file.

Usage:
    python build_lang_pack.py --lang fr --input kaikki.org-dictionary-French.jsonl.gz
    python build_lang_pack.py --lang es --input kaikki.org-dictionary-Spanish.jsonl.gz
    python build_lang_pack.py --lang de --input kaikki.org-dictionary-German.jsonl.gz

The output file will be: akshar_<lang>.db

Download source files from:
    https://kaikki.org/dictionary/  → pick your language → download the .jsonl.gz

DB Schema (same for every language pack):
    Table: entries
        id          INTEGER PRIMARY KEY
        word        TEXT NOT NULL        -- display form (original casing)
        word_lower  TEXT NOT NULL        -- lowercased for search
        pos         TEXT                 -- part of speech
        pos_order   INTEGER DEFAULT 99
        ipa         TEXT
        etymology   TEXT
        synonyms    TEXT                 -- comma-separated
        antonyms    TEXT                 -- comma-separated
        examples    TEXT                 -- pipe-separated
        sense_num   INTEGER
        priority    INTEGER DEFAULT 1000
        definition  TEXT NOT NULL

    View: words_search  (for generic search in LanguagePackService)
        display_word  TEXT  -- = word
        search_lower  TEXT  -- = word_lower

    Indexes:
        idx_word_lower  on entries(word_lower)
        idx_word_sort   on entries(word_lower, pos_order, priority)
"""

import argparse
import gzip
import json
import os
import re
import sqlite3

# ── Constants ─────────────────────────────────────────────────

VALID_POS = {
    'noun', 'verb', 'adjective', 'adverb', 'pronoun',
    'preposition', 'conjunction', 'interjection',
    'phrase', 'prefix', 'suffix', 'abbreviation',
    'adj', 'adv', 'prep', 'conj', 'interj', 'pron',
}

POS_MAP = {
    'adj': 'adjective', 'adv': 'adverb', 'prep': 'preposition',
    'conj': 'conjunction', 'interj': 'interjection', 'pron': 'pronoun',
}

POS_ORDER = {
    'noun': 0, 'verb': 1, 'adjective': 2, 'adverb': 3,
    'pronoun': 4, 'preposition': 5, 'conjunction': 6,
    'interjection': 7, 'phrase': 8, 'prefix': 9, 'suffix': 10,
    'abbreviation': 11, 'other': 99,
}

PENALTY_TAGS = {
    'rare', 'archaic', 'obsolete', 'dated', 'literary', 'poetic',
    'archaic-verb', 'uncommon', 'dialectal', 'regional', 'historical',
    'informal', 'slang', 'colloquial', 'vulgar', 'offensive',
    'technical', 'jargon', 'specialist', 'medicine', 'chemistry',
    'physics', 'biology', 'botany', 'zoology', 'mathematics', 'math',
    'computing', 'programming', 'nautical', 'military', 'heraldry',
    'law', 'legal', 'finance', 'economics', 'music', 'theatre',
}

TECHNICAL_RE = re.compile(
    r'\b(archaic|obsolete|dated|historical|rare|poetic|literary|'
    r'nautical|heraldic|ecclesiastical|law of|legal term|in law|'
    r'in medicine|medical term|genus|species|taxon|botanical|zoological)\b',
    re.IGNORECASE,
)

COMMON_RE = re.compile(
    r'\b(collection|group|set of|series|number of|amount|total|sum|'
    r'put|place|position|arrange|fix|establish|become|cause|make|turn|go)\b',
    re.IGNORECASE,
)

META_PHRASES = (
    'inflection of', 'form of', 'plural of', 'past tense of',
    'present participle of', 'alternative spelling of', 'misspelling of',
)


# ── Scoring ───────────────────────────────────────────────────

def score_sense(sense: dict, gloss: str, sense_index: int) -> int:
    score = 1000
    tags = set()
    for t in sense.get('tags', []):
        tags.add(str(t).lower())
    for cat in sense.get('categories', []):
        name = cat.get('name', '').lower() if isinstance(cat, dict) else str(cat).lower()
        tags.add(name)

    score += len(tags & PENALTY_TAGS) * 120
    score += len(TECHNICAL_RE.findall(gloss)) * 80
    score -= len(COMMON_RE.findall(gloss)) * 60

    length = len(gloss)
    if length < 10:
        score += 200
    elif length < 25:
        score += 80
    elif length > 200:
        score += 60
    elif 30 <= length <= 120:
        score -= 40

    if sense.get('examples'):
        score -= 80
    if sense.get('synonyms'):
        score -= 40

    score += sense_index * 15

    lower = gloss.lower()
    if any(p in lower for p in META_PHRASES):
        score += 500

    return max(0, score)


# ── Entry helpers ─────────────────────────────────────────────

def get_ipa(entry):
    for s in entry.get('sounds', []):
        if 'ipa' in s:
            return s['ipa']
    return ''


def get_synonyms(senses):
    words = []
    for s in senses:
        for syn in s.get('synonyms', []):
            w = syn.get('word', '').strip()
            if w and w not in words:
                words.append(w)
    return ', '.join(words[:8])


def get_antonyms(senses):
    words = []
    for s in senses:
        for ant in s.get('antonyms', []):
            w = ant.get('word', '').strip()
            if w and w not in words:
                words.append(w)
    return ', '.join(words[:8])


def get_examples(senses):
    examples = []
    for s in senses:
        for ex in s.get('examples', []):
            text = ex.get('text', '').strip()
            if text and len(text) < 300:
                examples.append(text)
            if len(examples) >= 3:
                break
        if len(examples) >= 3:
            break
    return ' | '.join(examples)


def get_scored_senses(senses):
    result = []
    for i, s in enumerate(senses):
        glosses = s.get('glosses', [])
        if not glosses:
            continue
        text = glosses[0].strip()
        if not text or len(text) > 500:
            continue
        result.append((text, score_sense(s, text, i)))
    result.sort(key=lambda x: x[1])
    return result


# ── Main build function ───────────────────────────────────────

def build_pack(lang_code: str, input_file: str, output_db: str):
    if os.path.exists(output_db):
        os.remove(output_db)

    conn = sqlite3.connect(output_db)
    cur  = conn.cursor()

    cur.executescript(f"""
        CREATE TABLE entries (
            id          INTEGER PRIMARY KEY,
            word        TEXT NOT NULL,
            word_lower  TEXT NOT NULL,
            pos         TEXT,
            pos_order   INTEGER DEFAULT 99,
            ipa         TEXT,
            etymology   TEXT,
            synonyms    TEXT,
            antonyms    TEXT,
            examples    TEXT,
            sense_num   INTEGER,
            priority    INTEGER DEFAULT 1000,
            definition  TEXT NOT NULL
        );

        CREATE INDEX idx_word_lower ON entries(word_lower);
        CREATE INDEX idx_word_sort  ON entries(word_lower, pos_order, priority);

        -- Generic search view used by LanguagePackService.searchInPack()
        CREATE VIEW words_search AS
            SELECT DISTINCT word AS display_word, word_lower AS search_lower
            FROM entries;
    """)

    opener = gzip.open if input_file.endswith('.gz') else open
    rows   = []
    count  = 0
    skipped = 0

    print(f"Processing {input_file} for lang_code='{lang_code}'…")

    with opener(input_file, 'rt', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f):
            if line_num % 100_000 == 0:
                print(f"  {line_num:,} lines, {count:,} entries…")

            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            if entry.get('lang_code') != lang_code:
                skipped += 1
                continue

            word = entry.get('word', '').strip()
            if not word or len(word) > 100:
                continue

            pos = entry.get('pos', '').strip().lower()
            if pos not in VALID_POS:
                continue

            pos       = POS_MAP.get(pos, pos)
            pos_order = POS_ORDER.get(pos, 99)
            ipa       = get_ipa(entry)
            etymology = entry.get('etymology_text', '').strip()[:500]
            senses    = entry.get('senses', [])
            synonyms  = get_synonyms(senses)
            antonyms  = get_antonyms(senses)
            examples  = get_examples(senses)
            scored    = get_scored_senses(senses)

            if not scored:
                continue

            for i, (definition, priority) in enumerate(scored):
                rows.append((
                    word, word.lower(), pos, pos_order, ipa,
                    etymology if i == 0 else '',
                    synonyms  if i == 0 else '',
                    antonyms  if i == 0 else '',
                    examples  if i == 0 else '',
                    i + 1, priority, definition,
                ))
                count += 1

            if len(rows) >= 50_000:
                cur.executemany(
                    "INSERT INTO entries (word,word_lower,pos,pos_order,ipa,"
                    "etymology,synonyms,antonyms,examples,sense_num,priority,definition)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    rows,
                )
                conn.commit()
                rows = []

    if rows:
        cur.executemany(
            "INSERT INTO entries (word,word_lower,pos,pos_order,ipa,"
            "etymology,synonyms,antonyms,examples,sense_num,priority,definition)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        conn.commit()

    # ── Stats ────────────────────────────────────────────────
    cur.execute("SELECT COUNT(DISTINCT word_lower) FROM entries")
    words_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM entries")
    senses_count = cur.fetchone()[0]
    conn.close()

    size_mb = os.path.getsize(output_db) / 1024 / 1024
    print(f"""
════════════════════════════════════
  Done!  [{lang_code}]
  Words  : {words_count:,}
  Senses : {senses_count:,}
  DB     : {output_db}  ({size_mb:.1f} MB)
════════════════════════════════════
""")


# ── CLI ───────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build an Akshar language pack DB')
    parser.add_argument('--lang',   required=True,
                        help="kaikki.org lang_code, e.g. 'fr', 'es', 'de', 'ja'")
    parser.add_argument('--input',  required=True,
                        help='Path to kaikki.org .jsonl or .jsonl.gz file')
    parser.add_argument('--output', default=None,
                        help='Output DB path (default: akshar_<lang>.db)')
    args = parser.parse_args()

    output = args.output or f"akshar_{args.lang}.db"
    build_pack(args.lang, args.input, output)