# RE2 N64 Research Notes

## ROM Data Mapping Summary

| Address Range         | Purpose                      |
| --------------------- | ---------------------------- |
| 0x00000000-0x00012CDF | Code                         |
| 0x00012CE0-0x0001310F | Table0 data addresses        |
| 0x00013110-0x0001441F | Unknown data                 |
| 0x00014420-0x0007260F | Table0 Compressed Block 0 (contains debug strings) |
| 0x00072610-0x000B6247 | Table0 Compressed data blocks (possibly MIPS R4300i code) |
| 0x000B6248-0x000C8623 | Table0 Uncompressed data blocks |
| 0x000C8624-0x000C8653 | Unknown data (cotains a date string) | 
| 0x000C8654-0x000D8323 | Table1 data addresses and sizes |
| 0x000D8324-0x00338FE9 | Compressed data blocks       |
| 0x00338FEA–0x00B63105 | Uncompressed data block (MORT blocks) |
| 0x00B63106-0x00B73FBB | Compressed data blocks       |
| 0x00B73FBC-0x01350E80 | Unknown binary data          |
| 0x01350E81-0x014030F6 | Uncompressed data            |
| 0x0140ED84-0x0142CFF1 | Compressed data              |
| 0x0142CFF2–0x014350CB | Text Strings (compressed and uncompressed) |
| 0x014350CC-0x01440F37 | Unknown binary data          |
| 0x01440F38–0x02B7D8E9 | M2V Video Files (uncompressed) |
| 0x02B7D8EA-0x02B842C9 | Room Camera Positions (mostly compressed) |
| 0x02B842CA-0x02B921AF | Room Camera Switches (compressed and uncompressed) |
| 0x02B921B0-0x02B93F8D | Room Blocks Data (mostly uncompressed) |
| 0x02B93F8E-0x02B9555D | Room Floor Data (mostly uncompressed) |
| 0x02B9555E-0x02B99E27 | Room Light Data (mostly compressed) |
| 0x02B99E28-0x02BA25BD | Room Collision Data (compressed) |
| 0x02BA25BE-0x02BA7003 | Room Init Scripts (compressed and uncompressed) |
| 0x02BA7004-0x02BC3A7D | Room Main Scripts (mostly compressed) |
| 0x02BC3A7E-0x02BDEFB1 | Compressed Data              |
| 0x02BDEFB2-0x03AF17FD | JPEG files (uncompressed)    |
| 0x03AF17FE-0x03B454EB | Compressed Data              |
| 0x03B454EC-0x03B7E061 | Item images (compressed)     |
| 0x03B7E062-0x03BBDE09 | Compressed Data              |
| 0x03BBDE0A-0x03BC5771 | Map images (compressed)      |
| 0x03BC5772-0x03F701EB | Compressed Data              |
| 0x03F701EC-0x03F93A3F | Sprites (compressed)         |
| 0x03F93A40-0x03FD0DF5 | Compressed Data              |
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

## Table 0 — Block Entry Format

**Range:** `0x00012CE0-0x0001310F`
**Number of entries:** 67 (0 – 66)

### Address Table Entry Structure

| Offset | Size | Field | Description |
|:-------|:-----|:------|:-------------|
| 0x00 | 1 byte | **Tag (0xB0)** | Constant marker identifying a valid block descriptor. Every record begins with `B0`. |
| 0x01 – 0x03 | 3 bytes | **ROM Start Address** | 24-bit (big-endian) offset into the ROM where the data block begins. |
| 0x04 – 0x07 | 4 bytes | **Block Size** | Length in bytes to read from the ROM start address. May be compressed (if `0x68DE` marker present) or uncompressed data. |
| 0x08 – 0x0B | 4 bytes | **Address A** | 32-bit value starting with `0x80xxxxxx` |
| 0x0C – 0x0F | 4 bytes | **Address B** | 32-bit value starting with `0x80xxxxxx` |

### Decompressed Block Contents

- **Block 0:** Contains debug strings and system messages
- **Blocks 1+:** Begin with `0x27BDFFE0` (MIPS function prologue: `addiu $sp, $sp, -32`)

## Table 1 — Address Chain Format

**Range:** `0x000C865C-0x000D8323`  
**Structure:** 8-byte entries containing address/size pairs  
**Pattern:** Sequential address chain with size-based offsets

### Address Chain Entry Structure

| Offset | Size | Field | Description |
|:-------|:-----|:------|:-------------|
| 0x00 – 0x03 | 4 bytes | **Next Address** | Target address for the next entry in the chain |
| 0x04 – 0x07 | 4 bytes | **Size** | Length of data block at this address |

### Address Chain Validation

The chain follows a size-based offset pattern in most cases:
- **Even size:** `next_address = current_address + size + 8`
- **Odd size:** `next_address = current_address + size + 9`

This pattern has been validated across thousands of entries in the chain, though it does not apply to all cases.

## MORT Block Format

**Range:** `0x00338FEA–0x00B63105`
**Magic:** `"MORT"` (0x4D4F5254)

### Address Table Discovery

MORT blocks are discovered through an address table located at the beginning of uncompressed files:

1. **Address Count:** First 4 bytes contain the number of addresses
2. **Address Array:** Followed by an array of 4-byte addresses  
3. **Address Extraction:** For each address, only the last 3 bytes are used as the target offset
4. **Leftmost Byte Correlation:** The leftmost byte (byte 0) of each address correlates with MORT block type:
   - **Leftmost = 0x00** → MORT blocks with bytes 6-7 = `0x1F40` (Type A)
   - **Leftmost = 0x01** → MORT blocks with bytes 6-7 = `0x3E80` (Type B)
5. **Block Extraction:** Blocks are extracted between consecutive addresses within the same file
6. **MORT Detection:** Each extracted block is searched for the "MORT" magic string (0x4D4F5254)

### MORT Block Header Structure

| Offset | Size | Field | Description |
|:-------|:-----|:------|:-------------|
| 0x00 – 0x03 | 4 bytes | **Magic** | `"MORT"` identifier (0x4D4F5254) |
| 0x04 – 0x05 | 2 bytes | **Unknown** | Purpose not yet determined |
| 0x06 – 0x07 | 2 bytes | **Type/Version** | Block type indicator: `0x1F40` (Type A, 565 occurrences) or `0x3E80` (Type B, 23 occurrences) |
| 0x08 – 0x0B | 4 bytes | **Entry Count** | Number of 4-byte entries in payload |
| 0x0C – 0x0F | 4 bytes | **Unknown** | Purpose not yet determined |
| 0x10+ | Variable | **Payload** | Array of 4-byte values (counted by entry count) |

### Validation

- **Entry Size:** `block_size / num_entries` should equal 4 bytes
- **Structure:** All MORT blocks follow the same header format with variable payload length

## Table0 Compressed Block 0

**ROM Range:** `0x00014420-0x0007260F` (Table0 Compressed Block 0)
**RAM Range:** `0x80018A80-0x80136D90`

| Address Range | Purpose |
| ------------- | --------- |
| 0x9E460-0x9F3D7 | Debug Strings |
| 0x9F3D8-0x9F58F | Address references to debug strings (0x9E460-0x9F3D5) |
| 0x9F5D0-0x9FB2B | Image Debug Strings |
| 0x9FB2C-0x9FBD3 | Address references to debug strings (0x9F5D0-0x9FB25) |
| 0xA01B0-0xA0475 | Computer Registration Strings |
| 0xA08C0-0xA0A42 | Debug Strings |
| 0x118234-0x1182D3 | Unknown 32-bit addresses and numbers |
| 0x1182D4-0x118373 | ECG_FINE curve |
| 0x118374-0x118413 | ECG_YELLOW_CAUTION curve |
| 0x118414-0x1184B3 | ECG_ORANGE_CAUTION curve |
| 0x1184B4-0x118553 | ECG_DANGER curve |
| 0x118554-0x1185F3 | ECG_POISON curve |
| 0x118634-0x11867B | St_disp_num() N_pos (int16[18][2]) |
| 0x1186DC-0x11870B | St_init_disp_face() Face_char_tbl (char[12][4]) |
| 0x118710-0x118738 | St_init_disp_face() Face_subchar_tbl (char[10][4]) |
| 0x11892C-0x118947 | St_init_disp_itemlist() Itemlist_char_tbl (char[7][4]) |
| 0x118948-0x118963 | St_disp_itemlist() Itemlist_pos_tbl (int16[7][2]) |
| 0x118964-0x11897F | St_init_disp_equip() Equip_char_tb (char[7][4]) |
| 0x118980-0x11899B | St_disp_equip() Equip_pos_tbl (int16[7][2]) |
| 0x11899C-0x1189A1 | ECG_FINE color and gradient |
| 0x1189A2-0x1189A7 | ECG_YELLOW_CAUTION color and gradient |
| 0x1189A8-0x1189AD | ECG_ORANGE_CAUTION color and gradient |
| 0x1189AE-0x1189B3 | ECG_DANGER color and gradient |
| 0x1189B4-0x1189B9 | ECG_POISON color and gradient |
| 0x1189BC-0x1189CF | ECG curve address table pointers (0x1182D4-0x1185F3) |

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
