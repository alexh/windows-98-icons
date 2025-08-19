#!/usr/bin/env python3
"""
Retry Failed Icons Script

Retries processing of icons that failed in a previous run.
Usage: uv run python retry_errors.py path/to/icons_errors.json
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from process_icons import IconProcessor


class RetryProcessor(IconProcessor):
    def __init__(self, error_file: str, batch_size: int = 10):
        # Initialize with smaller batch size for retries
        super().__init__(batch_size=batch_size)
        self.error_file = Path(error_file)
        
        # Override output directory for retry run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"outputs/retry_{timestamp}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "icons_processed_retry.json"
        self.error_file_out = self.output_dir / "icons_errors_retry.json"
        
    def load_error_data(self) -> List[Dict[str, Any]]:
        """Load the error icons data."""
        if not self.error_file.exists():
            raise FileNotFoundError(f"{self.error_file} not found.")
        
        print(f"📄 Loading error data from: {self.error_file}")
        with open(self.error_file, 'r') as f:
            data = json.load(f)
            return data.get('error_icons', [])
    
    async def retry_failed_icons(self):
        """Retry processing failed icons."""
        print("🔄 Starting retry of failed icons...")
        
        error_icons = self.load_error_data()
        total_errors = len(error_icons)
        
        print(f"📊 Found {total_errors} failed icons to retry")
        
        if total_errors == 0:
            print("✅ No failed icons to retry!")
            return
        
        # Show first few errors for debugging
        print(f"📝 First 3 errors to retry:")
        for i, error in enumerate(error_icons[:3]):
            icon_data = error.get('icon_data', {})
            error_msg = error.get('error', 'unknown')
            step = error.get('step', 'unknown')
            print(f"  {i+1}. {icon_data.get('name', 'unknown')} - {step}: {error_msg}")
        
        print(f"\n🚀 Retrying {total_errors} icons in batches of {self.batch_size}...")
        
        processed_count = 0
        failed_count = 0
        
        # Process in batches with parallel execution
        for i in range(0, total_errors, self.batch_size):
            batch = error_icons[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_errors + self.batch_size - 1) // self.batch_size
            
            print(f"\n📦 Retry Batch {batch_num}/{total_batches} ({len(batch)} icons)")
            
            # Process entire batch in parallel using asyncio.gather
            batch_start_time = time.time()
            
            try:
                # Extract icon_data from error entries
                icon_data_list = [error.get('icon_data', {}) for error in batch]
                
                # Create tasks for all icons in the batch
                tasks = [self.process_icon(icon_data) for icon_data in icon_data_list]
                
                # Execute all tasks concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        print(f"❌ Exception retrying {batch[j].get('icon_data', {}).get('name', 'unknown')}: {result}")
                        failed_count += 1
                    elif result is not None:
                        self.processed_data.append(result)
                        processed_count += 1
                    else:
                        failed_count += 1
                
            except Exception as e:
                print(f"❌ Batch retry error: {e}")
                failed_count += len(batch)
            
            # Save progress after each batch
            self.save_processed_data()
            
            batch_time = time.time() - batch_start_time
            print(f"📊 Retry Batch {batch_num} complete in {batch_time:.1f}s: {processed_count} total completed, {failed_count} total failed")
            
            # Brief pause between batches
            if i + self.batch_size < total_errors:
                print("⏳ Brief pause between retry batches...")
                await asyncio.sleep(2)
        
        print(f"\n🎉 Retry processing complete!")
        print(f"✅ Successfully processed: {processed_count}")
        print(f"❌ Still failed: {failed_count}")
        print(f"📄 Results saved to: {self.output_file}")
        if self.error_data:
            print(f"🚨 New errors saved to: {self.error_file_out}")
        print(f"📁 Output directory: {self.output_dir}")
    
    def save_processed_data(self):
        """Save processed data to JSON file."""
        with open(self.output_file, 'w') as f:
            json.dump({
                "processed_icons": self.processed_data,
                "total_count": len(self.processed_data),
                "timestamp": time.time(),
                "embedding_model": "text-embedding-3-small",
                "vision_model": "gpt-4o-mini",
                "retry_run": True,
                "original_error_file": str(self.error_file)
            }, f, indent=2)
        
        # Save errors if any occurred
        if self.error_data:
            with open(self.error_file_out, 'w') as f:
                json.dump({
                    "error_icons": self.error_data,
                    "total_errors": len(self.error_data),
                    "timestamp": time.time(),
                    "retry_run": True,
                    "original_error_file": str(self.error_file)
                }, f, indent=2)


async def main():
    """Main function to retry failed icons."""
    if len(sys.argv) < 2:
        print("❌ Usage: uv run python retry_errors.py path/to/icons_errors.json")
        print("📄 Available error files:")
        
        # Look for error files in outputs directory
        outputs_dir = Path("outputs")
        if outputs_dir.exists():
            error_files = list(outputs_dir.glob("*/icons_errors*.json"))
            if error_files:
                for error_file in sorted(error_files):
                    print(f"  {error_file}")
            else:
                print("  No error files found in outputs/")
        else:
            print("  No outputs directory found")
        return
    
    error_file = sys.argv[1]
    
    # Check for OpenAI API key
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    processor = RetryProcessor(error_file)
    
    print("🔄 Starting retry of failed Windows 98 icons...")
    print("This will use OpenAI Vision and Embeddings APIs")
    print("Rate limited to avoid exceeding API limits")
    print(f"📁 Output will be saved to: {processor.output_dir}")
    
    await processor.retry_failed_icons()


if __name__ == "__main__":
    asyncio.run(main())