import requests
from bs4 import BeautifulSoup
import json
import urllib3
from datetime import datetime
import re
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_date_or_year(text):
    """Pehle full date dhoondhega, warna 2015 ya aage ka Year nikalega"""
    date_patterns = [
        r'\d{1,2}-\d{1,2}-\d{4}',          
        r'\d{1,2}/\d{1,2}/\d{4}',          
        r'\d{1,2}\.\d{1,2}\.\d{4}',        
        r'\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+\d{4}'  
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
            
    year_match = re.search(r'\b(201[5-9]|20[2-3]\d)\b', text)
    if year_match:
        return year_match.group(0)
    return None

def scrape_dgms_circulars():
    url = "https://www.dgms.gov.in/UserView/index?mid=1648"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # 1. Purana data load karo
    existing_data = []
    if os.path.exists('circular.json'):
        with open('circular.json', 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
                
    # 2. Sirf 'Titles' ka ek set bana lo taaki match karna aasan ho
    existing_titles = {item['title'] for item in existing_data if 'title' in item}
    new_items_added = 0
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            form_tag = soup.find('form', action="/UserView")
            
            if form_tag:
                items = form_tag.find_all('li')
                
                for item in items:
                    link_tag = item.find('a', href=True)
                    
                    if link_tag:
                        title = item.get_text(separator=" ", strip=True)
                        clean_title = re.sub(r'\s*\(\s*\d+\.?\d*\s*[KMG]B\s*\).*', '', title).strip()
                        href = link_tag['href']
                        full_url = href if href.startswith('http') else f"https://www.dgms.gov.in{href}"
                        
                        if clean_title and len(clean_title) > 5:
                            
                            # 3. YAHAN HAI AAPKA LOGIC: Agar title pehle se nahi hai, tabhi add karo
                            if clean_title not in existing_titles:
                                published_at = extract_date_or_year(title)
                                scraped_at = datetime.now().isoformat()
                                
                                circular_item = {
                                    "title": clean_title,
                                    "link": full_url,
                                    "published_at": published_at,
                                    "scraped_at": scraped_at,
                                    "file_type": "PDF" if ".pdf" in full_url.lower() else "Link"
                                }
                                
                                existing_data.append(circular_item)
                                existing_titles.add(clean_title) # Naye title ko bhi track list mein daal do
                                new_items_added += 1
            
            # 4. Agar naye items mile hain, toh hi file save karo
            if new_items_added > 0:
                # Naye data ko date/year ke hisaab se sort kardo
                existing_data.sort(key=lambda x: x['published_at'] or '0000', reverse=True)
                
                with open('circular.json', 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=4, ensure_ascii=False)
                
                print(f"✅ Naye {new_items_added} circulars add kiye gaye!")
            else:
                print("📭 Koi naya circular nahi mila. File update nahi hui.")
                
        else:
            raise Exception(f"HTTP Request failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise e

if __name__ == "__main__":
    scrape_dgms_circulars()
