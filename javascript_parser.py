from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import httpx
from bs4 import BeautifulSoup
import execjs
from urllib.parse import urljoin, urlparse

app = FastAPI()

# JavaScript Wrapper for Esprima
esprima_wrapper = """
    var esprima;
    try {
        esprima = require('esprima');
    } catch (e) {
        console.log('Esprima not found. Please install it using npm install esprima');
    }

    function parseJSCode(jsCode) {
        const syntaxTree = esprima.parseScript(jsCode, { range: true, tokens: true, comment: true });
        return JSON.stringify(syntaxTree, null, 2);
    }
"""

# Initialize JS Runtime Context
ctx = execjs.compile(esprima_wrapper)

def is_valid_url(url: str) -> bool:
    """Check if the given URL is valid."""
    parsed_url = urlparse(url)
    return bool(parsed_url.scheme and parsed_url.netloc)

async def fetch_js(url: str):
    """Fetch external JavaScript file content."""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        print(f"Error fetching JS file {url}: {e}")
        return None

async def fetch_and_parse_js(url: str):
    """Fetch a webpage and parse both inline & external JavaScript."""
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format.")
    
    try:
        # Step 1: Fetch the Webpage
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text

        # Step 2: Extract JavaScript from <script> Tags
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script')

        js_code = ""
        external_js_urls = []

        for script in scripts:
            if script.string:  # Inline JavaScript
                js_code += script.string + "\n"
            elif script.get("src"):  # External JavaScript file
                full_url = urljoin(url, script["src"])
                external_js_urls.append(full_url)

        # Step 3: Fetch & Append External JavaScript Files
        for js_url in external_js_urls:
            external_js = await fetch_js(js_url)
            if external_js:
                js_code += "\n" + external_js

        if not js_code.strip():
            return {"message": "No JavaScript found on this page."}

        # Step 4: Parse the JavaScript Code using Esprima
        parsed_ast = ctx.call("parseJSCode", js_code)

        return {"url": url, "parsed_ast": parsed_ast}

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {e}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timed out.")
    except execjs.ProgramError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing JavaScript: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# FastAPI Route for Parsing JS from Live Webpages
@app.get("/parse-js/")
async def parse_js(url: str = Query(..., title="Website URL", description="URL of the webpage to parse JavaScript from")):
    result = await fetch_and_parse_js(url)
    return JSONResponse(content=result)