#!/usr/bin/env python3
"""
ROM Scanner - Finds and extracts compressed/uncompressed files from ROM.
Usage: python rom_scanner.py <rom_file>
"""

import argparse
import csv
import json
import sys
import os
import zlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ScanResult:
    """Represents a discovered file/block in the ROM."""
    start_addr: int
    end_addr: int
    size: int
    file_type: str  # 'compressed', 'uncompressed', 'unknown'
    filename: Optional[str] = None
    extracted_path: Optional[str] = None
    metadata: Optional[Dict] = None

class ROMScanner:
    """Unified ROM scanner with CSV export."""
    
    # Known large data regions to skip during scanning
    KNOWN_REGIONS = [
        (0x00338FEA, 0x00B63105), # MORT blocks
        (0x01440F38, 0x02B7D8E9),  # Video files
        (0x02BDEFB2, 0x03AF17FD),  # JPEG files
        (0x03FD0DF6, 0x03FFFFFF),  # Empty data
    ]
    
    def __init__(self, rom_path: str, output_dir: str = "extracted_files"):
        self.rom_path = rom_path
        self.output_dir = output_dir
        self.rom_data = None
        self.results = []
        self.file_table = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load existing file table (read-only)
        self.load_file_table()
        
    def load_file_table(self):
        """Load existing file table (read-only)."""
        try:
            with open("file_table.json", 'r') as f:
                self.file_table = json.load(f)
            print("File table loaded (read-only)")
        except FileNotFoundError:
            print("No file_table.json found - will mark all as unknown")
            self.file_table = None
        
    def load_rom(self):
        """Load ROM data into memory."""
        print(f"Loading ROM: {self.rom_path}")
        with open(self.rom_path, 'rb') as f:
            self.rom_data = f.read()
        print(f"ROM loaded: {len(self.rom_data):,} bytes")
        
    def is_known_file(self, start_addr: int) -> Tuple[bool, str, str]:
        """Check if address is already known in file table."""
        if not self.file_table:
            return False, "unknown", ""
            
        files_by_type = self.file_table.get('files', {})
        
        # Check all file types for matching addresses
        for file_type, files in files_by_type.items():
            for file_info in files:
                file_start = int(file_info['start_addr'], 16)
                file_end = int(file_info['end_addr'], 16)
                
                if file_start <= start_addr <= file_end:
                    return True, file_type, file_info.get('filename', '')
        
        return False, "unknown", ""
            
    def scan_compressed_blocks(self, start_addr: int = 0, end_addr: Optional[int] = None) -> List[ScanResult]:
        """Scan for compressed blocks with 0x68DE header."""
        if end_addr is None:
            end_addr = len(self.rom_data)
            
        print(f"Scanning for compressed blocks: 0x{start_addr:08X} - 0x{end_addr:08X}")
        
        results = []
        i = start_addr
        
        while i < end_addr - 1:
            # Skip known large data regions
            if self._is_in_known_region(i):
                i = self._skip_known_region(i)
                continue
                
            # Look for compressed block header (68 DE)
            if self.rom_data[i] == 0x68 and self.rom_data[i + 1] == 0xDE:
                result = self._process_compressed_block(i, end_addr)
                if result:
                    results.append(result)
                    print(f"Found compressed block at 0x{i:08X} -> {result.filename}")
                    i = result.end_addr + 1
                else:
                    i += 1
            else:
                i += 1
                
        print(f"Compressed block scan complete: Found {len(results)} blocks")
        return results
        
    def scan_uncompressed_files(self, compressed_results: List[ScanResult]) -> List[ScanResult]:
        """Scan for uncompressed files using footer patterns in gaps between compressed files."""
        print(f"Scanning gaps for uncompressed files...")
        
        results = []
        
        # Find gaps between known regions
        gaps = self._find_gaps_between_regions(compressed_results)
        
        print(f"  Found {len(gaps)} gaps to scan")
        
        # Look for 00 01 00 00 footer pattern in gaps only
        pattern = bytes([0x00, 0x01, 0x00, 0x00])
        
        for gap_start, gap_end in gaps:
            gap_size = gap_end - gap_start + 1
            print(f"  Scanning gap: 0x{gap_start:08X} - 0x{gap_end:08X} ({gap_size:,} bytes)")
            
            for offset in range(gap_start, gap_end - 6):
                if self.rom_data[offset:offset + 4] == pattern:
                    print(f"    Found footer pattern at 0x{offset:08X}")
                    result = self._process_uncompressed_file(offset, gap_start, gap_end)
                    if result:
                        results.append(result)
                        print(f"      -> Extracted to {result.filename} ({result.size} bytes)")
                    else:
                        print(f"      -> Failed to process")
                    
        print(f"Uncompressed file scan complete: Found {len(results)} files")
        return results
        
    def _process_compressed_block(self, start_addr: int, max_end: int) -> Optional[ScanResult]:
        """Process a single compressed block."""
        try:
            # Find block end by looking for terminator
            block_end = self._find_compressed_block_end(start_addr, max_end)
            if block_end is None:
                return None
                
            # Extract compressed data
            compressed_data = self.rom_data[start_addr:block_end]
            
            # Check if this is a known file
            is_known, known_type, known_filename = self.is_known_file(start_addr)
            
            # Attempt decompression
            try:
                decompressed_data = zlib.decompress(compressed_data)
                
                # Use known filename if available, otherwise generate one
                if is_known and known_filename:
                    filename = known_filename
                else:
                    filename = f"decompressed_0x{start_addr:08X}.bin"
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(decompressed_data)
                    
            except zlib.error:
                # Decompression failed, treat as binary
                if is_known and known_filename:
                    filename = known_filename
                else:
                    filename = f"compressed_0x{start_addr:08X}.bin"
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(compressed_data)
                decompressed_data = compressed_data
                
            return ScanResult(
                start_addr=start_addr,
                end_addr=block_end - 1,
                size=len(compressed_data),
                file_type="compressed",
                filename=filename,
                extracted_path=filepath,
                metadata={
                    "decompressed_size": len(decompressed_data),
                    "compression_ratio": len(decompressed_data) / len(compressed_data)
                }
            )
            
        except Exception as e:
            return None
            
    def _process_uncompressed_file(self, footer_pos: int, gap_start: int, gap_end: int) -> Optional[ScanResult]:
        """Process a single uncompressed file."""
        try:
            # Check we have enough data to read the size field
            size_field_start = footer_pos + 4
            size_field_end = footer_pos + 8
            if size_field_end > len(self.rom_data):
                return None
                
            # Read file size from 4 bytes after footer
            size_bytes = self.rom_data[size_field_start:size_field_end]
            file_size = int.from_bytes(size_bytes, byteorder='big')
            
            # Calculate file boundaries
            # File layout: [file_data][footer: 00 01 00 00][size: 4 bytes]
            file_data_start = footer_pos - file_size
            file_data_end = footer_pos - 1  # Just before footer
            
            # Validate file boundaries make sense
            if (file_data_start < 0 or 
                file_data_start >= footer_pos or 
                file_size < 4 or 
                file_size > 0x1000000):
                return None
            
            # Check if calculated file region overlaps with existing regions
            complete_file_start = file_data_start
            complete_file_end = size_field_end - 1
            
            # Check if the entire file region is within the gap we're scanning
            if complete_file_start < gap_start or complete_file_end > gap_end:
                print(f"      -> File region 0x{complete_file_start:08X}-0x{complete_file_end:08X} extends outside gap 0x{gap_start:08X}-0x{gap_end:08X}")
                return None
                
            # Extract complete file (data + footer + size)
            file_data = self.rom_data[complete_file_start:complete_file_end + 1]
            
            # Check if this is a known file
            is_known, known_type, known_filename = self.is_known_file(file_data_start)
            
            # Use known filename if available, otherwise generate one
            if is_known and known_filename:
                filename = known_filename
            else:
                filename = f"uncompressed_0x{file_data_start:08X}.bin"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(file_data)
                
            return ScanResult(
                start_addr=complete_file_start,
                end_addr=complete_file_end,
                size=file_size,
                file_type="uncompressed",
                filename=filename,
                extracted_path=filepath,
                metadata={
                    "footer_pos": footer_pos,
                    "size_bytes": size_bytes.hex().upper()
                }
            )
            
        except Exception as e:
            print(f"Error processing uncompressed file at 0x{footer_pos:08X}: {e}")
            return None
            
    def _find_compressed_block_end(self, start_addr: int, max_end: int) -> Optional[int]:
        """Find the end of a compressed block."""
        # Look for 00 10 00 00 terminator
        for offset in range(start_addr + 2, min(start_addr + 1000000, max_end - 7)):
            if (self.rom_data[offset] == 0x00 and self.rom_data[offset + 1] == 0x10 and 
                self.rom_data[offset + 2] == 0x00 and self.rom_data[offset + 3] == 0x00):
                return offset + 8  # Include terminator (4 bytes) + size field (4 bytes)
                
        # If no terminator found, assume reasonable limit
        return min(start_addr + 1000000, max_end)
        
            
    def _is_in_known_region(self, addr: int) -> bool:
        """Check if address is in a known large data region."""
        for start, end in self.KNOWN_REGIONS:
            if start <= addr <= end:
                return True
        return False
        
    def _skip_known_region(self, addr: int) -> int:
        """Skip to the end of a known region."""
        for start, end in self.KNOWN_REGIONS:
            if start <= addr <= end:
                return end + 1
        return addr + 1
        
    def _find_gaps_between_regions(self, compressed_results: List[ScanResult]) -> List[Tuple[int, int]]:
        """Find gaps between all known regions in the ROM."""
        # Get all known file regions to avoid scanning them
        known_regions = []
        
        # Add compressed file regions
        for result in compressed_results:
            known_regions.append((result.start_addr, result.end_addr))
        
        # Add regions from file table
        if self.file_table:
            files_by_type = self.file_table.get('files', {})
            for file_type, files in files_by_type.items():
                for file_info in files:
                    file_start = int(file_info['start_addr'], 16)
                    file_end = int(file_info['end_addr'], 16)
                    known_regions.append((file_start, file_end))
        
        # Add known large data regions
        known_regions.extend(self.KNOWN_REGIONS)
        
        # Sort regions by start address
        known_regions.sort(key=lambda x: x[0])
        
        # Find gaps between known regions
        gaps = []
        current_addr = 0
        rom_size = len(self.rom_data)
        
        # Find gaps between known regions
        for start, end in known_regions:
            if current_addr < start:
                gap_size = start - current_addr
                gaps.append((current_addr, start - 1))
                if gap_size > 1024:  # Only log gaps larger than 1KB
                    print(f"  Large gap: 0x{current_addr:08X} - 0x{start-1:08X} ({gap_size:,} bytes)")
            current_addr = max(current_addr, end + 1)
        
        # Add final gap if needed
        if current_addr < rom_size:
            gap_size = rom_size - current_addr
            gaps.append((current_addr, rom_size - 1))
            if gap_size > 1024:
                print(f"  Final gap: 0x{current_addr:08X} - 0x{rom_size-1:08X} ({gap_size:,} bytes)")
        
        print(f"  Found {len(gaps)} gaps total")
        return gaps
        
    def _create_file_entry(self, result: ScanResult) -> Dict:
        """Create a file entry for CSV export."""
        is_known, known_type, _ = self.is_known_file(result.start_addr)
        compressed_size = result.size
        decompressed_size = result.metadata.get('decompressed_size', result.size) if result.metadata else result.size
        
        return {
            'Start Address': f"0x{result.start_addr:08X}",
            'End Address': f"0x{result.end_addr:08X}",
            'Size (bytes)': result.end_addr - result.start_addr + 1,
            'Type': 'File',
            'Subtype': result.file_type,
            'Known': "Yes" if is_known else "No",
            'Filename': result.filename or "",
            'Compressed Size': compressed_size,
            'Decompressed Size': decompressed_size
        }
        
    def _create_gap_entry(self, start_addr: int, end_addr: int) -> Dict:
        """Create a gap entry for CSV export."""
        return {
            'Start Address': f"0x{start_addr:08X}",
            'End Address': f"0x{end_addr:08X}",
            'Size (bytes)': end_addr - start_addr + 1,
            'Type': 'Gap',
            'Subtype': 'Unmapped',
            'Known': "No",
            'Filename': "",
            'Compressed Size': "",
            'Decompressed Size': ""
        }
        
    def export_to_csv(self):
        """Export scan results to CSV file."""
        csv_file = "rom_scan_results.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Start Address', 'End Address', 'Compressed Size', 'Decompressed Size', 'File Type', 
                'Known', 'Filename'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                row = self._create_file_entry(result)
                # Adjust field names for CSV export
                csv_row = {
                    'Start Address': row['Start Address'],
                    'End Address': row['End Address'],
                    'Compressed Size': row['Compressed Size'],
                    'Decompressed Size': row['Decompressed Size'],
                    'File Type': row['Subtype'],
                    'Known': row['Known'],
                    'Filename': row['Filename']
                }
                writer.writerow(csv_row)
                
        print(f"Results exported to CSV: {csv_file}")
        
    def generate_rom_map(self, output_file: str = "rom_map.csv"):
        """Generate a complete ROM map showing all regions and gaps."""
        if not self.results:
            print("No results to map")
            return
            
        # Sort results by start address
        sorted_results = sorted(self.results, key=lambda x: x.start_addr)
        
        # Create mapping data
        map_data = []
        rom_size = len(self.rom_data)
        
        # Add all discovered files
        for result in sorted_results:
            map_data.append(self._create_file_entry(result))
        
        # Add known regions as proper entries
        known_region_labels = {
            (0x00338FEA, 0x00B63105): "MORT blocks",
            (0x01440F38, 0x02B7D8E9): "Video files", 
            (0x02BDEFB2, 0x03AF17FD): "JPEG files",
            (0x03FD0DF6, 0x03FFFFFF): "Empty data"
        }
        
        for start, end in self.KNOWN_REGIONS:
            map_data.append({
                'Start Address': f"0x{start:08X}",
                'End Address': f"0x{end:08X}",
                'Size (bytes)': end - start + 1,
                'Type': 'Known Region',
                'Subtype': known_region_labels.get((start, end), 'Unknown'),
                'Known': "Yes",
                'Filename': "",
                'Compressed Size': "",
                'Decompressed Size': ""
            })
        
        # Sort all regions by start address
        all_regions = sorted(map_data, key=lambda x: int(x['Start Address'], 16))
        
        # Find actual gaps between all regions
        gaps = []
        current_addr = 0
        
        for region in all_regions:
            region_start = int(region['Start Address'], 16)
            region_end = int(region['End Address'], 16)
            
            if current_addr < region_start:
                gaps.append(self._create_gap_entry(current_addr, region_start - 1))
            current_addr = region_end + 1
        
        # Add final gap if ROM doesn't end with last region
        if current_addr < rom_size:
            gaps.append(self._create_gap_entry(current_addr, rom_size - 1))
        
        # Combine and sort all regions
        all_regions = all_regions + gaps
        all_regions.sort(key=lambda x: int(x['Start Address'], 16))
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Start Address', 'End Address', 'Size (bytes)', 'Type', 'Subtype',
                'Known', 'Filename', 'Compressed Size', 'Decompressed Size'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for region in all_regions:
                writer.writerow(region)
        
        # Print summary
        total_files = len([r for r in all_regions if r['Type'] == 'File'])
        total_known_regions = len([r for r in all_regions if r['Type'] == 'Known Region'])
        total_gaps = len(gaps)
        
        # Calculate sizes properly
        discovered_files_size = sum(r['Size (bytes)'] for r in all_regions if r['Type'] == 'File')
        known_regions_size = sum(r['Size (bytes)'] for r in all_regions if r['Type'] == 'Known Region')
        total_mapped = discovered_files_size + known_regions_size
        total_gap_size = rom_size - total_mapped
        
        print(f"ROM map generated: {output_file}")
        print(f"  Discovered files: {total_files}")
        print(f"  Known regions: {total_known_regions}")
        print(f"  Unmapped gaps: {total_gaps}")
        print(f"  Discovered files size: {discovered_files_size:,} bytes ({discovered_files_size / (1024*1024):.1f} MB)")
        print(f"  Known regions size: {known_regions_size:,} bytes ({known_regions_size / (1024*1024):.1f} MB)")
        print(f"  Total mapped: {total_mapped:,} bytes ({total_mapped / (1024*1024):.1f} MB)")
        print(f"  Unmapped gaps: {total_gap_size:,} bytes ({total_gap_size / (1024*1024):.1f} MB)")
        print(f"  Coverage: {(total_mapped / rom_size) * 100:.1f}%")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified ROM Scanner Pipeline")
    parser.add_argument("rom_file", help="Path to ROM file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.rom_file):
        print(f"Error: ROM file '{args.rom_file}' not found")
        sys.exit(1)
        
    # Initialize scanner
    scanner = ROMScanner(args.rom_file)
    scanner.load_rom()
    
    # Scan the whole ROM for both compressed and uncompressed files
    print("\n" + "="*60)
    print("STARTING ROM SCAN")
    print("="*60)
    
    print("\n1. Scanning for compressed blocks...")
    compressed_results = scanner.scan_compressed_blocks()
    
    print("\n2. Scanning for uncompressed files...")
    uncompressed_results = scanner.scan_uncompressed_files(compressed_results)

    # Store all results
    all_results = compressed_results + uncompressed_results
    scanner.results = all_results
    
    print(f"\n3. Exporting results...")
    scanner.export_to_csv()
    
    print(f"\n4. Generating ROM map...")
    scanner.generate_rom_map()
        
    print(f"\n" + "="*60)
    print("SCAN COMPLETE!")
    print("="*60)
    print(f"Total files found: {len(all_results)}")
    print(f"  - Compressed blocks: {len(compressed_results)}")
    print(f"  - Uncompressed files: {len(uncompressed_results)}")
    print(f"Results exported to: rom_scan_results.csv")
    print(f"ROM map exported to: rom_map.csv")
    print(f"Files extracted to: extracted_files/")

if __name__ == "__main__":
    main()
