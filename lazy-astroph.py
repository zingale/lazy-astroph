#!/usr/bin/env python

from __future__ import print_function

import argparse
import datetime as dt
import feedparser
import os
import smtplib
import sys
import urllib
from email.mime.text import MIMEText

# class to hold a paper
# sort on # of categories and then on names
class Paper(object):

    def __init__(self, arxiv_id, title, url, keywords):
        self.arxiv_id = arxiv_id
        self.title = title
        self.url = url
        self.keywords = list(keywords)

    def __str__(self):
        return u"{} : {}\n  {}\n".format(self.arxiv_id, self.title, self.url)

    def kw_str(self):
        return ", ".join(self.keywords)

    def __cmp__(self, other):
        if len(self.keywords) == len(other.keywords):
            return cmp(self.kw_str(), other.kw_str())
        else:
            return cmp(len(self.keywords), len(other.keywords))


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
            # left off last time
            if arxiv_id == old_id:
                break

            # link
            for l in e.links:
                if l.rel == "alternate":
                    url = l.href

            abstract = e.summary

            # any keyword matches?
            keys_matched = []
            for k in keywords:
                if k in abstract.lower().replace("\n", "") or k in title.lower():
                    keys_matched.append(k)
                    continue

            if len(keys_matched) > 0:
                results.append(Paper(arxiv_id, title, url, keys_matched))

        return results, latest_id


def report(body, subject, sender, receiver):
    """ send an email """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receiver, msg.as_string())
    except smtp.SMTPException:
        sys.exit("ERROR sending mail")


def search_astroph(keywords, old_id=None, mail=None):

    today = dt.date.today()
    day = dt.timedelta(days=1)

    max_papers = 1000

    # we pick a wide-enough search range to ensure we catch papers
    # if there is a holiday
    q = AstrophQuery(today - 5*day, today, max_papers, old_id=old_id)
    print(q.get_url())

    papers, last_id = q.do_query(keywords=keywords)

    papers.sort(reverse=True)

    # compose the body of our e-mail
    body = ""

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

    return last_id


if __name__ == "__main__":

    # parse runtime parameters
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", help="e-mail address to send report to",
                        type=str, default=None)
    parser.add_argument("inputs", help="inputs file containing keywords",
                        type=str, nargs=1)

    args = parser.parse_args()

    # get the keywords
    keywords = []
    try: f = open(args.inputs[0], "r")
    except:
        sys.exit("ERROR: unable to open inputs file")
    else:
        for line in f:
            keywords.append(line.lower().rstrip())

    # have we done this before? if so, read the .lazy_astroph file to get
    # the id of the paper we left off with
    param_file = os.path.expanduser("~") + "/.lazy_astroph"
    try: f = open(param_file, "r")
    except:
        old_id = None
    else:
        old_id = f.readline().rstrip()
        f.close()

    last_id = search_astroph(keywords, old_id=old_id, mail=args.m)

    try: f = open(param_file, "w")
    except:
        sys.exit("ERROR: unable to open parameter file for writting")
    else:
        f.write(last_id)
        f.close()
