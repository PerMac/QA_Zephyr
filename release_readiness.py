import requests
import urllib.request
import json
from urllib.parse import parse_qs
from bs4 import BeautifulSoup
from colorama import Fore


class GitHubIssues:
    def __init__(self, api_url):
        """
        Initialize a dictionary with selected GitHub issues and their properties

        :param api_url: Url for GitHub api request
        """
        res = urllib.request.urlopen(api_url)
        assert res.status == 200, "Error when accessing issues api"
        self.issues = json.loads(res.read())

    def get_number(self):
        """
        Return the total number of issues

        :return: Total number of issues
        """
        return self.issues['total_count']

    def print_titles(self):
        """
        Print titles of all issues

        :return: Titles of all issues
        """
        for item in self.issues['items']:
            print(item['title'])


class ZephyrReleaseQA:
    zephr_repo = "zephyrproject-rtos/zephyr"
    zeph_wiki_url = "https://github.com/" + zephr_repo + "/wiki/Filters"
    # TODO: Read the following from https://docs.zephyrproject.org/latest/development_process/release_process.html
    #  #release-quality-criteria
    max_issues_count = {
        'high': 0,
        'medium': 20,
        'low': 150
    }

    def __init__(self):
        """
        Parse Wiki page searching for links to filtered issues. Translate the links into REST API queries.
        Call the GitHub REST API and load the results to GitHUbIssues dictionaries based on severity. Evaluate
        the status of the release_readiness according to the community criteria.
        """
        self.subset_names = ['high', 'medium', 'low']
        self.issues = {}
        zeph_wiki_soup = self.process_zeph_wiki()
        filters = self.get_filters(zeph_wiki_soup)
        self.filter_api_urls = self.filter_to_api_urls(filters)
        for key in self.subset_names:
            self.issues[key] = GitHubIssues(self.filter_api_urls[key])

        self.statuses = self.evaluate_statuses()

    def process_zeph_wiki(self):
        """
        Open and process the Wiki Page

        :return: Wiki Page processed into 'lxml' format
        """
        zeph_wiki_page = requests.get(self.zeph_wiki_url)
        assert zeph_wiki_page.status_code == 200, 'Wki page not collected'
        return BeautifulSoup(zeph_wiki_page.content, 'lxml')

    def get_filters(self, zeph_wiki_soup):
        """
        Find links to filtered GitHub issues on the given page and translate them to GitHub filters

        :param zeph_wiki_soup: Wiki Page processed into 'lxml' format
        :return: GitHub filters
        """
        filters = {
            'high': None,
            'medium': None,
            'low': None
        }

        links = zeph_wiki_soup.find_all("a")
        for link in links:
            for key in filters:
                if key.capitalize() in link.text:
                    assert filters[key] is None, f'There was another link with {key.capitalize()} text'
                    filters[key] = parse_qs(link.attrs['href'])['q'][0]

        return filters

    def filter_to_api_urls(self, filters):
        """
        Translate GitHub filters to GitHub api URLs

        :param filters: GitHub filters
        :return: GitHub api URLs
        """
        api_urls = {
            'high': None,
            'medium': None,
            'low': None
        }

        for severity in api_urls:
            filtr = filters[severity]
            #api_com = "+".join(filtr.split(" "))
            api_com = filtr.replace(" ", "+")
            api_urls[severity] = "https://api.github.com/search/issues" + "?q=" + api_com + "+repo:" + self.zephr_repo + "&per_page=50"

        return api_urls

    def evaluate_statuses(self):
        """
        Evaluate and return statuses of fulfillment of the release criteria

        :return: Statuses of fulfillment of the release criteria
        """
        return {key: bool(self.issues[key].get_number() < self.max_issues_count[key]) for key in self.subset_names}

    def release_readiness(self, verbose=False):
        """
        Evaluate if the version fulfills the given release quality criteria

        :param verbose: Print details of issues counts if True
        :return: State of the release_readiness
        """
        if verbose:
            for severity in self.subset_names:
                msg = (f'There are {self.issues[severity].get_number()} open issues with {severity} severity. '
                       f'Max allowed: {self.max_issues_count[severity]}')
                if self.statuses[severity]:
                    print(Fore.GREEN + msg + Fore.RESET)
                else:
                    print(Fore.RED + msg + Fore.RESET)

        if all(zephyr_release_qa.statuses.values()):
            print(Fore.GREEN + 'Release ready!' + Fore.RESET)
            return False
        else:
            print(Fore.RED + 'Release not ready!' + Fore.RESET)
            return True


if __name__ == '__main__':
    zephyr_release_qa = ZephyrReleaseQA()

    # examples
    high_num = zephyr_release_qa.issues['high'].get_number()
    mid_num = zephyr_release_qa.issues['medium'].get_number()
    low_num = zephyr_release_qa.issues['low'].get_number()
    zephyr_release_qa.issues['medium'].print_titles()
    print("test")

    zephyr_release_qa.release_readiness(verbose=True)
