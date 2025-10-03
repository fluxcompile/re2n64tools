# RE2 N64 Tools

Python tools for extracting assets from Resident Evil 2 (N64) ROM files.

## Legal Notice

This project is for educational and research purposes only. You must obtain the Resident Evil 2 N64 ROM legally. This project does not distribute or link to copyrighted content.

## Supported ROM

Requires Resident Evil 2 (USA) (Rev 1) N64 ROM in .z64 format (big endian).

- **SHA1**: `62ec19bead748c12d38f6c5a7ab0831edbd3d44b`

This tool only works with the specific ROM version listed above. Other dumps (.v64, .n64, different regions) will not work.

## Usage

```bash
python tools/extract_from_table.py re2.z64 tools/file_table.json extracted_assets
```

## Notes

See `NOTES.md` for technical documentation and research findings.