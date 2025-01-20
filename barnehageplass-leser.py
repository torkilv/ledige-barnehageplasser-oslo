import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
import json
import platform

def fetch_webpage():
    url = "https://www.oslo.kommune.no/barnehage/ledige-barnehageplasser/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching webpage: {e}")
        return None

def parse_kindergarten_spots(html_content):
    if not html_content:
        return {}

    # List of all districts in Oslo
    oslo_districts = [
        "Alna",
        "Bjerke",
        "Frogner",
        "Gamle Oslo",
        "Grorud",
        "Grünerløkka",
        "Nordre Aker",
        "Nordstrand",
        "Sagene",
        "St. Hanshaugen",
        "Stovner",
        "Søndre Nordstrand",
        "Ullern",
        "Vestre Aker",
        "Østensjø"
    ]

    soup = BeautifulSoup(html_content, 'html.parser')
    districts = {}
    
    # Find all text elements that might contain district information
    for district_name in oslo_districts:
        # Look for elements containing the district name
        district_elements = soup.find_all(text=re.compile(f"Bydel {district_name}", re.IGNORECASE))
        if not district_elements:
            # Try without "Bydel" prefix
            district_elements = soup.find_all(text=re.compile(f"{district_name}", re.IGNORECASE))
        
        for element in district_elements:
            # Get the parent element to search from
            parent = element.parent
            district_text = element.strip()
            
            # Find the next content
            spots = set()  # Using a set to avoid duplicates
            current = parent
            
            # Search through next siblings until we find another district or run out of content
            while current:
                current = current.find_next()
                if not current:
                    break
                    
                # Stop if we hit another district
                if any(f"Bydel {d}" in current.text for d in oslo_districts):
                    break
                    
                # Split text by newlines and process each line separately
                lines = current.text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for spots for children under 3 years
                    if line and any(term in line.lower() for term in ['0-3','1-3', 'under 3', 'småbarn']):
                        spots.add(line)  # Using add() instead of append() since we're using a set
            
            if spots:  # Only add districts that have spots for children under 3
                districts[district_name] = {
                    'available_spots': sorted(list(spots))  # Convert set back to sorted list
                }
            break  # Take only the first matching element for each district
    
    return districts

def save_last_check(data):
    with open('last_check.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_last_check():
    try:
        with open('last_check.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def send_notification(title, message):
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            try:
                import pync
                url = "https://www.oslo.kommune.no/barnehage/ledige-barnehageplasser/"
                pync.notify(
                    message=message,
                    title=title,
                    open=url,
                    sound="default"
                )
            except ImportError:
                print("Please install pync: pip install pync")
                
    except Exception as e:
        print(f"Failed to send notification: {e}")

def check_for_updates():
    print(f"Checking for updates at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    html_content = fetch_webpage()
    if not html_content:
        return
    
    current_data = parse_kindergarten_spots(html_content)
    last_check = load_last_check()
    
    if current_data != last_check:
        print("\nNew updates found!")
        print("\nAvailable spots for children under 3 years:")
        print("-" * 50)
        
        # Print detailed info to console
        for district, info in current_data.items():
            if info['available_spots']:
                print(f"\n{district}")
                for spot in info['available_spots']:
                    print(f"- {spot}")
        
        # Find which districts have changed
        updated_districts = []
        for district in current_data:
            if district not in last_check or current_data[district] != last_check[district]:
                updated_districts.append(district)
        
        # Prepare concise notification message with kindergarten names
        notification_lines = []
        notification_lines.append(f"Updates in: {', '.join(updated_districts)}")
        notification_lines.append("")  # Empty line for spacing
        
        for district, info in current_data.items():
            if district in updated_districts:  # Only show updated districts
                kindergartens = []
                for spot in info['available_spots']:
                    if ">" in spot:
                        kinder_name = spot.split(">")[1].split(",")[0].strip()
                    else:
                        kinder_name = spot.split(",")[0].strip()
                    kindergartens.append(kinder_name)
                if kindergartens:
                    notification_lines.append(f"{district}: {', '.join(kindergartens)}")
        
        notification_msg = "\n".join(notification_lines)
        
        # Send notification
        send_notification(
            "Kindergarten Updates Available",
            notification_msg
        )
        
        save_last_check(current_data)
    else:
        print("No new updates found.")

def main():
    while True:
        check_for_updates()
        print("\nWaiting 30 minutes before next check...")
        time.sleep(1800)  # Wait 30 minutes

if __name__ == "__main__":
    main()
