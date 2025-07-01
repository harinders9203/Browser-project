import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def fetch_html(url):
    """Fetch HTML content from a URL, handling encoding and errors."""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def fetch_html_js(url):
    """Fetch HTML using Selenium to handle JavaScript-rendered content."""
    try:
        service = Service(ChromeDriverManager().install())
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images for speed
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        driver.implicitly_wait(5)  # Wait for JS to load
        html = driver.page_source
        driver.quit()
        return html
    except Exception as e:
        print(f"Error loading JavaScript-rendered content: {e}")
        return None

def parse_html(html_content):
    """Parse the HTML content using BeautifulSoup."""
    return BeautifulSoup(html_content, 'html.parser')

def extract_data(soup, base_url):
    """Extract links, headings, paragraphs, images, and metadata."""
    data = {
        'links': [],
        'headings': [],
        'paragraphs': [],
        'images': [],
        'metadata': {}
    }
    
    for link in soup.find_all('a', href=True):
        absolute_url = urljoin(base_url, link['href'])
        data['links'].append(absolute_url)
    
    data['headings'] = [h.text.strip() for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
    data['paragraphs'] = [p.text.strip() for p in soup.find_all('p')]
    data['images'] = [urljoin(base_url, img['src']) for img in soup.find_all('img', src=True)]
    
    # Extract metadata (title, description, keywords)
    title = soup.find('title')
    data['metadata']['title'] = title.text.strip() if title else ""
    
    description = soup.find('meta', attrs={'name': 'description'})
    data['metadata']['description'] = description['content'].strip() if description else ""
    
    keywords = soup.find('meta', attrs={'name': 'keywords'})
    data['metadata']['keywords'] = keywords['content'].strip() if keywords else ""
    
    return data

def main():
    """Main function that fetches and processes a web page."""
    from render import get_url  # Import inside function to prevent circular import

    url = get_url()
    if url:
        html_content = fetch_html(url)
        
        # If the page is empty or needs JavaScript, use Selenium
        if not html_content or len(html_content.strip()) < 1000:
            html_content = fetch_html_js(url)
        
        if html_content:
            soup = parse_html(html_content)
            data = extract_data(soup, url)

            print("Metadata:")
            for key, value in data['metadata'].items():
                print(f"{key.capitalize()}: {value}")
            
            print("\nLinks:")
            for link in data['links'][:10]:  # Limit output
                print(link)
            
            print("\nHeadings:")
            for heading in data['headings'][:10]:
                print(heading)
            
            print("\nParagraphs:")
            for para in data['paragraphs'][:5]:
                print(para)
            
            print("\nImages:")
            for img in data['images'][:5]:
                print(img)
        else:
            print("Failed to retrieve the web page.")
    else:
        print("No URL provided by render.py.")

if __name__ == "__main__":
    main()
