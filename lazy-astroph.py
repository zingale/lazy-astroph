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

def doit():

    today = dt.date.today()
    oneday = dt.timedelta(days=1)

    today -= 4*oneday
    
    q = AstrophQuery(today - oneday, today)
    print(q.get_url())

if __name__ == "__main__":
    doit()
