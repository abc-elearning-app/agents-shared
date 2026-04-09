import json
import requests
import sys

def upload():
    file_path = 'fsc_final_data.json'
    url = 'https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec'
    
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
