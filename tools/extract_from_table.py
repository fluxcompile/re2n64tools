#!/usr/bin/env python3
"""
Extract assets from ROM using a pre-built file table.
"""

import json
import os
import sys
import csv
import zlib
import numpy as np
from PIL import Image

def decode_rgba5551_to_rgb(value):
    """Decode a single RGBA5551 value to RGB tuple."""
    r = ((value >> 11) & 0x1F) * 255 // 31
    g = ((value >> 6) & 0x1F) * 255 // 31
    b = ((value >> 1) & 0x1F) * 255 // 31
    return (r, g, b)

def decode_palette_to_rgb(palette_entries):
    """Decode palette entries to RGB values."""
    return [decode_rgba5551_to_rgb(entry) for entry in palette_entries]

def render_palette_image(pixel_indices, palette_rgb, width, height):
    """Render image using pixel indices and palette."""
    pixels = [palette_rgb[idx] if idx < len(palette_rgb) else (0, 0, 0) 
              for idx in pixel_indices]
    
    return np.array(pixels, dtype=np.uint8).reshape((height, width, 3))

def render_single_palette(pixel_indices, palette_entries, width, height, output_path):
    """Render image with single palette."""
    palette_rgb = decode_palette_to_rgb(palette_entries)
    pixels = render_palette_image(pixel_indices, palette_rgb, width, height)
    
    img = Image.fromarray(pixels)
    img.save(output_path, 'PNG')
    print(f"  [OK] Saved single palette: {output_path}")

def render_multiple_palettes(pixel_indices, palette_entries, palette_count, width, height, output_path, palette_color_size=256):
    """Render image with multiple palettes in a grid layout."""
    print(f"  Combining {palette_count} palettes into grid...")
    
    # Calculate grid dimensions
    cols = min(palette_count, 4)
    rows = (palette_count + cols - 1) // cols
    
    # Create combined image
    combined_pixels = np.zeros((height * rows, width * cols, 3), dtype=np.uint8)
    
    for i in range(palette_count):
        # Extract palette data
        start = i * palette_color_size
        end = start + palette_color_size
        
        if end > len(palette_entries):
            print(f"  [WARN] Palette {i} extends beyond available entries")
            break
        
        # Render this palette
        palette_rgb = decode_palette_to_rgb(palette_entries[start:end])
        pixels = render_palette_image(pixel_indices, palette_rgb, width, height)
        
        # Place in grid
        row, col = i // cols, i % cols
        y1, y2 = row * height, (row + 1) * height
        x1, x2 = col * width, (col + 1) * width
        combined_pixels[y1:y2, x1:x2] = pixels
    
    # Save image
    Image.fromarray(combined_pixels).save(output_path, 'PNG')
    print(f"  [OK] Saved combined image ({rows}x{cols} grid): {output_path}")
    
def convert_16bit_palette_to_png(compressed_data, output_path):
    """Convert 16-bit palette image data to PNG format."""
    try:
        # Decompress the data
        decompressed = zlib.decompress(compressed_data)
        
        # Parse header from decompressed data
        start_offset = 20

        # Parse header into 5 uint32 big-endian values
        header_values = [int.from_bytes(decompressed[i:i+4], byteorder='big') 
                        for i in range(0, start_offset, 4)]
        print(f"  Header values: {header_values}")

        width = header_values[1]
        height = header_values[2]
        palette_color_size = header_values[3]
        palette_count = header_values[4]

        if palette_color_size not in [16, 256]:
            print(f"  [WARN] Unexpected palette size: {palette_color_size}, expected 16 (CI4) or 256 (CI8)")
            return False
        
        # Determine format: CI4 (16 colors) or CI8 (256 colors)
        format_name = "CI4" if palette_color_size == 16 else "CI8"
        
        print(f"  {width}x{height} {format_name} ({palette_color_size} colors, {palette_count} palettes)")

        # Sanity check - palette count should be reasonable
        if palette_count > 100 or palette_count < 1:
            print(f"  [WARN] Unreasonable palette count {palette_count}, using default of 1")
            palette_count = 1

        # Calculate sizes
        palette_color_bytes = 2  # 16-bit RGBA5551 per color
        palette_size = palette_color_size * palette_color_bytes * palette_count
        
        # Calculate pixel indices size
        if format_name == "CI8":
            pixel_indices_size = width * height
        else:  # CI4
            pixel_indices_size = (width * height + 1) // 2
        
        expected_total = start_offset + pixel_indices_size + palette_size
        if expected_total != len(decompressed):
            print(f"  [WARN] Unexpected decompressed size: expected {expected_total}, got {len(decompressed)}")

        # Extract data sections
        pixel_indices_raw = decompressed[start_offset:start_offset+pixel_indices_size]
        palette_data = decompressed[-palette_size:]
        
        # Convert pixel indices based on format
        def unpack_ci4_indices(data, pixel_count):
            """Unpack 4-bit packed indices to 8-bit indices."""
            indices = []
            for byte in data:
                indices.append((byte >> 4) & 0x0F)  # Upper 4 bits
                indices.append(byte & 0x0F)  # Lower 4 bits
            return indices[:pixel_count]  # Trim to exact count
        
        if format_name == "CI8":
            pixel_indices = list(pixel_indices_raw)
        else:  # CI4
            pixel_indices = unpack_ci4_indices(pixel_indices_raw, width * height)
        
        print(f"  Pixel indices: {len(pixel_indices)} pixels ({format_name}), Palette data: {len(palette_data)} bytes")
        
        # Decode all palette entries
        palette_entries = np.frombuffer(palette_data, dtype='>u2').tolist()
        
        # Render based on palette count
        if palette_count == 1:
            render_single_palette(pixel_indices, palette_entries, width, height, output_path)
        else:
            render_multiple_palettes(pixel_indices, palette_entries, palette_count, width, height, output_path, palette_color_size)
        
        return True
        
    except Exception as e:
        print(f"  Error converting 16-bit palette: {e}")
        return False

def handle_compressed_image(file_info, data, output_path, filename):
    """Handle extraction and conversion of compressed images."""
    size = len(data)
    print(f"  Converting image: {filename} ({size:,} bytes)")

    # Early return if no format
    if 'format' not in file_info:
        print(f"  [WARN] No format specified: {filename}")
        return False

    format_type = file_info['format']

    # Handle palette formats (CI4/CI8)
    if format_type in ['CI4', 'CI8']:
        if convert_16bit_palette_to_png(data, output_path):
            print(f"  [OK] Converted palette image: {filename}")
            return True

    # Handle binary formats (16-bit, 24-bit)
    if format_type in ['16-bit', '24-bit'] and 'image_width' in file_info and 'image_height' in file_info:
        width = file_info['image_width']
        height = file_info['image_height']
        
        if convert_compressed_binary_to_png(data, width, height, output_path, format_type):
            print(f"  [OK] Converted binary image: {filename}")
            return True

    # Unknown format
    print(f"  [WARN] Unknown format '{format_type}': {filename}")
    return False

def calculate_file_size(file_info, file_type, start_addr, end_addr):
    """Calculate the size to read for a file based on its type and compression."""
    if 'is_compressed' in file_info:
        # If is_compressed flag exists (regardless of true/false), subtract 8-byte footer
        return end_addr - start_addr + 1 - 8
    else:
        # For files without is_compressed flag, read full data
        return end_addr - start_addr + 1

def read_file_data(rom, file_info, file_type):
    """Read file data from ROM based on file info."""
    start = int(file_info['start_addr'], 16)
    end = int(file_info['end_addr'], 16)
    size = calculate_file_size(file_info, file_type, start, end)
    
    rom.seek(start)
    return rom.read(size)

def handle_text_extraction(file_info, data, output_path, filename):
    """Handle text extraction for both compressed and uncompressed text blocks."""
    try:
        if file_info.get('is_compressed'):
            text_data = zlib.decompress(data)
        else:
            text_data = data

        # Convert to text and save
        text_content = text_data.decode('utf-8', errors='replace')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"  {filename} ({len(text_data)} bytes)")
        return True, text_content
        
    except Exception as e:
        print(f"  Error handling text block: {e}")
        return False, None

def convert_compressed_binary_to_png(compressed_data, width, height, output_path, format_type="24-bit"):
    """Convert compressed binary image data to PNG format."""
    try:
        # Decompress the data
        decompressed = zlib.decompress(compressed_data)
        
        # Convert to image
        if format_type == "16-bit":
            # Convert 16-bit RGBA5551 to RGB
            words = np.frombuffer(decompressed, dtype='>u2').reshape((height, width))
            rgb_pixels = [decode_rgba5551_to_rgb(word) for word in words.flatten()]
            image_data = np.array(rgb_pixels, dtype=np.uint8).reshape((height, width, 3))
        else:
            # 24-bit RGB
            image_data = np.frombuffer(decompressed, dtype=np.uint8).reshape((height, width, 3))
        
        # Save as PNG
        Image.fromarray(image_data).save(output_path, 'PNG')
        return True
        
    except Exception as e:
        print(f"  Error converting compressed binary: {e}")
        return False

def extract_from_file_table(rom_path, files_by_type, output_dir="extracted"):
    """Extract files using the organized file table."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    total_files = sum(len(files) for files in files_by_type.values())
    
    print(f"Extracting {total_files} files from {len(files_by_type)} types...")
    
    # Track text blocks for CSV generation
    text_blocks_data = []
    
    with open(rom_path, 'rb') as rom:
        for file_type, files in files_by_type.items():
            print(f"\nProcessing {file_type} files ({len(files)} files)...")
            
            # Create subdirectory for this file type
            type_dir = os.path.join(output_dir, file_type)
            os.makedirs(type_dir, exist_ok=True)
            
            for file_info in files:
                filename = file_info['filename']
                data = read_file_data(rom, file_info, file_type)
                out_path = os.path.join(type_dir, filename)
                
                # Special handling for compressed images
                if file_type == 'compressed_images':
                    if not handle_compressed_image(file_info, data, out_path, filename):
                        # Fallback: save raw data
                        with open(out_path, 'wb') as out:
                            out.write(data)
                # Special handling for text blocks
                elif file_type == 'text_blocks':
                    success, text_content = handle_text_extraction(file_info, data, out_path, filename)
                    if success and text_content:
                        # Collect text block data for CSV
                        text_blocks_data.append({
                            'start_addr': file_info['start_addr'],
                            'end_addr': file_info['end_addr'],
                            'filename': filename,
                            'content': text_content
                        })
                else:
                    # Normal file extraction
                    with open(out_path, 'wb') as out:
                        out.write(data)
                    print(f"  {filename} ({len(data):,} bytes)")
    
    # Generate CSV for text blocks if any were processed
    if text_blocks_data:
        write_text_blocks_csv(text_blocks_data, output_dir)
    
    print(f"\nExtraction complete! Files saved to: {output_dir}/")

def write_text_blocks_csv(text_blocks_data, output_dir):
    """Write text blocks data to CSV file."""
    csv_path = os.path.join(output_dir, "text_blocks_summary.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['start_addr', 'end_addr', 'filename', 'content']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in text_blocks_data:
            writer.writerow(row)
    print(f"\nText blocks summary saved to: {csv_path}")

def load_and_filter_file_table(file_table_json, filter_type=None):
    """Load file table and apply filter if specified."""
    with open(file_table_json, 'r') as f:
        file_table = json.load(f)
    
    files_by_type = file_table.get('files', {})
    
    if filter_type:
        if filter_type in files_by_type:
            print(f"Filtering to {filter_type} files only...")
            return {filter_type: files_by_type[filter_type]}
        else:
            print(f"Error: File type '{filter_type}' not found in file table")
            print(f"Available types: {', '.join(files_by_type.keys())}")
            return None
    
    return files_by_type

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_from_table.py <rom_file> <file_table_json> [output_dir] [--filter type]")
        print("Example: python extract_from_table.py re2.z64 file_table.json extracted_assets")
        print("         python extract_from_table.py re2.z64 file_table.json extracted_assets --filter compressed_images")
        sys.exit(1)
    
    rom_path = sys.argv[1]
    file_table_json = sys.argv[2]
    
    # Parse arguments
    output_dir = "extracted_assets"
    filter_type = None
    
    # Look for --filter argument
    if '--filter' in sys.argv:
        filter_idx = sys.argv.index('--filter')
        if filter_idx + 1 < len(sys.argv):
            filter_type = sys.argv[filter_idx + 1]
        else:
            print("Error: --filter requires a file type")
            sys.exit(1)
    
    # Set output_dir (only if it's not --filter)
    if len(sys.argv) > 3 and not sys.argv[3].startswith('--'):
        output_dir = sys.argv[3]
    
    # Load and filter file table
    files_by_type = load_and_filter_file_table(file_table_json, filter_type)
    if files_by_type is None:
        sys.exit(1)
    
    extract_from_file_table(rom_path, files_by_type, output_dir)
