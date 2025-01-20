#!/usr/bin/env python3
import json
import os
from datetime import datetime
from barnehageplass_leser import fetch_webpage, parse_kindergarten_spots

def main():
    html_content = fetch_webpage()
    if not html_content:
        return
    
    current_data = parse_kindergarten_spots(html_content)
    
    # Prepare data for the website
    web_data = {
        'lastUpdate': datetime.now().isoformat(),
        'spots': current_data
    }
    
    # Ensure docs directory exists
    os.makedirs('docs', exist_ok=True)
    
    # Save the data for the website
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main() 