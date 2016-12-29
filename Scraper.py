
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
import os


def main():

    # get configuration
    config = load_config()

    query_strings = []
    categories = {}
    for category, vals in config['categories'].iteritems():
        query_strings.append(vals['query'])
        categories[category] = vals['keywords']

    time = config['post_age'] if 'post_age' in config else 'now-1d'
    count = config['num_results'] if 'num_results' in config else 20

    request = Request(query_strings, time=time, count=count)

    # make the request with the given parameters
    r = requests.post(
        url='https://search.whoishiring.io/item/item/_search?scroll=10m',
        data=json.dumps(request.query)
    )

    data = json.loads(r.text)

    if data['timed_out']:
        print('request timed out')
    elif data['hits']['total'] < 1:
        print('nothing found')
    else:
        data = data['hits']['hits']

        for dict in data:

            # get email from the description if it is there
            email = get_email(description)

            if len(email) > 0:
                print email

                # Job description
                description = dict['_source']['description']

                # Company name truncated
                company = re.sub(r'[,(].*$', "", dict['_source']['company'])

                description = strip_all(description)
                counter = CategoryCounter(categories, description.split())

                counts = counter.get_counts_ordered()
                most_common = counts[0][0]
                primary_email_blurb = config['categories'][most_common]['email_primary']

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
        data = open('config.yml')
        data_map = yaml.load(data)
        data.close()
        return data_map
    except IOError:
        print('error opening config file (config.yml)')
        exit()


def get_email(description):
    match = re.search(r'[^@^:\s]+@[^@\s]+\.[a-zA-Z0-9]+', description)
    return match.group() if match is not None else ''

if __name__ == '__main__':
    main()

