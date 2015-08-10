from datetime import timedelta
import re

import arrow
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vText
import requests


def scrape(url):
    return BeautifulSoup((requests.get(url).text), 'html.parser')


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
        time = event_time(description)
        return [
            link.string,
            description,
            link.get('href'),
            (event_date(block)
             .replace(hour=time.hour, minute=time.minute, tzinfo=time.tzinfo)
             .to('UTC'))]

    def absolutify(self, url):
        return self.root + url


def event_time(event_details):
    time = re.findall(
        'kl\.? ([0-9]{2}[.:]?[0-9]{2})', event_details, re.MULTILINE)
    if not time:
        time = re.findall(
            '[^0-9]([0-9]{2}[.:]?[0-9]{2})[^0-9]', event_details,
            re.MULTILINE)
    if not time:
        time = ['00:00']
    time = time[0].replace('.', '').replace(':', '')
    return arrow.get(time, 'HHmm').replace(tzinfo='Europe/Oslo')


def event_date(event_summary):
    return arrow.get(
        ''.join(re.findall(
            '[0-9]{2}\.[0-9]{2}\.[0-9]{4}',
            event_summary.select(
                '.activity_list_loc_dates b')[0].string.strip())),
        'DD.MM.YYYY')


def icalize(events):
    cal = Calendar()
    cal.add('prodid', '-//Yaypython//python.org//')
    cal.add('version', '2.0')
    for header, description, url, date in events:
        ev = Event()
        ev.add('summary', vText(header))
        ev.add('description', vText(description))
        ev.add('location', url)
        ev.add('dtstart', date.datetime)
        ev.add('dtend', date.replace(seconds=60 * 60).datetime)
        ev.add('dtstamp', date.datetime)
        cal.add_component(ev)
    return cal.to_ical()


def main():
    scraper = BTScraper()
    print(
        icalize(
            [header, description, scraper.absolutify(url), date]
            for header, description, url, date in scraper.get_events(
                scraper.get_overview())))
