Yes, one script handles everything. Here's exactly how to set up your folder and use it.

---

## Folder structure

```
artha-language-packs/          ← your GitHub repo root
├── manifest.json              ← the file the app fetches (keep at root)
├── README.md                  ← optional
├── build_lang_pack.py         ← the builder script
└── [GitHub Releases]          ← DB files live here, NOT in the folder
    akshar_hi.db
    akshar_fr.db
    ...
```

**Important:** The `.db` files do **not** go in the repo folder itself. They go in GitHub **Releases** (explained below). Only `manifest.json` and `build_lang_pack.py` sit in the repo.

---

## One-time setup in VS Code terminal

```bash
# 1. Make sure you have Python 3 and pip
python --version

# 2. No extra pip installs needed — the script only uses stdlib (sqlite3, gzip, json, argparse)
```

That's it. No dependencies to install.

---

## How to build a language DB

**Hindi** (your existing data, just run through the new script):
```bash
python build_lang_pack.py --lang hi --input Hindi_dict.jsonl
```
Output: `akshar_hi.db`

**French** (download from kaikki.org first):
```bash
python build_lang_pack.py --lang fr --input kaikki.org-dictionary-French.jsonl.gz
```
Output: `akshar_fr.db`

**Any other language — same pattern, just change the two values:**
```bash
python build_lang_pack.py --lang es --input kaikki.org-dictionary-Spanish.jsonl.gz
python build_lang_pack.py --lang de --input kaikki.org-dictionary-German.jsonl.gz
python build_lang_pack.py --lang ja --input kaikki.org-dictionary-Japanese.jsonl.gz
```

The `--lang` value must match the `lang_code` field in the kaikki.org data. The table below has every language you listed:

| Language   | `--lang` | kaikki.org download URL path |
|------------|----------|-------------------------------|
| Hindi      | `hi`     | `/dictionary/Hindi/` |
| French     | `fr`     | `/dictionary/French/` |
| Spanish    | `es`     | `/dictionary/Spanish/` |
| German     | `de`     | `/dictionary/German/` |
| Italian    | `it`     | `/dictionary/Italian/` |
| Portuguese | `pt`     | `/dictionary/Portuguese/` |
| Russian    | `ru`     | `/dictionary/Russian/` |
| Chinese    | `zh`     | `/dictionary/Chinese/` |
| Japanese   | `ja`     | `/dictionary/Japanese/` |
| Thai       | `th`     | `/dictionary/Thai/` |
| Urdu       | `ur`     | `/dictionary/Urdu/` |
| Greek      | `el`     | `/dictionary/Greek/` |
| Bulgarian  | `bg`     | `/dictionary/Bulgarian/` |

---

## Uploading to GitHub Releases (where the DB files actually live)

Once you have an `akshar_hi.db` built:

1. Go to your `artha-language-packs` repo on GitHub
2. Click **Releases** on the right sidebar → **Draft a new release**
3. Tag: type `v1.0` and click "Create new tag"
4. Title: `v1.0 — Initial language packs`
5. Drag and drop your `.db` files into the assets area
6. Click **Publish release**

Your download URL will then be:
```
https://github.com/YOUR_USERNAME/artha-language-packs/releases/download/v1.0/akshar_hi.db
```

Update this URL in `manifest.json` and commit that file to the repo root. That's the only thing the app fetches directly — the manifest tells it where to download each DB.

---

## Adding a new language later (full workflow)

Say you want to add Spanish in 3 months:

```
1. Download:  kaikki.org/dictionary/Spanish/ → get the .jsonl.gz
2. Build:     python build_lang_pack.py --lang es --input kaikki.org-dictionary-Spanish.jsonl.gz
3. Upload:    GitHub → Releases → add akshar_es.db to existing or new release
4. Edit:      manifest.json → add the Spanish entry with the URL
5. Commit:    git add manifest.json && git commit -m "Add Spanish" && git push
```

No app update needed. Users see it in the Languages screen within 6 hours (or immediately when they open the Languages screen, since it refreshes the manifest on open).

---

## Updating an existing language pack

When kaikki.org publishes new data and you want to update Hindi:

```bash
# 1. Rebuild with fresh data
python build_lang_pack.py --lang hi --input Hindi_dict_new.jsonl

# 2. Upload akshar_hi.db to a NEW release tag (v1.1)
#    Don't overwrite v1.0 — GitHub Releases are immutable by convention

# 3. In manifest.json, update the Hindi entry:
#    "version": 2,
#    "url": ".../releases/download/v1.1/akshar_hi.db"

# 4. Push manifest.json
```

The app compares the manifest `version` number against what's installed. If it's higher, you can show an "Update available" badge — that UI isn't built yet but the data is already there to support it.