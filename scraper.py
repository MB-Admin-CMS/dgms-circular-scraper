import requests
from bs4 import BeautifulSoup
import json
import urllib3
from datetime import datetime
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_date_or_year(text):
    """
    Pehle full date dhoondhega, agar nahi mili toh sirf Year nikalega
    """
    # 1. Full date formats check karo
    date_patterns = [
        r'\d{1,2}-\d{1,2}-\d{4}',          # DD-MM-YYYY
        r'\d{1,2}/\d{1,2}/\d{4}',          # DD/MM/YYYY
        r'\d{1,2}\.\d{1,2}\.\d{4}',        # DD.MM.YYYY
        r'\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+\d{4}'  # 18th May 2023 ya 24 April 2024
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
            
    # 2. Agar full date nahi mili, toh sirf 4-digit Year dhoondho (e.g., 2018, 1952)
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    if year_match:
        return year_match.group(0)
        
    return None

def scrape_dgms_circulars():
    url = "https://www.dgms.gov.in/UserView/index?mid=1648"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            circular_list = []
            
            form_tag = soup.find('form', action="/UserView")
            
            if form_tag:
                items = form_tag.find_all('li')
                
                for item in items:
                    link_tag = item.find('a', href=True)
                    
                    if link_tag:
                        title = item.get_text(separator=" ", strip=True)
                        
                        # Clean title: Remove file size like "(540 KB)"
                        clean_title = re.sub(r'\s*\(\s*\d+\.?\d*\s*[KMG]B\s*\).*', '', title).strip()
                        
                        href = link_tag['href']
                        full_url = href if href.startswith('http') else f"https://www.dgms.gov.in{href}"
                        
                        if clean_title and len(clean_title) > 5:
                            # Naya function call kiya jo date ya year nikalega
                            published_at = extract_date_or_year(title)
                            scraped_at = datetime.now().isoformat()
                            
                            circular_item = {
                                "title": clean_title,
                                "link": full_url,
                                "published_at": published_at,
                                "scraped_at": scraped_at,
                                "file_type": "PDF" if ".pdf" in full_url.lower() else "Link"
                            }
                            
                            circular_list.append(circular_item)
            
            if circular_list:
                seen = set()
                final_circulars = []
                
                # Duplicates remove karo
                for n in circular_list:
                    key = (n['title'], n['link'])
                    if key not in seen:
                        final_circulars.append(n)
                        seen.add(key)
                
                # Sort by published_at (Descending). Agar date nahi hai toh bottom pe jayega
                final_circulars.sort(key=lambda x: x['published_at'] or '0000', reverse=True)
                
                with open('circular.json', 'w', encoding='utf-8') as f:
                    json.dump(final_circulars, f, indent=4, ensure_ascii=False)
                    
                # Print local test ke liye, GitHub pe action fast rakhne ke liye hata sakte ho
                # print(f"✅ Success! Found {len(final_circulars)} circulars.")
            else:
                raise Exception("No circulars found inside the <form action='/UserView'> tag.")
                
        else:
            raise Exception(f"HTTP Request failed with status code: {response.status_code}")
            
    except Exception as e:
        raise e

if __name__ == "__main__":
    scrape_dgms_circulars()
