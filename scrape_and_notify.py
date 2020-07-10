import urllib.request
import re
import json
import smtplib, ssl
from config import *
from pathlib import Path

# Create a secure SSL context
context = ssl.create_default_context()


def ids_from_immoscout_listings_source(search_url):
    mybytes = search_url.read()

    mystr = mybytes.decode("utf8")
    search_url.close()
    pattern = r'data-go-to-expose-id=\"[0-9]+\"'  # data-go-to-expose-id="119962085"
    matches = re.findall(pattern, mystr)
    ids = [match.split("\"")[1] for match in matches]
    return ids

listings_file = Path(__file__).parent / 'listings.json'

with open(listings_file) as file:
    listings = json.load(file)


def find_new_listings(ids, listings, search_identifier):
    new_listings = {}
    if listings.get(search_identifier) is None:
        listings[search_identifier] = {}
    for id in ids:
        if id not in listings[search_identifier].keys():
            new_listings[id] = f"https://www.immobilienscout24.de/expose/{id}"
    return new_listings


for config in (lovis_cfg, shana_cfg):
    sender_email = config['sender_email']
    receiver_email = config['receiver_email']
    password = config['password']
    for search_name, url in config['searches'].items():
        search_url = urllib.request.urlopen(url)
        ids = ids_from_immoscout_listings_source(search_url)
        new_listings = find_new_listings(ids, listings, search_name)
        if len(new_listings) == 0:
            continue
        listings[search_name] ={**listings[search_name], **new_listings}
        subject = ""
        mail_text = ""
        subject += f'{len(new_listings.keys())} neue {search_name}! '
        mail_text += '<p>Wie waers damit? </p>'
        mail_text += "".join([f'<a href=\"{link}\">Wohnung {id}</a><br />\n' for id, link in new_listings.items()])

        message = f"""From: Me <{sender_email}>
To: Myself <{receiver_email}>
MIME-Version: 1.0
Content-type: text/html
Subject: {subject}
    
{mail_text}
"""

        with open(listings_file, 'w') as file:
            json.dump(listings, file)

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
