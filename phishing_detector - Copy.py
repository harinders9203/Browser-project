import re
import urllib.parse
import requests
from urllib.parse import urlparse
import tldextract
import socket
import ssl
import whois
from datetime import datetime
import threading

class PhishingDetector:
    def __init__(self):
        self.suspicious_terms = [
            'login', 'signin', 'verify', 'account', 'secure', 'update', 'banking',
            'password', 'credential', 'confirm', 'paypal', 'security', 'authenticate'
        ]
        self.legitimate_domains = set([
            'google.com', 'facebook.com', 'twitter.com', 'microsoft.com', 'apple.com',
            'amazon.com', 'github.com', 'linkedin.com', 'instagram.com', 'netflix.com'
        ])
        self.cache = {}
        self.cache_lock = threading.Lock()

    def analyze_url(self, url):
        """Analyze a URL for potential phishing indicators."""
        try:
            # Check cache first
            with self.cache_lock:
                if url in self.cache:
                    return self.cache[url]

            score = 0
            reasons = []
            
            # Parse the URL
            parsed_url = urlparse(url)
            extracted = tldextract.extract(url)
            domain = f"{extracted.domain}.{extracted.suffix}"

            # Check if it's a known legitimate domain
            if domain in self.legitimate_domains:
                return {"is_suspicious": False, "score": 0, "reasons": ["Known legitimate domain"]}

            # Check for suspicious terms in URL
            if any(term in url.lower() for term in self.suspicious_terms):
                score += 20
                reasons.append("Contains suspicious terms")

            # Check for IP address instead of domain name
            if re.match(r'^https?://\d+\.\d+\.\d+\.\d+', url):
                score += 30
                reasons.append("Uses IP address instead of domain name")

            # Check for suspicious TLD
            suspicious_tlds = ['.xyz', '.top', '.work', '.live', '.tk', '.ml', '.ga', '.cf']
            if any(tld in domain for tld in suspicious_tlds):
                score += 25
                reasons.append("Suspicious top-level domain")

            # Check for excessive subdomains
            if len(extracted.subdomain.split('.')) > 3:
                score += 15
                reasons.append("Excessive number of subdomains")

            # Check domain age if possible
            try:
                w = whois.whois(domain)
                if w.creation_date:
                    creation_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
                    if (datetime.now() - creation_date).days < 365:
                        score += 25
                        reasons.append("Domain is less than a year old")
            except:
                score += 10
                reasons.append("Could not verify domain age")

            # Check SSL certificate
            try:
                context = ssl.create_default_context()
                with socket.create_connection((parsed_url.netloc, 443)) as sock:
                    with context.wrap_socket(sock, server_hostname=parsed_url.netloc) as ssock:
                        cert = ssock.getpeercert()
                        # Check certificate validity
                        if not cert:
                            score += 30
                            reasons.append("Invalid SSL certificate")
            except:
                score += 20
                reasons.append("SSL certificate verification failed")

            # Check for URL encoding abuse
            if '%' in url:
                decoded_url = urllib.parse.unquote(url)
                if decoded_url != url:
                    score += 15
                    reasons.append("Suspicious URL encoding")

            # Check for redirects
            try:
                response = requests.head(url, allow_redirects=True, timeout=5)
                if len(response.history) > 2:
                    score += 15
                    reasons.append("Multiple redirects")
            except:
                score += 10
                reasons.append("Could not check redirects")

            result = {
                "is_suspicious": score >= 50,
                "score": score,
                "reasons": reasons
            }

            # Cache the result
            with self.cache_lock:
                self.cache[url] = result

            return result

        except Exception as e:
            return {
                "is_suspicious": True,
                "score": 100,
                "reasons": [f"Error analyzing URL: {str(e)}"]
            }

    def clear_cache(self):
        """Clear the URL analysis cache."""
        with self.cache_lock:
            self.cache.clear()

    def add_legitimate_domain(self, domain):
        """Add a domain to the legitimate domains list."""
        self.legitimate_domains.add(domain)

    def add_suspicious_term(self, term):
        """Add a term to the suspicious terms list."""
        self.suspicious_terms.append(term.lower()) 