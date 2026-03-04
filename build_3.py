#!/usr/bin/env python3
"""
Akshar Language Pack Builder
Builds an akshar_<code>.db from a kaikki.org JSONL (or .jsonl.gz) file.

Usage:
    python build_lang_pack.py --lang th --input thai_dict.jsonl --output akshar_th.db
    python build_lang_pack.py --lang th --input thai_dict.jsonl.gz --output akshar_th.db
"""

import argparse
import gzip
import json
import os
import sqlite3


def get_ipa(entry):
    """Extract the first available IPA pronunciation."""
    for sound in entry.get('sounds', []):
        ipa = sound.get('ipa')
        if ipa:
            return ipa.strip()
    return ''


def get_romanization(entry):
    """Extract romanization from forms or sounds."""
    # Check forms for romanization tags
    for form in entry.get('forms', []):
        tags = form.get('tags', [])
        if any('roman' in tag.lower() for tag in tags):
            return form.get('form', '').strip()
    # Check sounds for roman field
    for sound in entry.get('sounds', []):
        roman = sound.get('roman')
        if roman:
            return roman.strip()
    return ''


def build_pack(lang_code: str, input_file: str, output_db: str):
    if os.path.exists(output_db):
        os.remove(output_db)

    conn = sqlite3.connect(output_db)
    cur = conn.cursor()

    # Create the required schema
    cur.executescript("""
        CREATE TABLE entries (
            word          TEXT NOT NULL,
            word_lower    TEXT NOT NULL,
            pos           TEXT NOT NULL,
            sense_num     INTEGER NOT NULL,
            definition    TEXT NOT NULL,
            definition_en TEXT NOT NULL,
            english_word  TEXT NOT NULL,
            romanization  TEXT,
            ipa           TEXT
        );

        CREATE INDEX idx_word_lower ON entries(word_lower);
        CREATE INDEX idx_english_word ON entries(lower(english_word));
        CREATE INDEX idx_roman_lower ON entries(lower(romanization));

        CREATE VIEW words_search AS
        SELECT word AS display_word,
               word_lower AS search_lower,
               lower(romanization) AS romanization_lower
        FROM entries;
    """)

    opener = gzip.open if input_file.endswith('.gz') else open
    rows = []
    count = 0
    processed_lines = 0

    print(f"Starting build: lang={lang_code}, file={input_file}")

    with opener(input_file, 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            processed_lines += 1
            if processed_lines % 500000 == 0:
                print(f"Processed {processed_lines:,} lines — {count:,} entries inserted")

            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get('lang_code') != lang_code:
                continue

            word = entry.get('word', '').strip()
            if not word or len(word) > 100:
                continue

            pos = entry.get('pos', 'other').strip()
            if not pos:
                pos = 'other'

            ipa = get_ipa(entry)
            romanization = get_romanization(entry)
            senses = entry.get('senses', [])

            for sense_num, sense in enumerate(senses):
                glosses = sense.get('glosses', [])
                if not glosses:
                    continue

                definition_en = glosses[0].strip()
                if not definition_en or len(definition_en) > 500:
                    continue

                # Derive pivot English word from the first gloss
                english_word = definition_en.split(';')[0]
                english_word = english_word.split(',')[0]
                english_word = english_word.split('(')[0]
                english_word = english_word.strip().lower()

                if not english_word:
                    continue

                # Native definition not available, use empty
                definition = ''

                rows.append((
                    word,
                    word.lower(),
                    pos,
                    sense_num,
                    definition,
                    definition_en,
                    english_word,
                    romanization,
                    ipa
                ))
                count += 1

                # Batch insert for performance
                if len(rows) >= 50000:
                    cur.executemany("""
                        INSERT INTO entries
                        (word, word_lower, pos, sense_num, definition, definition_en,
                         english_word, romanization, ipa)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, rows)
                    conn.commit()
                    rows = []
                    print(f"Final insert of {count - len(rows):,} entries")  # Note: this prints per batch, adjust if needed

    # Insert remaining rows
    if rows:
        cur.executemany("""
            INSERT INTO entries
            (word, word_lower, pos, sense_num, definition, definition_en,
             english_word, romanization, ipa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()

    conn.close()

    print(f"Build complete: {count:,} senses written to {output_db}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build an Akshar language pack from Wiktextract JSONL')
    parser.add_argument('--lang', required=True, help="Language code, e.g., 'th', 'fr'")
    parser.add_argument('--input', required=True, help='Input JSONL or JSONL.GZ file path')
    parser.add_argument('--output', default=None, help='Output DB path (default: akshar_<lang>.db)')
    args = parser.parse_args()

    output = args.output or f"akshar_{args.lang}.db"
    build_pack(args.lang, args.input, output)