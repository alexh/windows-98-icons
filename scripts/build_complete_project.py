#!/usr/bin/env python3
"""
Master Build Script for Windows 98 Icons Search
Runs the complete pipeline from scraping to deployment.
"""

import subprocess
import sys
import time
from pathlib import Path
import sqlite3
import shutil
from datetime import datetime
import glob

def run_command(cmd, description, working_dir=None):
    """Run a command with nice output formatting"""
    print(f"\n🔥 {description}")
    print(f"💻 Running: {cmd}")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            cwd=working_dir,
            capture_output=False,
            text=True
        )
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False

def check_requirements():
    """Check if all required tools are installed"""
    print("🔍 Checking requirements...")
    
    required_tools = [
        ("python", "python --version"),
        ("uv", "uv --version"),
        ("bun", "bun --version"),
        ("sqlite3", "sqlite3 --version"),
        ("node", "node --version"),
        ("npm", "npm --version")
    ]
    
    missing = []
    for tool, check_cmd in required_tools:
        try:
            subprocess.run(check_cmd, shell=True, check=True, capture_output=True)
            print(f"  ✅ {tool} is installed")
        except subprocess.CalledProcessError:
            print(f"  ❌ {tool} is missing")
            missing.append(tool)
    
    if missing:
        print(f"\n❌ Missing required tools: {', '.join(missing)}")
        print("Please install them before continuing.")
        return False
    
    print("✅ All requirements satisfied!")
    return True

def create_backup():
    """Create backup of existing important files"""
    database_file = Path("static/icons.db")
    
    if database_file.exists():
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"icons_db_backup_{timestamp}.db"
        
        shutil.copy2(database_file, backup_path)
        print(f"💾 Database backed up to: {backup_path}")
        return backup_path
    else:
        print("ℹ️  No existing database to backup")
        return None

def check_existing_data():
    """Check what data already exists"""
    print("\n🔍 Checking existing data...")
    
    metadata_file = Path("static/icons_metadata.json")
    database_file = Path("static/icons.db")
    
    status = {
        "has_metadata": metadata_file.exists(),
        "has_database": database_file.exists(),
        "has_embeddings": False,
        "icon_count": 0,
        "embedded_count": 0
    }
    
    if metadata_file.exists():
        import json
        with open(metadata_file) as f:
            data = json.load(f)
            status["icon_count"] = len(data.get("icons", []))
        print(f"  📄 Found metadata with {status['icon_count']} icons")
    
    if database_file.exists():
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM icons")
            db_count = cursor.fetchone()[0]
            print(f"  🗄️  Found database with {db_count} icons")
            
            cursor.execute("SELECT COUNT(*) FROM icons WHERE embedding IS NOT NULL AND embedding != ''")
            status["embedded_count"] = cursor.fetchone()[0]
            status["has_embeddings"] = status["embedded_count"] > 0
            
            if status["has_embeddings"]:
                print(f"  🧠 Found {status['embedded_count']} icons with embeddings")
            
        except sqlite3.OperationalError:
            print("  📄 Database exists but may be incomplete")
        finally:
            conn.close()
    
    return status

def main():
    """Main build pipeline"""
    print("🚀🚀🚀 WINDOWS 98 ICONS PROJECT BUILDER 🚀🚀🚀")
    print("This will build the complete Windows 98 Icons search project!")
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check existing data
    status = check_existing_data()
    
    # Create backup before proceeding
    create_backup()
    
    # Ask user what they want to do
    print("\n🎯 What would you like to build?")
    print("1. Complete build (scrape + process + embed + build)")
    print("2. Skip scraping (process + embed + build)")
    print("3. Skip to embedding (embed + build)")
    print("4. Just build frontend (build only)")
    print("5. Custom pipeline")
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            break
        print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
    
    start_time = time.time()
    steps_completed = 0
    total_steps = 0
    
    # Determine steps based on choice
    steps = []
    
    if choice == '1':
        steps = ['scrape', 'process', 'embed', 'build']
        total_steps = 4
    elif choice == '2':
        if not status['has_metadata']:
            print("❌ No metadata found! You need to scrape first or choose option 1.")
            sys.exit(1)
        steps = ['process', 'embed', 'build']
        total_steps = 3
    elif choice == '3':
        # Check if we have processed icons (either in outputs dir or existing DB with embeddings)
        processed_files = glob.glob("outputs/*/icons_processed.json")
        if not processed_files and not (status['has_database'] and status['embedded_count'] > 0):
            print("❌ No processed icons found! You need to process icons first.")
            sys.exit(1)
        steps = ['embed', 'build']
        total_steps = 2
    elif choice == '4':
        steps = ['build']
        total_steps = 1
    elif choice == '5':
        print("\n🛠️  Custom pipeline - select steps:")
        available_steps = ['scrape', 'process', 'embed', 'build']
        for i, step in enumerate(available_steps, 1):
            print(f"{i}. {step}")
        
        selected = input("Enter step numbers separated by commas (e.g., 1,3,4): ")
        try:
            indices = [int(x.strip()) - 1 for x in selected.split(',')]
            steps = [available_steps[i] for i in indices if 0 <= i < len(available_steps)]
            total_steps = len(steps)
        except:
            print("Invalid input. Exiting.")
            sys.exit(1)
    
    print(f"\n🎯 Pipeline: {' → '.join(steps)}")
    print(f"📊 Total steps: {total_steps}")
    
    # Execute steps
    for step in steps:
        steps_completed += 1
        print(f"\n{'='*60}")
        print(f"📍 Step {steps_completed}/{total_steps}: {step.upper()}")
        print(f"{'='*60}")
        
        success = False
        
        if step == 'scrape':
            success = run_command(
                "uv run python scripts/scraper.py",
                "Scraping Windows 98 icons from online sources"
            )
        
        elif step == 'process':
            success = run_command(
                "uv run python scripts/process_icons.py",
                "Processing icons with AI descriptions"
            )
        
        elif step == 'embed':
            success = run_command(
                "uv run python scripts/embed_single_process.py",
                "Generating embeddings for vector search"
            )
        
        elif step == 'build':
            # Build SQLite database first
            success = run_command(
                "uv run python scripts/build_db.py",
                "Building SQLite database with embeddings"
            )
            
            if success:
                # Build the React frontend
                print("\n🔧 Installing frontend dependencies...")
                success = run_command("bun install", "Installing React dependencies")
                
                if success:
                    success = run_command("bun run build", "Building React frontend")
        
        if not success:
            print(f"\n❌ Step '{step}' failed! Stopping pipeline.")
            sys.exit(1)
        
        print(f"✅ Step {steps_completed}/{total_steps} completed!")
    
    # Final summary
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print(f"\n{'🎉' * 20}")
    print("🎉 BUILD PIPELINE COMPLETED SUCCESSFULLY! 🎉")
    print(f"{'🎉' * 20}")
    print(f"⏱️  Total time: {minutes}m {seconds}s")
    print(f"📊 Steps completed: {steps_completed}/{total_steps}")
    
    # Check final status
    final_status = check_existing_data()
    print(f"\n📈 Final Status:")
    print(f"  📄 Icons scraped: {final_status['icon_count']}")
    print(f"  🗄️  Icons in database: {final_status['icon_count'] if final_status['has_database'] else 0}")
    print(f"  🧠 Icons with embeddings: {final_status['embedded_count']}")
    
    if Path("dist").exists():
        print(f"  🚀 Frontend built: dist/ directory ready for deployment")
    
    print(f"\n🌟 Your Windows 98 Icons search site is ready!")
    print(f"📁 Open dist/index.html in your browser to test it locally")
    print(f"🌐 Or deploy the dist/ folder to any static hosting service")

if __name__ == "__main__":
    main()