import os
import json
import hashlib
from datetime import datetime

class TempStorage:
    """Simple temporary storage for M3U data"""
    
    def __init__(self):
        self.storage_dir = 'temp_playlists'
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_playlist(self, playlist_id, name, content_hash, channels):
        """Save playlist data to temporary storage"""
        data = {
            'id': playlist_id,
            'name': name,
            'content_hash': content_hash,
            'channels': channels,
            'timestamp': datetime.now().isoformat()
        }
        
        filename = f"{playlist_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_playlist(self, playlist_id):
        """Load playlist data from temporary storage"""
        filename = f"{playlist_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def delete_playlist(self, playlist_id):
        """Delete playlist data from temporary storage"""
        filename = f"{playlist_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def cleanup_old_files(self, max_age_hours=24):
        """Clean up old temporary files"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for filename in os.listdir(self.storage_dir):
            filepath = os.path.join(self.storage_dir, filename)
            if os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)