import os
import sys
import time
import signal
import datetime
import multiprocessing

import yaml
import mp_throttle

from .initialize_logger import init_logging
from .downloader_thread import Downloader
from .parser_process import Parser
from .data_models import DataManager
from .db_model.db_handler import DBHandler
from .db_model.tables import CrawledUrl, QueuedUrl
from .relevance_models.build import build_model



ROOT_DIR = os.getcwd()


class Crawler():
    def __init__(self, *args, **kwargs):
        if 'config_file' in kwargs:
            with open(os.path.join(ROOT_DIR, kwargs.get('config_file')), 'r') as c_file:
                self.config = yaml.load(c_file)
        self.logger = init_logging(self.config['Logging'], os.path.join(ROOT_DIR, self.config['Logging']['logging_folder']))
        self.throttle = mp_throttle.Throttle(self.config['Downloader']['crawls_per_second'], 1, auto_emit=False)

        #self.RelevanceModel = RelAssesment()
        self.db = None
        self.crawl_queue = DataManager.PriorityQueue()
        self.parse_queue = multiprocessing.Queue()
        self.save_queue = multiprocessing.Queue()
        self.crawled_set = DataManager.ThreadSafeSet()

        self.crawl_settings = None
        self.running_processes = []
        self.running_threads = []
        self.db_shutdown = multiprocessing.Event()
        self.found = multiprocessing.Value('i')

    def initialize(self, crawl_id = None, crawl_settings = None, start_urls = []):
        '''Initialize database, build ML-Model, load or build Priority-Queue'''
        db_loaded = multiprocessing.Event()
        self.db = DBHandler(db_config=self.config['Database'],
                            root_dir=ROOT_DIR,
                            crawl_id=crawl_id,
                            initial_crawl_settings = crawl_settings,
                            save_queue = self.save_queue,
                            db_ready=db_loaded,
                            kill_flag=self.db_shutdown,
                            found = self.found)
        self.db.daemon = True
        # self.db.start()
        db_loaded.wait()
        self.crawl_settings = self.db.crawl_settings
        for queued_url in self.db.loaded_queue:
            self.crawl_queue.put(queued_url)
        for crawled_url in self.db.loaded_crawled:
            self.crawled_set.add(crawled_url)
        for url in start_urls:
            self.crawl_queue.put((1, url))
        build_model(self.config['Parser'], ROOT_DIR)
        Downloader.initialize(self.crawl_settings, self.config['Downloader'])
        Parser.initialize(self.crawl_settings, self.config['Parser'], ROOT_DIR)
        signal.signal(signal.SIGINT, self.signal_handler)


    def start_crawl(self):
        '''Starting the Web Crawl'''
        self.throttle.start()
        for _ in range(0, self.config['Parser']['max_parser_processes']):
            p = Parser(kill=self.throttle.kill_flag, save_q=self.save_queue, todo=self.parse_queue, priority_queue=self.crawl_queue, crawled_set=self.crawled_set)
            p.daemon = True
            self.running_processes.append(p)
            p.start()
        for _ in range(0, self.config['Downloader']['max_downloader_threads']):
            t = Downloader(name='Downloader-{}'.format(_+1),tank=self.throttle, crawled_set=self.crawled_set ,crawl_queue=self.crawl_queue, parse_queue=self.parse_queue)
            t.daemon = True
            self.running_threads.append(t)
            t.start()
        self.db.start()
        return

    def stop_crawl(self):
        '''Saves the progress of the Crawl and stops it.'''
        self.throttle.stop()
        self.logger.info('Stopping Downloaders')
        for thread in self.running_threads:
            thread.join()
        self.logger.info('Saving {} Crawled URLs'.format(len(self.crawled_set)))
        try:
            for url in self.crawled_set:
                to_save = CrawledUrl(url=url,
                                     last_fetched=time.time())
                self.save_queue.put(to_save)
        except Exception as e:
            self.logger.error('Error while saving crawled URLs to database: {}'.format(e))
        self.logger.info('Stopping Parsers')
        for process in self.running_processes:
            process.join()
        self.logger.info('Saving {} Queued URLs'.format(self.crawl_queue.qsize()))
        try:
            while not self.crawl_queue.empty():
                prio_link = self.crawl_queue.get()
                to_save = QueuedUrl(priority=prio_link[0],
                                    url=prio_link[1])
                self.save_queue.put(to_save)
        except Exception as e:
            self.logger.error('Error while saving queue to database: {}'.format(e))
        while not self.save_queue.empty():
            time.sleep(0.2)
        self.db_shutdown.set()
        self.db.join()
        DataManager.shutdown()
        return

    def finished(self):
        if self.crawl_queue.empty() and self.parse_queue.empty():
            return True
        else:
            return False

    def report(self):
        '''Reports the current status of the Crawl.'''
        status = {'crawled':len(self.crawled_set), 'queued':self.crawl_queue.qsize(), 'parse_queued':self.parse_queue.qsize(), 'relevant':self.found.value, 'latest_downloads_per_s':self.throttle.latest(), 'mean_downloads_per_s': self.throttle.mean()}
        print('---------------------------------------------------')
        print('Crawl status at {}'.format(datetime.datetime.now()))
        print('Crawled: {}'.format(status['crawled']))
        print('To be downloaded: {}'.format(status['queued']))
        print('To be parsed: {}'.format(status['parse_queued']))
        print('Found: {}'.format(status['relevant']))
        print('Mean Downloads per second: {}'.format(status['mean_downloads_per_s'][1]))
        print('Latest Downloads per second: {}'.format(status['latest_downloads_per_s'][1]))
        return status

    def signal_handler(self, signal, frame):
        print(multiprocessing.active_children())
        self.logger.debug('Signal {} catched. Stopping Crawl'.format(signal))
        self.stop_crawl()
        sys.exit(1)
