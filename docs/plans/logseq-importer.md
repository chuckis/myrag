# Logseq JSON Importer

## Goal
Add support for importing Logseq JSON exports into the RAG pipeline.

## JSON Format

```json
{
  "version": 1,
  "blocks": [
    {
      "id": "...",
      "page-name": "4th Jan 2025",
      "properties": null,
      "children": [
        {
          "id": "...",
          "properties": null,
          "format": "markdown",
          "children": [
            {
              "id": "...",
              "properties": null,
              "format": "markdown",
              "children": [],
              "content": "text content here"
            }
          ],
          "content": "#gamedev\ncollapsed:: true"
        }
      ]
    }
  ]
}
```

- Root: `version` + `blocks` array
- Each block: `id`, `page-name` (optional, on page-level blocks), `properties`, `children` (recursive), `content` (text)
- `format`: usually `"markdown"` on nested blocks

## Plan

### 1. `logseq_importer.py` (new file)
- `parse_logseq_export(filepath) -> list[dict]`
  - Recursively traverse `blocks` → `children` tree
  - Track current `page-name` as source
  - For each block with non-empty `content`, create a record
  - Content stored as plain text, skipping filtering/min-length
- `import_logseq(filepath) -> dict` (stats: total, imported)

### 2. `storage.py`
- Add `'logseq'` to the CHECK constraint: `CHECK(type IN ('chat', 'docx', 'text', 'logseq'))`

### 3. `add_view.py`
- Auto-detect JSON format in `_import_json`:
  - `"blocks"` key → `import_logseq`
  - `"messages"` key → `import_telegram`
- Update helper text to mention Logseq support

### 4. `cli.py`
- Add `import-logseq` subparser with `-f/--file` argument
- Wire to `import_logseq` function

### 5. `indexer.py`
- No changes needed — `logseq` type is plain text (like `chat`/`text`)