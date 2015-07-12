from __future__ import print_function

import datetime as dt
import feedparser
import sys
import urllib

# class to hold papers
# sort on # of categories and then on names
class Paper(object):

    def __init__(self, arxiv_id, title, url, keywords):
        self.arxiv_id = arxiv_id
        self.title = title
        self.url = url
        self.keywords = list(keywords)

    def __str__(self):
        return "{} : {}\n  {}\n".format(self.arxiv_id, title, url)

    def kw_str(self):
        return " ".join(self.keywords)

    def __cmp__(self, other):
        if len(self.keywords) == len(other.keywords):
            return cmp(self.kw_str(), other.kw_str())
        else:
            return cmp(len(self.keywords), len(other.keywords))


class AstrophQuery(object):

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

        self.base_url = "http://export.arxiv.org/api/query?"
        self.sort_query = "max_results=1000&sortBy=submittedDate&sortOrder=descending"

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

        feedparser._FeedParserMixin.namespaces['http://a9.com/-/spec/opensearch/1.1/'] = 'opensearch'
        feedparser._FeedParserMixin.namespaces['http://arxiv.org/schemas/atom'] = 'arxiv'

        feed = feedparser.parse(response)

        if feed.feed.opensearch_totalresults == 0:
            sys.exit("no results found")

        results = []

        for e in feed.entries:

            arxiv_id = e.id.split("/abs/")[-1]
            title = e.title

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

        return results


def doit():

    keywords = ["supernova", "x-ray burst", "nova", "progenitor",
                "code", "gpu", "flash", "castro", "maestro", "hydro", "MHD", "anelastic", "low mach"
                "flame", "deflagration", "turbulence", "detonation", 
                "adaptive mesh refinement", "AMR"]
    
    today = dt.date.today()
    oneday = dt.timedelta(days=1)

    today -= 4*oneday

    q = AstrophQuery(today - oneday, today)
    print(q.get_url())

    papers = q.do_query(keywords=keywords)

    papers.sort(reverse=True)
    
    for p in papers:
        print(p.title, p.keywords)
        print(" ")

if __name__ == "__main__":
    doit()
