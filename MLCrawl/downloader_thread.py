import time
import threading
import logging
from urllib import robotparser, parse
from urllib.request import urlopen, Request, HTTPError, quote
import queue

from lxml.html import fromstring

from .db_model.tables import RelevantDocument

logger = logging.getLogger()

class Downloader(threading.Thread):
    RobotsParser = robotparser.RobotFileParser()
    USER_AGENT = ''
    FETCH_PDFS = None
    CHARSET = None

    def __init__(self, **kwargs):
        super().__init__()
        self.name = kwargs.get('name')
        self.tank = kwargs.get('tank')
        self.parse_queue = kwargs.get('parse_queue')
        self.crawl_queue = kwargs.get('crawl_queue')
        self.crawled = kwargs.get('crawled_set')

    def run(self):
        while not self.tank.kill_flag.is_set():
            try:
                if self.tank.has_fuel():
                    try:
                        priority, url = self.crawl_queue.get(timeout=2)
                        logger.debug('Work: {}'.format(url))
                    except queue.Empty:
                        logger.debug('Queue Empty, sleeping for a bid.')
                        time.sleep(0.1)
                        continue
                    if self.crawled.__contains__(url):
                        logger.debug("Already crawled: {}".format(url))
                        continue
                    elif not Downloader.RobotsParser.can_fetch(Downloader.USER_AGENT, url):
                        self.crawled.add(url)
                        logger.debug("robots.txt forbids to crawl: {}".format(url))
                        continue
                    redirect = True
                    redirected_urls = set()
                    while redirect == True:
                        redirected_urls.add(url)
                        url, doc_type, doc_string, timestamp, index_follow, redirect  = self._download(url)
                    for r_url in redirected_urls:
                        logger.debug('Adding {} url to crawled-set.'.format(len(redirected_urls)))
                        self.crawled.add(r_url)
                    if doc_type == None:
                        continue
                    else:
                        new_doc = RelevantDocument(
                            url = url,
                            last_fetched = timestamp,
                            type = doc_type,
                            raw_content = doc_string,
                            follow = True if index_follow == 1 else False,
                        )
                        self.parse_queue.put((new_doc, priority))
                else:
                    logger.debug('Download limit exceeded. Sleeping.')
                    time.sleep(0.1)
            except Exception as e:
                logger.error('Crash in {}: {}'.format(threading.current_thread().name, e))


        return


    def _download(self, url):
        '''Tries to download .html or .pdf document.'''
        try:
            response = urlopen(Request(quote(url, safe = ':/?=#&'), headers={'User-Agent': Downloader.USER_AGENT}))
            timestamp = time.time()
            logger.debug('Downloaded')
        except HTTPError as e:
            logger.warning('No response or timeout for {}'.format(url))
            return url, None, None, None, None, False
        self.tank.emit()
        if 'text/html' in response.getheader('Content-Type'):
            raw_html = response.read()
            index_follow_instructions = self._meta_robots_parser(raw_html)
            if index_follow_instructions == -1:
                logger.debug('Indexing and Following forbidden for {}'.format(url))
                return url, None, None, None, None, False
            redirect_instruction = fromstring(raw_html).xpath("//meta[@http-equiv = 'refresh']/@content")
            if redirect_instruction:
                url = Downloader.BASE_URL + redirect_instruction[0].split(";")[1].strip().replace("url=", "")
                return url, None, None, None, index_follow_instructions, True
            else:
                try:
                    html_decoded = raw_html.decode(Downloader.CHARSET)
                    return url, 'html', html_decoded, timestamp, index_follow_instructions, False
                except Exception as e:
                    logger.error('Error while decoding {}: {}'.format(url, e))
                    return url, None, None, None, None, False
        elif 'application/pdf' in response.getheader('Content-Type') and Downloader.FETCH_PDFS == True:
            data = response.read()
            return url, 'pdf', data, timestamp, None, False
        else:
            logger.info('Ignoring document because of Content-Type: {}'.format(url))
            return None, None, None, None, None, False


    def _meta_robots_parser(self, html):
        '''Parses meta name='robots', to check if Crawlers are allowed to index/follow'''
        instructions = fromstring(html).xpath("//meta[@name = 'robots']/@content")
        for instruction in instructions:
            if 'noindex' in [x.strip() for x in instruction.split(',')]:
                return -1
            elif 'nofollow' in [x.strip() for x in instruction.split(',')]:
                return 0
        return 1

    @classmethod
    def initialize(cls, settings, config):
        cls.USER_AGENT= config['user-agent']
        cls.FETCH_PDFS = settings.search_pdfs
        cls.BASE_URL = settings.base_url
        try:
            cls.RobotsParser.set_url(cls.BASE_URL + '/robots.txt')
            cls.RobotsParser.read()
            logger.debug("Read robots.txt at {}".format(cls.BASE_URL + '/robots.txt'))
        except Exceptions as e:
            logger.warning("Couldn't parse robots.txt at {}".format(cls.BASE_URL + '/robots.txt'))
            logger.error(e)
        if settings.charset == None:
            possible_charsets = ["UTF-8", "ISO-8859-1", "ASCII"]
            html_bytes = urlopen(Request(cls.BASE_URL, headers={'User-Agent': cls.USER_AGENT})).read()
            for encoding in possible_charsets:
                try:
                    html_bytes.decode(encoding)
                    cls.CHARSET = encoding
                except:
                    continue
            if cls.CHARSET == None:
                logger.warning('No charset could be identified on {}'.format(cls.BASE_URL))
                cls.CHARSET = input('Enter charset manually: ')
            settings.charset = cls.CHARSET
        logger.debug("Charset for {} identified: {}".format(cls.BASE_URL, cls.CHARSET))
