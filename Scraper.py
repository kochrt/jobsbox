
'''
use_email_file: true

post_age: now-30d

num_results: 100

categories:
  ~category:
    query:
      ~string
    keywords:
      ~strings
    email_primary: >
      ~ ~ ~
    email_secondary: >
      ~ ~ ~
email:
  

'''

from Models import *
import requests
import yaml
from gmail import *
import os

CONFIG = 'config.yml'

CATEGORIES = 'categories'
EMAIL = 'email'
SUBJECT = 'subject'

QUERY = 'query'
KEYWORDS = 'keywords'
EMAIL_PRIMARY = 'email_primary'
POST_AGE = 'post_age'
NUM_RESULTS = 'num_results'
HITS = 'hits'

REQUEST_URL = 'https://search.whoishiring.io/item/item/_search?scroll=10m'


def main():

    # get configuration
    config = load_config()

    query_strings = []
    categories = {}
    for category, vals in config[CATEGORIES].iteritems():
        query_strings.append(vals[QUERY])
        categories[category] = vals[KEYWORDS]

    time = config[POST_AGE] if POST_AGE in config else 'now-1d'
    count = config[NUM_RESULTS] if NUM_RESULTS in config else 20

    request = Request(query_strings, time=time, count=count)

    # make the request with the given parameters
    r = requests.post(
        url=REQUEST_URL,
        data=json.dumps(request.query)
    )

    # get response text
    data = json.loads(r.text)

    if data['timed_out']:
        print('request timed out')
    elif data[HITS]['total'] < 1:
        print('nothing found')
    else:
        data = data[HITS][HITS]

        try:
            password = open(config['password']).read()
            print password
        except IOError:
            print("password file could not be opened")
            exit()

        gmail = GMail('kochrt@gmail.com', password)

        for dict in data:

            # Job description
            description = dict['_source']['description']

            # get email from the description if it is there
            email_address = get_email(description)

            if len(email_address) > 0:

                # Company name truncated
                company = re.sub(r'[,(].*$', "", dict['_source']['company'])

                description = strip_all(description)
                counter = CategoryCounter(categories, description.split())

                counts = counter.get_counts_ordered()
                most_common = counts[0][0]

                if EMAIL_PRIMARY in config[CATEGORIES][most_common]:
                    primary_email_blurb = config[CATEGORIES][most_common][EMAIL_PRIMARY]

                else:
                    pass
                    # don't put anything extra in email body

                # print primary_email_blurb
                #
                # print 'score:', json.dumps(dict['_score'])
                # print json.dumps(counter.get_counts_ordered(), indent=2)
                # print

                # for html
                # description = re.sub(r'<[/]?[\w]*>', ' ', description)

                # print description
                # print


def load_config():
    try:
        data = open(CONFIG)
        data_map = yaml.load(data)
        data.close()
        return data_map
    except IOError:
        print('error opening config file')
        exit()


def get_email(description):
    match = re.search(r'[^@^:\s]+@[^@\s]+\.[a-zA-Z0-9]+', description)
    return match.group() if match is not None else ''


if __name__ == '__main__':
    main()

