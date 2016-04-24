import logging
import re
import sys
from urllib import parse

import arrow
from bs4 import BeautifulSoup
import dateutil
from icalendar import Calendar, Event, vText
import requests


ROOT = 'https://troms.dnt.no/barnas-turlag/'
MONTHS = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli',
          'august', 'september', 'oktober', 'november', 'desember']
http = requests.session()


def scrape(url):
    return BeautifulSoup((http.get(url).text), 'html.parser')


def bstext(soup, selector):
    return ''.join(el.get_text().strip() for el in soup.select(selector))


def overview():
    return scrape(ROOT)


def event_urls(soup):
    return [
        parse.urljoin(ROOT, a.get('href'))
        for a in soup.select('a.aktivitet-item')]


def event(url):
    """
    Returns (title, description, url, start, end)
    """
    event = scrape(url)
    try:
        title = bstext(event, '.title')
        description = bstext(event, '.description')
        start, end = event_datetime(
            bstext(event, '.content dd:nth-of-type(1)'))
        return [title, description, url, start, end]
    except:
        logging.error('Failed to parse: {}'.format(event))


def event_datetime(text):
    # 25. mai kl. 08:00( - 10:00)
    groups = re.match(
        '\s*([0-9]+)\. ([a-z]+)\s+kl\. ([0-9]+:[0-9]+)(?:\s*-\s*([0-9]+:[0-9]+))?',
        text, re.MULTILINE).groups()
    day, month_name, start, end = groups
    if end is None:
        end = start

    month = MONTHS.index(month_name) + 1
    default = arrow.get()

    # Next year
    if month < default.month:
        default = default.replace(year=default.year + 1)

    return [arrow
            .get('{}{}{}'.format(day.rjust(2, '0'),
                                 str(month).rjust(2, '0'), time),
                 'DDMMHH:mm')
            .replace(year=default.year,
                     tzinfo=dateutil.tz.gettz('Europe/Oslo'))
            .to('UTC')
            for time in (start, end)]


def icalize(events):
    cal = Calendar()
    now = arrow.get()
    cal.add('prodid', '-//Yaypython//python.org//')
    cal.add('version', '2.0')
    for header, description, url, start, end in events:
        ev = Event()
        ev.add('summary', vText(header))
        ev.add('description', vText(description))
        ev.add('location', url)
        ev.add('dtstart', start.datetime)
        ev.add('dtend', end.datetime)
        ev.add('last-modified', now.datetime)
        cal.add_component(ev)
    return cal.to_ical().decode('utf-8')


def main():
    logging.basicConfig()
    sys.stdout.write(
        icalize((ev for ev in (
            event(url) for url in event_urls(overview())) if ev is not None)))
