import requests
from bs4 import BeautifulSoup
import json
import time

URLS = [
    # Admissions
    "https://www.ucmo.edu/future-students/admissions/incoming-freshman/index.php",
    "https://www.ucmo.edu/future-students/admissions/undergraduate-admissions/transfer-students/index.php",
    "https://www.ucmo.edu/future-students/admissions/graduate-admissions/index.php",
    "https://www.ucmo.edu/future-students/admissions/international-admissions/index.php",

    # Financial Aid
    "https://www.ucmo.edu/offices/student-financial-services/",
    "https://www.ucmo.edu/future-students/financing-your-education/contact-student-financial-services/",

    # Registrar
    "https://www.ucmo.edu/current-students/office-of-the-registrar-and-student-records/",
    "https://www.ucmo.edu/current-students/office-of-the-registrar-and-student-records/transcripts/",
    "https://www.ucmo.edu/current-students/office-of-the-registrar-and-student-records/academic-records/",

    # Housing
    "https://www.ucmo.edu/future-students/university-housing-and-dining-services/",
    "https://www.ucmo.edu/future-students/university-housing-and-dining-services/apply-for-housing/index.php",
    "https://www.ucmo.edu/future-students/university-housing-and-dining-services/residence-hall-living/index.php",
    "https://www.ucmo.edu/future-students/university-housing-and-dining-services/apartment-living/index.php",

    # IT Support
    "https://www.ucmo.edu/offices/office-of-technology/",
    "https://www.ucmo.edu/offices/office-of-technology/internal-resources/shared/technology-support-center/index.php",

    # Student Services
    "https://www.ucmo.edu/current-students/student-services/",
]

def scrape_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; UCMHelpdesk/1.0)"}
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code != 200:
            print(f"  Skipped {url} — status {response.status_code}")
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())
        print(f"  OK: {url} ({len(text)} chars)")
        return {"url": url, "text": text}
    except Exception as e:
        print(f"  Failed {url}: {e}")
        return None

print("Starting scraper...\n")
data = []
for url in URLS:
    result = scrape_page(url)
    if result:
        data.append(result)
    time.sleep(1)

with open("scraper/scraped_data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"\nDone. Scraped {len(data)}/{len(URLS)} pages successfully.")