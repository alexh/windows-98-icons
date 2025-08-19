#!/usr/bin/env python3
"""
Add Failed Icons to Database
Adds the 4 failed icons with descriptions directly to the database
"""

import sqlite3
import json
import os
from pathlib import Path

def main():
    print("🎯 Adding failed icons to database...")
    
    # Database path
    db_path = "static/icons.db"
    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    # Load the failed icons file
    with open('failed_icons_processed.json', 'r') as f:
        data = json.load(f)
    
    icons = data.get('processed_icons', [])
    print(f"📊 Found {len(icons)} failed icons to add")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("PRAGMA table_info(icons)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"📋 Database columns: {columns}")
    
    added = 0
    for icon in icons:
        name = icon['name']
        
        # Check if icon already exists
        cursor.execute("SELECT COUNT(*) FROM icons WHERE name = ?", (name,))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print(f"  ⚠️  {name} already exists, skipping")
            continue
        
        # Insert the icon
        insert_data = {
            'name': name,
            'filename': icon['filename'],
            'local_path': icon['local_path'],
            'description': icon['description'],
            'searchable_text': icon['searchable_text'],
            'width': icon['width'],
            'height': icon['height'],
            'embedding': None,  # Will add embeddings later
            'source_url': None,
            'alt_text': f"Icon {name}",
            'parent_text': "icon_gallery"
        }
        
        # Build dynamic insert query based on available columns
        available_columns = [col for col in insert_data.keys() if col in columns]
        placeholders = ', '.join(['?' for _ in available_columns])
        column_names = ', '.join(available_columns)
        values = [insert_data[col] for col in available_columns]
        
        query = f"INSERT INTO icons ({column_names}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, values)
            added += 1
            print(f"  ✅ Added {name}")
        except Exception as e:
            print(f"  ❌ Failed to add {name}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\\n🎉 Added {added}/{len(icons)} failed icons to database!")
    print("💡 Run the build script to regenerate embeddings and frontend")

if __name__ == "__main__":
    main()