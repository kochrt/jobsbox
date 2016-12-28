
'''

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


def main():

    data = open('config.yml')
    data_map = yaml.load(data)
    data.close()

    print json.dumps(data_map, indent=4)

    query_strings = []
    categories = {}
    for category, vals in data_map['categories'].iteritems():
        query_strings.append(vals['query'])
        categories[category] = vals['keywords']

    print 'categories', json.dumps(categories, indent=4)
    print 'query strings', json.dumps(query_strings, indent=4)

    # How old can the posts be
    time = data_map['post_age']
    count = data_map['num_results']

    request = Request(query_strings, time=time, count=count)

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

            description = dict['_source']['description']
            company = dict['_source']['company']

            # get email
            match = re.search(r'[^@^:\s]+@[^@\s]+\.[a-zA-Z0-9]+', description)
            if match is not None:
                email = match.group()
            else:
                email = ''

            print company
            description = strip_all(description)
            counter = CategoryCounter(categories, description.split())

            print 'score:', json.dumps(dict['_score'])
            if len(email) > 0:
                print email
            print counter.get_counts()
            print

            # for html
            # description = re.sub(r'<[/]?[\w]*>', ' ', description)

            # print description
            # print


if __name__ == '__main__':
    main()

