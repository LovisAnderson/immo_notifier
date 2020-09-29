import urllib.request
import re
import json
import smtplib, ssl
from config import *
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from contextlib import closing

from selenium.webdriver import Firefox
from abc import ABC, abstractmethod


class Scraper(ABC):
    def __init__(self, url, identifier, engine='selenium', listings_file='listings.json'):
        self.url = url
        self.identifier = identifier
        self.engine = engine
        self._html = None
        self.listings_file = Path(__file__).parent /  listings_file
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


class Mailer:
    def __init__(self, sender_mail, password):
        self.sender_mail = sender_mail
        self.password = password
        self.message = None

    def send_mail(self, receiver_email):
        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(self.sender_mail, self.password)
            server.sendmail(self.sender_mail, receiver_email, self.message.as_string())

    def mail_from_properties(self, new_listings, search_name, receiver_email):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'{len(new_listings.keys())} neue {search_name}! '
        msg['From'] = self.sender_mail
        msg['To'] = receiver_email

        mail_html = '<p>Wie waers damit? </p>'
        mail_html += "".join([f'<a href=\"{link}\">Wohnung {id}</a><br />\n' for id, link in new_listings.items()])

        mail_text = 'Wie waers damit?\n'
        mail_text += "".join([f'{link}>\n' for id, link in new_listings.items()])
        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(mail_text, 'plain')
        part2 = MIMEText(mail_html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)
        self.message = msg


def find_new_listings(ids, listings, search_identifier):
    new_listings = {}
    if listings.get(search_identifier) is None:
        listings[search_identifier] = {}
    for id in ids:
        if id not in listings[search_identifier].keys():
            new_listings[id] = f"https://www.immobilienscout24.de/expose/{id}"
    return new_listings


for config in (lovis_cfg,
               shana_cfg):
    sender_email = config['sender_email']
    receiver_email = config['receiver_email']
    password = config['password']

    for search_name, url in config['searches'].items():
        scraper = ImmoScout(url, search_name)
        new_listings = scraper.new_listings()
        if len(new_listings) == 0:
            continue
        scraper.listings = new_listings
        scraper.save_listings()
        mailer = Mailer(sender_email, password)
        mailer.mail_from_properties(new_listings, search_name, receiver_email)
        mailer.send_mail(receiver_email)






