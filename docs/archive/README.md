# Archive

Obsolete or superseded documentation.

## 📁 Purpose

This directory contains documentation that is:
- **Obsolete**: Relates to code/features that no longer exist
- **Superseded**: Replaced by newer, more accurate documentation
- **Historical**: Valuable for reference but not current

## 🗂️ What Gets Archived

### Automatically Archived
- Documentation for removed code/features
- Old versions of living documents
- Superseded bug fixes (when a better solution is implemented)
- Outdated guides/references

### Manually Archived
- Documents marked as "archived" or "superseded" in frontmatter
- Historical documentation valuable for context but not current

## 📝 Archival Process

When archiving a document:

1. **Move**: Move file to this directory
2. **Update**: Add archival information to frontmatter:
   ```markdown
   ---
   status: archived
   archived_date: YYYY-MM-DD
   archived_reason: "Superseded by X" or "Feature removed"
   superseded_by: path/to/new/doc.md (if applicable)
   ---
   ```
3. **Link**: Update any referring documents to point to replacement
4. **Index**: Add entry to this README with reason and replacement

## 📋 Archived Documents

### Superseded Documents
List documents that have been superseded here with links to replacements.

### Removed Features
List documents for removed features here with removal dates.

### Historical Context
List documents kept for historical reference here.

## 🔍 Finding Archived Content

Use your editor's search or git history to locate archived content:
```bash
# Find when a document was archived
git log --follow --oneline -- docs/archive/filename.md

# Search archived content
grep -r "search term" docs/archive/
```

## ⚠️ Important Notes

- Archived documents may be outdated or inaccurate
- Always check for newer versions before referencing archived content
- Archived documents are NOT maintained
- When in doubt, consult current documentation in main sections

---

**Last Updated**: 2025-10-27  
**Total Archived Documents**: TBD (populated during migration)
