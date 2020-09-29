import smtplib, ssl
from config import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from scraper import get_scraper


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
        scraper = get_scraper(url)(url, search_name)
        new_listings = scraper.new_listings()
        if len(new_listings) == 0:
            continue
        scraper.listings = new_listings
        scraper.save_listings()
        mailer = Mailer(sender_email, password)
        mailer.mail_from_properties(new_listings, search_name, receiver_email)
        mailer.send_mail(receiver_email)






