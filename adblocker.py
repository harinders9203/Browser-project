import re
from bs4 import BeautifulSoup
import requests
import json
import os
from pathlib import Path

class AdBlocker:
    def __init__(self):
        self.blocked_domains = set()
        self.blocked_selectors = set()
        # Expanded list of ad domains with new keywords
        self.common_ad_domains = {
            'sharethis.com', 'doubleclick.net', 'google-analytics.com', 
            'adnxs.com', 'facebook.com', 'scorecardresearch.com',
            'quantserve.com', 'amazon-adsystem.com', 'googlesyndication.com',
            'outbrain.com', 'taboola.com', 'adroll.com', 'criteo.com',
            'bet', 'betting', 'casino', 'gambling', 'stake.com', '10bet',
            'betway', 'bet365', 'betting-ad', 'freebet', 'iframely.net',
            'iframe.ly', 'disqus.com', 'addthis.com', 'cloudflare.com',
            'mcafee', 'norton', 'avg', 'avast', 'kaspersky', 'bitdefender',
            'totalav', 'pcprotect', 'scanguard', 'antivirus', 'security-alert',
            'virus-alert', 'malware', 'clean-pc', 'system-alert', 'windows-security',
            'revcontent.com', 'zergnet.com', 'media.net', 'connatix.com',
            'infolinks.com', 'popads.net', 'propellerads.com', 'mgid.com',
            'yandex.com', 'adblade.com', 'adsafeprotected.com', 'teads.tv',
            'smartadserver.com', 'openx.net', 'rubiconproject.com', 'pubmatic.com',
            'adform.net', 'adition.com', 'advertising.com', 'bidswitch.net',
            'casalemedia.com', 'chartbeat.com', 'clicktale.net', 'cxense.com',
            'emxdgt.com', 'exelator.com', 'exponential.com', 'flashtalking.com',
            'gemius.pl', 'hotjar.com', 'id5-sync.com', 'innovid.com',
            'jsdelivr.net', 'keyade.com', 'krxd.net', 'lijit.com',
            'mathtag.com', 'moatads.com', 'mookie1.com', 'msecnd.net',
            'nexac.com', 'oneaudience.com', '33across.com', 'ad4m.at',
            'adocean.pl', 'adsrvr.org', 'adtech.de', 'adtelligent.com',
            'advanced-web-analytics.com', 'advertising.com', 'appnexus.com',
            'betweendigital.com', 'bidr.io', 'bidtheatre.com', 'bluekai.com',
            'bnmla.com', 'bttrack.com', 'contextweb.com', 'conversantmedia.com',
            'dotomi.com', 'dyntrk.com', 'everesttech.net', 'exdynsrv.com',
            'gumgum.com', 'hybrid.ai', 'improvedigital.com', 'justpremium.com',
            'light-speed-hosting.net', 'loopme.me', 'mfadsrvr.com', 'nr-data.net',
            'onesignal.com', 'optimizely.com', 'parsely.com', 'playground.xyz',
            'publiway.com', 'pusher.com', 'richaudience.com', 'seedtag.com',
            'sharethrough.com', 'simpli.fi', 'socdm.com', 'sonobi.com',
            'tremorhub.com', 'triplelift.com', 'trustarc.com', 'twiago.com',
            'tynt.com', 'undertone.com', 'vidible.tv', 'visualwebsiteoptimizer.com',
            'vmweb.net', 'zeotap.com', 'zemanta.com', 'zorosrv.com',
            # Add specific ad domains for hianime.tv
            'hianime.tv.ads', 'ads.hianime.tv', 'analytics.hianime.tv',
            'tracker.hianime.tv', 'stats.hianime.tv', 'pixel.hianime.tv',
            'metrics.hianime.tv', 'counter.hianime.tv', 'log.hianime.tv',
            'track.hianime.tv', 'analytics.hianime.to', 'ads.hianime.to',
            'push-notification', 'browser-notification', 'notify', 'alert-system',
            'notification-center', 'push-service', 'brave-notification',
            'chrome-alert', 'firefox-alert', 'edge-alert', 'safari-alert',
            'browser-update', 'browser-check', 'browser-verify', 'verify-browser',
            'validate-browser', 'check-browser', 'update-required',
            'crypto', 'bitcoin', 'ethereum', 'dogecoin', 'binance', 'coinbase',
            'forex', 'trading', 'broker', 'investment', 'profit', 'lucky',
            'jackpot', 'win-money', 'bonus', 'free-money', 'easy-money',
            'lottery', 'poker', 'bingo', 'slots', 'roulette', 'blackjack',
            'sportsbet', 'sportbook', 'boomaker', 'odds', 'wager', 'gamble',
            'popup', 'pop-up', 'popunder', 'pop-under', 'interstitial',
            'overlay', 'modal', 'lightbox', 'newsletter', 'subscribe',
            'subscription', 'sign-up', 'signup', 'register', 'registration',
            'join-now', 'join-today', 'limited-time', 'limited-offer',
            'special-offer', 'exclusive-offer', 'discount', 'sale',
            'clearance', 'best-price', 'best-deal', 'coupon', 'promo-code',
            'download-now', 'install-now', 'get-now', 'click-here',
            'click-now', 'act-now', 'buy-now', 'purchase-now', 'order-now',
            'trojan', 'spyware', 'adware', 'ransomware', 'phishing',
            'virus-detected', 'infection-detected', 'malware-detected',
            'clean-your-pc', 'speed-up-pc', 'optimize-pc', 'boost-pc',
            'your-pc-is', 'your-computer-is', 'system-compromised',
            'system-at-risk', 'privacy-at-risk', 'security-risk',
            'critical-alert', 'urgent-alert', 'important-alert',
            'security-scan', 'virus-scan', 'system-scan', 'pc-scan',
            'scan-result', 'scan-results', 'security-breach', 'data-breach',
            'infected-with', 'compromised-by', 'at-risk', 'detect',
            'security-warning', 'windows-warning', 'apple-warning',
            'mac-warning', 'android-warning', 'ios-warning',
            'system-warning', 'browser-warning', 'attention-required',
            'action-required', 'immediate-action', 'warning-do-not-close',
            'do-not-close-this', 'do-not-leave', 'leave-page-warning',
            'vpn-alert', 'vpn-warning', 'ip-exposed', 'ip-visible',
            'location-exposed', 'location-visible', 'privacy-risk',
            'privacy-alert', 'privacy-warning', 'privacy-notice',
            'privacy-breach', 'data-exposed', 'data-visible',
            'browsing-history', 'browsing-activity', 'online-activity',
            'online-behavior', 'tracking-alert', 'tracking-warning',
            'surveillance-alert', 'surveillance-warning',
            'monitored', 'watched', 'spied-on', 'hacked',
            'malvertising', 'black-friday', 'apk',
            'public wi-fi', 'whatsapp', 'stay safe', 'at risk',
            'mcafee', 'scan', 'virus', 'trojan', 'hianime',
            'push notifications', 'chrome mobile', 'learn more'  # New keywords
        }
        
        # Expanded aggressive popup selectors
        self.popup_selectors = {
            '[class*="popup"]', '[class*="modal"]', '[class*="overlay"]',
            '[id*="popup"]', '[id*="modal"]', '[id*="overlay"]',
            '[class*="betting"]', '[class*="bet-"]', '[class*="casino"]',
            '[class*="gambling"]', '[class*="stake"]', '[class*="freebet"]',
            'iframe[src*="bet"]', 'iframe[src*="stake"]', 'iframe[src*="gambling"]',
            'div[style*="position: fixed"]', 'div[style*="position:fixed"]',
            'div[style*="z-index"]', 'div[style*="pointer-events"]',
            'div[style*="visibility"]', 'div[style*="backdrop"]',
            'div[style*="background-color: rgba"]', 'div[style*="background: rgba"]',
            '[class*="ad"]', '[id*="ad"]', '[class*="ads"]', '[id*="ads"]',
            '[class*="banner"]', '[id*="banner"]', '[class*="sponsor"]', '[id*="sponsor"]',
            '[class*="promo"]', '[id*="promo"]', '[class*="advert"]', '[id*="advert"]',
            '[class*="notification"]', '[id*="notification"]', '[class*="alert"]', '[id*="alert"]',
            '[class*="warning"]', '[id*="warning"]', '[class*="float"]', '[id*="float"]',
            '[class*="sticky"]', '[id*="sticky"]', '[class*="interstitial"]', '[id*="interstitial"]',
            '[class*="mcafee"]', '[id*="mcafee"]', '[class*="norton"]', '[id*="norton"]',
            '[class*="antivirus"]', '[id*="antivirus"]', '[class*="security"]', '[id*="security"]',
            '[class*="scan"]', '[id*="scan"]', '[class*="virus"]', '[id*="virus"]',
            '[class*="malware"]', '[id*="malware"]', '[class*="protect"]', '[id*="protect"]',
            '[class*="totalav"]', '[id*="totalav"]', '[class*="update"]', '[id*="update"]',
            '[class*="dangers"]', '[id*="dangers"]', '[class*="stay-safe"]', '[id*="stay-safe"]',
            '[class*="public-wifi"]', '[id*="public-wifi"]', '[class*="chrome-notification"]', '[id*="chrome-notification"]',
            '[class*="click-here"]', '[id*="click-here"]', '[class*="learn-more"]', '[id*="learn-more"]',
            '[class*="important-updates"]', '[id*="important-updates"]', '[class*="pending"]', '[id*="pending"]',
            '[class*="spyware"]', '[id*="spyware"]', '[class*="malicious-software"]', '[id*="malicious-software"]',
            '[class*="install-updates"]', '[id*="install-updates"]',
            'img[src*="ad"]', 'img[src*="banner"]', 'img[src*="sponsor"]', 'img[src*="promo"]',
            'img[src*="mcafee"]', 'img[src*="norton"]', 'img[src*="antivirus"]',
            'img[src*="alert"]', 'img[src*="warning"]', 'img[src*="security"]',
            'script[src*="ad"]', 'script[src*="analytics"]', 'script[src*="tracking"]',
            'div[onclick]', 'div[onmouseover]', 'div[onmouseout]',
            '[aria-label*="ad"]', '[aria-label*="sponsored"]', '[aria-label*="promoted"]',
            '[data-ad]', '[data-ads]', '[data-banner]', '[data-promo]', '[data-sponsored]',
            'ins[class*="ads"]', 'ins[id*="ads"]', 'aside[class*="ad"]', 'aside[id*="ad"]',
            'body > div:not([id]):not([class])', 'body > div[style]', 'body > div[style*="opacity"]',
            'div[style*="transform"]', 'div[style*="transition"]', 'div[style*="animation"]', 
            'div[style*="overflow: hidden"]', 'div[style*="overflow:hidden"]',
            '[style*="top: 0"]', '[style*="top:0"]', '[style*="left: 0"]', '[style*="left:0"]',
            '[style*="right: 0"]', '[style*="right:0"]', '[style*="bottom: 0"]', '[style*="bottom:0"]',
            '[style*="width: 100%"]', '[style*="width:100%"]', '[style*="height: 100%"]', '[style*="height:100%"]',
            '[style*="position: absolute"]', '[style*="position:absolute"]',
            '[style*="box-shadow"]', '[style*="box-shadow"]', '[style*="filter: blur"]', '[style*="filter:blur"]',
            '[class*="consent"]', '[id*="consent"]', '[class*="cookie"]', '[id*="cookie"]',
            '[class*="gdpr"]', '[id*="gdpr"]', '[class*="ccpa"]', '[id*="ccpa"]',
            '[class*="privacy-notice"]', '[id*="privacy-notice"]', '[class*="privacy-policy"]', '[id*="privacy-policy"]',
            '[class*="accept"]', '[id*="accept"]', '[class*="agree"]', '[id*="agree"]',
            'div[aria-label*="consent"]', 'div[aria-label*="cookie"]', 'div[aria-describedby*="consent"]',
            '[class*="newsletter"]', '[id*="newsletter"]', '[class*="subscription"]', '[id*="subscription"]',
            '[class*="subscribe"]', '[id*="subscribe"]', '[class*="sign-up"]', '[id*="sign-up"]',
            '[class*="signup"]', '[id*="signup"]', '[class*="register"]', '[id*="register"]',
            '[class*="registration"]', '[id*="registration"]', '[class*="join"]', '[id*="join"]',
            '[class*="free-trial"]', '[id*="free-trial"]', '[class*="trial"]', '[id*="trial"]',
            '[class*="social"]', '[id*="social"]', '[class*="share"]', '[id*="share"]',
            '[class*="follow"]', '[id*="follow"]', '[class*="facebook"]', '[id*="facebook"]',
            '[class*="twitter"]', '[id*="twitter"]', '[class*="instagram"]', '[id*="instagram"]',
            '[class*="linkedin"]', '[id*="linkedin"]', '[class*="pinterest"]', '[id*="pinterest"]',
            '[class*="youtube"]', '[id*="youtube"]', '[class*="tiktok"]', '[id*="tiktok"]',
            '[class*="exit"]', '[id*="exit"]', '[class*="leave"]', '[id*="leave"]',
            '[class*="before-you-go"]', '[id*="before-you-go"]', '[class*="wait"]', '[id*="wait"]',
            '[class*="dont-miss"]', '[id*="dont-miss"]', '[class*="don\'t-miss"]', '[id*="don\'t-miss"]',
            '[class*="special-offer"]', '[id*="special-offer"]', '[class*="limited-time"]', '[id*="limited-time"]',
            '[class*="last-chance"]', '[id*="last-chance"]', '[class*="one-time"]', '[id*="one-time"]',
            '[class*="feedback"]', '[id*="feedback"]', '[class*="survey"]', '[id*="survey"]',
            '[class*="questionnaire"]', '[id*="questionnaire"]', '[class*="opinion"]', '[id*="opinion"]',
            '[class*="review"]', '[id*="review"]', '[class*="rating"]', '[id*="rating"]',
            '[class*="chat"]', '[id*="chat"]', '[class*="support"]', '[id*="support"]',
            '[class*="help"]', '[id*="help"]', '[class*="assistant"]', '[id*="assistant"]',
            '[class*="service"]', '[id*="service"]', '[class*="livechat"]', '[id*="livechat"]',
            '[class*="live-chat"]', '[id*="live-chat"]', '[class*="messenger"]', '[id*="messenger"]',
            '[class*="intercom"]', '[id*="intercom"]', '[class*="drift"]', '[id*="drift"]',
            '[class*="tawk"]', '[id*="tawk"]', '[class*="zendesk"]', '[id*="zendesk"]',
            '[class*="crisp"]', '[id*="crisp"]', '[class*="olark"]', '[id*="olark"]',
            '[class*="push-notification"]', '[id*="push-notification"]',
            '[class*="web-notification"]', '[id*="web-notification"]',
            '[class*="browser-notification"]', '[id*="browser-notification"]',
            '[class*="notification-center"]', '[id*="notification-center"]',
            '[class*="notification-bar"]', '[id*="notification-bar"]',
            '[class*="notification-popup"]', '[id*="notification-popup"]',
            '[class*="notification-modal"]', '[id*="notification-modal"]',
            '[class*="notification-overlay"]', '[id*="notification-overlay"]',
            '[class*="notification-banner"]', '[id*="notification-banner"]',
            '[class*="notification-alert"]', '[id*="notification-alert"]',
            '[class*="notification-warning"]', '[id*="notification-warning"]',
            '[class*="notification-message"]', '[id*="notification-message"]',
            '[class*="notification-content"]', '[id*="notification-content"]',
            '[class*="notification-container"]', '[id*="notification-container"]',
            '[class*="notification-wrapper"]', '[id*="notification-wrapper"]',
            '[class*="notification-box"]', '[id*="notification-box"]',
            '[class*="notification-frame"]', '[id*="notification-frame"]',
            '[class*="notification-iframe"]', '[id*="notification-iframe"]',
            '[class*="notification-window"]', '[id*="notification-window"]',
            '[class*="notification-dialog"]', '[id*="notification-dialog"]',
            '[class*="notification-lightbox"]', '[id*="notification-lightbox"]',
            '[class*="notification-toast"]', '[id*="notification-toast"]',
            '[class*="malvertising"]', '[id*="malvertising"]',
            '[class*="black-friday"]', '[id*="black-friday"]',
            '[class*="apk"]', '[id*="apk"]',
            '[class*="shop-now"]', '[id*="shop-now"]',
            'button[class*="sale"]', 'a[class*="sale"]',
            'button[style*="border"]', 'a[style*="border"]',
            'button:contains("Shop Now")', 'a:contains("Shop Now")',
            '[class*="public-wifi"]', '[id*="public-wifi"]',
            '[class*="whatsapp"]', '[id*="whatsapp"]',
            '[class*="stay-safe"]', '[id*="stay-safe"]',
            '[class*="at-risk"]', '[id*="at-risk"]',
            '[style*="display: flex"]', '[style*="display:flex"]',
            '[style*="display: grid"]', '[style*="display:grid"]',
            '[style*="justify-content: center"]', '[style*="align-items: center"]',
            '[style*="z-index"]', '[style*="z-index: 1"]', '[style*="z-index: 2"]',
            'div[style*="margin: auto"]', 'div[style*="margin:auto"]',
            'button', 'a',
            '[class*="mcafee"]', '[id*="mcafee"]',
            '[class*="scan"]', '[id*="scan"]',
            '[class*="virus"]', '[id*="virus"]',
            '[class*="trojan"]', '[id*="trojan"]',
            '[class*="hianime"]', '[id*="hianime"]',
            '[class*="push-notifications"]', '[id*="push-notifications"]',  # New selectors
            '[class*="chrome-mobile"]', '[id*="chrome-mobile"]',
            '[class*="learn-more"]', '[id*="learn-more"]',
            # Add specific selectors for hianime.tv
            '[class*="hianime-ad"]',
            '[id*="hianime-ad"]',
            '[class*="hianime-popup"]',
            '[id*="hianime-popup"]',
            '[class*="hianime-overlay"]',
            '[id*="hianime-overlay"]',
            '[class*="hianime-modal"]',
            '[id*="hianime-modal"]',
            '[class*="hianime-float"]',
            '[id*="hianime-float"]',
            '[class*="hianime-sticky"]',
            '[id*="hianime-sticky"]',
            '[class*="hianime-banner"]',
            '[id*="hianime-banner"]',
            '[class*="hianime-promo"]',
            '[id*="hianime-promo"]',
            '[class*="hianime-sponsor"]',
            '[id*="hianime-sponsor"]',
            '[class*="hianime-social"]',
            '[id*="hianime-social"]',
            '[class*="hianime-newsletter"]',
            '[id*="hianime-newsletter"]',
            '[class*="hianime-subscribe"]',
            '[id*="hianime-subscribe"]',
            # Add specific iframe selectors
            'iframe[src*="ads"]',
            'iframe[src*="banner"]',
            'iframe[src*="popup"]',
            'iframe[src*="overlay"]',
            'iframe[src*="promo"]',
            'iframe[src*="sponsor"]',
            'iframe[src*="analytics"]',
            'iframe[src*="tracker"]',
            'iframe[src*="pixel"]',
            'iframe[src*="counter"]',
            'iframe[src*="stats"]',
            'iframe[src*="metrics"]',
            'iframe[src*="log"]',
            'iframe[src*="track"]'
        }
        
        self.load_filters()

    def load_filters(self):
        """Load filter lists from local files or download them"""
        filter_dir = Path("filters")
        filter_dir.mkdir(exist_ok=True)
        
        self.blocked_domains.update(self.common_ad_domains)
        self.blocked_selectors.update(self.popup_selectors)
        
        default_filters = {
            "easylist.txt": [
                "https://easylist.to/easylist/easylist.txt",
                "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_block.txt",
                "https://secure.fanboy.co.nz/easylist.txt"
            ],
            "easyprivacy.txt": [
                "https://easylist.to/easylist/easyprivacy.txt",
                "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_general.txt",
                "https://secure.fanboy.co.nz/easyprivacy.txt"
            ],
            "annoyances.txt": [
                "https://easylist.to/easylist/fanboy-annoyance.txt",
                "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-social/fanboy_annoyance_general_block.txt",
                "https://secure.fanboy.co.nz/fanboy-annoyance.txt"
            ],
            "fanboy-social.txt": [
                "https://easylist.to/easylist/fanboy-social.txt",
                "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-social/fanboy_social_general.txt",
                "https://secure.fanboy.co.nz/fanboy-social.txt"
            ],
            "anti-adblock.txt": [
                "https://easylist-downloads.adblockplus.org/antiadblockfilters.txt",
                "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/anti-adblock.txt"
            ],
            "ublock-filters.txt": [
                "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/filters.txt",
                "https://filters.adtidy.org/extension/ublock/filters/2_without_easylist.txt"
            ],
            "ublock-badware.txt": [
                "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/badware.txt"
            ],
            "ublock-privacy.txt": [
                "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/privacy.txt"
            ],
            "adguard-base.txt": [
                "https://filters.adtidy.org/extension/ublock/filters/2_without_easylist.txt",
                "https://adguardteam.github.io/AdGuardFilters/BaseFilter/filters.txt"
            ],
            "adguard-mobile.txt": [
                "https://filters.adtidy.org/extension/ublock/filters/11.txt",
                "https://adguardteam.github.io/AdGuardFilters/MobileFilter/filters.txt"
            ],
            "adguard-social.txt": [
                "https://filters.adtidy.org/extension/ublock/filters/4.txt",
                "https://adguardteam.github.io/AdGuardFilters/SocialFilter/filters.txt"
            ],
            "adguard-annoyances.txt": [
                "https://filters.adtidy.org/extension/ublock/filters/14.txt",
                "https://adguardteam.github.io/AdGuardFilters/AnnoyancesFilter/filters.txt"
            ],
            "peter-lowe-list.txt": [
                "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=adblockplus&showintro=0&mimetype=plaintext",
                "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
            ],
            "nocoin-filter.txt": [
                "https://raw.githubusercontent.com/hoshsadiq/adblock-nocoin-list/master/nocoin.txt"
            ],
            "popup-overlay.txt": [
                "https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_3_Popups/filter.txt",
                "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/PopupFilter/sections/general.txt"
            ]
        }
        
        for filename, urls in default_filters.items():
            filter_path = filter_dir / filename
            success = False
            for url in urls:
                try:
                    if not filter_path.exists():
                        print(f"Downloading filter list from {url}")
                        self.download_filter_list(url, filter_path)
                    print(f"Parsing filter list: {filename}")
                    self.parse_filter_list(filter_path)
                    success = True
                    break
                except Exception as e:
                    print(f"Error with {url}: {e}")
                    continue
            if not success:
                print(f"Failed to process filter list {filename} from all sources")
                
    def download_filter_list(self, url, path):
        """Download a filter list from URL with enhanced error handling"""
        try:
            for attempt in range(3):
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    }
                    response = requests.get(url, timeout=20, headers=headers)
                    response.raise_for_status()
                    if len(response.text) < 100:
                        print(f"Warning: Filter from {url} seems too small ({len(response.text)} bytes)")
                        if attempt < 2:
                            continue
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"Successfully downloaded filter list to {path}")
                    return
                except requests.RequestException as e:
                    print(f"Download attempt {attempt+1} failed: {e}")
                    if attempt < 2:
                        print("Retrying download...")
                        continue
            raise Exception(f"All download attempts failed for {url}")
        except Exception as e:
            print(f"Error downloading filter list from {url}: {e}")
            
    def parse_filter_list(self, path):
        """Parse a filter list file with improved pattern extraction"""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('!') or line.startswith('#'):
                        continue
                    if line.startswith('||'):
                        domain = line[2:].split('^')[0].split('$')[0]
                        self.blocked_domains.add(domain)
                    elif line.startswith('|http'):
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(line[1:].split('$')[0]).netloc
                            if domain:
                                self.blocked_domains.add(domain)
                        except:
                            pass
                    elif '##' in line:
                        parts = line.split('##')
                        if len(parts) > 1:
                            selector = parts[1]
                            self.blocked_selectors.add(selector)
                    elif '#@#' in line:
                        parts = line.split('#@#')
                        if len(parts) > 1:
                            selector = parts[1]
                            self.blocked_selectors.add(selector)
                    elif line.startswith('/') and line.endswith('/'):
                        pattern = line[1:-1]
                        if 'ad' in pattern.lower():
                            self.blocked_domains.add(pattern.lower())
                    elif any(keyword in line.lower() for keyword in ['ad', 'banner', 'popup', 'tracking', 'analytics']):
                        self.blocked_domains.add(line.lower())
            print(f"Successfully parsed filter list: {path}")
            print(f"Total loaded: {len(self.blocked_domains)} domains and {len(self.blocked_selectors)} selectors")
        except Exception as e:
            print(f"Error parsing filter list {path}: {e}")
            
    def is_ad_domain(self, url):
        """Check if a domain is in the blocked list with enhanced pattern matching"""
        try:
            if not url:
                return False
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                domain_parts = domain.split('.')
                check_variations = []
                check_variations.append(domain)
                if len(domain_parts) > 2:
                    check_variations.append('.'.join(domain_parts[-2:]))
                for variation in check_variations:
                    if variation in self.blocked_domains:
                        return True
                    for blocked in self.blocked_domains:
                        if blocked in variation:
                            return True
                path = parsed.path.lower()
                query = parsed.query.lower()
                ad_path_patterns = ['/ad', '/ads', '/adv', '/banner', '/popup', '/sponsor', 
                                   '/tracking', '/analytics', '/pixel', '/click', '/track',
                                   '/beacon', '/stat', '/log', '/metrics', '/contador',
                                   '/affiliates', '/promo', '/promotion', '/redirect',
                                   '/creative', 'campaign', '/bid', '/rtb']
                for pattern in ad_path_patterns:
                    if pattern in path:
                        return True
                tracking_params = ['utm_', 'affiliate', 'adid', 'adclid', 'banner', 'click',
                                  'campaign', 'creative', 'placement', 'track', 'source', 'ref']
                for param in tracking_params:
                    if param in query:
                        return True
                return False
            except:
                return any(blocked in url.lower() for blocked in self.blocked_domains)
        except Exception as e:
            print(f"Error checking domain: {e}")
            return True
            
    def block_security_popups(self, html_content):
        """Block security update popups with ultra-aggressive preemptive approach"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Add security-specific meta tags with stricter CSP
            meta_tags = [
                {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'},
                {'http-equiv': 'X-Frame-Options', 'content': 'DENY'},
                {'http-equiv': 'Content-Security-Policy', 'content': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'; object-src 'none'; manifest-src 'none';"},
                {'http-equiv': 'X-Content-Type-Options', 'content': 'nosniff'},
                {'http-equiv': 'X-XSS-Protection', 'content': '1; mode=block'},
                {'http-equiv': 'Referrer-Policy', 'content': 'no-referrer'},
                {'http-equiv': 'Permissions-Policy', 'content': 'notifications=(), popup=()'}
            ]
            
            # Add ultra-aggressive style targeting specific popup patterns
            style = """
                /* Target Chrome notification style popups */
                [style*="chrome-notification"],
                [class*="chrome-notification"],
                [id*="chrome-notification"],
                [class*="browser-notification"],
                [id*="browser-notification"],
                [class*="notification-popup"],
                [id*="notification-popup"],
                [class*="notification-overlay"],
                [id*="notification-overlay"],
                /* Target security warning popups */
                [class*="security-warning"],
                [id*="security-warning"],
                [class*="wifi-warning"],
                [id*="wifi-warning"],
                [class*="public-wifi"],
                [id*="public-wifi"],
                /* Target specific text patterns */
                div:has(> *:contains("Public Wi-Fi")),
                div:has(> *:contains("Chrome Notifications")),
                div:has(> *:contains("CLICK TO LEARN MORE")),
                div:has(> *:contains("NO MORE ANNOYING")),
                /* Target common popup structures */
                [style*="position: fixed"],
                [style*="position:fixed"],
                [style*="z-index: 9"],
                [style*="z-index:9"],
                [style*="background: rgba"],
                [style*="background-color: rgba"],
                [style*="transform"],
                [style*="transition"],
                [style*="animation"],
                [style*="pointer-events"],
                /* Target overlay patterns */
                [class*="overlay"],
                [id*="overlay"],
                [class*="modal"],
                [id*="modal"],
                [class*="popup"],
                [id*="popup"],
                [class*="dialog"],
                [id*="dialog"],
                /* Target specific elements */
                button:contains("Learn More"),
                a:contains("Learn More"),
                button:contains("Click Here"),
                a:contains("Click Here"),
                /* Force hide all fixed position elements */
                body > div[style*="position:"],
                body > div[style*="z-index"],
                body > div:not([class]):not([id]) {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                    clip: rect(0, 0, 0, 0) !important;
                    position: absolute !important;
                    width: 1px !important;
                    height: 1px !important;
                    padding: 0 !important;
                    margin: -1px !important;
                    overflow: hidden !important;
                    border: 0 !important;
                    transform: scale(0) !important;
                    animation: none !important;
                    transition: none !important;
                }

                /* Prevent scrolling locks */
                html, body {
                    overflow: auto !important;
                    position: static !important;
                    pointer-events: auto !important;
                }
            """

            # Add ultra-aggressive script with specific popup targeting
            script = """
                (function() {
                    const targetTexts = [
                        'public wi-fi',
                        'chrome notification',
                        'click to learn more',
                        'no more annoying',
                        'learn more',
                        'click here',
                        'stay safe',
                        'warning',
                        'alert',
                        'danger'
                    ];

                    function blockElement(el) {
                        if (!el || el.tagName === 'BODY' || el.tagName === 'HTML') return false;
                        const text = (el.innerText || '').toLowerCase();
                        const style = window.getComputedStyle(el);
                        
                        // Check for target text patterns
                        if (targetTexts.some(t => text.includes(t))) return true;
                        
                        // Check for fixed positioning
                        if (style.position === 'fixed' || style.position === 'absolute') return true;
                        
                        // Check for high z-index
                        const zIndex = parseInt(style.zIndex) || 0;
                        if (zIndex > 10) return true;
                        
                        // Check for overlay characteristics
                        if (style.backgroundColor && style.backgroundColor.includes('rgba')) return true;
                        
                        // Check for size and position
                        const rect = el.getBoundingClientRect();
                        if (rect.width > window.innerWidth * 0.5 && rect.height > window.innerHeight * 0.3) return true;
                        
                        return false;
                    }

                    function aggressiveRemoval() {
                        const elements = document.querySelectorAll('div, section, aside, article, dialog, button, a');
                        elements.forEach(el => {
                            if (blockElement(el)) {
                                el.remove();
                            }
                        });
                        
                        // Force enable scrolling
                        document.documentElement.style.setProperty('overflow', 'auto', 'important');
                        document.body.style.setProperty('overflow', 'auto', 'important');
                        
                        // Remove inline styles that might create overlays
                        document.body.style.setProperty('position', 'static', 'important');
                        document.documentElement.style.setProperty('position', 'static', 'important');
                    }

                    // Block all popup-related methods
                    window.open = () => null;
                    window.alert = () => null;
                    window.confirm = () => null;
                    window.prompt = () => null;
                    window.print = () => null;
                    window.showModalDialog = () => null;
                    window.showModal = () => null;
                    window.Notification = undefined;
                    window.Notification.requestPermission = () => Promise.resolve('denied');
                    
                    // Block navigation attempts
                    window.onbeforeunload = null;
                    window.history.pushState = () => {};
                    window.history.replaceState = () => {};
                    
                    // Run aggressive removal
                    aggressiveRemoval();
                    setInterval(aggressiveRemoval, 100);
                    
                    // Watch for DOM changes
                    new MutationObserver((mutations) => {
                        aggressiveRemoval();
                    }).observe(document.documentElement, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        characterData: true
                    });
                    
                    // Capture and prevent all events that might trigger popups
                    const events = ['click', 'mousedown', 'mouseup', 'touchstart', 'touchend', 
                                  'focus', 'blur', 'change', 'submit'];
                    events.forEach(event => {
                        document.addEventListener(event, (e) => {
                            if (blockElement(e.target)) {
                                e.stopPropagation();
                                e.preventDefault();
                            }
                        }, true);
                    });
                })();
            """
            
            # Apply all changes to the document
            style_tag = soup.new_tag('style')
            style_tag.string = style
            soup.head.append(style_tag) if soup.head else soup.append(style_tag)
            
            script_tag = soup.new_tag('script')
            script_tag.string = script
            soup.body.append(script_tag) if soup.body else soup.append(script_tag)
            
            # Add meta tags
            for meta in meta_tags:
                meta_tag = soup.new_tag('meta')
                for key, value in meta.items():
                    meta_tag[key] = value
                if soup.head:
                    soup.head.insert(0, meta_tag)
                else:
                    soup.insert(0, meta_tag)
            
            # Pre-emptively remove potential popup elements
            for element in soup.find_all(['div', 'section', 'aside', 'article', 'dialog', 'button', 'a']):
                if element.name in ['html', 'body', 'head']:
                    continue
                    
                text = element.get_text().lower()
                if any(keyword in text for keyword in [
                    'public wi-fi', 'chrome notification', 'click to learn more',
                    'no more annoying', 'learn more', 'click here', 'stay safe',
                    'warning', 'alert', 'danger'
                ]):
                    element.decompose()
                    continue
                    
                style = element.get('style', '')
                if any(prop in style.lower() for prop in [
                    'position: fixed', 'position: absolute', 'z-index',
                    'background: rgba', 'background-color: rgba',
                    'transform', 'transition', 'animation'
                ]):
                    element.decompose()
                    continue
            
            return str(soup)
        except Exception as e:
            print(f"Error blocking security popups: {e}")
            return html_content
            
    def block_ads(self, html_content):
        """Remove ad elements from HTML content with ultra-aggressive preemptive approach"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Add ultra-aggressive preemptive style
            style_tag = soup.new_tag('style')
            style_tag.string = """
                /* Block all popups and overlays */
                [class*="popup"], [id*="popup"],
                [class*="modal"], [id*="modal"],
                [class*="overlay"], [id*="overlay"],
                [class*="dialog"], [id*="dialog"],
                [class*="alert"], [id*="alert"],
                [class*="notification"], [id*="notification"],
                [class*="banner"], [id*="banner"],
                [class*="float"], [id*="float"],
                [class*="sticky"], [id*="sticky"],
                [class*="fixed"], [id*="fixed"],
                [class*="ad"], [id*="ad"],
                [class*="promo"], [id*="promo"],
                [class*="sponsor"], [id*="sponsor"],
                [class*="social"], [id*="social"],
                [class*="newsletter"], [id*="newsletter"],
                [class*="subscribe"], [id*="subscribe"],
                iframe:not([src*="about:blank"]),
                div[style*="position: fixed"],
                div[style*="position:fixed"],
                div[style*="z-index"],
                div[style*="display: flex"],
                div[style*="display: grid"],
                div[style*="justify-content: center"],
                div[style*="align-items: center"],
                div[style*="margin: auto"],
                button, a,
                [class*="mcafee"], [id*="mcafee"],
                [class*="scan"], [id*="scan"],
                [class*="virus"], [id*="virus"],
                [class*="trojan"], [id*="trojan"],
                [class*="hianime"], [id*="hianime"],
                [class*="push-notifications"], [id*="push-notifications"],
                [class*="chrome-mobile"], [id*="chrome-mobile"],
                [class*="learn-more"], [id*="learn-more"],
                /* Specific rules for hianime.tv */
                [class*="hianime-ad"], [id*="hianime-ad"],
                [class*="hianime-popup"], [id*="hianime-popup"],
                [class*="hianime-overlay"], [id*="hianime-overlay"],
                [class*="hianime-modal"], [id*="hianime-modal"],
                [class*="hianime-float"], [id*="hianime-float"],
                [class*="hianime-sticky"], [id*="hianime-sticky"],
                [class*="hianime-banner"], [id*="hianime-banner"],
                [class*="hianime-promo"], [id*="hianime-promo"],
                [class*="hianime-sponsor"], [id*="hianime-sponsor"],
                [class*="hianime-social"], [id*="hianime-social"],
                [class*="hianime-newsletter"], [id*="hianime-newsletter"],
                [class*="hianime-subscribe"], [id*="hianime-subscribe"],
                /* Block all iframes */
                iframe[src*="ads"],
                iframe[src*="banner"],
                iframe[src*="popup"],
                iframe[src*="overlay"],
                iframe[src*="promo"],
                iframe[src*="sponsor"],
                iframe[src*="analytics"],
                iframe[src*="tracker"],
                iframe[src*="pixel"],
                iframe[src*="counter"],
                iframe[src*="stats"],
                iframe[src*="metrics"],
                iframe[src*="log"],
                iframe[src*="track"] {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                    clip: rect(0, 0, 0, 0) !important;
                    position: absolute !important;
                    width: 1px !important;
                    height: 1px !important;
                    padding: 0 !important;
                    margin: -1px !important;
                    overflow: hidden !important;
                    border: 0 !important;
                }

                /* Force enable scrolling */
                html, body {
                    overflow: auto !important;
                    position: static !important;
                    pointer-events: auto !important;
                }
            """
            soup.head.append(style_tag) if soup.head else soup.append(style_tag)
            
            # Add ultra-aggressive preemptive script
            script_tag = soup.new_tag('script')
            script_tag.string = """
                (function() {
                    // Block all window methods that could create popups
                    window.open = function() { return null; };
                    window.alert = function() { return null; };
                    window.confirm = function() { return null; };
                    window.prompt = function() { return null; };
                    window.print = function() { return null; };
                    window.showModalDialog = function() { return null; };
                    window.showModal = function() { return null; };
                    window.Notification = undefined;
                    window.Notification.requestPermission = () => Promise.resolve('denied');
                    
                    // Block navigation attempts
                    window.onbeforeunload = null;
                    window.history.pushState = () => {};
                    window.history.replaceState = () => {};
                    
                    // Aggressive element removal
                    function removeAds() {
                        const selectors = [
                            '[class*="popup"]', '[id*="popup"]',
                            '[class*="modal"]', '[id*="modal"]',
                            '[class*="overlay"]', '[id*="overlay"]',
                            '[class*="dialog"]', '[id*="dialog"]',
                            '[class*="alert"]', '[id*="alert"]',
                            '[class*="notification"]', '[id*="notification"]',
                            '[class*="banner"]', '[id*="banner"]',
                            '[class*="float"]', '[id*="float"]',
                            '[class*="sticky"]', '[id*="sticky"]',
                            '[class*="fixed"]', '[id*="fixed"]',
                            '[class*="ad"]', '[id*="ad"]',
                            '[class*="promo"]', '[id*="promo"]',
                            '[class*="sponsor"]', '[id*="sponsor"]',
                            '[class*="social"]', '[id*="social"]',
                            '[class*="newsletter"]', '[id*="newsletter"]',
                            '[class*="subscribe"]', '[id*="subscribe"]',
                            'iframe:not([src*="about:blank"])',
                            'div[style*="position: fixed"]',
                            'div[style*="position:fixed"]',
                            'div[style*="z-index"]',
                            // Specific selectors for hianime.tv
                            '[class*="hianime-ad"]', '[id*="hianime-ad"]',
                            '[class*="hianime-popup"]', '[id*="hianime-popup"]',
                            '[class*="hianime-overlay"]', '[id*="hianime-overlay"]',
                            '[class*="hianime-modal"]', '[id*="hianime-modal"]',
                            '[class*="hianime-float"]', '[id*="hianime-float"]',
                            '[class*="hianime-sticky"]', '[id*="hianime-sticky"]',
                            '[class*="hianime-banner"]', '[id*="hianime-banner"]',
                            '[class*="hianime-promo"]', '[id*="hianime-promo"]',
                            '[class*="hianime-sponsor"]', '[id*="hianime-sponsor"]',
                            '[class*="hianime-social"]', '[id*="hianime-social"]',
                            '[class*="hianime-newsletter"]', '[id*="hianime-newsletter"]',
                            '[class*="hianime-subscribe"]', '[id*="hianime-subscribe"]'
                        ];
                        
                        selectors.forEach(selector => {
                            document.querySelectorAll(selector).forEach(element => {
                                element.remove();
                            });
                        });
                        
                        // Remove elements with fixed position or high z-index
                        document.querySelectorAll('*').forEach(element => {
                            const style = window.getComputedStyle(element);
                            if (style.position === 'fixed' || 
                                style.position === 'sticky' ||
                                parseInt(style.zIndex) > 100) {
                                element.remove();
                            }
                        });
                        
                        // Remove iframes
                        document.querySelectorAll('iframe').forEach(iframe => {
                            const src = iframe.src.toLowerCase();
                            if (src.includes('ads') || 
                                src.includes('banner') || 
                                src.includes('popup') || 
                                src.includes('overlay') || 
                                src.includes('promo') || 
                                src.includes('sponsor') || 
                                src.includes('analytics') || 
                                src.includes('tracker') || 
                                src.includes('pixel') || 
                                src.includes('counter') || 
                                src.includes('stats') || 
                                src.includes('metrics') || 
                                src.includes('log') || 
                                src.includes('track')) {
                                iframe.remove();
                            }
                        });
                    }
                    
                    // Run immediately and set up observers
                    removeAds();
                    
                    // Create a mutation observer to remove new ads
                    new MutationObserver(mutations => {
                        removeAds();
                    }).observe(document.documentElement, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        characterData: true
                    });
                    
                    // Run periodically to catch dynamically added content
                    setInterval(removeAds, 100);
                    
                    // Force scrollable
                    document.documentElement.style.setProperty('overflow', 'auto', 'important');
                    document.body.style.setProperty('overflow', 'auto', 'important');
                })();
            """
            soup.body.append(script_tag) if soup.body else soup.append(script_tag)
            
            # Pre-emptively remove potential ad elements
            for element in soup.find_all(['div', 'iframe', 'script', 'style', 'link']):
                if element.name in ['html', 'body', 'head']:
                    continue
                    
                # Check attributes for ad-related content
                for attr in element.attrs:
                    attr_value = str(element[attr]).lower()
                    if any(keyword in attr_value for keyword in [
                        'ad', 'popup', 'overlay', 'modal', 'banner', 'promo',
                        'sponsor', 'social', 'newsletter', 'subscribe', 'notification',
                        'alert', 'fixed', 'sticky', 'float', 'hianime'
                    ]):
                        element.decompose()
                        break
                
                # Check for fixed positioning
                style = element.get('style', '')
                if any(prop in style.lower() for prop in [
                    'position: fixed', 'position:fixed', 'position: absolute',
                    'position:absolute', 'z-index', 'display: flex', 'display:flex'
                ]):
                    element.decompose()
                    continue
            
            return str(soup)
        except Exception as e:
            print(f"Error blocking ads: {e}")
            return html_content