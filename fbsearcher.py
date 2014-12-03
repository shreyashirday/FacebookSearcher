import re
import urllib2
import urllib
import gzip
import os
import json
import sys
import time
import StringIO
import collections
from time import *
import fbmdown

"""
Author: Shreyas Hirday
Contact Info - Email: shreyashirday@gmail.com or add me on Facebook!
"""

emails = '([\w.-]+)@([\w.-]+.com)'
regexurl = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA\
-F]))+'
phone = '(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'


ROWSPPAGE = 50

search = False


#this decorator was copied and pasted lol
def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = clock()
            return ret
        return rateLimitedFunction
    return decorate

@RateLimited(100)
def returnData(tid,offset):
        comments = 'comments.limit(30).offset({0})'.format(offset)
        params = urllib.urlencode({'fields': comments, 'access_token': token})
        url = 'https://graph.facebook.com/v2.2/'+tid+'?' + params
        #print "FACEBOOK GRAPH REQUEST URL: " + url
        data = urllib.urlopen(url).read()
        data = json.loads(data)
        return data










print "Welcome!\n"


token = raw_input("Enter your access token:")
zero = False
while not zero:
    if len(token) > 0:
        zero = True
    else:
        token = raw_input("Enter your access token:")
fb = fbmdown.FBMDown(token)
for i, thread in enumerate(fb.list_threads(),1):
    print u'- Thread ID: {0} for conversation with {1}'.format(thread.msg_id, thread.sender)
        #print u' -Conversation with {0}'.format(thread.sender)
    if i % ROWSPPAGE == 0:
        key = raw_input(' Press Enter for next, press q to quit, press n to search a conversation\n')
        if key == 'q':
            break
        elif key == 'n':
            search = True
            break
index = 0
if search == True:


    tid = raw_input('Copy and paste the thread id and pick query(email,url, or phone)\n')
    inputs = tid.split()
    tidinput = inputs[0]
    queryinput = inputs[1]
    #data = returnData(tidinput)
    #data = data['comments']['data']



    while True:
    #while 'paging' in data:

        data = returnData(tidinput,index)
        if 'comments' in data:
            if 'data' in data['comments']:

                data = data['comments']['data']
            else:
                break
        else:
            break




        for comment in data:


            if comment['from']['id'] is not fb.graph._user_id:
                if 'message' in comment:
                    text = comment['message']
                                #text = text[1:-1]
                #print text
                    if queryinput == 'email':
                    #print text + " ... checking for email"
                        match = re.search(emails,text)
                        if match:
                            print match.group()
                    elif queryinput == 'url':
                        #print text + "...checking URL"
                        match = re.search(regexurl,text)
                        if match:
                            print match.group()
                    else:
                        match = re.search(phone,text)
                        if match:
                            print match.group()


        index += 50

        sleep(2)
    print "Goodbye!"
