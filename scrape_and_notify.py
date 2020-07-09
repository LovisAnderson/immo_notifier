import urllib.request
import re
import json
import smtplib, ssl
from login import *
from pathlib import Path
import sys

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


search_identifier = 'buy'
search_url = urllib.request.urlopen("https://www.immobilienscout24.de/Suche/shape/wohnung-kaufen?rented=false&shape=bXtyX0l3ZGdwQWprR3F6Q3hoQHFfQnBDdWRBZVVtYEF8QmFwRGVZdUhhbEBsRW1abnZEfXFAakRxUmJ8QG9WbGJAa35AZVBfXW1iQGNIdklnU2NBdWxAeWdAZVNmQmlRdHVAcEN2ZkB6VWxjQGxJfmpA&price=-240000.0&constructionyear=-1940&floor=1-&enteredFrom=saved_search")
ids = ids_from_immoscout_listings_source(search_url)
new_listings_buy = find_new_listings(ids, listings, search_identifier)
listings[search_identifier] = {**listings[search_identifier], **new_listings_buy}

search_identifier = 'buy_no_courtage'
search_url = urllib.request.urlopen("https://www.immobilienscout24.de/Suche/shape/provisionsfreie-wohnung-kaufen?rented=false&shape=fWxyX0l3aGdwQWxnQH1adH1Aekt0X0BlX0BiSGtiQHZbfWlAeGhAfUx2SGlScnRBaEN8YEBfTXZdYWpBY1ltYEFzUnVIZ1NtY0BlV2FOcUNze0NtfEB1ZkBnU3RXc1BwekNtaUB_XGlvQHRIZ3NAamJAd0pnQ1R9THdMZUFnUWBOYXtAbEVlRHdJP2NBYVtxZEB7U2BAaVF6ZkFoQGZgQHhIblRmcUB8akBqWnZkQX5PbH1B&price=-250000.0&livingspace=40.0-&constructionyear=-1945&enteredFrom=result_list#/")
ids = ids_from_immoscout_listings_source(search_url)
new_listings_buy_2 = find_new_listings(ids, listings, search_identifier)
listings[search_identifier] = {**listings[search_identifier], **new_listings_buy_2}

search_identifier = 'rent'
search_url = urllib.request.urlopen("https://www.immobilienscout24.de/Suche/shape/wohnung-mieten?shape=dXdxX0l9Z2VwQXBjQGNecENrcEBjSGl_QGhgQG9hQXJwQHRmQGhxQ2BAelV9eEBuVmV1Q3V9QGNtQGlAd2RBY1l1ZkA-b35Bd1ttRXNjQXxkQml_QHBfQmFoRGJsQGVVYm5AfGBCaHtHZkB8eEA.&numberofrooms=1.5-&price=-700.0&livingspace=40.0-&enteredFrom=saved_search")
ids = ids_from_immoscout_listings_source(search_url)
new_listings_rent = find_new_listings(ids, listings, search_identifier)
listings[search_identifier] = {**listings[search_identifier], **new_listings_rent}



if len(new_listings_buy.keys()) == 0 and len(new_listings_rent.keys()) == 0 and len(new_listings_buy_2.keys()):
    sys.exit()

subject = ""
mail_text = ""

if len(new_listings_buy.keys()) > 0:
    subject += f'{len(new_listings_buy.keys())} neue Kaufanzeigen! '
    mail_text += '<p>Wohnungen zu kaufen: </p>'
    mail_text += "".join([f'<a href=\"{link}\">Wohnung {id}</a><br />\n' for id, link in new_listings_buy.items()])


if len(new_listings_buy_2.keys()) > 0:
    subject += f'{len(new_listings_buy.keys())} neue provisionsfreie Kaufanzeigen! '
    mail_text += '<p>Wohnungen zu kaufen (provisionsfrei): </p>'
    mail_text += "".join([f'<a href=\"{link}\">Wohnung {id}</a><br />\n' for id, link in new_listings_buy_2.items()])


if len(new_listings_rent.keys()) > 0:
    mail_text += '<p>Wohnungen zu mieten:</p>'
    mail_text += "".join([f'<a href=\"{link}\">Wohnung {id}</a><br />\n' for id, link in new_listings_rent.items()])

    subject += f'{len(new_listings_rent.keys())} neue Mietanzeigen! '


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
