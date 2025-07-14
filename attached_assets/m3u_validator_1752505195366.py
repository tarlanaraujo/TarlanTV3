import re
import requests
from urllib.parse import urlparse, urljoin
import logging
from typing import List, Dict, Optional

class M3UValidator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 10
        
    def fetch_m3u_content(self, url: str) -> Optional[str]:
        """Fetch M3U content from URL"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching M3U from {url}: {e}")
            return None
    
    def validate_m3u_format(self, content: str) -> bool:
        """Validate if content is in M3U format"""
        if not content:
            return False
        
        # Check for M3U header
        if not content.strip().startswith('#EXTM3U'):
            return False
        
        # Check for at least one channel entry
        if '#EXTINF:' not in content:
            return False
        
        return True
    
    def parse_m3u_content(self, content: str) -> List[Dict]:
        """Parse M3U content and extract channel information"""
        channels = []
        
        if not self.validate_m3u_format(content):
            return channels
        
        lines = content.strip().split('\n')
        current_channel = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('#EXTINF:'):
                # Parse channel info
                current_channel = self._parse_extinf_line(line)
                
            elif line and not line.startswith('#'):
                # This is the URL line
                if current_channel:
                    current_channel['url'] = line
                    channels.append(current_channel)
                    current_channel = {}
        
        return channels
    
    def _parse_extinf_line(self, line: str) -> Dict:
        """Parse EXTINF line to extract channel metadata"""
        channel_info = {'name': '', 'category': None, 'logo': None, 'group': None}
        
        # Extract channel name (everything after the last comma)
        if ',' in line:
            channel_info['name'] = line.split(',')[-1].strip()
        
        # Extract group-title (category)
        group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
        if group_match:
            channel_info['category'] = group_match.group(1)
        
        # Extract logo
        logo_match = re.search(r'tvg-logo="([^"]*)"', line, re.IGNORECASE)
        if logo_match:
            channel_info['logo'] = logo_match.group(1)
        
        # Extract group
        group_match = re.search(r'tvg-name="([^"]*)"', line, re.IGNORECASE)
        if group_match:
            channel_info['group'] = group_match.group(1)
        
        return channel_info
    
    def categorize_channel(self, channel_name: str, existing_category: str = None) -> str:
        """Automatically categorize channel based on name"""
        if existing_category:
            return existing_category
        
        channel_name_lower = channel_name.lower()
        
        # Sports categories
        sports_keywords = ['sport', 'espn', 'fox sports', 'sportv', 'combate', 'premiere', 'futebol', 'soccer', 'football']
        if any(keyword in channel_name_lower for keyword in sports_keywords):
            return 'Esportes'
        
        # News categories
        news_keywords = ['news', 'notícias', 'globo news', 'cnn', 'band news', 'record news', 'sbt news']
        if any(keyword in channel_name_lower for keyword in news_keywords):
            return 'Notícias'
        
        # Movies categories
        movie_keywords = ['cinema', 'movie', 'film', 'telecine', 'megapix', 'cinemax', 'hbo', 'paramount']
        if any(keyword in channel_name_lower for keyword in movie_keywords):
            return 'Filmes'
        
        # Kids categories
        kids_keywords = ['kids', 'infantil', 'cartoon', 'disney', 'nickelodeon', 'discovery kids', 'gloob']
        if any(keyword in channel_name_lower for keyword in kids_keywords):
            return 'Infantil'
        
        # Entertainment categories
        entertainment_keywords = ['entretenimento', 'entertainment', 'comedy', 'variety', 'multishow', 'mtv']
        if any(keyword in channel_name_lower for keyword in entertainment_keywords):
            return 'Entretenimento'
        
        # Documentary categories
        doc_keywords = ['discovery', 'history', 'national geographic', 'animal planet', 'documentário']
        if any(keyword in channel_name_lower for keyword in doc_keywords):
            return 'Documentários'
        
        return 'Geral'
    
    def test_stream_connectivity(self, url: str) -> bool:
        """Test if stream URL is accessible"""
        try:
            # First try HEAD request
            response = self.session.head(url, timeout=5, allow_redirects=True)
            
            # If HEAD fails, try GET with limited data
            if response.status_code >= 400:
                response = self.session.get(url, timeout=5, stream=True)
                # Read just a small amount to test connectivity
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        break
            
            return response.status_code < 400
            
        except requests.exceptions.RequestException as e:
            logging.debug(f"Stream test failed for {url}: {e}")
            return False
    
    def extract_playlist_info(self, content: str) -> Dict:
        """Extract general playlist information"""
        info = {
            'title': None,
            'description': None,
            'total_channels': 0,
            'categories': set()
        }
        
        # Count total channels
        info['total_channels'] = content.count('#EXTINF:')
        
        # Extract title
        title_match = re.search(r'#EXTM3U.*?title="([^"]*)"', content, re.IGNORECASE)
        if title_match:
            info['title'] = title_match.group(1)
        
        # Extract categories
        category_matches = re.findall(r'group-title="([^"]*)"', content, re.IGNORECASE)
        info['categories'] = set(category_matches) if category_matches else set()
        
        return info
import requests
import re
from urllib.parse import urlparse

class M3UValidator:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_m3u_content(self, url):
        """Fetch M3U content from URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching M3U content: {e}")
            return None
    
    def parse_m3u_content(self, content):
        """Parse M3U content and extract channel information"""
        channels = []
        lines = content.split('\n')
        
        current_channel = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('#EXTINF:'):
                current_channel = self._parse_extinf_line(line)
            elif line and not line.startswith('#') and current_channel:
                current_channel['url'] = line
                channels.append(current_channel)
                current_channel = None
        
        return channels
    
    def _parse_extinf_line(self, line):
        """Parse EXTINF line to extract channel information"""
        channel = {}
        
        # Extract name (everything after the last comma)
        name_match = re.search(r',([^,]+)$', line)
        if name_match:
            channel['name'] = name_match.group(1).strip()
        
        # Extract logo
        logo_match = re.search(r'tvg-logo="([^"]+)"', line)
        if logo_match:
            channel['logo'] = logo_match.group(1)
        
        # Extract category/group
        group_match = re.search(r'group-title="([^"]+)"', line)
        if group_match:
            channel['category'] = group_match.group(1)
        
        return channel
    
    def test_stream_connectivity(self, url):
        """Test if stream URL is accessible"""
        try:
            response = requests.head(url, headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False
