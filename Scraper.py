
from Models import *
import requests
import yaml
from gmail import *
import re
import os
from time import gmtime, time, strftime

CONFIG = 'config.yml'
HISTORY = 'history.json'

USE_EMAIL_FILE = 'use_email_file'

CATEGORIES = 'categories'
EMAIL = 'email'
SUBJECT = 'subject'

POST_SITE_REGEX = '\{[\W]*site[\W]*\}'
COMPANY_REGEX = '\{[\W]*company[\W]*\}'
EMAIL_PRIMARY_REGEX = '\{[\W]*email_primary[\W]*\}'
EMAIL_SECONDARY_REGEX = '\{[\W]*email_secondary[\W]*\}'
LINK_REGEX = '\{[\W]*link[\W]*\}'

QUERY = 'query'
KEYWORDS = 'keywords'
EMAIL_PRIMARY = 'email_primary'
EMAIL_SECONDARY = 'email_secondary'
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
    'gh': 'Github',
    'wh': 'Who is Hiring'
}


def main():

    # get configuration
    config = load_config()
    history = load_history()
    log_file = create_log()

    query_strings = []
    categories = {}
    for category, vals in config[CATEGORIES].iteritems():
        query_strings.append(vals[QUERY])
        categories[category] = vals[KEYWORDS]

    age = config[POST_AGE] if POST_AGE in config else 'now-1d'
    count = config[NUM_RESULTS] if NUM_RESULTS in config else 20

    request = Request(query_strings, time=age, count=count)

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
                continue

            elif config[USE_EMAIL_FILE] and email_address in history:
                log(log_file, 'previous email encountered: %s' % email_address)
                continue
                # yes I know these continues aren't necessary
                # I'm just being explicit
            else:

                email = {
                    'to': email_address,
                    'from': config[EMAIL]['from'],
                    'subject': config[EMAIL]['subject'],
                    'body_plaintext': config[EMAIL]['body'],
                    'body_html': config[EMAIL]['body']
                }

                # begin amassing what substitutions we need to make
                substitutions = {
                    EMAIL_SECONDARY_REGEX: config[EMAIL]['email_secondary_preamble']
                }

                source_abbreviation = result['_source']['source_name']
                if source_abbreviation not in SOURCE_MAPPING:
                    log(log_file, 'new source encountered: %s' % source_abbreviation)
                    log(log_file, json.dumps(result['_source'], indent=2))
                    substitutions[POST_SITE_REGEX] = SOURCE_MAPPING['wh']
                else:
                    substitutions[POST_SITE_REGEX] = SOURCE_MAPPING[source_abbreviation]

                # Company name truncated
                company = re.sub(r'[,(].*$', "", result['_source']['company'])

                substitutions[COMPANY_REGEX] = company if len(company) > 0 else config[EMAIL]['company_alternative']

                # get rid of all html and extra punctuation
                description = strip_all(description)

                # count what's left
                counter = CategoryCounter(categories, description.split())
                counts = counter.get_greater_than_zero()

                if len(counts) == 0 or EMAIL_PRIMARY not in config[CATEGORIES][counts[0][0]]:
                    # don't add anything to the email, get rid of {email_primary}
                    # and {email_secondary}
                    substitutions[EMAIL_PRIMARY_REGEX] = ''
                    substitutions[EMAIL_SECONDARY_REGEX] = ''

                else:
                    most_common = counts[0][0]
                    primary_email_blurb = config[CATEGORIES][most_common][EMAIL_PRIMARY]

                    substitutions[EMAIL_PRIMARY_REGEX] = primary_email_blurb

                    if len(counts) > 1:
                        secondary_email_blurb = config[EMAIL]['email_secondary_preamble']
                        phrases = []
                        for keyword in counts[1:]:
                            if EMAIL_SECONDARY in config[CATEGORIES][keyword[0]]:
                                phrases.append(config[CATEGORIES][keyword[0]][EMAIL_SECONDARY])

                        if len(phrases) == 0:
                            substitutions[EMAIL_SECONDARY_REGEX] = config[EMAIL]['email_secondary_alternative']
                        else:
                            phrase = " " + delimit_commas(phrases) + config[EMAIL]['email_secondary_suffix']
                            secondary_email_blurb += phrase
                            substitutions[EMAIL_SECONDARY_REGEX] = secondary_email_blurb
                    else:
                        substitutions[EMAIL_SECONDARY_REGEX] = config[EMAIL]['email_secondary_alternative']

                email = perform_substitutions(email, substitutions)

                message = Message(email['subject'], email['to'], text=email['body_plaintext'], html=email['body_html'])
                # gmail.send(message)

                history[email['to']] = {
                    EMAIL: email,
                    '_source': result['_source'],
                    'time': string_formatted_time()
                }

        # save history
        if config[USE_EMAIL_FILE]:
            history_file = open(HISTORY, 'w')
            json.dump(history, history_file)
        else:
            log(log_file, json.dumps(history, indent=2))

        save_log(log_file)


def load_config():
    try:
        data = open(CONFIG)
        data_map = yaml.load(data)
        data.close()
        return data_map
    except IOError:
        print('error opening config file')
        exit()


def load_history():
    try:
        history = open(HISTORY, 'r')
        history_json = json.loads(history.read())
        history.close()
        return history_json
    except IOError:
        return {}


def get_email(description):
    match = re.search(r'[^@^:\s]+@[^@\s]+\.[a-zA-Z0-9]+', description)
    return match.group() if match is not None else ''


def string_formatted_time():
    return strftime('%Y-%m-%d %H.%M.%S', gmtime())


def create_log():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    return open('logs/%s.log' % string_formatted_time(), 'w+')


def log(log_file, *string):
    for s in string:
        log_file.write(string_formatted_time() + ": " + s)
    log_file.write('\r\n')


def save_log(log_file):
    log_file.close()


def perform_substitutions(email, substitutions):
    replaced = {}
    for email_key, string in email.iteritems():

        for sub_key, replacement in substitutions.iteritems():
            string = re.sub(sub_key, replacement, string)

        # replace newline with corresponding newline in plaintext/html
        if email_key == 'body_html':
            string = re.sub('\n', '<br>', string)
        elif email_key == 'body_plaintext':
            string = re.sub('\n', '\r\n', string)

        replaced[email_key] = string
    return replaced


def delimit_commas(strings):
    if len(strings) == 1:
        return strings[0]
    if len(strings) == 2:
        return strings[0] + " and " + strings[1]
    built = strings[0] + ", and " + strings[1]
    return __delimit_commas(built, strings[2:])


def __delimit_commas(built, strings):
    if len(strings) < 1:
        return built
    return __delimit_commas(strings[0] + ", " + built, strings[1:])


if __name__ == '__main__':
    main()

