# RE2 N64 Research Notes

## ROM Data Mapping Summary

| Address Range         | Purpose                      |
| --------------------- | ---------------------------- |
| 0x00000000-0x000B628B | Code                         |
| 0x000B628C-0x000D8323 | Unknown binary data          |
| 0x000D8324-0x00338FE1 | Compressed data              |
| 0x0034C18B–0x00B2C346 | Unknown binary data          |
| 0x00B63106-0x00B73FB3 | Compressed data              |
| 0x00BF20FD-0x01350E80 | Unknown binary data          |
| 0x01350E81-0x014030F6 | Uncompressed data            |
| 0x0140ED84-0x0142CFE9 | Compressed data              |
| 0x0142CFFE–0x014350CB | Text Strings                 |
| 0x01440F38–0x02B7D8E9 | M2V Video Files              |
| 0x02B7D8EA-0x02BDEFB1 | Compressed Data              |
| 0x02BDEFB2-0x03AF17FD | JPEG files                   |
| 0x03AF17FE-0x03FD0DF5 | Compressed Data              |
| 0x03FD0DF6-0x03FFFFFF | Empty Data                   |

## File Formats

* **Compressed Data**: Zlib-compressed blocks with various content types
* **Uncompressed Data**: Raw files with 8-byte footers (`0x00010000` + size) after each file
  * **Videos (M2V)**: `0x01440F38-0x02B7D8E9` - Raw MPEG-2 video files
  * **Images (JPEG)**: `0x02BDEFB2-0x03AF17FD` - JPEG files
  * **Other Files**: Various uncompressed data scattered throughout unmapped regions

## Compressed Data Blocks

The ROM contains numerous compressed text blocks using zlib compression. 

Each compressed text block follows this pattern:

1. **68 DE marker** (2 bytes) - identifies the start of a compressed block
2. **Compressed data** (zlib format) - contains the actual text content
3. **00 10 00 00 terminator** (4 bytes) - marks block as compressed
4. **Size field** (4 bytes, big-endian) - contains the decompressed size of the block

The compressed blocks contain various types of text content. Some blocks also contain binary data (images, audio, etc.) which are dumped to separate files during extraction.

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
