import json
import requests
import sys

def upload():
    file_path = 'fsc_final_data.json'
    url = 'https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec'
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"Sending {len(data['flashcards'])} flashcards for app: {data['appName']}...")
        
        # GAS follows redirects. requests handles this.
        response = requests.post(url, json=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    upload()
