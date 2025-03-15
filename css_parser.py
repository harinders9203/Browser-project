import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import cssutils

def fetch_html(url):
    """Fetch HTML content from a URL, handling encoding and errors."""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def fetch_css(url):
    """Fetch CSS content from a given URL."""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch CSS from {url}: {e}")
        return None

def parse_html_for_css(url, html_content):
    """Extract inline, internal, and external CSS from an HTML document."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Extract Inline CSS
    inline_styles = {}
    for tag in soup.find_all(style=True):
        selector = tag.name
        if 'id' in tag.attrs:
            selector += f"#{tag['id']}"
        if 'class' in tag.attrs:
            selector += '.' + '.'.join(tag['class'])
        inline_styles[selector] = tag['style']

    # 2. Extract Internal CSS
    internal_styles = []
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            internal_styles.append(style_tag.string)

    # 3. Extract External CSS
    external_styles = []
    external_css_urls = []
    for link_tag in soup.find_all('link', rel='stylesheet'):
        href = link_tag.get('href')
        if href:
            full_url = urljoin(url, href)
            external_css_urls.append(full_url)
            css_content = fetch_css(full_url)
            if css_content:
                external_styles.append(css_content)

    return inline_styles, internal_styles, external_styles, external_css_urls

def parse_css(css_text):
    """Parse standalone CSS to extract selectors and properties."""
    parsed_css = {}
    css_rules = re.findall(r'([^{]+)\s*\{([^}]+)\}', css_text)  # Extract CSS rules

    for selector, properties in css_rules:
        properties_dict = {}
        properties = properties.strip().split(";")  # Split properties
        for prop in properties:
            if ":" in prop:
                key, value = prop.split(":", 1)
                properties_dict[key.strip()] = value.strip()
        parsed_css[selector.strip()] = properties_dict

    return parsed_css

def extract_imports(css_text, base_url):
    """Find @import rules and fetch those CSS files."""
    imported_css = []
    imports = re.findall(r'@import\s+["\']?(.*?)["\']?;', css_text)

    for css_url in imports:
        full_url = urljoin(base_url, css_url)
        css_content = fetch_css(full_url)
        if css_content:
            imported_css.append(css_content)

    return imported_css

def apply_css(html_structure, css_text):
    """Apply CSS rules as inline styles to HTML elements."""
    soup = BeautifulSoup(html_structure, "html.parser")
    parsed_css = cssutils.parseString(css_text)
    
    for rule in parsed_css:
        if rule.type == rule.STYLE_RULE:
            for selector in rule.selectorList:
                elements = soup.select(selector.selectorText)
                for element in elements:
                    existing_style = element.get("style", "")
                    new_style = rule.style.cssText
                    element["style"] = f"{existing_style}; {new_style}".strip()
    
    return str(soup)

def main():
    """Main function that fetches a webpage and extracts CSS."""
    example_url = os.environ.get("TARGET_URL")

    if not example_url:
        print("No URL provided. Set the 'TARGET_URL' environment variable.")
        return

    html_content = fetch_html(example_url)
    if not html_content:
        return

    inline_styles, internal_styles, external_styles, external_css_urls = parse_html_for_css(example_url, html_content)

    # Process @import in external CSS
    full_external_css = "\n".join(external_styles)
    imported_styles = extract_imports(full_external_css, example_url)

    print("\n🔹 INLINE CSS:")
    for selector, styles in inline_styles.items():
        print(f"{selector} {{ {styles} }}")

    print("\n🔹 INTERNAL CSS:")
    for style in internal_styles:
        parsed_internal = parse_css(style)
        for selector, properties in parsed_internal.items():
            print(f"{selector} {{ {properties} }}")

    print("\n🔹 EXTERNAL CSS:")
    for url, style in zip(external_css_urls, external_styles):
        print(f"\n🔹 From {url}:\n")
        parsed_external = parse_css(style)
        for selector, properties in parsed_external.items():
            print(f"{selector} {{ {properties} }}")

    print("\n🔹 IMPORTED CSS:")
    for style in imported_styles:
        parsed_imported = parse_css(style)
        for selector, properties in parsed_imported.items():
            print(f"{selector} {{ {properties} }}")

if __name__ == "__main__":
    main()
