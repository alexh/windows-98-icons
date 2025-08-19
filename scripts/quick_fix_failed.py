#!/usr/bin/env python3
"""
Quick fix for failed icons - add dummy embeddings and rebuild
"""

import sqlite3
import json
from pathlib import Path

def main():
    print("🚀 Quick fix for failed icons...")
    
    # Database path
    db_path = "static/icons.db"
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a dummy 768-dimension embedding (all zeros)
    dummy_embedding = json.dumps([0.0] * 768)
    
    # Update the 4 failed icons with dummy embeddings
    failed_names = [
        'media_player_stream_mono_0',
        'media_player_stream_no2_0', 
        'media_player_stream_stereo_0',
        'odbc_6'
    ]
    
    updated = 0
    for name in failed_names:
        cursor.execute(
            "UPDATE icons SET embedding = ? WHERE name = ? AND (embedding IS NULL OR embedding = '')",
            (dummy_embedding, name)
        )
        if cursor.rowcount > 0:
            updated += 1
            print(f"  ✅ Updated {name}")
    
    conn.commit()
    conn.close()
    
    print(f"🎉 Updated {updated} icons with dummy embeddings")
    print("💡 Now rebuilding frontend...")

if __name__ == "__main__":
    main()