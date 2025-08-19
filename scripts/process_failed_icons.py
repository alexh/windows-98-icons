#!/usr/bin/env python3
"""
Process Failed Icons Script
Processes only the 4 PNG icons that failed during the original run.
"""

import json
import os
import sys
from pathlib import Path
from openai import OpenAI
import base64
from io import BytesIO
from PIL import Image

def setup_openai():
    """Initialize OpenAI client"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)

def decode_base64_image(base64_data):
    """Decode base64 image data"""
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:image/'):
            base64_data = base64_data.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(base64_data)
        
        # Open with PIL to verify it's valid
        image = Image.open(BytesIO(image_bytes))
        return image
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None

def encode_image_for_openai(image):
    """Convert PIL image to base64 for OpenAI"""
    buffered = BytesIO()
    # Convert to RGB if it has transparency
    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGB')
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def generate_description(client, image_data, icon_name):
    """Generate description for an icon using OpenAI Vision API"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this Windows 95/98 era icon called '{icon_name}' and provide a concise description.

Focus on:
- What the icon represents (application, file type, system function, etc.)
- Visual elements and their meaning
- Likely use case or context

Keep the description under 100 words and make it searchable (include relevant keywords someone might search for)."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data
                            }
                        }
                    ]
                }
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating description for {icon_name}: {e}")
        return None

def main():
    # The 4 failed PNG icons
    failed_icons = [
        {
            "name": "media_player_stream_mono_0",
            "base64": "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgAQAAAABbAUdZAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAnRSTlMAAHaTzTgAAAACYktHRAAB3YoTpAAAAAd0SU1FB+IGGBcRMg/SXZwAAAAMSURBVAjXY2AY3AAAAKAAAWElfUcAAAAldEVYdGRhdGU6Y3JlYXRlADIwMTgtMDYtMjRUMjM6MTc6NTAtMDQ6MDAwxrhoAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE4LTA2LTI0VDIzOjE3OjUwLTA0OjAwQZsA1AAAAABJRU5ErkJggg==",
            "filename": "media_player_stream_mono_0.png",
            "local_path": "static/icons/media_player_stream_mono_0.png"
        },
        {
            "name": "media_player_stream_no2_0", 
            "base64": "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgAQAAAABbAUdZAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAnRSTlMAAHaTzTgAAAACYktHRAAB3YoTpAAAAAd0SU1FB+IGGBcRM3jVbQoAAAAMSURBVAjXY2AY3AAAAKAAAWElfUcAAAAldEVYdGRhdGU6Y3JlYXRlADIwMTgtMDYtMjRUMjM6MTc6NTEtMDQ6MDCWsbPcAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE4LTA2LTI0VDIzOjE3OjUxLTA0OjAw5+wLYAAAAABJRU5ErkJggg==",
            "filename": "media_player_stream_no2_0.png",
            "local_path": "static/icons/media_player_stream_no2_0.png"
        },
        {
            "name": "media_player_stream_stereo_0",
            "base64": "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgAQAAAABbAUdZAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAnRSTlMAAHaTzTgAAAACYktHRAAB3YoTpAAAAAd0SU1FB+IGGBcRNOax+KkAAAAMSURBVAjXY2AY3AAAAKAAAWElfUcAAAAldEVYdGRhdGU6Y3JlYXRlADIwMTgtMDYtMjRUMjM6MTc6NTItMDQ6MDCnWalBAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE4LTA2LTI0VDIzOjE3OjUyLTA0OjAW1gQR/QAAAABJRU5ErkJggg==",
            "filename": "media_player_stream_stereo_0.png", 
            "local_path": "static/icons/media_player_stream_stereo_0.png"
        },
        {
            "name": "odbc_6",
            "base64": "iVBORw0KGgoAAAANSUhEUgAAADQAAAA0AQAAAADtAyZGAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAnRSTlMAAHaTzTgAAAACYktHRAAB3YoTpAAAAAd0SU1FB+IGGgAtMs9BWR0AAAAOSURBVBjTY2AYBYMZAAABoAABhi6iFwAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAxOC0wNi0yNlQwMDo0NTo1MC0wNDowMJ5gSRcAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMTgtMDYtMjZUMDA6NDU6NTAtMDQ6MDDvPfGrAAAAAElFTkSuQmCC",
            "filename": "odbc_6.png",
            "local_path": "static/icons/odbc_6.png"
        }
    ]
    
    print(f"🎯 Processing {len(failed_icons)} failed icons...")
    
    # Setup OpenAI
    client = setup_openai()
    
    processed_icons = []
    
    for i, icon_data in enumerate(failed_icons, 1):
        print(f"\n📝 Processing {i}/{len(failed_icons)}: {icon_data['name']}")
        
        # Decode the base64 image
        image = decode_base64_image(icon_data['base64'])
        if not image:
            print(f"  ❌ Failed to decode image")
            continue
            
        print(f"  ✅ Decoded image: {image.size} pixels")
        
        # Encode for OpenAI
        image_for_openai = encode_image_for_openai(image)
        
        # Generate description
        description = generate_description(client, image_for_openai, icon_data['name'])
        if not description:
            print(f"  ❌ Failed to generate description")
            continue
            
        print(f"  ✅ Generated description: {description[:50]}...")
        
        # Create searchable text
        searchable_text = f"{icon_data['name']} {description}"
        
        # Get image dimensions
        width, height = image.size
        
        # Create processed icon entry
        processed_icon = {
            "name": icon_data['name'],
            "filename": icon_data['filename'], 
            "local_path": icon_data['local_path'],
            "description": description,
            "searchable_text": searchable_text,
            "width": width,
            "height": height
        }
        
        processed_icons.append(processed_icon)
        
    print(f"\n🎉 Successfully processed {len(processed_icons)} icons!")
    
    # Save to output file
    output_file = "failed_icons_processed.json"
    with open(output_file, 'w') as f:
        json.dump({
            "processed_icons": processed_icons,
            "total_count": len(processed_icons),
            "timestamp": "2025-08-19"
        }, f, indent=2)
    
    print(f"💾 Saved to {output_file}")
    
    # Print summary
    print("\n📊 Summary:")
    for icon in processed_icons:
        print(f"  • {icon['name']}: {icon['description'][:60]}...")

if __name__ == "__main__":
    main()