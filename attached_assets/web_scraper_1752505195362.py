import trafilatura
import re
import requests
from urllib.parse import urljoin, urlparse
import logging

def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text
    except Exception as e:
        logging.error(f"Error extracting content from {url}: {e}")
        return ""

def search_m3u_links(url: str) -> list:
    """
    Search for M3U links on a webpage
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        
        # Parse base URL for relative links
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Find M3U links
        m3u_links = []
        
        # Pattern for M3U links
        patterns = [
            r'href=["\']([^"\']*\.m3u[^"\']*)["\']',
            r'href=["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'(https?://[^\s<>"\']+\.m3u[^\s<>"\']*)',
            r'(https?://[^\s<>"\']+\.m3u8[^\s<>"\']*)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Convert relative URLs to absolute
                if match.startswith('http'):
                    m3u_links.append(match)
                else:
                    absolute_url = urljoin(url, match)
                    m3u_links.append(absolute_url)
        
        return list(set(m3u_links))  # Remove duplicates
        
    except Exception as e:
        logging.error(f"Error searching M3U links on {url}: {e}")
        return []

def extract_m3u_from_text(text: str) -> str:
    """
    Extract M3U content from text if it contains M3U data
    """
    if not text:
        return ""
    
    # Look for M3U content in the text
    if '#EXTM3U' in text:
        # Find the start of M3U content
        start_idx = text.find('#EXTM3U')
        if start_idx != -1:
            # Extract everything from #EXTM3U onwards
            m3u_content = text[start_idx:]
            return m3u_content
    
    return ""
import requests
from urllib.parse import urljoin, urlparse
import re

def get_website_text_content(url):
    """Get website content and look for M3U links"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Look for M3U content in the page
        content = response.text
        
        # Check if the content itself is M3U
        if '#EXTM3U' in content:
            return content
        
        # Look for M3U links in the HTML
        m3u_links = re.findall(r'href=["\']([^"\']*\.m3u[^"\']*)["\']', content, re.IGNORECASE)
        
        if m3u_links:
            # Try to fetch the first M3U link found
            m3u_url = urljoin(url, m3u_links[0])
            m3u_response = requests.get(m3u_url, headers=headers, timeout=10)
            m3u_response.raise_for_status()
            return m3u_response.text
        
        return None
        
    except Exception as e:
        print(f"Error scraping website: {e}")
        return None
