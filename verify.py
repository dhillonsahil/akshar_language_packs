import sqlite3

c = sqlite3.connect('akshar_hi.db')

# Check what tables/views exist
print('-- Tables and views --')
for row in c.execute("SELECT type, name FROM sqlite_master ORDER BY type, name"):
    print(f'  {row[0]:<6} {row[1]}')

# Check row counts
print()
print('-- Row counts --')
print('  entries     :', c.execute('SELECT COUNT(*) FROM entries').fetchone()[0])
print('  words_search:', c.execute('SELECT COUNT(*) FROM words_search').fetchone()[0])

# Test Devanagari search
print()
print('-- Search नमस्ते (Devanagari) --')
for r in c.execute("SELECT display_word, romanization_lower FROM words_search WHERE display_word LIKE 'नमस्ते%' LIMIT 3"):
    print(f'  {r[0]} | {r[1]}')

# Test romanization search
print()
print('-- Search namaste (romanized) --')
for r in c.execute("SELECT display_word, romanization_lower FROM words_search WHERE romanization_lower LIKE 'namaste%' LIMIT 3"):
    print(f'  {r[0]} | {r[1]}')

# Test English lookup
print()
print('-- English lookup: peace --')
for r in c.execute("SELECT word, english_word, pos, definition_en FROM entries WHERE lower(english_word) = 'peace' LIMIT 3"):
    print(f'  {r[0]} | {r[1]} | {r[2]} | {r[3]}')

c.close()
print()
print('Done.')