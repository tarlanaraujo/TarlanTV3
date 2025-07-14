import requests
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
import time

class M3UValidator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_m3u_content(self, url):
        """Fetch M3U content from URL"""
        try:
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/vnd.apple.mpegurl, application/x-mpegurl, audio/mpegurl, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Try to decode with different encodings
            try:
                content = response.content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = response.content.decode('latin-1')
                except UnicodeDecodeError:
                    content = response.content.decode('utf-8', errors='ignore')
            
            # Check if it's M3U content
            if '#EXTM3U' in content or '#EXTINF:' in content:
                return content
            else:
                print(f"Content doesn't appear to be M3U format")
                return None
            
        except requests.RequestException as e:
            print(f"Error fetching M3U content: {e}")
            return None
    
    def parse_m3u_content(self, content):
        """Parse M3U content and extract channel information"""
        channels = []
        lines = content.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('#EXTINF:'):
                # Parse EXTINF line
                channel_info = self._parse_extinf_line(line)
                
                # Get the next non-empty line as URL
                i += 1
                while i < len(lines) and not lines[i].strip():
                    i += 1
                
                if i < len(lines):
                    url = lines[i].strip()
                    if url and not url.startswith('#'):
                        channel_info['url'] = url
                        channels.append(channel_info)
            
            i += 1
        
        return channels
    
    def _parse_extinf_line(self, line):
        """Parse EXTINF line and extract channel information"""
        # Remove #EXTINF: prefix
        info_line = line[8:].strip()
        
        # Extract duration (first part before comma)
        duration_match = re.match(r'^(-?\d+(?:\.\d+)?),', info_line)
        duration = int(float(duration_match.group(1))) if duration_match else -1
        
        # Extract channel name (after the last comma)
        name_match = re.search(r',([^,]*)$', info_line)
        name = name_match.group(1).strip() if name_match else 'Unknown Channel'
        
        # Extract attributes
        attributes = {}
        attr_pattern = r'(\w+(?:-\w+)*)="([^"]*)"'
        for match in re.finditer(attr_pattern, info_line):
            key, value = match.groups()
            attributes[key.lower().replace('-', '_')] = value
        
        return {
            'name': name,
            'duration': duration,
            'tvg_id': attributes.get('tvg_id', ''),
            'tvg_name': attributes.get('tvg_name', ''),
            'tvg_logo': attributes.get('tvg_logo', ''),
            'logo': attributes.get('tvg_logo', ''),
            'group': attributes.get('group_title', ''),
            'category': attributes.get('group_title', ''),
            'url': ''  # Will be filled by caller
        }
    
    def test_stream_connectivity(self, url, timeout=10):
        """Test if a stream URL is accessible"""
        try:
            # For M3U8 streams, just check if we can get the playlist
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except:
            try:
                # Fallback to GET request with limited data
                response = self.session.get(url, timeout=timeout, stream=True)
                # Read only first few bytes to check if stream is accessible
                next(response.iter_content(1024))
                return True
            except:
                return False
    
    def validate_m3u_format(self, content):
        """Validate if content is a valid M3U format"""
        if not content:
            return False
        
        lines = content.strip().split('\n')
        if not lines or not lines[0].strip().startswith('#EXTM3U'):
            return False
        
        # Check if there's at least one EXTINF entry
        has_extinf = any(line.strip().startswith('#EXTINF:') for line in lines)
        return has_extinf
    
    def extract_playlist_info(self, content):
        """Extract playlist metadata from M3U content"""
        info = {
            'title': '',
            'description': '',
            'channels_count': 0
        }
        
        lines = content.strip().split('\n')
        
        # Look for playlist title in first line
        first_line = lines[0].strip() if lines else ''
        if 'title=' in first_line:
            title_match = re.search(r'title="([^"]*)"', first_line)
            if title_match:
                info['title'] = title_match.group(1)
        
        # Count channels
        info['channels_count'] = len([line for line in lines if line.strip().startswith('#EXTINF:')])
        
        return info
