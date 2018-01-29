import logging
import urllib.request
import xml.etree.ElementTree as ET


LOGGER = logging.getLogger(__name__)

BJCP_GUIDELINES = r'https://raw.githubusercontent.com/meanphil/bjcp-guidelines-2015/master/styleguide.xml'


def add_styles(apps, _):
    """Loads styles from BJCP cached XML data and updates styles in BeerStyle.
    """
    BeerStyle = apps.get_model('brewery', 'BeerStyle')
    styles = get_bjcp_guidelines(BeerStyle)
    for style in styles:
        if BeerStyle.objects.filter(name=style.name).exists():
            style.pk = BeerStyle.objects.get(name=style.name).pk
        style.save()


def get_bjcp_guidelines(BeerStyle):
    style_data = urllib.request.urlopen(BJCP_GUIDELINES)
    root = ET.fromstring(style_data.read())

    styles = []
    for category in root.findall('.//category'):
        styles += get_bjcp_category(category, BeerStyle)
    return styles


def get_bjcp_category(category_elem, BeerStyle):
    name = category_elem.find('name').text
    LOGGER.info('Loading category %s.', name)

    styles = []
    for subcategory in category_elem.findall('.//subcategory'):
        styles.append(get_bjcp_subcategory(subcategory, BeerStyle))
    return styles


def get_bjcp_subcategory(subcategory_elem, BeerStyle):
    name = subcategory_elem.find('name').text
    LOGGER.info('Loading subcategory %s.', name)

    stats = subcategory_elem.find('stats')
    low_ibu, high_ibu = get_low_high(stats.find('ibu'), int)
    low_og, high_og = get_low_high(stats.find('og'), float)
    low_fg, high_fg = get_low_high(stats.find('fg'), float)
    low_abv_pct, high_abv_pct = get_low_high(stats.find('abv'), float)
    low_abv = low_abv_pct / 100.0
    high_abv = high_abv_pct / 100.0
    low_srm, high_srm = get_low_high(stats.find('srm'), float)
    return BeerStyle(
        name=name, low_ibu=low_ibu, high_ibu=high_ibu,
        low_original_gravity=low_og, high_original_gravity=high_og,
        low_final_gravity=low_fg, high_final_gravity=high_fg, low_abv=low_abv,
        high_abv=high_abv, low_srm=low_srm, high_srm=high_srm)


def get_low_high(elem, obj):
    low = high = 0.0
    if elem.get('flexible') == 'false':
        low = obj(elem.find('low').text)
        high = obj(elem.find('high').text)
    return low, high
