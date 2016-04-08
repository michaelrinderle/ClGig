#!/usr/bin/python2
# -*- coding: utf-8 -*-

import requests
import sys
from urlparse import urljoin
from time import sleep
from bs4 import BeautifulSoup
from requests.exceptions import RequestException


def main():

    f = open('clgiglist.html', 'w')
    f.write('''<!DOCTYPE html><html><head><link rel="stylesheet" type="text/css" href='https://cdnjs.cloudflare.com/ajax/libs/foundation/6.2.0/foundation.css'>
               <style>a{color:rosybrown;}</style></head><body><table><thead><tr><th>#</th><th width='200'>Site</th><th>Listing</th></tr></thead><tbody>''')

    for location in sites:
        cl_1 = GetGigs(site=location)
        listings = set()

        for results in cl_1.results():
            if results['name'] in listings:
                continue
            else:
                listings.add(results['name'])
                add_item(results, f)

                if results['areas'] is not None:
                    for area in results['areas']:
                        cl_2 = GetGigs(site=area)

                        for sub_results in cl_2.results(area=False):
                            if sub_results['name'] in listings:
                                continue
                            else:
                                add_item(sub_results, f)

        sleep(delay)

    f.write('''</tbody></table></body></html>''')
    f.close()


def add_item(results, f):
    global inc
    try:
        f.write('''<tr><td>{}</td><td>{}</td><td><a href="{}"><b>{}</b></a></td></tr>'''.format(inc, results['current'].upper(), results['url'].encode('utf-8'), results['name'].encode('utf-8').upper()))
        inc += 1
        sys.stdout.write('\r' + str(inc) + '  hits -- working site {}                              '.format(results['current']))
        sys.stdout.flush()
    except UnicodeEncodeError:
        return False
    except IOError:
        return False


def results_grab(*args, **kwargs):
    try:
        return requests.get(*args, **kwargs)
    except RequestException as exc:
        sys.stdout.write('\r' + str(exc) + '                                   '.format(exc))
        return requests.get(*args, **kwargs)


class GetGigs(object):

    sort_by = {'newest': 'date'}

    def __init__(self, site):

        self.site = site
        self.url = 'http://{}.craigslist.org/search/cpg'.format(self.site)

    def results(self, limit=None, area=False):
        start = 0
        total_right_now = 0
        total = 0

        while True:

            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 \
                                      (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A',
                       'Referer': 'http://{}.craigslist.org'.format(self.site)}
            try:
                response = requests.get(self.url, headers=headers, timeout=10)
            except requests.exceptions.ConnectionError:
                continue
            except requests.exceptions.ReadTimeout:
                continue
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions:
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            try:
                current = soup.find('select', id='areaAbb').find('option')['value'].upper()
            except AttributeError:
                current = 'Unknown'

            if area is True:

                site_grab = soup.find('select', id='areaAbb').find_all('option')
                areas = set()

                for area in site_grab:
                    if area['value'] not in sites:
                        areas.add(area['value'])
                        with open('sites.txt', 'a') as f:
                            f.write(area['value'] + '\n')
            else:
                areas = None

            if not total:
                totalcount = soup.find('span', {'class': 'totalcount'})
                total = int(totalcount.text) if totalcount else 0

            for row in soup.find_all('p', {'class': 'row'}):
                if limit is not None and total_right_now >= limit:
                    break

                link = row.find('a', {'class': 'hdrlnk'})
                id = link.attrs['data-id']
                name = link.text
                url = urljoin(self.url, link.attrs['href'])

                result = {'id': id,
                          'name': name,
                          'url': url,
                          'current': current,
                          'areas': areas
                          }

                yield result
                total_right_now += 1

            if total_right_now == limit:
                break
            if (total_right_now - start) < per_request:
                break
            start = total_right_now

if __name__ == '__main__':

    inc = 1
    per_request = 150
    delay = 30
    sites = set(line.strip() for line in open('sites.txt'))
    main()

