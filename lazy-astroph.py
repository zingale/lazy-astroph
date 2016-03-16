#!/usr/bin/env python

from __future__ import print_function

import argparse
import datetime as dt
import feedparser
import json
import os
import shlex
import smtplib
import subprocess
import sys
import urllib
from email.mime.text import MIMEText

# class to hold a paper
# sort on # of categories and then on names
class Paper(object):

    def __init__(self, arxiv_id, title, url, keywords, channels):
        self.arxiv_id = arxiv_id
        self.title = title
        self.url = url
        self.keywords = list(keywords)
        self.channels = list(set(channels))

    def __str__(self):
        return u"{} : {}\n  {} (channels: {})\n".format(self.arxiv_id, self.title, self.url, self.channels)

    def kw_str(self):
        return ", ".join(self.keywords)

    def __cmp__(self, other):
        if len(self.keywords) == len(other.keywords):
            return cmp(self.kw_str(), other.kw_str())
        else:
            return cmp(len(self.keywords), len(other.keywords))

class Keyword(object):

    def __init__(self, name, matching="any", channel=None, excludes=None):
        self.name = name
        self.matching = matching
        self.channel = channel
        self.excludes = list(set(excludes))

    def __str__(self):
        return "{}: matching={}, channel={}, NOTs={}".format(
            self.name, self.matching, self.channel, self.excludes)

class AstrophQuery(object):

    def __init__(self, start_date, end_date, max_papers, old_id=None):
        self.start_date = start_date
        self.end_date = end_date
        self.max_papers = max_papers
        self.old_id = old_id

        self.base_url = "http://export.arxiv.org/api/query?"
        self.sort_query = "max_results={}&sortBy=submittedDate&sortOrder=descending".format(self.max_papers)

        self.subcat = ["GA", "CO", "EP", "HE", "IM", "SR"]

    def get_cat_query(self):

        cat_query = "%28" # open parenthesis
        for n, s in enumerate(self.subcat):
            cat_query += "astro-ph.{}".format(s)
            if n < len(self.subcat)-1:
                cat_query += "+OR+"
            else:
                cat_query += "%29"  # close parenthesis

        return cat_query

    def get_range_query(self):
        range_str = "[{}2000+TO+{}2000]".format(self.start_date.strftime("%Y%m%d"), self.end_date.strftime("%Y%m%d"))
        range_query = "lastUpdatedDate:{}".format(range_str)
        return range_query

    def get_url(self):
        cat_query = self.get_cat_query()
        range_query = self.get_range_query()

        full_query = "search_query={}+AND+{}&{}".format(cat_query, range_query, self.sort_query)

        return self.base_url + full_query

    def do_query(self, keywords=None):
        response = urllib.urlopen(self.get_url()).read()
        response = response.replace("author", "contributor")

        # this feedparser magic comes from the example of Julius Lucks / Andrea Zonca
        # https://github.com/zonca/python-parse-arxiv/blob/master/python_arXiv_parsing_example.py
        feedparser._FeedParserMixin.namespaces['http://a9.com/-/spec/opensearch/1.1/'] = 'opensearch'
        feedparser._FeedParserMixin.namespaces['http://arxiv.org/schemas/atom'] = 'arxiv'

        feed = feedparser.parse(response)

        if feed.feed.opensearch_totalresults == 0:
            sys.exit("no results found")

        results = []

        latest_id = None

        for e in feed.entries:

            arxiv_id = e.id.split("/abs/")[-1]
            title = e.title.replace("\n","")

            # the papers are sorted now such that the first is the
            # most recent -- we want to store this id, so the next
            # time we run the script, we can pick up from here
            if latest_id is None:
                latest_id = arxiv_id

            # now check if we hit the old_id -- this is where we
            # left off last time.  Note things may not be in id order,
            # so we keep looking through the entire list of returned
            # results.
            if arxiv_id < old_id:
                continue

            # link
            for l in e.links:
                if l.rel == "alternate":
                    url = l.href

            abstract = e.summary

            # any keyword matches?
            # we do two types of matches here.  If the keyword tuple has the "any"
            # qualifier, then we don't care how it appears in the text, but if
            # it has "unique", then we want to make sure only that word matches,
            # i.e., "nova" and not "supernova"
            keys_matched = []
            channels = []
            for k in keywords:
                # first check the "NOT"s
                excluded = False
                for n in k.excludes:
                    if n in abstract.lower().replace("\n", "") or n in title.lower():
                        # we've matched one of the excludes
                        excluded = True

                if excluded: continue

                if k.matching == "any":
                    if k.name in abstract.lower().replace("\n", "") or k.name in title.lower():
                        keys_matched.append(k.name)
                        channels.append(k.channel)

                elif k.matching == "unique":
                    qa = [l.lower().strip('\":.,!?') for l in abstract.split()]
                    qt = [l.lower().strip('\":.,!?') for l in title.split()]
                    if k.name in qa + qt:
                        keys_matched.append(k.name)
                        channels.append(k.channel)

            if len(keys_matched) > 0:
                results.append(Paper(arxiv_id, title, url, keys_matched, channels))

        return results, latest_id


def report(body, subject, sender, receiver):
    """ send an email """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        sm = smtplib.SMTP('localhost')
        sm.sendmail(sender, receiver, msg.as_string())
    except smtplib.SMTPException:
        sys.exit("ERROR sending mail")


def search_astroph(keywords, old_id=None):

    today = dt.date.today()
    day = dt.timedelta(days=1)

    max_papers = 1000

    # we pick a wide-enough search range to ensure we catch papers
    # if there is a holiday

    # also, something wierd happens -- the arxiv ids appear to be
    # in descending order if you look at the "pastweek" listing
    # but the submission dates can vary wildly.  It seems that some
    # papers are held for a week or more before appearing.  
    q = AstrophQuery(today - 10*day, today, max_papers, old_id=old_id)
    print(q.get_url())

    papers, last_id = q.do_query(keywords=keywords)

    papers.sort(reverse=True)

    return papers, last_id


def send_email(papers, mail=None):

    # compose the body of our e-mail
    body = ""

    # sort papers by keywords
    current_kw = None
    for p in papers:
        if not p.kw_str() == current_kw:
            current_kw = p.kw_str()
            body += "\nkeywords: {}\n\n".format(current_kw)

        body += u"{}\n".format(p)

    # e-mail it
    if not len(papers) == 0:
        if not mail is None:
            report(body.encode("ascii","replace"), "astro-ph papers of interest",
                   "lazy-astroph@localhost <lazy-astroph search>", mail)
        else:
            print(body)


def run(string):

    # shlex.split will preserve inner quotes
    prog = shlex.split(string)
    p0 = subprocess.Popen(prog, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)

    stdout0, stderr0 = p0.communicate()
    rc = p0.returncode
    p0.stdout.close()

    return stdout0, stderr0, rc


def slack_post(papers, channel_req, webhook=None):

    # loop by channel
    for c in channel_req:
        channel_body = ""
        for p in papers:
            if c in p.channels:
                if len(p.keywords) >= channel_req[c]:
                    channel_body += u"{}\n".format(p)

        if webhook is None:
            print("channel: {}".format(c))
            print(channel_body)        
            continue

        payload = {}
        payload["channel"] = c
        payload["text"] = channel_body

        cmd = "curl -X POST --data-urlencode 'payload={}' {}".format(json.dumps(payload), webhook)
        so = run(cmd)

if __name__ == "__main__":

    # parse runtime parameters
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", help="e-mail address to send report to",
                        type=str, default=None)
    parser.add_argument("inputs", help="inputs file containing keywords",
                        type=str, nargs=1)
    parser.add_argument("-w", help="file containing slack webhook URL",
                        type=str, default=None)

    args = parser.parse_args()

    # get the keywords
    keywords = []
    try: f = open(args.inputs[0], "r")
    except:
        sys.exit("ERROR: unable to open inputs file")
    else:
        channel = None
        channel_req = {}
        for line in f:
            l = line.lower().rstrip()

            if l == "":
                continue

            elif l.startswith("#"):
                # this line defines a channel
                ch = l.split()
                channel = ch[0]
                if len(ch) == 2:
                    requires = int(ch[1].split("=")[1])
                else:
                    requires = 1
                channel_req[channel] = requires

            else:
                # this line has a keyword (and optional NOT keywords)
                if "not:" in l:
                    kw, nots = l.split("not:")
                    kw = kw.strip()
                    excludes = [x.strip() for x in nots.split(",")]
                else:
                    kw = l.strip()
                    excludes = []

                if kw[len(kw)-1] == "-":
                    matching = "unique"
                    kw = kw[:len(kw)-1]
                else:
                    matching = "any"

                keywords.append(Keyword(kw, matching=matching,
                                        channel=channel, excludes=excludes))


    # have we done this before? if so, read the .lazy_astroph file to get
    # the id of the paper we left off with
    param_file = os.path.expanduser("~") + "/.lazy_astroph"
    try: f = open(param_file, "r")
    except:
        old_id = None
    else:
        old_id = f.readline().rstrip()
        f.close()

    papers, last_id = search_astroph(keywords, old_id=old_id)

    send_email(papers, mail=args.m)

    if not args.w is None:
        try: f = open(args.w)
        except: sys.exit("ERROR: unable to open webhook file")

        webhook = str(f.readline())
        f.close()

    slack_post(papers, channel_req, webhook=webhook)

    try: f = open(param_file, "w")
    except:
        sys.exit("ERROR: unable to open parameter file for writting")
    else:
        f.write(last_id)
        f.close()
