import multiprocessing
import logging
import time
import queue

logger = logging.getLogger()

from .relevance_models.build import build_model
from .relevance_models.assesment_model import RelAssesment

class Parser(multiprocessing.Process):
    THRESHOLD = None
    PARSE_SUBDOMAINS = None
    CRAWL_SINGLE_DOMAIN = None
    MAX_DEPTH = None
    RelevanceModel = None

    def __init__(self, **kwargs):
        super().__init__()
        self.kill_flag = kwargs.get('kill')
        self.to_do_queue = kwargs.get('todo')
        self.save_queue = kwargs.get('save_q')
        self.to_download_queue = kwargs.get('priority_queue')
        self.crawled = kwargs.get('crawled_set')
        #self.relevance_model = kwargs.get('relevance_model')
        return

    @classmethod
    def initialize(cls, settings, config, root_dir):
        cls.THRESHOLD = config['General']['threshold']
        cls.CRAWL_SINGLE_DOMAIN = settings.search_singledomain
        cls.PARSE_SUBDOMAINS = settings.search_subdomains
        cls.MAX_DEPTH = config['General']['search_depth']
        cls.RelevanceModel = RelAssesment
        # build_model(config, root_dir)


    def run(self):
        while not self.kill_flag.is_set():
            logger.debug('Parse Start: {} to do'.format(self.to_do_queue.qsize()))
            try:
                document, parent_priority = self.to_do_queue.get(timeout=2)
            except queue.Empty:
                continue
            try:
                if document.type == 'html':
                    logger.debug('HTML Parser working on doc with size {}'.format(len(document.raw_content)))
                    document.content = self.RelevanceModel.html_to_text(document.raw_content)
                    logger.debug('GOT CONTENT')
                else:
                    document.content = self.RelevanceModel.pdf_to_text(document.raw_content)
            except Exception as e:
                logger.error("Error while extracting text: {}".format(e))
                document.content = ''
                logger.debug('NO CONTENT')
            try:
                document.relevance = self.RelevanceModel.classify_text(document.content)
                logging.debug('Predicted relevance: {}'.format(document.relevance))
            except Exception as e:
                logging.error('Error while predicting relevance: {}'.format(e))
                logging.debug(document.url)
            if document.relevance > Parser.THRESHOLD:
                own_priority = 1
            else:
                own_priority = parent_priority + 1
            if own_priority < self.MAX_DEPTH and document.type == 'html':
                internal, sub, external = self.RelevanceModel.extract_links(document.raw_content, document.url)
                logger.debug('Adding {} internal links to crawl queue.'.format(len(internal)))
                for url in internal:
                    self.add_link(url, own_priority)
                if self.CRAWL_SINGLE_DOMAIN == False:
                    logger.debug('Adding {} external links to crawl queue.'.format(len(external)))
                    for url in external:
                        self.add_link(url, own_priority)
                if self.PARSE_SUBDOMAINS == True:
                    logger.debug('Adding {} sub_domain links to crawl queue.'.format(len(sub)))
                    for url in sub:
                        self.add_link(url, own_priority)
            if document.relevance > Parser.THRESHOLD:
                self.save_queue.put(document)
            else:
                del document
        return

    def add_link(self, link, priority):
        if not self.crawled.__contains__(link):
            self.to_download_queue.put((priority, link))
