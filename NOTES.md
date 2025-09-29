# RE2 N64 Research Notes

## ROM Data Mapping Summary

| Address Range         | Purpose                      | Status   |
| --------------------- | ---------------------------- | -------- |
| 0x0142CFFE–0x014350CB | Text Strings                 | Partial |
| 0x01440F38–0x02B7D8E9 | M2V Video Files              | ✅ Mapped |
| 0x02B7D8EA-0x02BDEFB1 | Compressed Data              | Parital |
| 0x02BDEFB2-0x03AF17FD | JPEG files                   | ✅ Mapped |
| 0x03AF17FE-0x03B27C93 | Compressed Data              | Partial |
| 0x03FD0DF6-0x03FFFFFF | Empty Data                   | ✅ Mapped |

**Mapped**: 45,953,026 bytes (~68.5%)
**Total**: 67,108,864 bytes (64 MB)

## File Formats

**Videos (M2V)**: `0x01440F38-0x02B7D8E9` - Raw MPEG-2 video files with 8-byte footers (`0x00010000` + size) after each file
**Images (JPEG)**: `0x02BDEFB2-0x03AF17FD` - JPEG files with 8-byte footers (`0x00010000` + size) after each file
**Compressed Data**: `0x03AF17FE-0x03B27C93` - Zlib-compressed blocks with various content types

## Compressed Data Blocks

The ROM contains numerous compressed text blocks using zlib compression. 

Each compressed text block follows this pattern:

1. **68 DE marker** (2 bytes) - identifies the start of a compressed block
2. **Compressed data** (zlib format) - contains the actual text content
3. **00 10 00 00 terminator** (4 bytes) - marks block as compressed
4. **Size field** (4 bytes, big-endian) - contains the decompressed size of the block

The compressed blocks contain various types of text content. Some blocks also contain binary data (images, audio, etc.) which are dumped to separate files during extraction.

### Images

All image assets are now cataloged in `file_table.json` under the `compressed_images` section. This includes:
- 24-bit images (logos, etc.)
- 16-bit palette-based images (UI screens, menus)
- Complete metadata (addresses, dimensions, formats, sizes)

Use `extract_from_table.py` to extract images from the file table.

## String Header Analysis (Work in Progress)

Preliminary findings suggest that text entries follow a consistent header format:
`[ID] 0x20 [Length] [Text...]`.

- The **ID** byte varies by entry and may classify the string type (e.g., reports, memos, film labels).
- The **Length** byte matches the visible character count of the string, though some entries are followed by additional control codes (e.g., `0x0D`, `0x0A`).
- The exact meaning of different ID values and how terminators are handled is still under investigation.

### Complete String Header Data

| Header Addr | String Addr | Header bytes | String                  |
| ----------- | ----------- | ------------ | ----------------------- |
| 0x0142CFFB  | 0x0142CFFE  | F8 20 0F     | CHRIS'S DIARY           |
| 0x0142D765  | 0x0142D768  | F7 20 0C     | Memo To Leon            |
| 0x0142D84D  | 0x0142D850  | FA 20 11     | Police Memorandum       |
| 0x0142D993  | 0x0142D996  | F9 20 12     | OPERATION REPORT        |
| 0x0142E0E1  | 0x0142E0E4  | F8 20 11     | MAIL TO THE CHIEF       |
| 0x0142F167  | 0x0142F16A  | FA 20 11     | USER REGISTRATION       |
| 0x0142F213  | 0x0142F216  | E7 20 06     | FILM A                  |
| 0x0142F269  | 0x0142F26C  | E7 20 06     | FILM B                  |
| 0x0142F383  | 0x0142F386  | E7 20 06     | FILM C                  |
| 0x0142F43F  | 0x0142F442  | F8 20 0D     | PATROL REPORT           |
| 0x0142FBC3  | 0x0142FBC6  | F8 20 0D     | CHIEF'S DIARY           |
| 0x014309D1  | 0x014309D4  | E9 20 07     | RECRUIT                 |
| 0x0143125B  | 0x0143125E  | FD 20 19     | INVESTIGATIVE REPORT ON |
| 0x01431277  | 0x0143127A  | F8 20 0F     | P-EPSILON GAS           |
| 0x01434BD5  | 0x01434BD8  | F7 20 0D     | #FILE 15/16             |
| 0x01434BE5  | 0x01434BE8  | F5 20 09     | WANT AD                 |


## System / Debug Strings

These strings are not part of in-game text, but come from libraries, error handling, or ROM metadata.

| Address    | String                                   | Notes                                |
| ---------- | ---------------------------------------- | ------------------------------------ |
| 0x00000020 | Resident Evil II                         | ROM title string                     |
| 0x00012160 | invalid block type                       | zlib inflate error                   |
| 0x00012174 | invalid stored block lengths             | zlib inflate error                   |
| 0x00012194 | too many length or distance symbols      | zlib inflate error                   |
| 0x000121B8 | invalid bit length repeat                | zlib inflate error                   |
| 0x000121FE | !Xinvalid literal/length code            | zlib inflate error                   |
| 0x0001221C | invalid distance code                    | zlib inflate error                   |
| 0x0001225E | *hinvalid distance code                  | zlib inflate error (truncated form?) |
| 0x00012278 | invalid literal/length code              | zlib inflate error                   |
| 0x000122A0 | unknown compression method               | zlib inflate error                   |
| 0x000122BC | invalid window size                      | zlib inflate error                   |
| 0x000122E8 | need dictionary                          | zlib inflate error                   |
| 0x000122F8 | incorrect data check                     | zlib inflate error                   |
| 0x00012350 | oversubscribed dynamic bit lengths tree  | zlib inflate error                   |
| 0x00012378 | incomplete dynamic bit lengths tree      | zlib inflate error                   |
| 0x0001239C | oversubscribed literal/length tree       | zlib inflate error                   |
| 0x000123C0 | incomplete literal/length tree           | zlib inflate error                   |
| 0x000123F4 | incompatible version                     | zlib inflate error                   |
| 0x0001240C | buffer error                             | zlib inflate error                   |
| 0x0001241C | insufficient memory                      | zlib inflate error                   |
| 0x00012430 | data error                               | zlib inflate error                   |
| 0x0001243C | stream error                             | zlib inflate error                   |
| 0x0001244C | file error                               | zlib inflate error                   |
| 0x0001245C | stream end                               | zlib inflate status                  |
| 0x00012468 | need dictionary                          | zlib inflate error (duplicate)       |
| 0x00012714 | epirawread.c                             | N64 SDK source file reference        |
| 0x00012734 | pirawread.c                              | N64 SDK source file reference        |
| 0x00012824 | sirawdma.c                               | N64 SDK source file reference        |
| 0x00012834 | sirawread.c                              | N64 SDK source file reference        |
| 0x00012844 | sirawwrite.c                             | N64 SDK source file reference        |
| 0x00012864 | sprawdma.c                               | N64 SDK source file reference        |
