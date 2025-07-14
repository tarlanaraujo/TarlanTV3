import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

def get_website_text_content(url):
    """Extract text content from website, looking for M3U links"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Try to decode with different encodings
        try:
            content = response.content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = response.content.decode('latin-1')
            except UnicodeDecodeError:
                content = response.content.decode('utf-8', errors='ignore')
        
        # If content contains M3U data directly, return it
        if '#EXTM3U' in content:
            return content
        
        # Otherwise, try to extract M3U links from HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for M3U links
        m3u_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith(('.m3u', '.m3u8')) or 'm3u' in href.lower():
                full_url = urljoin(url, href)
                m3u_links.append(full_url)
        
        # If we found M3U links, try to fetch the first one
        if m3u_links:
            return fetch_m3u_from_url(m3u_links[0])
        
        # Look for M3U content in script tags or pre tags
        for tag in soup.find_all(['script', 'pre', 'code']):
            if tag.string and '#EXTM3U' in tag.string:
                return tag.string
        
        return None
        
    except Exception as e:
        print(f"Error scraping website: {e}")
        return None

def fetch_m3u_from_url(url):
    """Fetch M3U content from a direct URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Try to decode with different encodings
        try:
            content = response.content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = response.content.decode('latin-1')
            except UnicodeDecodeError:
                content = response.content.decode('utf-8', errors='ignore')
        
        return content if '#EXTM3U' in content else None
        
    except Exception as e:
        print(f"Error fetching M3U from URL: {e}")
        return None

def extract_m3u_links_from_text(text):
    """Extract M3U URLs from text content"""
    m3u_pattern = r'https?://[^\s<>"\']+\.m3u8?(?:\?[^\s<>"\']*)?'
    return re.findall(m3u_pattern, text, re.IGNORECASE)
