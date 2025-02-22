import json
from typing import List
import requests
from markdownify import markdownify
import re
from parsel import Selector
from typing_extensions import TypedDict

# TEST 2
## PROMPT SCRAPING SINGLE PROPERTY DATA FROM URL (LIVE DATA)

# First, we sneed to establish a persisten HTTPX session 
# with browser-like headers to avoid instant blocking
BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US;en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
}

# Replace async httpx client with regular requests session
session = requests.Session()
session.headers.update(BASE_HEADERS)

# type hints fo expected results - property listing has a lot of data!
class PropertyResult(TypedDict):
    property_id: str
    listing_id: str
    href: str
    status: str
    list_price: int
    list_date: str
    ...  # and much more!


def parse_property(response: requests.Response) -> PropertyResult:
    """parse Realtor.com property page"""
    # load response's HTML tree for parsing:
    # print(response.text)
        # Convert the HTML content to Markdown
    # markdown_content = markdownify(response.text).strip()

    # # Remove multiple line breaks
    # markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

    selector = Selector(text=response.text)
    # find <script id="__NEXT_DATA__"> node and select it's text:
    data = selector.css("script#__NEXT_DATA__::text").get()
    if not data:
        print(f"page {response.url} is not a property listing page")
        return
    # load JSON as python dictionary and select property value:
    data = json.loads(data)
    return data["props"]["pageProps"]["initialReduxState"]


def scrape_properties(urls: List[str]) -> List[PropertyResult]:
    """Scrape Realtor.com properties"""
    properties = []
    for url in urls:
        response = session.get(url)
        if response.status_code != 200:
            print(f"|can't scrape property: {response.url}")
            continue
        properties.append(parse_property(response))
    return properties

# some realtor.com property urls
urls = [
    "https://www.realtor.com/realestateandhomes-detail/12355-Attlee-Dr_Houston_TX_77077_M70330-35605"
]
results = scrape_properties(urls)
print(json.dumps(results, indent=2))
