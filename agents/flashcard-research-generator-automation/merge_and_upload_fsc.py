import json
import requests

def merge_and_upload():
    app_name = "fsc"
    url = "https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec"
    
    all_flashcards = []
    for i in range(1, 6):
        file_path = f"topic{i}.json"
        try:
            with open(file_path, "r") as f:
                cards = json.load(f)
                all_flashcards.extend(cards)
                print(f"Loaded {len(cards)} cards from {file_path}")
        except Exception as e:
            print(f"Could not load {file_path}: {e}")

    data = {
        "appName": app_name,
        "flashcards": all_flashcards
    }

    print(f"Total flashcards to upload: {len(all_flashcards)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    merge_and_upload()
