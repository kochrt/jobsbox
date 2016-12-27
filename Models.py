
import json
import re
from collections import Counter


class Request(object):
    def __init__(self, query_strings, time='now-1d', count=40, should_print=False):
        attr = {}

        if len(query_strings) > 0:

            attr = Match.default_match(query_strings[0])

        if len(query_strings) > 1:

            attr = {
                "bool": {
                    "should": [
                        Match.default_match(query_strings[1]),
                        attr
                    ],
                    "minimum_should_match": 1
                }
            }

        if len(query_strings) > 2:
            attr = Request.add_string(attr, query_strings[2:])

        attr = {
            "query": {
                "bool": {
                    "must": [],
                    "should": [attr],
                    "must_not": [],
                    "filter": {
                        "bool": {
                            "must": [
                                {
                                    "geo_bounding_box": {
                                        "location": {
                                            "bottom_left": {
                                                "lat": -15.287661010299214,
                                                "lon": -129.68296875
                                            },
                                            "top_right": {
                                                "lat": 70.95852159126582,
                                                "lon": -65.34703124999999
                                            }
                                        }
                                    }
                                },
                                {
                                    "range": {
                                        "time": {
                                            "gt": time
                                        }
                                    }
                                }
                            ],
                            "should": [],
                            "must_not": []
                        }
                    },
                    "minimum_should_match": 1
                }
            },
            "sort": [
                "_score"
            ],
            "size": count
        }

        self.query = attr

        if should_print:
            print(json.dumps(attr, indent=3))


    @staticmethod
    def add_string(attr, strings):
        if len(strings) < 1:
            return attr

        attr = {
            "bool": {
                "should": [
                    attr,
                    Match.default_match(strings[0])
                ],
                "minimum_should_match": 1
            }
        }

        return Request.add_string(attr, strings[1:])


class Match(object):

    where = ["company", "title", "description"]

    def __init__(self, phrase, where, kind="phrase", boost=1):
        self.phrase = phrase
        self.where = where
        self.kind = kind
        self.boost = boost

    def dict(self):
        return {
            "match": {
                self.where: {
                    "query": self.phrase,
                    "boost": self.boost,
                    "type": self.kind
                }
            }
        }

    @staticmethod
    def default_match(phrases):
        results = []
        for phrase in phrases:
            for w in Match.where:
                boost = 1 if w == "description" else 5
                results.append(Match(phrase, w, "phrase", boost).dict())

        return {
            "bool": {
                "should": results
            }
        }


class Trie:

    _end = '_end_'

    def __init__(self, *words):
        self.root = dict()
        for word in words:
            self.add_word(word)

    def add_word(self, word):
        current_dict = self.root
        for letter in word:
            current_dict = current_dict.setdefault(letter, {})
        current_dict[Trie._end] = 0

    def __contains__(self, word):
        return self.traverse(self.root, word, lambda r: Trie._end in r)

    def increment_seen(self, word):
        return self.traverse(self.root, word, self.__increment)

    def get_count(self, word):
        return self.traverse(self.root, word, self.__c)

    def traverse(self, root, word, f):
        if len(word) < 1:
            return f(root)
        elif word[0] in root:
            return self.traverse(root[word[0]], word[1:], f)

    @staticmethod
    def __c(root):
        return root[Trie._end] if Trie._end in root else 0

    @staticmethod
    def __increment(root):
        if Trie._end in root:
            root[Trie._end] += 1
            return root[Trie._end]
        return 0


class TrieCategoryCounter(object):

    # Takes a dictionary of categories : array of relevant words
    # { "category": ["word"] }
    def __init__(self, categories={}):
        self.trie = Trie()
        self.categories = categories
        for words in categories.itervalues():
            for word in words:
                self.trie.add_word(word)

    # Takes category and its associated words
    def add_category(self, category, words):
        self.categories[category] = words
        for word in words:
            self.trie.add_word(word)

    def __count_array(self, array):
        for word in array:
            if self.trie.increment_seen(word) > 0:
                print word

    def count_line(self, line):
        self.__count_array(line.split())

    def count(self, string):
        for line in string:
            self.count_line(line)

    def get_count(self, category):
        return self.trie.get_count(category)

    def get_counts(self):
        counts = {}
        for cat in self.categories.iterkeys():
            counts[cat] = self.get_count(cat)
        return counts


class CategoryCounter(object):

    def __init__(self, categories={}, counter=None):
        self.categories = categories
        self.counter = counter

    # Takes category and its associated words
    def add_category(self, category, words):
        self.categories[category] = words

    def count(self, parsed_array):
        self.counter = Counter(parsed_array)

    def get_count(self, category):
        count = 0
        for string in self.categories[category]:
            count += self.counter[string]
        return count

    def get_counts(self):
        counts = {}
        for cat in self.categories.iterkeys():
            counts[cat] = self.get_count(cat)
        return counts


def main():

    categories = {
        'ios':      ['ios', 'swift', 'objective-c', 'objective c'],
        'java':     ['java'],
        'web':      ['angular', 'angularjs', 'angular js', 'html', 'css', 'javascript'],
        'aws':      ['aws', 'amazon', 'cloud'],
        'junior':   ['junior', 'entry']
    }

    categories = CategoryCounter(categories)

    with open("description.txt") as data:

        data = strip_all(data.read())
        print(data.split())
        categories.count(data.split())

        print categories.get_counts()


def strip_with_regex(string, regex):
    return re.sub(r'\s+', ' ', re.sub(regex, " ", string)).lower()


def strip_all(string):
    regex = r'(<[^>]*>|[!\?#-\.\'";:,\+\(\)])'
    return strip_with_regex(string, regex)

if __name__ == '__main__':
    main()
