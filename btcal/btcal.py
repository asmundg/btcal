from datetime import timedelta
import re

from bs4 import BeautifulSoup
from dateutil import parser as dtparser
from icalendar import Calendar, Event, vText
import pytz
import requests


def scrape(url):
    return BeautifulSoup((requests.get(url).text))


class BTScraper(object):
    root = 'http://troms.turistforeningen.no'

    def get_overview(self):
        return scrape(self.root + '/activity.php?ac_owner=183')

    def get_events(self, soup):
        return [
            self.get_event(block)
            for block in soup.select('.activity_list_item')]

    def get_event(self, block):
        link = block.select('.activity_list_header a')[0]
        event = scrape(self.root + link.get('href'))
        description = ' '.join(
            (event.select('.activity_trip_view_ingress')[0].get_text(),
             event.select('.activity_trip_view_content')[0].get_text()))
        time = self.find_time(description)
        return [
            link.string,
            description,
            link.get('href'),
            (dtparser.parse(
                block.select(
                    '.activity_list_loc_dates b')[0].string.strip() + time,
                dayfirst=True)
             .replace(tzinfo=pytz.timezone('Europe/Oslo'))
             .astimezone(pytz.utc))]

    def absolutify(self, url):
        return self.root + url

    def find_time(self, description):
        time = re.findall(
            'kl\.? ([0-9]{2}[.:]?[0-9]{2})', description, re.MULTILINE)
        if not time:
            time = re.findall(
                '([0-9]{2}[.:]?[0-9]{2})', description, re.MULTILINE)
        if not time:
            time = ['00:00']
        time = time[0].replace('.', '').replace(':', '')
        return time


def icalize(events):
    cal = Calendar()
    cal.add('prodid', '-//Yaypython//python.org//')
    cal.add('version', '2.0')
    for header, description, url, date in events:
        ev = Event()
        ev.add('summary', vText(header))
        ev.add('description', vText(description))
        ev.add('location', url)
        ev.add('dtstart', date)
        ev.add('dtend', date + timedelta(seconds=60 * 60))
        ev.add('dtstamp', date)
        cal.add_component(ev)
    return cal.to_ical()


scraper = BTScraper()
print(
    icalize(
        [header, description, scraper.absolutify(url), date]
        for header, description, url, date in scraper.get_events(
            scraper.get_overview())))
