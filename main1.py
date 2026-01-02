import json
import re
import sys
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings()

KEYWORDS = {
    'news': ['news', 'media', 'announcement', 'notice', 'समाचार', 'सूचना'],
    'press_release': ['press', 'press-release'],
    'annual_report': ['annual', 'annual-report', 'वार्षिक'],
}

class Crawler:
    def __init__(self, url):
        self.url = url if url.startswith('http') else 'https://' + url
        self.domain = urlparse(self.url).netloc
        self.results = {cat: [] for cat in KEYWORDS}

    def fetch(self, url):
        try:
            resp = requests.get(url, timeout=10, verify=False, 
                headers={'User-Agent': 'Mozilla/5.0'})
            return resp.text if resp.ok else None
        except:
            return None

    def get_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            full_url = urljoin(self.url, a['href'])
            links.append({'url': full_url, 'text': a.get_text(strip=True)})
        return links

    def categorize(self, text, url):
        text, url = text.lower(), url.lower()
        return [cat for cat, words in KEYWORDS.items() 
                if any(w in text or w in url for w in words)]

    def is_main_page(self, url):
        path = urlparse(url.lower()).path
        # Skip files and detail pages
        if path.endswith(('.pdf', '.doc', '.xls', '.xlsx')):
            return False
        if re.search(r'/\d+/?$', path):
            return False
        return True

    def crawl(self):
        html = self.fetch(self.url)
        if not html:
            return

        for link in self.get_links(html):
            url, text = link['url'], link['text']
            
            # Only internal, main section pages
            if self.domain not in urlparse(url).netloc:
                continue
            if not self.is_main_page(url):
                continue

            for cat in self.categorize(text, url):
                self.results[cat].append(url)

    def print_results(self):
        print(f"\nResults for: {self.url}\n" + "=" * 50)
        for cat, links in self.results.items():
            unique = sorted(set(links))
            if unique:
                print(f"\n{cat.replace('_', ' ').title()}:")
                for link in unique:
                    print(f"  - {link}")
        print()

    def save_json(self):
        # Use domain name as filename
        name = self.domain.replace('www.', '').split('.')[0]
        filename = f"{name}.json"
        clean = {cat: sorted(set(links)) for cat, links in self.results.items()}
        data = {"url": self.url, "results": clean}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {filename}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main_crawler.py <url>")
        sys.exit(1)
    
    crawler = Crawler(sys.argv[1])
    crawler.crawl()
    crawler.print_results()
    crawler.save_json()
