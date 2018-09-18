import time
import MLCrawl

crawler = MLCrawl.Crawler(config_file='example/configuration.yaml')
crawler.initialize(crawl_settings={'name':'Giessen', 'full_url': 'https://www.giessen.de', 'search_subdomains':True, 'search_single_domain':True, 'search_pdfs':True}, start_urls=['https://www.giessen.de','https://www.giessen.de/buergerbeteiligung', 'https://www.giessen.de/Rathaus_und_Service/B%C3%BCrgerbeteiligung/', 'https://www.giessen.de/suche.phtml', 'https://www.giessen.de/media/custom/684_13123_1.PDF?1426847241'])
crawler.start_crawl()
while not crawler.finished():
    stats = crawler.report()
    time.sleep(2)
crawler.stop_crawl()


#crawler.initialize(crawl_id=1)
