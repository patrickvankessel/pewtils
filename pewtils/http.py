from __future__ import division
from bs4 import BeautifulSoup
from builtins import str
from functools import wraps
from pewtils import get_hash, decode_text
from six.moves.urllib import parse as urlparse
from unidecode import unidecode
import re
import requests
import threading
import time
import tldextract
import warnings


def hash_url(url):

    """
    Clears out http/https prefix and returns an MD5 hash of the URL. All this does is remove http/s prefixes; it can be
    far more effective when used in conjunction with :py:func:`pewtils.http.canonical_link`.

    :param url: The URL to hash
    :type url: str
    :return: Hashed string representation of the URL using the md5 hashing algorithm.
    :rtype: str

    Usage::

        from pewtils.http import hash_url

        >>> hash_url("http://www.example.com")
        "7c1767b30512b6003fd3c2e618a86522"
        >>> hash_url("www.example.com")
        "7c1767b30512b6003fd3c2e618a86522"

    """

    http_regex = re.compile(r"^http(s)?\:\/\/")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = get_hash(
            unidecode(http_regex.sub("", url.lower())), hash_function="md5"
        )
        return result


def strip_html(html, simple=False, break_tags=None):

    """
    Attempts to strip out HTML code from an arbitrary string while preserving meaningful text components.

    | By default, the function will use BeautifulSoup to parse the HTML and try to parse out text from the document \
    using a process that we have found to work fairly well. Setting `simple=True` will make the function use \
    a much simpler regular expression approach to parsing.

    .. note:: This function isn't always 100% effective, but it does a decent job of usually removing the vast \
    majority of HTML without stripping out valuable content.

    :param html: The HTML to process
    :type html: str
    :param simple: Whether or not to use a simple regex or more complex parsing rules (default=False)
    :type simple: bool
    :param break_tags: A custom list of tags on which to break (default is ["strong", "em", "i", "b", "p"])
    :type break_tags: list
    :return: The text with HTML components removed (perfection not guaranteed)
    :rtype: str

    Usage::

        from pewtils.http import strip_html

        >>> my_html = "<html><head>Header text</head><body>Body text</body></html>"
        >>> strip_html(my_html)
        'Header text\n\nBody text'

    """

    html = re.sub(r"\n", " ", html)
    html = re.sub(r"\s+", " ", html)
    if not break_tags:
        break_tags = ["strong", "em", "i", "b", "p"]
    if not simple:
        try:

            split_re = re.compile(r"\s{2,}")
            soup = BeautifulSoup(html, "lxml")
            for tag in soup():
                if (
                    "class" in tag.attrs
                    and ("menu" in tag.attrs["class"] or "header" in tag.attrs["class"])
                ) or ("menu" in str(tag.id) or "header" in str(tag.id)):
                    tag.extract()
            for tag in soup(["script", "style"]):
                tag.extract()
            for br in soup.find_all("br"):
                br.replace_with("\n")
            for t in soup(break_tags):
                try:
                    t.replace_with("\n{0}\n".format(t.text))
                except (UnicodeDecodeError, UnicodeEncodeError):
                    t.replace_with("\n{0}\n".format(decode_text(t.text)))
            if hasattr(soup, "body") and soup.body:
                text = soup.body.get_text()
            else:
                text = soup.get_text()
            lines = [l.strip() for l in text.splitlines()]
            lines = [l2.strip() for l in lines for l2 in split_re.split(l)]
            text = "\n".join([l for l in lines if l])
            text = re.sub(r"(\sA){2,}\s", " ", text)
            text = re.sub(r"\n+(\s+)?", "\n\n", text)
            text = re.sub(r" +", " ", text)
            text = re.sub(r"\t+", " ", text)

            return text

        except Exception as e:

            print("strip_html error")
            print(e)
            text = re.sub(r"<[^>]*>", " ", re.sub("\\s+", " ", html)).strip()
            return text

    else:
        return "\n".join(
            [
                re.sub(r"\s+", " ", re.sub(r"\<[^\>]+\>", " ", section))
                for section in re.sub(r"\<\/?div\>|\<\/?p\>|\<br\>", "\n", html).split(
                    "\n"
                )
            ]
        )


GENERAL_LINK_SHORTENERS = [
    "wp.me",
    "trib.al",
    "t.co",
    "spr.ly",
    "shout.lt",
    "shar.es",
    "scr.bi",
    "ow.ly",
    "ora.cl",
    "is.gd",
    "ht.ly",
    "goo.gl",
    "fw.to",
    "dlvr.it",
    "cutt.ly",
    "buff.ly",
    "j.mp",
    "hubs.ly",
    "bit.ly",
    "hub.am",
    "ht.ly",
    "every.tw",
    "crwd.fr",
    "bit.do",
    "snp.tv",
    "snip.ly",
    "shr.gs",
    "qoo.ly",
    "po.st",
    "fwdaga.in",
    "fw.to",
    "tiny.cc",
    "owl.li",
    "mvnt.us",
    "msgp.pl",
    "flip.it",
    "urlm.in",
    "trib.it",
    "shoo.ly",
    "loom.ly",
    "disq.us",
    "abre.ai",
    "bit.do",
    "adf.ly",
    "su.pr",
]
"""
A list of known generic URL shorteners
"""

VANITY_LINK_SHORTENERS = {
    "pdora.co": "pandora.com",
    "tgam.ca": "theglobeandmail.com",
    "stjr.nl": "statesmanjournal.com",
    "amzn.com": "amazon.com",
    "meetu.ps": "meetup.com",
    "flic.kr": "flickr.com",
    "ampr.gs": "americanprogress.org",
    "rol.st": "rollingstone.com",
    "mapq.st": "mapquest.com",
    "newspr.es": "news-press.com",
    "interc.pt": "theintercept.com",
    "ind.pn": "independent.co.uk",
    "bizj.us": "bizjournals.com",
    "pewrsr.ch": "pewresearch.org",
    "on.fb.me": "facebook.com",
    "fb.me": "facebook.com",
    "dbtg.tv": "bundestag.de",
    "m.me": "messenger.com",
    "trib.in": "chicagotribune.com",
    "wtrne.ws": "timesrecordnews.com",
    "icont.ac": "icontact-archive.com",
    "entm.ag": "entrepreneur.com",
    "engt.co": "engadget.com",
    "nyti.ms": "nytimes.com",
    "gph.is": "giphy.com",
    "fxn.ws": "foxnews.com",
    "conta.cc": "constantcontact.com",
    "wh.gov": "whitehouse.gov",
    "harlem.in": "harlemunited.org",
    "n.pr": "npr.org",
    "apne.ws": "apnews.com",
    "ap.org": "apnews.com",
    "youtu.be": "youtube.com",
    "grnol.co": "greenvilleonline.com",
    "washex.am": "washingtonexaminer.com",
    "usat.ly": "usatoday.com",
    "cbsloc.al": "cbslocal.com",
    "cbsn.ws": "cbsnews.com",
    "bloom.bg": "bloomberg.com",
    "wtr.ie": "water.ie",
    "reut.rs": "reuters.com",
    "ti.me": "time.com",
    "politi.co": "politico.com",
    "cnn.it": "cnn.com",
    "bzfd.it": "buzzfeed.com",
    "bcove.me": "brightcove.com",
    "c-spanvideo.org": "c-span.org",
    "lat.ms": "latimes.com",
    "nbcnews.to": "nbcnews.com",
    "ab.co": "abc.net.au",
    "onforb.es": "forbes.com",
    "nwsdy.li": "newsday.com",
    "spon.de": "spiegel.de",
    "mol.im": "dailymail.co.uk",
    "theatln.tc": "theatlantic.com",
    "yhoo.it": "yahoo.com",
    "jrnl.ie": "thejournal.ie",
    "sen.gov": "senate.gov",
    "es.pn": "espn.com",
    "wrd.cm": "wired.com",
    "cour.at": "courant.com",
    "read.bi": "businessinsider.com",
    "dailysign.al": "dailysignal.com",
    "buswk.co": "bloomberg.com",
    "cnnmon.ie": "cnn.com",
    "cnb.cx": "cnbc.com",
    "atxne.ws": "statesman.com",
    "slate.me": "slate.com",
    "detne.ws": "detroitnews.com",
    "injo.com": "ijr.com",
    "njersy.co": "northjersey.com",
    "nj-ne.ws": "nj.com",
    "amzn.to": "amazon.com",
    "fb.com": "facebook.com",
    "lnkd.in": "linkedin.com",
    "linkd.in": "linkedin.com",
    "histv.co": "history.com",
    "mailchi.mp": "mailchimp.com",
    "indy.st": "indystar.com",
    "strib.mn": "startribune.com",
    "nydn.us": "nydailynews.com",
    "bsun.md": "baltimoresun.com",
    "bayareane.ws": "eastbaytimes.com",
    "thebea.st": "thedailybeast.com",
    "dmreg.co": "desmoinesregister.com",
    "bernie.to": "berniesanders.com",
    "dpo.st": "denverpost.com",
    "delonline.us": "delawareonline.com",
    "azc.cc": "azcentral.com",
    "goldenisles.news": "thebrunswicknews.com",
    "ohne.ws": "newarkadvocate.com",
    "thkpr.gs": "thinkprogress.org",
    "wef.ch": "weforum.org",
    "comsen.se": "commonsensemedia.org",
    "huffpost.com": "huffingtonpost.com",
    "huffp.st": "huffingtonpost.com",
    "huff.to": "huffingtonpost.com",
    "bbc.in": "bbc.co.uk",
    "brook.gs": "brookings.edu",
    "lp.ca": "lapresse.ca",
    "virg.in": "virgin.com",
    "hill.cm": "thehill.com",
    "tnw.to": "thenextweb.com",
    "dailym.ai": "dailymail.co.uk",
    "instagr.am": "instagram.com",
    "chng.it": "change.org",
    "tws.io": "weeklystandard.com",
    "spoti.fi": "spotify.com",
    "nyp.st": "nypost.com",
    "bv.ms": "bloomberg.com",
    "glo.bo": "globo.com",
    "gizmo.do": "gizmodo.com",
    "prn.to": "prnewswire.com",
    "usm.ag": "usmagazine.com",
    "txnne.ws": "thetexan.news",
    "u.pw": "upworthy.com",
    "ihr.fm": "iheart.com",
    "hulu.tv": "hulu.com",
    "herit.ag": "heritage.org",
    "econ.st": "economist.com",
    "dai.ly": "dailymotion.com",
    "chn.ge": "change.org",
    "ble.ac": "bleacherreport.com",
    "aje.io": "aljazeera.com",
}
"""
A list of known URL shorteners for specific websites (primarily news websites)
"""

HISTORICAL_VANITY_LINK_SHORTENERS = {
    "nws.mx": "newsmax.com",
    "tonyr.co": "tonyrobbins.com",
    "d-news.co": "dallasnews.com",
    "fanda.co": "fandango.com",
    "uni.vi": "univision.com",
    "jwatch.us": "judicialwatch.org",
    "nm.us": "state.nm.us",
    "hrld.us": "miamiherald.com",
    "ma.us": "state.ma.us",
    "nyer.cm": "newyorker.com",
    "ny.us": "state.ny.us",
    "ptrtvoic.es": "patriotvoices.com",
    "cjky.it": "courier-journal.com",
    "md.us": "state.md.us",
    "pa.us": "state.pa.us",
    "g.co": "google.com",
    "mn.us": "state.mn.us",
    "hrld.us": "miamiherald.com",
    "oh.us": "state.oh.us",
    "ofa.bo": "ofa.us",
    "dot.gov": "transportation.gov",
    "wapo.st": "washingtonpost.com",
    "hrld.us": "miamiherald.com",
    "wpo.st": "washingtonpost.com",
    "abcn.ws": "abcnews.com",
    "cs.pn": "c-span.org",
}

VANITY_LINK_SHORTENERS.update(HISTORICAL_VANITY_LINK_SHORTENERS)


def canonical_link(url, timeout=5.0, session=None, user_agent=None):

    """
    Tries to resolve a link to the "most correct" version. Useful for expanding short URLs from bit.ly / Twitter \
    and for checking HTTP status codes without retrieving the actual data. Follows redirects and tries to pick the \
    most informative version of a URL while avoiding redirects to generic 404 pages. Also tries to iteratively remove \
    optional GET parameters. This function may not be particularly effective on dead links, but may still be able \
    to follow redirects enough to return a URL with the correct domain associated with the original link.

    .. note:: This function is not perfect but it has been tested on a wide variety of URLs and resolves \
    to the correct final page in most cases while (usually) avoiding redirects to generic error pages.

    :param url: The URL to test. Should be fully qualified.
    :type url: str
    :param timeout: How long to wait for a response before giving up (default is one second)
    :type timeout: int or float
    :param session: (Optional) A persistent session that can optionally be passed (useful if you're processing many \
    links at once)
    :type session: :py:class:`requests.Session` object
    :param user_agent: User agent for the auto-created requests Session to use, if a preconfigured requests Session \
    is not provided
    :type user_agent: str
    :return: The "canonical" URL as supplied by the server, or the original URL if the server was not helpful.
    :rtype: str

    Usage::

        from pewtils.http import canonical_link

        >>> canonical_link("https://pewrsr.ch/2lxB0EX")
        "https://www.pewresearch.org/interactives/how-does-a-computer-see-gender/"

    """

    BAD_STATUS_CODES = [
        302,
        307,
        400,
        404,
        405,
        407,
        500,
        501,
        502,
        503,
        504,
        520,
        530,
        404,
    ]
    PROXY_REQUIRED = [307, 407]
    CHECK_LENGTH = [301, 302, 200, 404]

    close_session = False
    if not session:
        close_session = True
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})
    if not url.startswith("http"):
        url = "http://" + url
    response = None
    try:
        response = session.head(url, allow_redirects=True, timeout=timeout)
    except requests.ConnectionError:
        try:
            response = session.head(url, allow_redirects=False, timeout=timeout)
        except:
            pass
    except:
        pass

    if response != None:

        history = [(h.status_code, h.url) for h in response.history]
        history.append((response.status_code, response.url))

        last_good_url = history[0][1]
        original_parsed = urlparse.urlparse(last_good_url)
        has_path = original_parsed.path not in ["/", ""]
        has_query = original_parsed.query != ""
        prev_was_shortener = False
        prev_path = None
        prev_query = None
        for i, resp in enumerate(history):
            status_code, response_url = resp
            if "errors/404" in response_url:
                # If it's clearly a 404 landing page, stop and use the last observed good URL
                break
            parsed = urlparse.urlparse(response_url)
            if (
                parsed.netloc in VANITY_LINK_SHORTENERS.keys()
                or parsed.netloc in GENERAL_LINK_SHORTENERS
            ):
                # Don't consider known shortened URLs
                is_shortener = True
            else:
                is_shortener = False
            if not is_shortener:
                if i != 0:
                    for param, val in urlparse.parse_qs(parsed.query).items():
                        if len(val) == 1 and val[0].startswith("http"):
                            parsed_possible_url = urlparse.urlparse(val[0])
                            if (
                                parsed_possible_url.scheme
                                and parsed_possible_url.netloc
                            ):
                                # If the URL contains a GET parameter that is, itself, a URL, it's likely redirecting to it
                                # So we're going to stop this run and start the process over with the new URL
                                return canonical_link(
                                    val[0],
                                    timeout=timeout,
                                    session=session,
                                    user_agent=user_agent,
                                )
                if status_code in PROXY_REQUIRED:
                    # These codes tend to indicate the last good URL in the chain
                    last_good_url = response_url
                    break
                good_path = not has_path or parsed.path not in ["/", ""]
                good_query = not has_query or parsed.query != ""
                # If the URL has a path or some GET parameters, we'll inspect further
                # Otherwise we just go with the previous URL
                # Link shorteners are very rarely used to reference root domains
                if good_query or good_path:
                    if (
                        re.sub("https", "http", response_url)
                        == re.sub("https", "http", last_good_url)
                        or parsed.path == original_parsed.path
                    ) or response_url.lower() == last_good_url.lower():
                        # If it's the same link but only the domain, protocol, or casing changed, it's fine
                        last_good_url = response_url
                    elif i != 0 and status_code in CHECK_LENGTH:
                        # For these codes, we're going to see how much the link changed
                        # Redirects and 404s sometimes preserve a decent URL, sometimes they go to a landing page
                        # The following cutoffs seem to do a good job most of the time:
                        # 1) The new URL has a long domain more than 7 characters, so it's not likely a shortened URL
                        # 2) The prior URL had a long path and this one has fewer than 20 characters and it wasn't swapped out for GET params
                        # 3) Or the prior URL had GET params and this one has far fewer and no replacement path
                        # If these conditions are met and the path or query do not identically match the prior link
                        # Then it's usually a generic error page
                        bad = False
                        if (
                            has_path
                            and len(parsed.netloc) > 7
                            and len(parsed.path) < 20
                            and len(parsed.query) == 0
                            and prev_path != parsed.path
                        ) or (
                            has_query
                            and len(parsed.netloc) > 7
                            and len(parsed.query) < 20
                            and len(parsed.path) <= 1
                            and prev_query != parsed.query
                        ):
                            bad = True
                        if not bad or prev_was_shortener:
                            last_good_url = response_url
                            # print("GOOD: {}, {}".format(status_code, response_url))
                        else:
                            # These can sometimes resolve further though, so we continue onward
                            prev_path = None
                            prev_query = None
                    else:
                        if status_code not in BAD_STATUS_CODES:
                            last_good_url = response_url
                        else:
                            break
                else:
                    # Resolved to a general URL
                    break

            prev_was_shortener = is_shortener
            prev_path = parsed.path
            prev_query = parsed.query

        if status_code not in BAD_STATUS_CODES:
            # If the URL ended on a good status code, we'll try to trim out any unnecessary GET parameters
            last_good_url = trim_get_parameters(
                last_good_url, session=session, timeout=timeout, user_agent=user_agent
            )

        url = last_good_url

    if close_session:
        session.close()

    return url


def trim_get_parameters(url, session=None, timeout=30, user_agent=None):

    """
    Takes a URL (presumed to be the final end point) and iterates over GET parameters, attempting to find optional
    ones that can be removed without generating any redirects.

    :param url: The URL to trim
    :type url: str
    :param session: (Optional) A persistent session that can optionally be passed (useful if you're processing many \
    links at once)
    :type session: :py:class:`requests.Session` object
    :param user_agent: User agent for the auto-created requests Session to use, if a preconfigured requests Session \
    is not provided
    :type user_agent: str
    :param timeout: Timeout for requests
    :type timeout: int or float
    :return: The original URL with optional GET parameters removed
    :rtype: str

    Usage::

        from pewtils.http import trim_get_parameters

        >>> trim_get_parameters("https://httpbin.org/status/200?param=1")
        "https://httpbin.org/status/200"

    """

    close_session = False
    if not session:
        close_session = True
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})

    # Often there's extra information about social sharing and referral sources that can be removed
    ditch_params = []
    parsed = urlparse.urlparse(url)
    if parsed.query:
        params = urlparse.parse_qs(parsed.query)
        for k, v in params.items():
            # We iterate over all of the GET parameters and try holding each one out
            check = True
            for skipper in ["document", "article", "id", "qs"]:
                # If the parameter is named something that's probably a unique ID, we'll keep it
                if skipper in k.lower():
                    check = False
            for skipper in ["html", "http"]:
                # Same goes for parameters that contain URL information
                if skipper in v[0].lower():
                    check = False
            if check:
                new_params = {
                    k2: v2[0] for k2, v2 in params.items() if k2 != k and len(v2) == 1
                }
                new_params = urlparse.urlencode(new_params)
                new_parsed = parsed._replace(query=new_params)
                new_url = urlparse.urlunparse(new_parsed)
                resp = session.head(new_url, allow_redirects=True, timeout=timeout)
                new_parsed = urlparse.urlparse(resp.url)
                if new_parsed.query != "" or new_parsed.path not in ["", "/"]:
                    # If removing a parameter didn't redirect to a root domain...
                    new_url = resp.url
                    compare_new = new_url.split("?")[0] if "?" in new_url else new_url
                    compare_old = url.split("?")[0] if "?" in url else url
                    if compare_new == compare_old:
                        # And the domain is the same as it was before, then the parameter was probably unnecessary
                        ditch_params.append(k)

    if len(ditch_params) > 0:
        # Now we remove all of the unnecessary get parameters and finalize the URL
        new_params = {
            k: v[0] for k, v in params.items() if len(v) == 1 and k not in ditch_params
        }
        new_params = urlparse.urlencode(new_params)
        parsed = parsed._replace(query=new_params)
        url = urlparse.urlunparse(parsed)

    if close_session:
        session.close()

    return url


def extract_domain_from_url(
    url,
    include_subdomain=True,
    resolve_url=False,
    timeout=1.0,
    session=None,
    user_agent=None,
):

    """
    Attempts to extract a standardized domain from a url by following the link and extracting the TLD.

    .. note:: If you set `resolve_url` to True, the link will be standardized prior to extracting the domain (in which \
    case you can provide optional timeout, session, and user_agent parameters that will be passed to `canonical_link). \
    By default, however, the link will be operated on as-is. The final extracted domain is then checked against known \
    URL vanity shorteners (see :py:data:`pewtils.http.VANITY_LINK_SHORTENERS`) and if it is recognized, the expanded \
    domain will be returned instead. Shortened URLs that are not standardized and do not follow patterns included in \
    this dictionary of known shorteners may be returned with an incorrect domain.


    :param url:  The link from which to extract the domain
    :type url: str
    :param include_subdomain: Whether or not to include the subdomain (e.g. 'news.google.com'); default is True
    :type include_subdomain: bool
    :param resolve_url: Whether to fully resolve the URL.  If False (default), it will operate on the URL as-is; if \
    True, the URL will be passed to :py:func:`pewtils.http.canonical_link` to be standardized prior to extracting the \
    domain.
    :param timeout: (Optional, for use with `resolve_url`) Maximum number of seconds to wait on a request before \
    timing out (default is 1)
    :type timeout: int or float
    :param session: (Optional, for use with `resolve_url`) A persistent session that can optionally be passed \
    (useful if you're processing many links at once)
    :type session: :py:class:`requests.Session` object
    :param user_agent: (Optional, for use with `resolve_url`) User agent for the auto-created requests Session to use, \
    if a preconfigured requests Session is not provided
    :type user_agent: str
    :return: The domain for the link
    :rtype: str

    Usage::

        from pewtils.http import extract_domain_from_url

        >>> extract_domain_from_url("http://forums.bbc.co.uk", include_subdomain=False)
        "bbc.co.uk"
        >>> extract_domain_from_url("http://forums.bbc.co.uk", include_subdomain=True)
        "forums.bbc.co.uk"

    """

    if resolve_url:
        url = canonical_link(
            url, timeout=timeout, session=session, user_agent=user_agent
        )
    domain = tldextract.extract(url)
    if domain:
        if include_subdomain and domain.subdomain and domain.subdomain != "www":
            domain = ".".join([domain.subdomain, domain.domain, domain.suffix])
        else:
            domain = ".".join([domain.domain, domain.suffix])
        domain = VANITY_LINK_SHORTENERS.get(domain, domain)
    return domain
