# Dictionary Database Contribution Guide

This repository accepts **SQLite dictionary databases (`.db`)** for different languages.

If you want to contribute a new dictionary, please convert your dataset into the **standard schema below** and submit a **Pull Request**.

---

# 📦 Database Format

All dictionary databases must use **SQLite** and contain a table named:

```
entries
```

Schema:

```sql
CREATE TABLE entries (
    word TEXT NOT NULL,
    word_lower TEXT NOT NULL,
    english_word TEXT NOT NULL,
    romanization TEXT NOT NULL,
    pos TEXT NOT NULL,
    sense_num INTEGER NOT NULL DEFAULT 0,
    ipa TEXT NOT NULL,
    definition TEXT NOT NULL,
    definition_en TEXT NOT NULL
);
```

Indexes:

```sql
CREATE INDEX idx_entries_english_word ON entries(lower(english_word));
CREATE INDEX idx_entries_romanization ON entries(lower(romanization));
CREATE INDEX idx_entries_word_lower ON entries(word_lower);
```

Search View:

```sql
CREATE VIEW words_search AS
SELECT
    word AS display_word,
    word_lower AS search_lower,
    lower(romanization) AS romanization_lower
FROM entries;
```

---

# 🧠 Column Meaning

| Column          | Description                                  |
| --------------- | -------------------------------------------- |
| `word`          | Original word in the dictionary language     |
| `word_lower`    | Lowercase version of the word (for search)   |
| `english_word`  | English translation or keyword               |
| `romanization`  | Latin transliteration if applicable          |
| `pos`           | Part of speech (noun, verb, adjective, etc.) |
| `sense_num`     | Meaning index (0,1,2...)                     |
| `ipa`           | IPA pronunciation (optional)                 |
| `definition`    | Definition in the original language          |
| `definition_en` | Definition translated to English             |

---

# 📂 Example Entry

| word    | word_lower | english_word | romanization | pos          | sense_num | ipa | definition      | definition_en |
| ------- | ---------- | ------------ | ------------ | ------------ | --------- | --- | --------------- | ------------- |
| Bonjour | bonjour    | hello        | bonjour      | interjection | 0         |     | French greeting | hello         |

---

# 🔧 Creating the Database

You can generate the `.db` file using:

* Python
* SQL scripts
* Data conversion tools
* AI tools like ChatGPT

Example Python snippet:

```python
import sqlite3

conn = sqlite3.connect("dictionary.db")

conn.execute("""
CREATE TABLE entries (
    word TEXT NOT NULL,
    word_lower TEXT NOT NULL,
    english_word TEXT NOT NULL,
    romanization TEXT NOT NULL,
    pos TEXT NOT NULL,
    sense_num INTEGER NOT NULL DEFAULT 0,
    ipa TEXT NOT NULL,
    definition TEXT NOT NULL,
    definition_en TEXT NOT NULL
);
""")

conn.commit()
```

---

# 📥 Contribution Steps

1. Fork the repository
2. Convert your dictionary dataset into the required schema
3. Create a `.db` file
4. Place it inside:

```
/dictionaries/
```

Example:

```
/submissions
    english.db
    french.db
    chinese.db
    bulgarian.db
```

5. Open a **Pull Request**

---

# 📏 Contribution Rules

Please ensure:

* SQLite format (`.db`)
* Uses the **exact schema**
* No duplicate entries
* UTF-8 encoded text
* File size is reasonable

---

# 💡 Tip: Using AI to Convert Datasets

If you have datasets like:

```
CSV
TSV
JSON
Wiktionary dumps
StarDict dictionaries
```

You can ask AI something like:

```
Convert this dataset into SQLite using this schema:
[paste schema]
```

Then run the generated script to produce the `.db` file.

---

# 🌍 Goal

The goal is to build a **large multilingual offline dictionary database** that anyone can use in apps or research projects.

Every contribution helps expand the dictionary for more languages.

---

Thank you for contributing ❤️
