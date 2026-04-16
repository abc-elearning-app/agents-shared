import json
import urllib.request
import urllib.parse
import sys

def get_youtube_autosuggest(query):
    url = f"http://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            res = response.read().decode('utf-8')
            # The response is usually in the format: window.google.ac.h(["query",[["suggestion1",0],["suggestion2",0]]])
            # Or JSON if client=firefox: ["query",["suggestion1","suggestion2"]]
            pass
    except Exception as e:
        print(f"Error fetching autosuggest: {e}", file=sys.stderr)
        return []

def get_youtube_autosuggest_firefox(query):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            res = response.read().decode('utf-8')
            data = json.loads(res)
            return data[1][:5]
    except Exception as e:
        print(f"Error fetching autosuggest: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    niche = "PMP"
    if len(sys.argv) > 1:
        niche = sys.argv[1]
    
    suggestions_1 = get_youtube_autosuggest_firefox(f"{niche} ")
    suggestions_2 = get_youtube_autosuggest_firefox(f"how to {niche} ")
    suggestions_3 = get_youtube_autosuggest_firefox(f"{niche} exam ")
    suggestions_4 = get_youtube_autosuggest_firefox(f"{niche} 2026 ")
    
    print("AUTOSUGGEST_RESULTS")
    all_suggs = suggestions_1 + suggestions_2 + suggestions_3 + suggestions_4
    for s in list(dict.fromkeys(all_suggs))[:10]: # unique
        print(f"- {s}")
