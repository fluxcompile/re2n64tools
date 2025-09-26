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
python extract_from_table.py re2.z64 file_table.json extracted_assets
```

## File Format

### Video Data

The ROM contains 271 videos with addresses ranging from `0x01440F48` to `0x2B7D8E9`. These are M2V (MPEG-2 video) files containing cutscenes and FMVs.

The ROM stores videos in a simple format:

1. **Video data** (M2V file)
2. **8-byte header** containing:
   - Constant: `0x00010000` (4 bytes, big-endian)
   - Previous file size: How big the video was (4 bytes, big-endian)

This repeats for all 271 videos. The overall structure looks like:

```
[Video 0 data] [0x00010000] [size of Video 0]
[Video 1 data] [0x00010000] [size of Video 1]
[Video 2 data] [0x00010000] [size of Video 2]
...
```

For example, video 0 (`annet_ab22.m2v`):

```
[Video data (273,508 bytes)] [0x00010000] [0x00042C04]
```

Where `0x00042C04` (273,508 in decimal) is the size of the video data.