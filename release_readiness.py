import requests
from urllib.parse import parse_qs
from bs4 import BeautifulSoup
import urllib.request
import json


class Issues():
    def __init__(self, filter_api_urls, severity):
        res = urllib.request.urlopen(filter_api_urls[severity])
        assert res.status == 200, "Error when accessing issues api"
        self.issues = json.loads(res.read())

    def get_number(self):
        return self.issues['total_count']

    def print_titles(self):
        for item in self.issues['items']:
            print(item['title'])


class Zephyr_release_issues():
    zephr_repo = "zephyrproject-rtos/zephyr"
    zeph_wiki_url = "https://github.com/" + zephr_repo + "/wiki/Filters"
    high = None
    medium = None
    low = None
    # TODO: Read the following from https://docs.zephyrproject.org/latest/development_process/release_process.html
    #  #release-quality-criteria
    max_high = 0
    max_medium = 20
    max_low = 150

    def __init__(self):
        zeph_wiki_soup = self.process_zeph_wiki()
        filters = self.get_filters(zeph_wiki_soup)
        filter_api_urls = self.get_filter_api_urls(filters)
        self.high = Issues(filter_api_urls=filter_api_urls, severity='High')
        self.medium = Issues(filter_api_urls=filter_api_urls, severity='Medium')
        self.low = Issues(filter_api_urls=filter_api_urls, severity='Low')
        self.release_readiness = self.statuses()

    def process_zeph_wiki(self):
        zeph_wiki_page = requests.get(self.zeph_wiki_url)
        assert zeph_wiki_page.status_code == 200, 'Wki page not collected'
        return BeautifulSoup(zeph_wiki_page.content, 'lxml')

    def get_filters(self, zeph_wiki_soup):
        filters = {
            'High': None,
            'Medium': None,
            'Low': None
        }

        links = zeph_wiki_soup.find_all("a")
        for link in links:
            for key in filters:
                if key in link.text:
                    assert filters[key] is None, f'There was another link with {key} text'
                    filters[key] = parse_qs(link.attrs['href'])['q'][0]

        return filters

    def get_filter_api_urls(self, filters):
        api_urls = {
            'High': None,
            'Medium': None,
            'Low': None
        }

        for severity in api_urls:
            filtr = filters[severity]
            api_com = "+".join(filtr.split(" "))
            api_urls[severity] = "https://api.github.com/search/issues" + "?q=" + api_com + "+repo:" + self.zephr_repo

        return api_urls

    def statuses(self):
        return {'high': bool(self.high.get_number() < self.max_high),
                'medium': bool(self.medium.get_number() < self.max_medium),
                'low': bool(self.low.get_number() < self.max_low)}


if __name__ == '__main__':
    zephyr_release_issues = Zephyr_release_issues()

    """    
    # examples
    high_num = zephyr_release_issues.high.get_number()
    mid_num = zephyr_release_issues.medium.get_number()
    low_num = zephyr_release_issues.low.get_number()
    zephyr_release_issues.high.print_titles()
    """

    print(zephyr_release_issues.release_readiness)
    if all(zephyr_release_issues.release_readiness.values()):
        print('Release ready!')
    else:
        print('Release not ready!')
