
from Models import *
import requests


def main():

    # What we're searching for, separated by 'OR'
    # synonyms should be in the array
    query_strings = [
        ['iOS'],
        ['Swift'],
        ['Java'],
        ['Angular', 'angularjs', 'angular2', 'angular.js'],
        ['junior'],
        ['aws']
    ]

    # Words that might be found in a post for a specific role.
    # Based on how many words of each type we see, modify email accordingly
    categories = {
        'ios':      ['ios', 'swift', 'objective-c', 'objective c'],
        'java':     ['java'],
        'web':      ['angular', 'angularjs', 'angular js', 'html', 'css', 'javascript'],
        'aws':      ['aws', 'amazon', 'cloud'],
        'junior':   ['junior', 'entry']
    }

    # How old can the posts be
    time = 'now-1d'

    request = Request(query_strings, time=time, count=100)

    r = requests.post(
        url='https://search.whoishiring.io/item/item/_search?scroll=10m',
        data=json.dumps(request.query)
    )

    data = json.loads(r.text)

    if data["timed_out"]:
        print("request timed out")
    elif data["hits"]["total"] < 1:
        print("nothing found")
    else:
        data = data["hits"]["hits"]

        for dict in data:
            description = dict["_source"]["description"]
            print dict["_source"]["company"]

            # match = re.search(r'[^@^:\s]+@[^@\s]+\.[a-zA-Z0-9]+', description)
            # if match is not None:
            #     print dict["_source"]["company"], match.group()

            # for html
            # description = re.sub(r'<[/]?[\w]*>', " ", description)

            print description
            print


if __name__ == '__main__':
    main()

