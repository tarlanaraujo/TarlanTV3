import requests
import json

# Test the upload endpoint
files = {'file': open('test_sample.m3u', 'rb')}
data = {'source_type': 'file'}

response = requests.post('http://localhost:5000/upload', files=files, data=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Check if temp file was created
import os
temp_dir = 'temp_playlists'
if os.path.exists(temp_dir):
    print(f"Temp files: {os.listdir(temp_dir)}")
else:
    print("Temp directory not found")
