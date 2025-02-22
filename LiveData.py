import asyncio
import json
from typing import List
import httpx
from parsel import Selector
from typing_extensions import TypedDict

## PROMPT SCRAPING SINGLE PROPERTY DATA FROM URL (LIVE DATA)

# First, we sneed to establish a persisten HTTPX session 
# with browser-like headers to avoid instant blocking
BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US;en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
}
session = httpx.AsyncClient(headers=BASE_HEADERS)

# type hints fo expected results - property listing has a lot of data!
class PropertyResult(TypedDict):
    property_id: str
    listing_id: str
    href: str
    status: str
    list_price: int
    list_date: str
    ...  # and much more!


def parse_property(response: httpx.Response) -> PropertyResult:
    """parse Realtor.com property page"""
    # load response's HTML tree for parsing:
    selector = Selector(text=response.text)
    # find <script id="__NEXT_DATA__"> node and select it's text:
    data = selector.css("script#__NEXT_DATA__::text").get()
    if not data:
        print(f"page {response.url} is not a property listing page")
        return
    # load JSON as python dictionary and select property value:
    data = json.loads(data)
    return data["props"]["pageProps"]["initialReduxState"]


async def scrape_properties(urls: List[str]) -> List[PropertyResult]:
    """Scrape Realtor.com properties"""
    properties = []
    to_scrape = [session.get(url) for url in urls]
    # tip: asyncio.as_completed allows concurrent scraping - super fast!
    for response in asyncio.as_completed(to_scrape):
        response = await response
        if response.status_code != 200:
            print(f"|can't scrape property: {response.url}")
            continue
        properties.append(parse_property(response))
    return properties

# some realtor.com property urls
urls = [
        "https://www.realtor.com/realestateandhomes-detail/12355-Attlee-Dr_Houston_TX_77077_M70330-35605"
    ]
results = await scrape_properties(urls)
print(json.dumps(results, indent=2))
