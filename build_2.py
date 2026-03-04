#!/usr/bin/env python3
"""
Akshar Language Pack Builder (NEW UNIVERSAL SCHEMA)
Builds an akshar_<code>.db from a kaikki.org JSONL (or .jsonl.gz) file.

Usage:
    python build_lang_pack.py --lang fr --input kaikki.org-dictionary-French.jsonl.gz
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

PENALTY_TAGS = {'rare','archaic','obsolete','dated','literary','poetic'}

META_PHRASES = (
    'inflection of', 'form of', 'plural of', 'past tense of',
    'present participle of', 'alternative spelling of',
)

# ── Scoring ───────────────────────────────────────────────────

def score_sense(sense: dict, gloss: str, sense_index: int) -> int:
    score = 1000
    lower = gloss.lower()

    if any(p in lower for p in META_PHRASES):
        score += 500

    score += sense_index * 10
    return max(0, score)


# ── Helpers ───────────────────────────────────────────────────

def get_ipa(entry):
    for s in entry.get('sounds', []):
        if 'ipa' in s:
            return s['ipa']
    return ''


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

    # ─────────────────────────────────────────────────────────
    # NEW UNIVERSAL SCHEMA
    # ─────────────────────────────────────────────────────────

    cur.executescript("""
        CREATE TABLE entries (
            word          TEXT NOT NULL,
            word_lower    TEXT NOT NULL,
            english_word  TEXT NOT NULL,
            romanization  TEXT NOT NULL,
            pos           TEXT NOT NULL,
            sense_num     INTEGER NOT NULL,
            ipa           TEXT NOT NULL,
            definition    TEXT NOT NULL,
            definition_en TEXT NOT NULL
        );

        CREATE INDEX idx_word_lower
            ON entries(word_lower);

        CREATE INDEX idx_english_word
            ON entries(lower(english_word));

        CREATE INDEX idx_romanization
            ON entries(lower(romanization));

        CREATE VIEW words_search AS
            SELECT
                word AS display_word,
                word_lower AS search_lower,
                lower(romanization) AS romanization_lower
            FROM entries;
    """)

    opener = gzip.open if input_file.endswith('.gz') else open
    rows   = []
    count  = 0

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
                continue

            word = entry.get('word', '').strip()
            if not word or len(word) > 100:
                continue

            pos = entry.get('pos', '').strip().lower()
            if pos not in VALID_POS:
                continue

            pos = POS_MAP.get(pos, pos)
            ipa = get_ipa(entry)
            senses = entry.get('senses', [])

            scored = get_scored_senses(senses)
            if not scored:
                continue

            for i, (definition_en, priority) in enumerate(scored):

                # derive english pivot word
                english_word = definition_en.split(';')[0]
                english_word = english_word.split(',')[0]
                english_word = english_word.split('(')[0]
                english_word = english_word.strip().lower()

                if not english_word:
                    continue

                rows.append((
                    word,
                    word.lower(),
                    english_word,
                    "",                     # romanization (empty)
                    pos or "other",
                    i,
                    ipa or "",
                    "",                     # native definition unused
                    definition_en.strip(),
                ))

                count += 1

            if len(rows) >= 50_000:
                cur.executemany("""
                    INSERT INTO entries (
                        word, word_lower, english_word, romanization,
                        pos, sense_num, ipa, definition, definition_en
                    )
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, rows)
                conn.commit()
                rows = []

    if rows:
        cur.executemany("""
            INSERT INTO entries (
                word, word_lower, english_word, romanization,
                pos, sense_num, ipa, definition, definition_en
            )
            VALUES (?,?,?,?,?,?,?,?,?)
        """, rows)
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