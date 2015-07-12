from __future__ import print_function

import datetime as dt
import urllib
import feedparser


# class to hold papers
# sort on # of categories and then on names
class Papers(object):

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

def get_cat_query():

    subcat = ["GA", "CO", "EP", "HE", "IM", "SR"]
    cat_query = "%28" # open parenthesis
    for n, s in enumerate(subcat):
        cat_query += "astro-ph.{}".format(s)
        if n < len(subcat)-1:
            cat_query += "+OR+"
        else:
            cat_query += "%29"  # close parenthesis

    return cat_query


def get_range_query():

    today = dt.date.today()
    oneday = dt.timedelta(days=1)

    today -= 4*oneday
    
    range_str = "[{}2000+TO+{}2000]".format((today-oneday).strftime("%Y%m%d"), today.strftime("%Y%m%d"))

    range_query = "lastUpdatedDate:{}".format(range_str)    
    return range_query


def doit():

    base_url = "http://export.arxiv.org/api/query?"

    cat_query = get_cat_query()
    range_query = get_range_query()
    sort_query = "max_results=1000&sortBy=submittedDate&sortOrder=descending"

    full_query = "search_query={}+AND+{}&{}".format(cat_query, range_query, sort_query)

    url = base_url + full_query

    print(url)

if __name__ == "__main__":
    doit()
