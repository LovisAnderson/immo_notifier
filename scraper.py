import json
import re
import urllib.request
from abc import ABC, abstractmethod
from contextlib import closing
from pathlib import Path
from selenium.webdriver import Firefox


def get_scraper(url):
    if 'immobilienscout24' in url:
        return ImmoScout
    elif 'gewobag' in url:
        return Gewobag
    elif 'degewo' in url:
        return Degewo
    elif 'gesobau' in url:
        return Gesobau
    elif 'immowelt' in url:
        return ImmoWelt
    else:
        raise NotImplementedError(f'No scraper implemented for url {url}!')


class Scraper(ABC):
    def __init__(self, url, identifier, engine='selenium', listings_file='listings.json'):
        self.url = url
        self.identifier = identifier
        self.engine = engine
        self._html = None
        self.listings_file = Path(__file__).parent / listings_file
        self._listings = None

    @property
    def html(self):
        if self._html is None:
            self._html = self.get_html()
        return self._html

    @property
    def listings(self):
        if self._listings is None:
            with open(self.listings_file) as file:
                all_listings = json.load(file)
                listings = all_listings.get(self.identifier, {})
            self._listings = listings
        return self._listings

    @listings.setter
    def listings(self, listings):
        self._listings = {**self.listings, **listings}

    def get_html(self):
        if self.engine == 'selenium':
            with closing(Firefox()) as browser:
                browser.get(self.url)
                html = browser.page_source
        elif self.engine == 'urllib':
            search_url = urllib.request.urlopen(self.url)
            html = search_url.read()

            html = html.decode("utf8")
            search_url.close()
        return html

    @abstractmethod
    def listings_from_html(self):
        pass

    def new_listings(self):
        new_listings = {}
        for listing_id, url in self.listings_from_html().items():
            if listing_id not in self.listings:
                new_listings[listing_id] = url
        return new_listings

    def save_listings(self):
        with open(self.listings_file, 'r') as file:
            all_listings = json.load(file)
        with open(self.listings_file, 'w') as file:
            all_listings[self.identifier] = self.listings
            json.dump(all_listings, file, indent=4, sort_keys=True)


class ImmoScout(Scraper):
    def __init__(self, url, identifier, engine='selenium', listings_file='listings.json'):
        super(ImmoScout, self).__init__(url, identifier, engine, listings_file)

    def listings_from_html(self):
        pattern = r'data-go-to-expose-id=\"[0-9]+\"'  # data-go-to-expose-id="119962085"
        matches = re.findall(pattern, self.html)
        ids = [match.split("\"")[1] for match in matches]
        return {ID: f"https://www.immobilienscout24.de/expose/{ID}" for ID in ids}


class Gewobag(Scraper):
    def __init__(self, url, identifier, engine='urllib', listings_file='listings.json'):
        super(Gewobag, self).__init__(url, identifier, engine, listings_file)

    def listings_from_html(self):
        pattern = r"""<a class="angebot-header" href=".*">"""
        html = self.html.split('<section class="overview-list small-layout aktuelle-mietangebote">')[0]
        matches = re.findall(pattern, html)
        urls = [match.split("\"")[-2].replace("\'", "") for match in matches]
        ids = [url.split('/')[-2] for url in urls]
        return {ID: urls[i] for i, ID in enumerate(ids)}


class Degewo(Scraper):
    def __init__(self, url, identifier, engine='urllib', listings_file='listings.json'):
        super(Degewo, self).__init__(url, identifier, engine, listings_file)

    def listings_from_html(self):
        pattern = r"""href="/de/properties/W.*">"""

        url_stem = 'https://immosuche.degewo.de/de/properties/'
        matches = re.findall(pattern, self.html)
        url_relatives = [match.split('"')[1].split('/')[-1] for match in matches]
        urls = [url_stem + url for url in url_relatives]
        ids = [url.split('/')[-1] for url in url_relatives]
        return {ID: urls[i] for i, ID in enumerate(ids)}


class Gesobau(Scraper):
    def __init__(self, url, identifier, engine='urllib', listings_file='listings.json'):
        super(Gesobau, self).__init__(url, identifier, engine, listings_file)

    def listings_from_html(self):
        pattern = r"""<a href="/wohnung/.*.html">"""

        url_stem = 'https://www.gesobau.de'
        matches = re.findall(pattern, self.html)
        url_relatives = [match.split('\"')[1] for match in matches]
        urls = [url_stem + url for url in url_relatives]
        ids = [match.split('/')[2][:-7] for match in matches]
        return {ID: urls[i] for i, ID in enumerate(ids)}


class ImmoWelt(Scraper):
    def __init__(self, url, identifier, engine='urllib', listings_file='listings.json'):
        super(ImmoWelt, self).__init__(url, identifier, engine, listings_file)

    def listings_from_html(self):

        pattern = r"""<a href="/expose/.*"></a>"""

        url_stem = 'https://www.immowelt.de'
        matches = re.findall(pattern, self.html)
        url_relatives = [match.split('\"')[1] for match in matches]
        urls = [url_stem + url for url in url_relatives]
        ids = [url.split('/')[2] for url in url_relatives]
        return {ID: urls[i] for i, ID in enumerate(ids)}