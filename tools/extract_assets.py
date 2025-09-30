#!/usr/bin/env python3
import os, sys

rom = sys.argv[1]
outdir = sys.argv[2]

os.makedirs(outdir, exist_ok=True)

# Hard-coded split: everything before 0xD8324 is code
code_start = 0x00000000
code_end   = 0x000D8324
asset_start = code_end
rom_size = os.path.getsize(rom)

with open(rom, "rb") as f:
    rom_data = f.read()

# Write code region -> bin
code_bin = os.path.join(outdir, "re2_code.bin")
with open(code_bin, "wb") as f:
    f.write(rom_data[code_start:code_end])
print(f"Wrote {code_bin} ({code_end - code_start} bytes)")

# Write assets region -> bin
assets_bin = os.path.join(outdir, "re2_assets.bin")
with open(assets_bin, "wb") as f:
    f.write(rom_data[asset_start:])
print(f"Wrote {assets_bin} ({rom_size - asset_start} bytes)")
