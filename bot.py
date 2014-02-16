# -*- coding: utf-8 -*-
from shelve import open as open_shelf
from contextlib import closing
from tweepy import OAuthHandler, API
from requests import get
from operator import not_
from config import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET, MAX_TWEETS
from lxml.html import ElementSoup
from string import Template
from StringIO import StringIO

LIST_URL = 'http://ticket.interpark.com/Webzine/Paper/TPNoticeList_iFrame.asp?bbsno=34&pageno=0&stext=&KindOfGoods=&Genre=&sort='
SHELF_FILENAME = 'events.db'
NODE_XPATH = '//table/tbody/tr'
INFO_XPATHS = {'url': ".//td[@class='subject']/a/@href",
               'title': ".//td[@class='subject']/a/text()",
               'opens': ".//td[@class='date']/text()"
         }
TWEET_TEMPLATE = Template(u'[$title] $opens http://ticket.interpark.com/Webzine/Paper/$url')

api = None

def get_api():
    global api
    if api is not None: return api

    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = API(auth)
    return api

def fetch_list(url):
    res = get(url)
    res.encoding = 'euc-kr'
    return res

def parse_event(node):
    return {key: ' '.join(node.xpath(value))
            for key, value in INFO_XPATHS.items()}

def get_all_events(res):
    if res.status_code != 200: return []

    sio = StringIO(res.text)
    tree = ElementSoup.parse(sio)
    event_nodes = tree.xpath(NODE_XPATH)
    return map(parse_event, event_nodes)

def render_event(event):
    if len(event['title']) > 80:
        event['title'] = event['title'][:75] + ' ..'
    return TWEET_TEMPLATE.substitute(event)

def tweet(text):
    print 'tweeting', text.encode('utf-8')
    get_api().update_status(text)

def update_twitter(events):
    for ev in events:
        try:
            tweet(render_event(ev))
        except:
            pass

def has_seen(storage, event):
    return event['url'] in storage

def record_events(storage, events):
    for e in events:
        storage[e['url']] = 1

def main():
    with closing(open_shelf(SHELF_FILENAME)) as storage:
        events = get_all_events(fetch_list(LIST_URL))
        # for e in events: 
        #     print TWEET_TEMPLATE.substitute(e).encode('utf-8')
        new_events = [e for e in events if not has_seen(storage, e)]
        new_events = new_events[:MAX_TWEETS]

        update_twitter(new_events)
        record_events(storage, new_events)


if __name__ == '__main__':
    main()

