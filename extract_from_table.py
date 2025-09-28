#!/usr/bin/env python3
"""
Extract assets from ROM using a pre-built file table.
"""

import json
import os
import sys

def extract_from_file_table(rom_path, file_table_json, output_dir="extracted"):
    """Extract files using the organized file table."""
    
    with open(file_table_json, 'r') as f:
        file_table = json.load(f)
    
    os.makedirs(output_dir, exist_ok=True)
    
    files_by_type = file_table.get('files', {})
    total_files = sum(len(files) for files in files_by_type.values())
    
    print(f"Extracting {total_files} files from {len(files_by_type)} types...")
    
    with open(rom_path, 'rb') as rom:
        for file_type, files in files_by_type.items():
            print(f"\nProcessing {file_type} files ({len(files)} files)...")
            
            # Create subdirectory for this file type
            type_dir = os.path.join(output_dir, file_type)
            os.makedirs(type_dir, exist_ok=True)
            
            for file_info in files:
                filename = file_info['filename']
                start = int(file_info['start_addr'], 16)
                end = int(file_info['end_addr'], 16)
                size = file_info['size_bytes']
                
                rom.seek(start)
                data = rom.read(size)
                
                out_path = os.path.join(type_dir, filename)
                with open(out_path, 'wb') as out:
                    out.write(data)
                
                print(f"  {filename} ({size:,} bytes)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_from_table.py <rom_file> <file_table_json> [output_dir]")
        print("Example: python extract_from_table.py re2.z64 file_table.json extracted")
        sys.exit(1)
    
    rom_path = sys.argv[1]
    file_table_json = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "extracted"
    
    extract_from_file_table(rom_path, file_table_json, output_dir)
