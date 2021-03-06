"""Scrapes Wyeast's site for their yeast specs.

Writes the data to brewery/migrations/yeast_ingredients_wyeast.tsv.
"""

import logging

import urllib.request
import urllib.parse
from bs4 import BeautifulSoup


LOGGER = logging.getLogger(__name__)

WYEAST_ROOT = r'http://www.wyeastlab.com'
WYEAST_YEASTS_PAGE = r'http://www.wyeastlab.com/beer-strains'
WYEAST_YEAST_FILE = 'brewery/migrations/yeast_ingredients_wyeast.tsv'


def get_wyeast_yeasts():
    yeasts_page = urllib.request.urlopen(WYEAST_YEASTS_PAGE)
    yeasts_soup = BeautifulSoup(yeasts_page, 'html.parser')
    yeast_links = yeasts_soup.find_all('div', class_='node-type-yeast-strain')
    with open(WYEAST_YEAST_FILE, 'wb') as yeast_file:
        yeast_file.write('# Generated by scraping {}\n'
                             .format(WYEAST_YEASTS_PAGE)
                             .encode('utf-8'))
        yeast_file.write('# name\tlow_attenuation\thigh_attenuation\t'
                         'low_temperature\thigh_temperature\tabv\n'
                             .encode('utf-8'))
        for i, yeast_link in enumerate(yeast_links):
            if i % 10 == 0:
                LOGGER.info("Yeast retrieval progress: %d/%d.", i,
                            len(yeast_links))
            yeast_href = yeast_link.a['href']
            yeast_data = get_wyeast_yeast(yeast_href)
            yeast_line = '{}\n'.format('\t'.join(yeast_data))
            yeast_file.write(yeast_line.encode('utf-8'))


def parse_unicode_url(iri):
    iri_parts = list(urllib.parse.urlsplit(iri))
    iri_parts[2] = urllib.parse.quote(iri_parts[2])
    uri = urllib.parse.urlunsplit(iri_parts)
    return uri


def get_wyeast_yeast(yeast_href):
    """Gets the yeast information from Wyeast site.

    Args:
        yeast_href: URL relative to Wyeast root to get yeast data from.

    Returns:
        Tuple with (name, low_attenuation, high_attenuation, low_temperature,
            high_temperature, abv). Attenuations and abv are in per-unit,
            temperatures are in degF.
    """
    yeast_url = parse_unicode_url("{}{}".format(WYEAST_ROOT, yeast_href))
    LOGGER.debug("Getting yeast info at url %s.", yeast_url)
    yeast_page = urllib.request.urlopen(yeast_url)
    yeast_soup = BeautifulSoup(yeast_page, 'html.parser')

    strain_elem = yeast_soup.find('div', class_='field--name-field-strain-code')
    strain = strain_elem.text

    description_elem = yeast_soup.find(
        'div', class_='field--name-field-admin-title')
    description = description_elem.text

    name = "Wyeast {} {}".format(strain, description)

    low_attenuation_elem = yeast_soup.find(
        'div', class_='field--name-field-attenuation-low')
    low_attenuation = low_attenuation_elem.text

    high_attenuation_elem = yeast_soup.find(
        'div', class_='field--name-field-attenuation-high')
    high_attenuation = high_attenuation_elem.text

    low_temperature_elem = yeast_soup.find(
        'div', class_='field--name-field-temperature-low')
    low_temperature = low_temperature_elem.text

    high_temperature_elem = yeast_soup.find(
        'div', class_='field--name-field-temperature-high')
    high_temperature = high_temperature_elem.text

    abv_elem = yeast_soup.find('div', class_='field--name-field-abv')
    abv = abv_elem.text

    yeast_info = (name, low_attenuation, high_attenuation, low_temperature,
                  high_temperature, abv)

    LOGGER.debug("Got yeast information %s.", yeast_info)

    return yeast_info

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    get_wyeast_yeasts()
