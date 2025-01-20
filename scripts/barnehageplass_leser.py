import requests
from bs4 import BeautifulSoup
import re

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

    oslo_districts = [
        "Alna", "Bjerke", "Frogner", "Gamle Oslo", "Grorud",
        "Grünerløkka", "Nordre Aker", "Nordstrand", "Sagene",
        "St. Hanshaugen", "Stovner", "Søndre Nordstrand",
        "Ullern", "Vestre Aker", "Østensjø"
    ]

    soup = BeautifulSoup(html_content, 'html.parser')
    districts = {}
    
    for district_name in oslo_districts:
        district_elements = soup.find_all(text=re.compile(f"Bydel {district_name}", re.IGNORECASE))
        if not district_elements:
            district_elements = soup.find_all(text=re.compile(f"{district_name}", re.IGNORECASE))
        
        for element in district_elements:
            parent = element.parent
            district_text = element.strip()
            spots = set()
            current = parent
            
            while current:
                current = current.find_next()
                if not current:
                    break
                if any(f"Bydel {d}" in current.text for d in oslo_districts):
                    break
                
                lines = current.text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and any(term in line.lower() for term in ['0-3','1-3', 'under 3', 'småbarn']):
                        spots.add(line)
            
            if spots:
                districts[district_name] = {
                    'available_spots': sorted(list(spots))
                }
            break
    
    return districts 