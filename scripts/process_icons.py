#!/usr/bin/env python3
"""
Icon Description and Embedding Generator

Processes downloaded Windows 98 icons to generate:
1. AI descriptions using OpenAI Vision API

Saves results to icons_processed.json. 
Vector embeddings are generated separately by embed_single_process.py.
"""

import asyncio
import base64
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import openai
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)


class IconProcessor:
    def __init__(self, icons_dir: str = "static/icons", batch_size: int = 20):
        self.icons_dir = Path(icons_dir)
        self.batch_size = batch_size
        self.client = OpenAI()  # Uses OPENAI_API_KEY env var
        self.processed_data: List[Dict[str, Any]] = []
        self.error_data: List[Dict[str, Any]] = []
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"outputs/{timestamp}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "icons_processed.json"
        self.error_file = self.output_dir / "icons_errors.json"
        
        # Rate limiting for parallel processing
        self.vision_semaphore = asyncio.Semaphore(15)  # Max 15 concurrent vision calls
        # Embedding generation moved to embed_single_process.py
        self.requests_per_minute = 0
        self.minute_start = time.time()
        
    def load_metadata(self) -> Dict[str, Any]:
        """Load the scraped icons metadata."""
        metadata_file = Path("static/icons_metadata.json")
        if not metadata_file.exists():
            raise FileNotFoundError("static/icons_metadata.json not found. Run scraper.py first.")
        
        with open(metadata_file, 'r') as f:
            return json.load(f)
    
    def prepare_icon_for_vision(self, image_path: Path) -> Optional[str]:
        """Prepare icon image for OpenAI Vision API."""
        try:
            if not image_path.exists():
                print(f"❌ Image not found: {image_path}")
                return None
            
            # Open and ensure the image is in a good format
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (OpenAI has size limits)
                max_size = 512
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save to bytes and encode as base64
                import io
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_bytes = buffer.getvalue()
                return base64.b64encode(img_bytes).decode('utf-8')
                
        except Exception as e:
            print(f"❌ Error preparing image {image_path}: {e}")
            return None
    
    async def check_rate_limit(self):
        """Smart rate limiting for parallel requests."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.minute_start > 60:
            self.requests_per_minute = 0
            self.minute_start = current_time
        
        # If we're approaching limits, wait
        if self.requests_per_minute > 800:  # Conservative limit
            wait_time = 60 - (current_time - self.minute_start)
            if wait_time > 0:
                print(f"  ⏳ Rate limit approaching, waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                self.requests_per_minute = 0
                self.minute_start = time.time()
        
        self.requests_per_minute += 1
    
    async def generate_description(self, icon_name: str, image_base64: str) -> Optional[str]:
        """Generate a description of the icon using OpenAI Vision API."""
        async with self.vision_semaphore:
            await self.check_rate_limit()
            
            try:
                # Use sync client in async context (OpenAI client handles this)
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Use the vision-capable model
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"""Describe this icon named '{icon_name}' in 1-2 sentences. 
                                    Focus on what the icon represents and its function. No boilerplate, no style references, just describe what it is. Examples:
                                    - 'A folder for organizing files and directories'
                                    - 'A computer monitor for system or hardware settings'
                                    - 'A calculator for mathematical calculations'"""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}",
                                        "detail": "low"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=150,
                    temperature=0.3  # Lower temperature for more consistent descriptions
                )
                
                description = response.choices[0].message.content.strip()
                return description
                
            except Exception as e:
                print(f"❌ Error generating description for {icon_name}: {e}")
                return None
    
    # Embedding generation removed - use embed_single_process.py instead
    
    async def process_icon(self, icon_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single icon: generate AI description only."""
        icon_name = icon_data.get('name', 'unknown')
        
        try:
            if 'local_path' not in icon_data:
                error_info = {
                    "icon_data": icon_data,
                    "error": "no local file path",
                    "step": "validation",
                    "timestamp": time.time()
                }
                self.error_data.append(error_info)
                print(f"⚠️ Skipping {icon_name}: no local file")
                return None
                
            image_path = Path(icon_data['local_path'])
            
            print(f"\n🎨 Processing: {icon_name}")
            
            # Prepare image for Vision API
            print(f"  📷 Preparing image: {image_path}")
            image_base64 = self.prepare_icon_for_vision(image_path)
            if not image_base64:
                error_info = {
                    "icon_data": icon_data,
                    "error": "failed to prepare image",
                    "step": "image_preparation",
                    "timestamp": time.time()
                }
                self.error_data.append(error_info)
                print(f"  ❌ Failed to prepare image: {image_path}")
                return None
            
            # Generate description (async with semaphore)
            print(f"  📝 Generating description with OpenAI Vision...")
            description = await self.generate_description(icon_name, image_base64)
            if not description:
                error_info = {
                    "icon_data": icon_data,
                    "error": "failed to generate description",
                    "step": "vision_api",
                    "timestamp": time.time()
                }
                self.error_data.append(error_info)
                print(f"  ❌ Failed to generate description for: {icon_name}")
                return None
            
            # Print the generated description
            print(f"  ✨ DESCRIPTION: '{description}'")
            
            # Create searchable text (name + description)
            searchable_text = f"{icon_name.replace('_', ' ')} {description}"
            
            # Note: Embeddings will be generated separately by embed_single_process.py
            
            # Get image dimensions
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
            except:
                width, height = None, None
            
            processed_icon = {
                "name": icon_name,
                "filename": icon_data.get('filename', ''),
                "local_path": str(image_path),
                "description": description,
                "searchable_text": searchable_text,
                "width": width,
                "height": height,
                "source_data": icon_data  # Keep original metadata
            }
            
            print(f"  ✅ COMPLETE: {icon_name}")
            print(f"     📝 Description: {description}")
            return processed_icon
            
        except Exception as e:
            error_info = {
                "icon_data": icon_data,
                "error": str(e),
                "step": "general_exception",
                "timestamp": time.time()
            }
            self.error_data.append(error_info)
            print(f"  ❌ Exception processing {icon_name}: {e}")
            return None
    
    async def process_all_icons(self):
        """Process all icons in batches."""
        print("📁 Loading metadata...")
        metadata = self.load_metadata()
        print(f"✅ Metadata loaded successfully")
        
        # Get successfully downloaded icons
        successful_icons = metadata.get('download_results', {}).get('successful', [])
        total_icons = len(successful_icons)
        
        print(f"📊 Found {total_icons} successfully downloaded icons")
        
        if total_icons == 0:
            print("❌ No successfully downloaded icons found!")
            print("📋 Available metadata keys:", list(metadata.keys()))
            if 'download_results' in metadata:
                print("📋 Download results keys:", list(metadata['download_results'].keys()))
            return
        
        # Show first few icons for debugging
        print(f"📝 First 3 icons to process:")
        for i, icon in enumerate(successful_icons[:3]):
            print(f"  {i+1}. {icon.get('name', 'unknown')} -> {icon.get('local_path', 'no path')}")
        
        print(f"\n🚀 Processing {total_icons} icons in batches of {self.batch_size}...")
        
        processed_count = 0
        failed_count = 0
        
        # Process in batches with parallel execution
        for i in range(0, total_icons, self.batch_size):
            batch = successful_icons[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_icons + self.batch_size - 1) // self.batch_size
            
            print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} icons) - PARALLEL PROCESSING")
            
            # Process entire batch in parallel using asyncio.gather
            batch_start_time = time.time()
            
            try:
                # Create tasks for all icons in the batch
                tasks = [self.process_icon(icon_data) for icon_data in batch]
                
                # Execute all tasks concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        print(f"❌ Exception processing {batch[j].get('name', 'unknown')}: {result}")
                        failed_count += 1
                    elif result is not None:
                        self.processed_data.append(result)
                        processed_count += 1
                    else:
                        failed_count += 1
                
            except Exception as e:
                print(f"❌ Batch processing error: {e}")
                failed_count += len(batch)
            
            # Save progress after each batch
            self.save_processed_data()
            
            batch_time = time.time() - batch_start_time
            print(f"📊 Batch {batch_num} complete in {batch_time:.1f}s: {processed_count} total completed, {failed_count} total failed")
            
            # Brief pause between batches
            if i + self.batch_size < total_icons:
                print("⏳ Brief pause between batches...")
                await asyncio.sleep(3)
        
        print(f"\n🎉 Processing complete!")
        print(f"✅ Successfully processed: {processed_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📄 Results saved to: {self.output_file}")
        if self.error_data:
            print(f"🚨 Errors saved to: {self.error_file}")
        print(f"📁 Output directory: {self.output_dir}")
    
    def save_processed_data(self):
        """Save processed data to JSON file."""
        with open(self.output_file, 'w') as f:
            json.dump({
                "processed_icons": self.processed_data,
                "total_count": len(self.processed_data),
                "timestamp": time.time(),
                "embedding_model": "text-embedding-3-small",
                "vision_model": "gpt-4o-mini"
            }, f, indent=2)
        
        # Save errors if any occurred
        if self.error_data:
            with open(self.error_file, 'w') as f:
                json.dump({
                    "error_icons": self.error_data,
                    "total_errors": len(self.error_data),
                    "timestamp": time.time()
                }, f, indent=2)


async def main():
    """Main function to process icons."""
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    processor = IconProcessor()
    
    print("🤖 Starting Windows 98 icon processing...")
    print("This will use OpenAI Vision and Embeddings APIs")
    print("Rate limited to avoid exceeding API limits")
    print(f"📁 Output will be saved to: {processor.output_dir}")
    
    await processor.process_all_icons()


if __name__ == "__main__":
    asyncio.run(main())