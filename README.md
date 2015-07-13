# about lazy-astroph.py

This is a simple script to get the latest papers from astro-ph/arxiv
and search their abstracts and titles for keywords and mail a report
of the papers matching those keys.  This way if we forget to read
astro-ph for a bit, we can atleast get notified of the papers deemed
important to us.

## usage

```
./lazy-astroph.py -m e-mail-address inputs
```

where `inputs` is just a file of (case-insensitive) keywords, one per
line.

## automating

To have this run nightly, add a line to your crontab.  Assuming that
you've put the `lazy-astroph.py` script and an `inputs` file in your
~/bin/, then do something like:

```
crontab -e
```

add a new line with:

```
00 04 * * * /home/username/bin/lazy-astroph.py -m me@something.edu /home/username/bin/inputs
```

replacing the e-mail with your e-mail and `username` with your username.


# arXiv appearance dates

articles appear according to the following schedule:

  ```
  submitted                    appear

  Th 20:00 -> F  19:59           M
  F  20:00 -> M  19:59           Tu
  M  20:00 -> Tu 19:59           W
  Tu 20:00 -> W  19:59           Th
  W  20:00 -> Th 19:59           F
  ```
  
  but note that holidays can throw this off by a day or so.

A possible solution is to store in a config file the id of the last
paper parsed and then start each day by requesting 1000 papers leading
up to today and go back only until we hit the previously parsed paper.


# inspiration

* The basic feedparser mechanism of interacting with the arxiv API
came from this example:

   https://github.com/zonca/python-parse-arxiv/blob/master/python_arXiv_parsing_example.py

* The instructions on how to search by date range came from the arxiv API google group:

   https://groups.google.com/forum/#!msg/arxiv-api/I95YLIPesSE/3MZ83Pq_cugJ

   https://groups.google.com/forum/#!searchin/arxiv-api/lastupdateddate/arxiv-api/GkTlg6tikps/C-E5noLbu94J

   
