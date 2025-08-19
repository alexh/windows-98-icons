#!/usr/bin/env python3
"""
Windows 98 Icons Scraper

Scrapes icon names and images from https://windows98-ui.netlify.app/
and downloads them to the static/icons directory.
"""

import asyncio
import base64
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any

import requests
from playwright.async_api import async_playwright


class IconScraper:
    def __init__(self, output_dir: str = "static/icons"):
        self.base_url = "https://windows98-ui.netlify.app/"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.scraped_data: List[Dict[str, Any]] = []
        
    async def scrape_icons(self) -> List[Dict[str, Any]]:
        """Main scraping function using Playwright to handle JavaScript-rendered content."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print(f"Navigating to {self.base_url}")
            await page.goto(self.base_url, wait_until="networkidle")
            
            # Wait for the content to load and look for the icon gallery window
            print("Waiting for icons to load...")
            await page.wait_for_timeout(5000)  # Give more time for JS to render
            
            # Take a screenshot to help debug
            await page.screenshot(path="debug_screenshot.png")
            print("Screenshot saved as debug_screenshot.png")
            
            # Debug: print page title and some basic info
            title = await page.title()
            print(f"Page title: {title}")
            
            # Debug: look for any windows or containers
            all_elements = await page.query_selector_all('*')
            print(f"Total elements on page: {len(all_elements)}")
            
            # Look for elements with "icon" in their text or attributes
            elements_with_icon = await page.query_selector_all('*:has-text("icon")')
            print(f"Elements containing 'icon': {len(elements_with_icon)}")
            
            # Look for the "List of icons" window specifically
            print("Looking for 'List of icons' window...")
            icons_found = []
            
            # Try to find the window with "List of icons" title
            window_selectors = [
                '*[class*="window"]',
                '*[class*="Window"]', 
                'div[class*="react95"]',
                '*:has-text("List of icons")',
                '*:has-text("icon")'
            ]
            
            icon_window = None
            for selector in window_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text_content = await element.text_content()
                        if text_content and "list of icons" in text_content.lower():
                            icon_window = element
                            print(f"Found icon window with selector: {selector}")
                            break
                    if icon_window:
                        break
                except:
                    continue
            
            if icon_window:
                print("Found icon window! Extracting icons from it...")
                # Look for all images within the icon window
                window_images = await icon_window.query_selector_all('img')
                print(f"Found {len(window_images)} images in icon window")
                
                for img in window_images:
                    try:
                        src = await img.get_attribute("src")
                        alt = await img.get_attribute("alt") or ""
                        
                        if src:
                            # Look for the icon name in nearby text elements
                            icon_name = await self._extract_icon_name_from_gallery(img, page)
                            
                            icon_info = {
                                "name": icon_name,
                                "src": src,
                                "alt": alt,
                                "parent_text": "icon_gallery"
                            }
                            icons_found.append(icon_info)
                            print(f"Gallery icon: {icon_name} -> {src[:60]}...")
                    except Exception as e:
                        print(f"Error processing gallery image: {e}")
            
            # Also try broader selectors to catch any icons we missed
            print("Scanning for additional icons...")
            icon_selectors = [
                'img[src*=".png"]',  # Any PNG images
                'img[src*="icon"]',   # Images with "icon" in path
                'img[alt*="icon"]',   # Images with icon in alt text
                '[class*="icon"] img', # Images in icon containers
            ]
            
            for selector in icon_selectors:
                print(f"Trying selector: {selector}")
                elements = await page.query_selector_all(selector)
                
                for element in elements:
                    try:
                        # Get image source
                        src = await element.get_attribute("src")
                        if not src:
                            continue
                            
                        # Skip if we already have this icon
                        if any(icon["src"] == src for icon in icons_found):
                            continue
                            
                        # Get alt text for name
                        alt = await element.get_attribute("alt") or ""
                        
                        # Get parent elements for additional context
                        parent = await element.query_selector("xpath=..")
                        parent_text = ""
                        if parent:
                            parent_text = await parent.text_content() or ""
                        
                        # Try to find associated text/name
                        name = self._extract_icon_name(src, alt, parent_text)
                        
                        if src and name:
                            icon_info = {
                                "name": name,
                                "src": src,
                                "alt": alt,
                                "parent_text": parent_text.strip()
                            }
                            
                            icons_found.append(icon_info)
                            print(f"Additional icon: {name} -> {src[:60]}...")
                    
                    except Exception as e:
                        print(f"Error processing element: {e}")
                        continue
            
            print(f"Found {len(icons_found)} unique icons")
            
            # Also try to find icons by examining the page source for common patterns
            content = await page.content()
            additional_icons = self._extract_icons_from_html(content)
            
            # Merge with found icons
            for icon in additional_icons:
                if not any(existing["src"] == icon["src"] for existing in icons_found):
                    icons_found.append(icon)
                    print(f"Found additional icon: {icon['name']} -> {icon['src']}")
            
            await browser.close()
            
            self.scraped_data = icons_found
            return icons_found
    
    def _extract_icon_name(self, src: str, alt: str, parent_text: str) -> str:
        """Extract a meaningful name for the icon from various sources."""
        # Try alt text first
        if alt and not alt.lower() in ["icon", "image", "img"]:
            return self._clean_name(alt)
        
        # Try parent text
        if parent_text:
            # Remove common words and clean up
            text = re.sub(r'\b(icon|image|img|png|svg)\b', '', parent_text, flags=re.IGNORECASE)
            text = text.strip()
            if text:
                return self._clean_name(text)
        
        # Fall back to filename from src
        if src:
            filename = Path(urlparse(src).path).stem
            return self._clean_name(filename)
        
        return "unknown_icon"
    
    def _clean_name(self, name: str) -> str:
        """Clean and normalize icon names."""
        # Remove file extensions
        name = re.sub(r'\.(png|svg|jpg|jpeg|gif)$', '', name, flags=re.IGNORECASE)
        # Replace special characters with underscores
        name = re.sub(r'[^\w\s-]', '_', name)
        # Replace spaces and dashes with underscores
        name = re.sub(r'[\s-]+', '_', name)
        # Remove multiple underscores
        name = re.sub(r'_+', '_', name)
        # Strip leading/trailing underscores
        name = name.strip('_')
        return name.lower() if name else "unknown"
    
    def _extract_icons_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract icon references from HTML source code."""
        icons = []
        
        # Look for common icon file patterns in the HTML
        icon_patterns = [
            r'src=["\']([^"\']*(?:icon|Icon)[^"\']*\.(?:png|svg|jpg|jpeg))["\']',
            r'["\']([^"\']*\/icons?\/[^"\']*\.(?:png|svg|jpg|jpeg))["\']',
            r'["\']([^"\']*\.(?:png|svg))["\']',  # All PNG/SVG files
        ]
        
        for pattern in icon_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                src = match.group(1)
                name = self._clean_name(Path(urlparse(src).path).stem)
                
                icons.append({
                    "name": name,
                    "src": src,
                    "alt": "",
                    "parent_text": ""
                })
        
        return icons
    
    def download_icons(self) -> Dict[str, Any]:
        """Download all scraped icons to the output directory."""
        if not self.scraped_data:
            print("No icons to download. Run scrape_icons() first.")
            return {}
        
        download_results = {
            "successful": [],
            "failed": [],
            "total": len(self.scraped_data)
        }
        
        print(f"Downloading {len(self.scraped_data)} icons...")
        
        for icon in self.scraped_data:
            try:
                # Handle base64 data URLs
                if icon["src"].startswith("data:"):
                    self._save_base64_icon(icon, download_results)
                    continue
                
                # Resolve relative URLs
                if icon["src"].startswith("//"):
                    url = "https:" + icon["src"]
                elif icon["src"].startswith("/"):
                    url = urljoin(self.base_url, icon["src"])
                elif not icon["src"].startswith("http"):
                    url = urljoin(self.base_url, icon["src"])
                else:
                    url = icon["src"]
                
                # Determine file extension
                parsed_url = urlparse(url)
                original_ext = Path(parsed_url.path).suffix.lower()
                if not original_ext or original_ext not in ['.png', '.svg', '.jpg', '.jpeg', '.gif']:
                    original_ext = '.png'  # Default to PNG
                
                # Create filename
                filename = f"{icon['name']}{original_ext}"
                filepath = self.output_dir / filename
                
                # Download the file
                print(f"Downloading: {filename}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Save the file
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Update icon data with local path
                icon["local_path"] = str(filepath)
                icon["filename"] = filename
                icon["download_url"] = url
                
                download_results["successful"].append(icon)
                print(f"✅ Downloaded: {filename}")
                
            except Exception as e:
                print(f"❌ Failed to download {icon['name']}: {e}")
                download_results["failed"].append({
                    "icon": icon,
                    "error": str(e)
                })
        
        # Save metadata
        metadata_file = self.output_dir.parent / "icons_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                "icons": self.scraped_data,
                "download_results": download_results,
                "source_url": self.base_url
            }, f, indent=2)
        
        print(f"\n📊 Download Summary:")
        print(f"✅ Successful: {len(download_results['successful'])}")
        print(f"❌ Failed: {len(download_results['failed'])}")
        print(f"📄 Metadata saved to: {metadata_file}")
        
        return download_results
    
    def _save_base64_icon(self, icon: Dict[str, Any], download_results: Dict[str, Any]) -> None:
        """Save a base64 data URL as an image file."""
        try:
            # Parse the data URL
            data_url = icon["src"]
            if not data_url.startswith("data:"):
                raise ValueError("Not a valid data URL")
            
            # Extract mime type and base64 data
            header, data = data_url.split(',', 1)
            mime_type = header.split(';')[0].split(':')[1]
            
            # Determine file extension from mime type
            ext_map = {
                'image/png': '.png',
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/gif': '.gif',
                'image/svg+xml': '.svg',
                'image/webp': '.webp'
            }
            
            ext = ext_map.get(mime_type, '.png')
            filename = f"{icon['name']}{ext}"
            filepath = self.output_dir / filename
            
            # Decode and save the base64 data
            image_data = base64.b64decode(data)
            
            print(f"Saving base64 icon: {filename}")
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Update icon data
            icon["local_path"] = str(filepath)
            icon["filename"] = filename
            icon["download_url"] = "base64_data"
            icon["mime_type"] = mime_type
            
            download_results["successful"].append(icon)
            print(f"✅ Saved base64 icon: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save base64 icon {icon['name']}: {e}")
            download_results["failed"].append({
                "icon": icon,
                "error": str(e)
            })
    
    async def _extract_icon_name_from_gallery(self, img_element, page):
        """Extract the actual icon filename from the gallery layout."""
        try:
            # Strategy 1: Look for text near the image (sibling elements)
            parent = await img_element.query_selector("xpath=..")
            if parent:
                # Look for text content in the parent or siblings
                text_content = await parent.text_content()
                if text_content and text_content.strip():
                    # Clean up the text to get just the filename
                    lines = text_content.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and '.png' in line.lower():
                            return self._clean_name(line)
                        elif line and len(line) > 3 and not line.isspace():
                            # If it looks like a filename, use it
                            if any(char in line for char in ['_', '-', '.']):
                                return self._clean_name(line)
            
            # Strategy 2: Look for nearby text elements in the DOM
            siblings = await page.evaluate("""
                (img) => {
                    const parent = img.parentElement;
                    if (!parent) return [];
                    
                    // Look for text nodes or elements with text near this image
                    const walker = document.createTreeWalker(
                        parent,
                        NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
                        null,
                        false
                    );
                    
                    const texts = [];
                    let node;
                    while (node = walker.nextNode()) {
                        if (node.nodeType === Node.TEXT_NODE) {
                            const text = node.textContent.trim();
                            if (text && text.length > 2) {
                                texts.push(text);
                            }
                        } else if (node.textContent) {
                            const text = node.textContent.trim();
                            if (text && text.length > 2 && text.includes('.')) {
                                texts.push(text);
                            }
                        }
                    }
                    return texts;
                }
            """, img_element)
            
            # Look for the most likely filename in the collected text
            for text in siblings:
                if '.png' in text.lower() or '.ico' in text.lower():
                    return self._clean_name(text)
                elif '_' in text or '-' in text:
                    # Looks like a filename pattern
                    return self._clean_name(text)
            
            # Strategy 3: Check if the alt attribute has a meaningful name
            alt = await img_element.get_attribute("alt")
            if alt and len(alt) > 3 and alt != "icon":
                return self._clean_name(alt)
            
            # Strategy 4: Try to extract from any data attributes
            data_attrs = await page.evaluate("""
                (img) => {
                    const attrs = {};
                    for (let attr of img.attributes) {
                        if (attr.name.startsWith('data-') || attr.name.includes('name') || attr.name.includes('file')) {
                            attrs[attr.name] = attr.value;
                        }
                    }
                    return attrs;
                }
            """, img_element)
            
            for attr_name, attr_value in data_attrs.items():
                if attr_value and len(attr_value) > 3:
                    return self._clean_name(attr_value)
                    
        except Exception as e:
            print(f"Error extracting icon name: {e}")
        
        # Fallback: generate a descriptive name based on position
        try:
            # Get the image's position in the gallery for a fallback name
            position = await page.evaluate("""
                (img) => {
                    const parent = img.closest('[class*="window"], [class*="gallery"], [class*="list"]');
                    if (parent) {
                        const images = parent.querySelectorAll('img');
                        return Array.from(images).indexOf(img);
                    }
                    return -1;
                }
            """, img_element)
            
            if position >= 0:
                return f"windows98_icon_{position:03d}"
            else:
                return f"unknown_icon_{hash(str(await img_element.get_attribute('src')))}"
        except:
            return "unknown_icon"


async def main():
    """Main function to run the scraper."""
    scraper = IconScraper()
    
    print("🔍 Starting Windows 98 icons scraper...")
    icons = await scraper.scrape_icons()
    
    if icons:
        print(f"\n📥 Downloading {len(icons)} icons...")
        results = scraper.download_icons()
        
        print(f"\n🎉 Scraping complete!")
        print(f"Icons saved to: {scraper.output_dir}")
        print(f"Check icons_metadata.json for detailed results")
    else:
        print("❌ No icons found. The site structure might have changed.")


if __name__ == "__main__":
    asyncio.run(main())