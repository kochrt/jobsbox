
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
import re
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

SOURCE_MAPPING = {
    'so': 'Stack Overflow',
    'hn': 'Hacker News',
    'bo': 'Boolerang',
    'aj': 'Authentic Jobs',
    'ww': 'We Work Remotely',
    'cf': 'Coroflot',
    'gh': "Github",
    'wh': "Who is Hiring"
}

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
        except IOError:
            print("password file could not be opened")
            exit()

        gmail = GMail('kochrt@gmail.com', password)

        # iterate over results
        for result in data:

            # Job description
            description = result['_source']['description']

            # get email from the description/apply if it is there
            email_address = get_email(result['_source']['apply'])
            if len(email_address) == 0:
                email_address = get_email(description)

            if len(email_address) == 0:
                # do something even if we can't email
                pass
            else:

                email = {
                    'to': email_address,
                    'from': config['email']['from'],
                    'subject': config['email']['subject'],
                    'body_plaintext': config['email']['body_plaintext'],
                    'body_html': config['email']['body_html']
                }

                substitutions = {}

                source_abbreviation = result['_source']['source_name']
                if source_abbreviation not in SOURCE_MAPPING:
                    log('new source encountered: %s' % source_abbreviation)
                    log(json.dumps(result['_source'], indent=2))
                    substitutions['{0}'] = SOURCE_MAPPING['wh']
                else:
                    substitutions['{0}'] = SOURCE_MAPPING[source_abbreviation]

                # Company name truncated
                company = re.sub(r'[,(].*$', "", result['_source']['company'])
                substitutions['{1}'] = company

                description = strip_all(description)
                counter = CategoryCounter(categories, description.split())

                counts = counter.get_counts_ordered()
                most_common = counts[0][0]

                # do replacements in the body of the email
                if EMAIL_PRIMARY in config[CATEGORIES][most_common]:
                    primary_email_blurb = config[CATEGORIES][most_common][EMAIL_PRIMARY]
                    substitutions['{2}'] = primary_email_blurb
                    print perform_substitutions(email, substitutions)
                else:
                    pass
                    # don't put anything extra in email body

                # print primary_email_blurb
                #
                # print 'score:', json.dumps(result['_score'])
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


def log(string):
    # TODO: should output to log file
    print string


def perform_substitutions(email, substitutions):
    replaced = {}
    for email_key, string in email.iteritems():
        for sub_key, replacement in substitutions.iteritems():
            print 'replace %s with %s in %s' % (sub_key, replacement, string)
            string = re.sub(sub_key, replacement, string)
        replaced[email_key] = string
    return replaced


if __name__ == '__main__':
    main()

