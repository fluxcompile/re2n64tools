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

def decode_palette_entries(palette_data):
    """Decode palette data into 16-bit entries."""
    return [(palette_data[i] << 8) | palette_data[i + 1] 
            for i in range(0, len(palette_data), 2)]

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
    
    # Calculate grid dimensions (prefer wider grids)
    cols = min(palette_count, 4)  # Max 4 columns
    rows = (palette_count + cols - 1) // cols  # Ceiling division
    
    # Create combined image
    combined_width = width * cols
    combined_height = height * rows
    combined_pixels = np.zeros((combined_height, combined_width, 3), dtype=np.uint8)
    
    for palette_idx in range(palette_count):
        # Calculate palette start/end based on actual palette size
        palette_start = palette_idx * palette_color_size
        palette_end = palette_start + palette_color_size
        
        if palette_end > len(palette_entries):
            print(f"  [WARN] Palette {palette_idx} extends beyond available entries")
            break
        
        # Extract this palette's entries
        current_palette_entries = palette_entries[palette_start:palette_end]
        palette_rgb = decode_palette_to_rgb(current_palette_entries)
        pixels = render_palette_image(pixel_indices, palette_rgb, width, height)
        
        # Calculate position in combined image
        row = palette_idx // cols
        col = palette_idx % cols
        y_start = row * height
        y_end = y_start + height
        x_start = col * width
        x_end = x_start + width
        
        # Place in combined image
        combined_pixels[y_start:y_end, x_start:x_end] = pixels
        
        print(f"  [OK] Added palette {palette_idx} at position ({row}, {col})")
    
    # Create PIL Image and save as PNG
    img = Image.fromarray(combined_pixels)
    img.save(output_path, 'PNG')
    
    print(f"  [OK] Saved combined image ({rows}x{cols} grid): {output_path}")
    
def convert_16bit_palette_to_png(compressed_data, output_path):
    """Convert 16-bit palette image data to PNG format."""
    try:
        # Decompress the data
        decompressed = zlib.decompress(compressed_data)
        
        # Parse header from decompressed data
        start_offset = 20
        print(f"  Decompressed size: {len(decompressed)} bytes")

        # Parse header into 5 uint32 big-endian values
        header_values = [int.from_bytes(decompressed[i:i+4], byteorder='big') 
                        for i in range(0, start_offset, 4)]
        print(f"  Header values: {header_values}")

        width = header_values[1]
        height = header_values[2]
        print(f"  Dimensions from header: {width}x{height}")

        palette_color_size = header_values[3]
        if palette_color_size not in [16, 256]:
            print(f"  [WARN] Unexpected palette size: {palette_color_size}, expected 16 (CI4) or 256 (CI8)")
            return False
        
        # Determine format: CI4 (16 colors) or CI8 (256 colors)
        format_name = "CI4" if palette_color_size == 16 else "CI8"
        print(f"  Format: {format_name} ({palette_color_size} colors)")

        palette_count = header_values[4]
        print(f"  Palette count: {palette_count}")
        
        # Sanity check - palette count should be reasonable
        if palette_count > 100 or palette_count < 1:
            print(f"  [WARN] Unreasonable palette count {palette_count}, using default of 1")
            palette_count = 1

        # Calculate sizes
        palette_color_bytes = 2  # 16-bit RGBA5551 per color
        palette_size = palette_color_size * palette_color_bytes * palette_count
        
        # Pixel indices: CI8 uses 8-bit indices, CI4 uses 4-bit packed indices
        if palette_color_size == 256:  # CI8
            pixel_indices_size = width * height  # 8-bit indices
        else:  # CI4
            pixel_indices_size = (width * height + 1) // 2  # 4-bit indices packed
        
        expected_total = start_offset + pixel_indices_size + palette_size
        if expected_total != len(decompressed):
            print(f"  [WARN] Unexpected decompressed size: expected {expected_total}, got {len(decompressed)}")

        # Extract data sections
        pixel_indices_raw = decompressed[start_offset:start_offset+pixel_indices_size]
        palette_data = decompressed[-palette_size:]
        
        # Convert pixel indices based on format
        if palette_color_size == 256:  # CI8 - 8-bit indices
            pixel_indices = list(pixel_indices_raw)
        else:  # CI4 - 4-bit packed indices (big-endian)
            pixel_indices = []
            for byte in pixel_indices_raw:
                pixel_indices.append((byte >> 4) & 0x0F)  # Upper 4 bits (first pixel)
                pixel_indices.append(byte & 0x0F)  # Lower 4 bits (second pixel)
            # Trim to exact pixel count
            pixel_indices = pixel_indices[:width * height]
        
        print(f"  Pixel indices: {len(pixel_indices)} pixels ({format_name}), Palette data: {len(palette_data)} bytes")
        
        # Decode all palette entries
        palette_entries = decode_palette_entries(palette_data)
        print(f"  Total palette entries: {len(palette_entries)}")
        
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

    if 'format' in file_info and file_info['format'] in ['CI4', 'CI8']:
        format_type = file_info['format']
        print(f"  Converting {format_type} palette image: {filename} ({size:,} bytes)")
        
        if convert_16bit_palette_to_png(data, output_path):
            print(f"  [OK] Converted to PNG: {filename}")
            return True
        else:
            print(f"  [FAIL] Failed to convert: {filename}")
            return False

    elif 'image_width' in file_info and 'image_height' in file_info:
        width = file_info['image_width']
        height = file_info['image_height']
        format_type = file_info.get('format', '24-bit')
        
        print(f"  Converting compressed image: {filename} ({size:,} bytes) -> {width}x{height} {format_type} PNG")
        
        if convert_compressed_binary_to_png(data, width, height, output_path, format_type):
            print(f"  [OK] Converted to PNG: {filename}")
            return True
        else:
            print(f"  [FAIL] Failed to convert: {filename}")
            return False
    else:
        # Unknown format - save as raw data
        print(f"  Unknown image format for {filename}, saving as raw data")
        with open(output_path, 'wb') as out:
            out.write(data)
        return True

def calculate_file_size(file_info, file_type, start_addr, end_addr):
    """Calculate the size to read for a file based on its type and compression."""
    if 'is_compressed' in file_info:
        # If is_compressed flag exists (regardless of true/false), subtract 8-byte footer
        return end_addr - start_addr + 1 - 8
    else:
        # For files without is_compressed flag, read full data
        return end_addr - start_addr + 1

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
        
        # Determine bytes per pixel based on format
        if format_type == "24-bit":
            bytes_per_pixel = 3
            pil_mode = 'RGB'
        elif format_type == "16-bit":
            bytes_per_pixel = 2
            pil_mode = 'RGB'  # Will need conversion
        elif format_type == "32-bit":
            bytes_per_pixel = 4
            pil_mode = 'RGBA'
        else:
            print(f"  Warning: Unknown format '{format_type}', defaulting to 24-bit")
            bytes_per_pixel = 3
            pil_mode = 'RGB'
        
        pixel_count = width * height
        expected_size = pixel_count * bytes_per_pixel
        
        if len(decompressed) != expected_size:
            print(f"  Warning: Expected {expected_size} bytes, got {len(decompressed)} bytes")
            # Truncate or pad as needed
            if len(decompressed) > expected_size:
                decompressed = decompressed[:expected_size]
            else:
                decompressed = decompressed + b'\x00' * (expected_size - len(decompressed))
        
        # Convert to numpy array and reshape
        pixels = np.frombuffer(decompressed, dtype=np.uint8)
        
        if format_type == "16-bit":
            # Reshape to 2-byte words (big-endian)
            pixels = pixels.reshape((height, width, 2))
            
            # Convert to 16-bit words (big-endian)
            words = (pixels[:, :, 0].astype(np.uint16) << 8) | pixels[:, :, 1].astype(np.uint16)
            
            # Decode RGBA5551: 5 bits R, 5 bits G, 5 bits B, 1 bit A (ignored)
            rgb_pixels = np.array([decode_rgba5551_to_rgb(word) for word in words.flatten()], dtype=np.uint8)
            rgb_pixels = rgb_pixels.reshape((height, width, 3))
            pixels = rgb_pixels
        else:
            pixels = pixels.reshape((height, width, bytes_per_pixel))
        
        # Create PIL Image and save as PNG
        img = Image.fromarray(pixels)
        img.save(output_path, 'PNG')
        
        return True
        
    except Exception as e:
        print(f"  Error converting compressed binary: {e}")
        return False

def extract_from_file_table(rom_path, file_table_json, output_dir="extracted", filter_type=None):
    """Extract files using the organized file table."""
    
    with open(file_table_json, 'r') as f:
        file_table = json.load(f)
    
    os.makedirs(output_dir, exist_ok=True)
    
    files_by_type = file_table.get('files', {})
    
    # Apply filter if specified
    if filter_type:
        if filter_type in files_by_type:
            files_by_type = {filter_type: files_by_type[filter_type]}
            print(f"Filtering to {filter_type} files only...")
        else:
            print(f"Error: File type '{filter_type}' not found in file table")
            print(f"Available types: {', '.join(files_by_type.keys())}")
            return
    
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
                start = int(file_info['start_addr'], 16)
                end = int(file_info['end_addr'], 16)
                
                # Calculate size to read
                size = calculate_file_size(file_info, file_type, start, end)
                
                rom.seek(start)
                data = rom.read(size)
                
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
                    print(f"  {filename} ({size:,} bytes)")
    
    # Generate CSV for text blocks if any were processed
    if text_blocks_data:
        csv_path = os.path.join(output_dir, "text_blocks_summary.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['start_addr', 'end_addr', 'filename', 'content']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in text_blocks_data:
                writer.writerow(row)
        print(f"\nText blocks summary saved to: {csv_path}")
    
    print(f"\nExtraction complete! Files saved to: {output_dir}/")

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
    
    extract_from_file_table(rom_path, file_table_json, output_dir, filter_type)
