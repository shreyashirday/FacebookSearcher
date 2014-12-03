#coding: utf-8
"""
Facebook Message Downloader - A very simple application for downloading
inbox messages from Facebook
"""

import math
import json
import urllib
import urllib2
import datetime
import collections

MessageHead = collections.namedtuple('MessageThread', 'sender, sender_id, msg_id')
Message = collections.namedtuple('Message', 'time, sender, msg')

class SimpleGraph(object):
    """
    Implementation of some basic methods for FB communication
    """

    def __init__(self, token):
        """
        Setups object for network communication and get the user_id

        @param token: A Facebook Access Token with 'read_mailbox' permission
        @type token: str
        """

        self._graph_url = 'https://graph.facebook.com/'

        self._net = urllib2.build_opener()
        self._net.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 (KHTML, like Gec'
                                               'ko) Chrome/25.0.1364.152 Safari/537.22')]
        self._token = token
        self._user_id = self.call(path='me')['id']

    def call(self, params=None, path='me'):
        """
        GET a dict of params from path

        @param params: Query params
        @type params: dict

        @param path: Path under graph.facebook.com
        @type path: str

        @rtype: dict
        """
        std = {'method': 'GET',
               'format': 'json',
               'access_token': self._token}

        if params:
            std.update(params)

        if path:
            path = '{0}?'.format(path)

        return self.raw_call(self._graph_url + path + urllib.urlencode(std))

    def raw_call(self, uri):
        try:
            return json.loads(self._net.open(uri).read())
        except urllib2.HTTPError, err:
            reply = json.loads(err.read())
            raise FBError(reply['error']['code'], reply['error']['message'])

class FBError(Exception):
    """
    Wraps FB API exceptions into Python ones
    """

    INVALID_TOKEN = 190

    def __init__(self, code, reason):
        Exception.__init__(self)

        self.code = code
        self.reason = reason

    def __str__(self):
        return '{0} ({1})'.format(self.reason, self.code)

class FBMDown(object):
    TIME_ASCEND = 'ASC'
    TIME_DESCEND = 'DESC'
    OFFSET = 25

    def __init__(self, token):
        self.graph = SimpleGraph(token)
        self.last_msg_count = 0

    def _message_count(self, thread_id):
        #TODO: Sanitize thread_id
        p = {'q': 'SELECT message_count FROM thread WHERE thread_id = {0} LIMIT 1'.format(thread_id)}
        self.last_msg_count = int(self.graph.call(params=p, path='fql')['data'][0]['message_count'])
        return self.last_msg_count

    def _extract_message_headers(self, data):
        """
        Yields MessageHead object from the given data dict.
        """
        for thread in data:
            for user in thread['to']['data']:
                if user['id'] != self.graph._user_id:
                    yield MessageHead(user['name'], user['id'], thread['id'])

    def get_thread(self, thread_id, order=TIME_ASCEND):
        """
        Yields a page from the requested thread in the given order
        """
        page_actual = 0
        page_total = int(math.ceil(self._message_count(thread_id) / float(self.OFFSET)))
        recipients_json = self.graph.call(params={'fields': 'to'}, path=thread_id)['to']['data']
        recipients = {int(user['id']):user['name'] for user in recipients_json}

        #TODO: Sanitize some input here too
        query = 'SELECT author_id, created_time, body FROM message WHERE thread_id = {0} ORDER BY created_time {1}'\
                ' LIMIT 25 OFFSET {2}'.format(thread_id, order, '{0}')

        while page_actual < page_total:
            for msg in self.graph.call(params={'q': query.format(page_actual * self.OFFSET)}, path='fql')['data']:
                yield Message(msg['created_time'], recipients[msg['author_id']], msg['body'])
            page_actual += 1

    def list_threads(self):
        """
        Yields a page of your inbox as MessageHead objects
        """
        page = self.graph.call({'fields': 'inbox.to'})
        for head in self._extract_message_headers(page['inbox']['data']):
            yield head

        if 'inbox' in page:
            page = page['inbox']

        while 'paging' in page:
            page = self.graph.raw_call(page['paging']['next'])
            for msg_head in self._extract_message_headers(page['data']):
                yield msg_head

class FBMPPrinters(object):
    def __init__(self):
        self.last_date = None

    def prettify_2(self, msg):
        """
        Pretty print using the following template

        ***** YYYY-MM-DD *************** (padded to 80 chars)
        [HH:MM:SS] <username> message

        @param msg:
        @return:
        """

        date = datetime.datetime.fromtimestamp(msg.time)
        if self.last_date != date.date():
            self.last_date = date.date()
            return ' '.join(['*****', str(self.last_date), '*' * 62]) + '\n'\
                   + u'[{0}] <{1}> {2}'.format(date.strftime('%H:%M:%S'), msg.sender, msg.msg).encode('utf-8')
        else:
            return u'[{0}] <{1}> {2}'.format(date.strftime('%H:%M:%S'), msg.sender, msg.msg).encode('utf-8')

    @staticmethod
    def prettify_1(msg):
        """
        Pretty print using the following template:

        [YYYY-MM-DD HH:MM:SS] <username> message

        @type msg: Message
        """
        date = datetime.datetime.fromtimestamp(msg.time).strftime('%Y-%m-%d %H:%M:%S')
        return u'[{0}] <{1}> {2}'.format(date, msg.sender, msg.msg).encode('utf-8')