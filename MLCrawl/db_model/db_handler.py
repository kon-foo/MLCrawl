import time
import multiprocessing
import queue
import logging

from sqlalchemy.orm import sessionmaker

from .tables import *
from .database import initialize_db

logger = logging.getLogger()

class DBHandler(multiprocessing.Process):
    def __init__(self, db_config, root_dir, crawl_id, initial_crawl_settings, save_queue, db_ready, kill_flag, found):
        super().__init__()
        self.engine = initialize_db(db_config, root_dir)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

        self.crawl_id = crawl_id
        self.crawl_settings = None
        self.loaded_queue = set()
        self.loaded_crawled = set()
        if self.crawl_id == None:
            self.crawl_settings = self.new_crawl(initial_crawl_settings)
        else:
            self.crawl_settings = self.load_crawl(crawl_id)
        self.kill_flag = kill_flag
        self.found = found
        self.save_queue = save_queue
        db_ready.set()

    def run(self):
        session = self.Session()
        while not self.kill_flag.is_set():
            try:
                to_save = self.save_queue.get(timeout=1)
                to_save.crawl_id = self.crawl_id
                session.add(to_save)
                session.commit()
                if to_save.__tablename__ == 'relevant_documents':
                    with self.found.get_lock():
                        self.found.value += 1
                logger.debug('Saved one {} to {}'.format(to_save.__class__.__name__, to_save.__tablename__))
            except queue.Empty:
                continue
        return

    def new_crawl(self, settings):
        session = self.Session()
        current_crawl = Crawl(name=settings['name'],
                              base_url=settings['full_url'],
                              started=time.time(),
                              last_change=time.time(),
                              search_singledomain=settings['search_single_domain'],
                              search_subdomains=settings['search_subdomains'],
                              search_pdfs=settings['search_pdfs'],
                              )
        session.add(current_crawl)
        session.commit()
        self.crawl_id = current_crawl.id
        return current_crawl

    def load_crawl(self, crawl_id):
        tmp_set = set()
        session = self.Session()
        current_crawl = session.query(Crawl).filter_by(id=crawl_id).first()
        self.crawl_id = current_crawl.id
        for crawled_url in current_crawl.crawled_urls:
            self.loaded_crawled.add(crawled_url.url)
            tmp_set.add(crawled_url.url)
        for queue_url in current_crawl.queued_urls:
            if queue_url.url not in tmp_set:
                self.loaded_queue.add((queue_url.priority, queue_url.url))
        session.commit()
        return current_crawl
