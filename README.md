# about lazy_astroph.py

This is a simple script to get the latest papers from astro-ph/arxiv,
search their abstracts and titles for keywords, and report the
results.  Reports are done either through e-mail or by posting to
slack/discord channels using web-hooks.  This way if we forget to read
astro-ph for a bit, we can atleast get notified of the papers deemed
important to us (and discuss them on slack).

Note: this requires python 3

## usage

```
./lazy_astroph.py [-m e-mail-address] [-w webhook-file] inputs
```

where `inputs` is a file of (case-insensitive) keywords, one per
line.  Note, ending a keyword with "-" will make sure that keyword
is uniquely matched, and not embedded in another keyword.  Adding
a clause "NOT:" to a keyword line followed by common-separated
terms will result in a match only if the terms following NOT are
not found

E.g.,

```
supernova               NOT: dark energy, interstellar medium, ISM
nova-
xrb
```

will return the matching papers containing "supernova", so long as
they don't also contain "dark energy", "interstellar medium", or
"ISM".  It will also return papers that contain "nova" distinct from
"supernova" (since `"nova" in "supernova"` is `True` in python).
And it will return those papers containing xrb.

Slack/Discord channels are indicated by a line beginning with "#",
with an optional "requires=N", where N is the number of keywords
we must match before posting a paper to a channel.
Discord channels must be specified using their channel ID, not
the channel name.

You need to create a webhook via slack or discord.  Put the URL
into a file (just the URLs, nothing else) and then pass the name
of that file into `lazy_astroph.py` using the `-w` parameter.


## automating

To have this run nightly, add a line to your crontab.  Assuming that
you've put the `lazy_astroph.py` script and an `inputs` file in your
~/bin/, then do something like:

```
crontab -e
```

add a new line with:

```
00 04 * * * /home/username/bin/lazy_astroph.py -m me@something.edu /home/username/bin/inputs
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

   
