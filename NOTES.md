# RE2 N64 Research Notes

## ROM Data Mapping Summary

| Address Range         | Size (bytes) | Purpose                      | Status   |
| --------------------- | ------------ | ---------------------------- | -------- |
| 0x01440F48–0x02B7D8E9 | 24,365,473   | M2V Video Files (271 files)  | ✅ Mapped |
| 0x0142CFFE–0x01434BE8 | 15,754       | Text Strings (16 identified) | 🔍 Partial |
| 0x00000000–0x03FFFFFF | 67,108,864   | Total ROM Size (64 MB)       | -        |

**Mapped**: 24,381,227 bytes (~36.3%)
**Unmapped**: 42,727,637 bytes (~63.7%)

## Video File Format

The ROM contains 271 video files located between `0x01440F48` and `0x02B7D8E9`. These are M2V (MPEG-2 video) files used for cutscenes and FMVs.

Each video is stored with a simple repeating structure:

1. **Video data** (raw M2V stream)  
2. **8-byte footer** consisting of:  
   - A constant value: `0x00010000` (4 bytes, big-endian)  
   - The size of the preceding video file (4 bytes, big-endian)  

This pattern repeats for all 271 videos, producing a sequence like:

```
[Video 0 data] [0x00010000] [Size of Video 0]
[Video 1 data] [0x00010000] [Size of Video 1]
[Video 2 data] [0x00010000] [Size of Video 2]
...
```

**Example:** Video 0 (`annet_ab22.m2v`) is 273,508 bytes long:

```
[Video data (273,508 bytes)] [0x00010000] [0x00042C04]
```

Where `0x00042C04` (273,508 in decimal) is the size of the video data.

Together, the 271 video files account for ~24.3 MB of the ROM (about 36% of the total 64 MB).

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

### ID Value Patterns

Based on the data above, different ID values appear to correlate with content types:

- **E7**: Short film labels (FILM A, FILM B, FILM C)
- **E9**: Short identifiers (RECRUIT)
- **F5**: Advertisements/notices (WANT AD)
- **F7**: Personal memos and file references (Memo To Leon, #FILE 15/16)
- **F8**: Reports, diaries, notes (CHRIS'S DIARY, MAIL TO THE CHIEF, PATROL REPORT, CHIEF'S DIARY, P-EPSILON GAS)
- **F9**: Operation reports (OPERATION REPORT)
- **FA**: Police/memorandum entries (Police Memorandum, USER REGISTRATION)
- **FD**: Investigative reports (INVESTIGATIVE REPORT ON)

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
