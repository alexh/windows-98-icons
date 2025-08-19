#!/usr/bin/env python3
"""
SQLite Database Builder with Vector Search

Creates a SQLite database with sqlite-vec extension for the processed Windows 98 icons.
The database will be served as a static file for client-side search.
"""

import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import glob
import os

import sqlite_vec


class DatabaseBuilder:
    def __init__(self, db_path: str = "static/icons.db", input_file: str = None):
        self.db_path = Path(db_path)
        self.input_file = self.find_latest_processed_file(input_file)
        self.embedding_dimensions = int(os.getenv('EMBEDDING_DIMENSIONS', '768'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"🔢 Using embedding dimensions: {self.embedding_dimensions}")
        
        # Remove existing database
        if self.db_path.exists():
            self.db_path.unlink()
            print(f"🗑️ Removed existing database: {self.db_path}")
    
    def find_latest_processed_file(self, input_file: str = None) -> Path:
        """Find the latest icons_processed.json file."""
        if input_file and Path(input_file).exists():
            return Path(input_file)
        
        # Look for the most recent output directory
        output_dirs = glob.glob("outputs/*/icons_processed.json")
        if output_dirs:
            # Sort by modification time, newest first
            latest_file = max(output_dirs, key=lambda x: Path(x).stat().st_mtime)
            print(f"📁 Found latest processed file: {latest_file}")
            return Path(latest_file)
        
        # Fallback to root directory
        root_file = Path("icons_processed.json")
        if root_file.exists():
            return root_file
            
        raise FileNotFoundError("No icons_processed.json found. Run process_icons.py first.")
    
    def load_processed_data(self) -> Dict[str, Any]:
        """Load the processed icons data."""
        print(f"📄 Loading data from: {self.input_file}")
        with open(self.input_file, 'r') as f:
            return json.load(f)
    
    def create_database(self):
        """Create SQLite database with vector search capabilities."""
        print(f"🏗️ Creating database: {self.db_path}")
        
        # Connect and enable vector extension
        conn = sqlite3.connect(str(self.db_path))
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        
        # Create main icons table
        conn.execute("""
            CREATE TABLE icons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                local_path TEXT NOT NULL,
                description TEXT NOT NULL,
                searchable_text TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Metadata from scraping
                source_url TEXT,
                alt_text TEXT,
                parent_text TEXT
            )
        """)
        
        # Create virtual table for vector search using sqlite-vec
        conn.execute(f"""
            CREATE VIRTUAL TABLE icon_embeddings USING vec0(
                icon_id INTEGER PRIMARY KEY,
                embedding FLOAT[{self.embedding_dimensions}]
            )
        """)
        
        # Create indexes for better search performance
        conn.execute("CREATE INDEX idx_icons_name ON icons(name)")
        conn.execute("CREATE INDEX idx_icons_description ON icons(description)")
        conn.execute("CREATE INDEX idx_icons_searchable_text ON icons(searchable_text)")
        
        # Create FTS (Full Text Search) table for text search
        conn.execute("""
            CREATE VIRTUAL TABLE icons_fts USING fts5(
                name, 
                description, 
                searchable_text,
                content='icons',
                content_rowid='id'
            )
        """)
        
        print("✅ Database schema created")
        return conn
    
    def insert_icons(self, conn: sqlite3.Connection, processed_data: Dict[str, Any]):
        """Insert processed icons into the database."""
        icons = processed_data.get('processed_icons', [])
        total_icons = len(icons)
        
        if total_icons == 0:
            print("❌ No processed icons found!")
            return
        
        print(f"📥 Inserting {total_icons} icons...")
        
        inserted_count = 0
        failed_count = 0
        
        for icon in icons:
            try:
                # Get source data for additional metadata
                source_data = icon.get('source_data', {})
                
                # Insert main icon record
                cursor = conn.execute("""
                    INSERT INTO icons (
                        name, filename, local_path, description, searchable_text,
                        width, height, embedding, source_url, alt_text, parent_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    icon['name'],
                    icon['filename'],
                    icon['local_path'],
                    icon['description'],
                    icon['searchable_text'],
                    icon.get('width'),
                    icon.get('height'),
                    json.dumps(icon.get('embedding')) if icon.get('embedding') and len(icon.get('embedding', [])) == self.embedding_dimensions else None,
                    source_data.get('src', ''),
                    source_data.get('alt', ''),
                    source_data.get('parent_text', '')
                ))
                
                icon_id = cursor.lastrowid
                
                # Insert vector embedding
                embedding = icon.get('embedding')
                if embedding and len(embedding) == self.embedding_dimensions:
                    conn.execute("""
                        INSERT INTO icon_embeddings (icon_id, embedding)
                        VALUES (?, ?)
                    """, (icon_id, json.dumps(embedding)))
                else:
                    print(f"⚠️ Invalid embedding for {icon['name']}: size {len(embedding) if embedding else 0}")
                
                # Insert into FTS table
                conn.execute("""
                    INSERT INTO icons_fts (rowid, name, description, searchable_text)
                    VALUES (?, ?, ?, ?)
                """, (icon_id, icon['name'], icon['description'], icon['searchable_text']))
                
                inserted_count += 1
                
                if inserted_count % 100 == 0:
                    print(f"  📊 Inserted {inserted_count}/{total_icons}...")
                
            except Exception as e:
                print(f"❌ Failed to insert {icon.get('name', 'unknown')}: {e}")
                failed_count += 1
        
        conn.commit()
        
        print(f"✅ Database population complete!")
        print(f"  📊 Successfully inserted: {inserted_count}")
        print(f"  ❌ Failed: {failed_count}")
    
    def create_metadata_table(self, conn: sqlite3.Connection, processed_data: Dict[str, Any]):
        """Create metadata table with build information."""
        conn.execute("""
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        metadata_entries = [
            ('total_icons', str(len(processed_data.get('processed_icons', [])))),
            ('build_timestamp', str(time.time())),
            ('embedding_model', processed_data.get('embedding_model', 'text-embedding-3-small')),
            ('vision_model', processed_data.get('vision_model', 'gpt-4o-mini')),
            ('database_version', '1.0'),
            ('sqlite_vec_version', 'installed'),
        ]
        
        for key, value in metadata_entries:
            conn.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", (key, value))
        
        conn.commit()
        print("✅ Metadata table created")
    
    def optimize_database(self, conn: sqlite3.Connection):
        """Optimize database for better performance."""
        print("⚡ Optimizing database...")
        
        # Run VACUUM to clean up and optimize
        conn.execute("VACUUM")
        
        # Analyze tables for better query planning
        conn.execute("ANALYZE")
        
        conn.commit()
        print("✅ Database optimized")
    
    def verify_database(self, conn: sqlite3.Connection):
        """Verify database integrity and show statistics."""
        print("🔍 Verifying database...")
        
        # Count records
        icons_count = conn.execute("SELECT COUNT(*) FROM icons").fetchone()[0]
        embeddings_count = conn.execute("SELECT COUNT(*) FROM icon_embeddings").fetchone()[0]
        fts_count = conn.execute("SELECT COUNT(*) FROM icons_fts").fetchone()[0]
        
        print(f"  📊 Icons: {icons_count}")
        print(f"  🔢 Embeddings: {embeddings_count}")
        print(f"  🔍 FTS entries: {fts_count}")
        
        # Test vector search
        try:
            # Use a simple test embedding (all zeros)
            test_embedding = [0.0] * 1536
            result = conn.execute("""
                SELECT ie.icon_id, i.name 
                FROM icon_embeddings ie
                JOIN icons i ON ie.icon_id = i.id
                WHERE embedding MATCH ?
                LIMIT 5
            """, (json.dumps(test_embedding),)).fetchall()
            
            print(f"  ✅ Vector search working ({len(result)} test results)")
        except Exception as e:
            print(f"  ❌ Vector search error: {e}")
        
        # Test FTS search
        try:
            result = conn.execute("""
                SELECT name FROM icons_fts 
                WHERE icons_fts MATCH 'computer' 
                LIMIT 5
            """).fetchall()
            
            print(f"  ✅ FTS search working ({len(result)} test results)")
        except Exception as e:
            print(f"  ❌ FTS search error: {e}")
        
        # Get database file size
        file_size = self.db_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        print(f"  💾 Database size: {file_size_mb:.2f} MB")
    
    def build(self):
        """Main build process."""
        print("🚀 Building Windows 98 Icons database...")
        
        # Load processed data
        print("📁 Loading processed icons...")
        processed_data = self.load_processed_data()
        
        total_icons = len(processed_data.get('processed_icons', []))
        print(f"  📊 Found {total_icons} processed icons")
        
        if total_icons == 0:
            print("❌ No processed icons found! Run process_icons.py first.")
            return
        
        # Create database
        conn = self.create_database()
        
        try:
            # Insert data
            self.insert_icons(conn, processed_data)
            
            # Create metadata
            self.create_metadata_table(conn, processed_data)
            
            # Optimize
            self.optimize_database(conn)
            
            # Verify
            self.verify_database(conn)
            
            print(f"\n🎉 Database build complete!")
            print(f"📄 Database saved to: {self.db_path}")
            print(f"🌐 Ready for static site deployment!")
            
        finally:
            conn.close()


def main():
    """Main function to build the database."""
    # Check for command line argument
    input_file = "icons_processed.json"
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    builder = DatabaseBuilder(input_file=input_file)
    builder.build()


if __name__ == "__main__":
    main()