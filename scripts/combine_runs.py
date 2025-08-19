#!/usr/bin/env python3
"""
Combine Multiple Processing Runs

Combines successful results from multiple process_icons.py runs with deduplication.
Usage: uv run python combine_runs.py output1.json output2.json output3.json
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set


def load_processed_file(file_path: str) -> List[Dict[str, Any]]:
    """Load processed icons from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return []
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            icons = data.get('processed_icons', [])
            print(f"📄 Loaded {len(icons)} icons from {path.name}")
            return icons
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return []


def deduplicate_icons(all_icons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate icons, keeping the first occurrence of each name."""
    seen_names: Set[str] = set()
    deduplicated: List[Dict[str, Any]] = []
    duplicates_count = 0
    
    for icon in all_icons:
        name = icon.get('name', '')
        if name and name not in seen_names:
            seen_names.add(name)
            deduplicated.append(icon)
        else:
            duplicates_count += 1
            if name:
                print(f"  🗑️ Skipping duplicate: {name}")
            else:
                print(f"  🗑️ Skipping icon with no name")
    
    print(f"📊 Deduplication: {len(all_icons)} → {len(deduplicated)} icons ({duplicates_count} duplicates removed)")
    return deduplicated


def validate_icon_data(icon: Dict[str, Any]) -> bool:
    """Validate that an icon has all required fields."""
    required_fields = ['name', 'description', 'embedding', 'local_path']
    missing_fields = []
    
    for field in required_fields:
        if field not in icon or not icon[field]:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"  ⚠️ Icon {icon.get('name', 'unknown')} missing fields: {missing_fields}")
        return False
    
    # Check embedding is a list of numbers
    embedding = icon.get('embedding', [])
    if not isinstance(embedding, list) or len(embedding) == 0:
        print(f"  ⚠️ Icon {icon.get('name', 'unknown')} has invalid embedding")
        return False
    
    return True


def combine_runs(input_files: List[str], output_file: str = None) -> str:
    """Combine multiple processing runs into a single file."""
    if not input_files:
        print("❌ No input files provided")
        return ""
    
    print(f"🔄 Combining {len(input_files)} processing runs...")
    
    # Load all icons from all files
    all_icons: List[Dict[str, Any]] = []
    file_stats = {}
    
    for file_path in input_files:
        icons = load_processed_file(file_path)
        file_stats[Path(file_path).name] = len(icons)
        all_icons.extend(icons)
    
    print(f"\n📊 File statistics:")
    for filename, count in file_stats.items():
        print(f"  {filename}: {count} icons")
    
    if not all_icons:
        print("❌ No icons loaded from any file")
        return ""
    
    print(f"\n📦 Total icons loaded: {len(all_icons)}")
    
    # Deduplicate icons
    print("\n🧹 Deduplicating icons...")
    deduplicated_icons = deduplicate_icons(all_icons)
    
    # Validate icon data
    print("\n✅ Validating icon data...")
    valid_icons = []
    invalid_count = 0
    
    for icon in deduplicated_icons:
        if validate_icon_data(icon):
            valid_icons.append(icon)
        else:
            invalid_count += 1
    
    print(f"📊 Validation: {len(deduplicated_icons)} → {len(valid_icons)} icons ({invalid_count} invalid removed)")
    
    if not valid_icons:
        print("❌ No valid icons remaining after validation")
        return ""
    
    # Create output filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"outputs/combined_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = str(output_dir / "icons_processed_combined.json")
    
    # Sort icons by name for consistency
    valid_icons.sort(key=lambda x: x.get('name', ''))
    
    # Save combined results
    combined_data = {
        "processed_icons": valid_icons,
        "total_count": len(valid_icons),
        "timestamp": time.time(),
        "embedding_model": "text-embedding-3-small",
        "vision_model": "gpt-4o-mini",
        "combined_run": True,
        "source_files": input_files,
        "file_stats": file_stats,
        "deduplication_stats": {
            "total_loaded": len(all_icons),
            "after_dedup": len(deduplicated_icons),
            "after_validation": len(valid_icons),
            "duplicates_removed": len(all_icons) - len(deduplicated_icons),
            "invalid_removed": invalid_count
        }
    }
    
    print(f"\n💾 Saving combined results...")
    with open(output_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"✅ Combined file saved: {output_file}")
    print(f"📊 Final count: {len(valid_icons)} unique, valid icons")
    
    return output_file


def list_available_files():
    """List available processed files in outputs directory."""
    print("📄 Available processed files:")
    
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        print("  No outputs directory found")
        return
    
    # Find all processed icon files
    processed_files = []
    for subdir in outputs_dir.iterdir():
        if subdir.is_dir():
            for file in subdir.glob("icons_processed*.json"):
                processed_files.append(file)
    
    if not processed_files:
        print("  No processed files found")
        return
    
    # Sort by modification time (newest first)
    processed_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for file in processed_files:
        # Get file size and modification time
        stat = file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        
        # Get icon count if possible
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                count = len(data.get('processed_icons', []))
                print(f"  {file.relative_to(outputs_dir)} ({count} icons, {size_mb:.1f}MB, {mtime})")
        except:
            print(f"  {file.relative_to(outputs_dir)} ({size_mb:.1f}MB, {mtime})")


def main():
    """Main function to combine processing runs."""
    if len(sys.argv) < 2:
        print("❌ Usage: uv run python combine_runs.py file1.json file2.json [file3.json ...]")
        print()
        list_available_files()
        print()
        print("💡 Example:")
        print("  uv run python combine_runs.py outputs/20241219_143052/icons_processed.json outputs/retry_20241219_150000/icons_processed_retry.json")
        return
    
    input_files = sys.argv[1:]
    
    # Validate input files exist
    valid_files = []
    for file_path in input_files:
        if Path(file_path).exists():
            valid_files.append(file_path)
        else:
            print(f"⚠️ File not found, skipping: {file_path}")
    
    if not valid_files:
        print("❌ No valid input files found")
        return
    
    # Combine the runs
    output_file = combine_runs(valid_files)
    
    if output_file:
        print(f"\n🎉 Success! Combined file ready for database building:")
        print(f"  uv run python build_db.py {output_file}")


if __name__ == "__main__":
    main()