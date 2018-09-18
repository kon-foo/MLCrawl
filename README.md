# MLCrawl - focused, machine-learning based web crawler
MLCrawl is an advanced and modularized version of [KommunenCrawler](https://github.com/elpunkt/KommunenCrawler), a web cralwer with the aim to find documents related to citizen participation on websites of german municipalities.

> Warning: The current version sometimes faces unexpected issues with the boilerplate extraction and the manual termination of a crawl. Don't use MLCrawl in production.

MLCrawl is a multi-processing, multi-threaded focused web crawler. The focussing is based on a [One-class Support Vector Machines](http://scikit-learn.org/stable/modules/generated/sklearn.svm.OneClassSVM.html#sklearn.svm.OneClassSVM) implemented in [scikit-learn](http://scikit-learn.org). 


## Installation
MLCrawl depends on several quite big python packages, such as sci-kit learn for the machine-learning part and nltk for the text processing. Make sure you install all libraries in the requirements file.
Clone the repository, cd into it, run:
```
python setup.py install
```

## Quick-Start
Before starting a Crawl, a configuration-file needs to be written. Use [example/configuration.yaml](https://github.com/elpunkt/MLCrawl/blob/master/example/configuration.yaml) as a template.
```yaml
Logging:
  level: INFO
  debug_file_logging: True

Database:
  dialect: sqlite
  driver:
  username:
  password:
  host:
  port:
  name: example/crawl.db

Downloader:
  user-agent: MyCrawler | https://path-to-website-with-crawler-information.com/
  max_downloader_threads: 1 # Download threads to run simultaneaously.
  crawls_per_second: 5 #Maximum downloads per second.

Parser:
  max_parser_processes: 4 #Parsing processes to run simultaneaously.
  General:
    traindata: example/traindata/traindata.csv #Path to your train data.
    stopword_path: example/stopwords #Path to your stopword file
    threshold: -0.5 #Threshold -1 to 1 to define how many relevant sentences a document needs to have to be considered releevant.
    search_depth: 3 #Number of child pages to download after the last relevant document.
  TextProcessing:
    language: german #Supported languages in : nltk.stem.SnowballStemmer.languages
    boilerplate_extractor: LargestContentExtractor #See https://github.com/misja/python-boilerpipe
    vectorizer: count #Can be count or tfidf
    ngramrange: [1,2]
    custom_regualar_expressions:
      - ['/innen|\*innen|/-innen', 'innen'] #unifies different gender-formats.
      - ['-\s*\n', ''] #removes hyphenation.
      - ['(?:[\t ]*(?:\r?\n|\r)+)', ' '] #removes linebreaks.
  SVM: #See http://scikit-learn.org/stable/modules/generated/sklearn.svm.OneClassSVM.html#sklearn.svm.OneClassSVM
    feature_percentage: 0.8
    kernel: sigmoid
    nu: 0.05
    gamma: 0.1
    coef0: -1
    degree: 3
    cache_size: 1000 #MB memory
```

To run a Crawl with the example data, run:
```python
import time
import MLCrawl

crawler = MLCrawl.Crawler(config_file='example/configuration.yaml')
crawler.initialize(crawl_settings={'name':'Giessen', 'full_url': 'https://www.giessen.de', 'search_subdomains':True, 'search_single_domain':True, 'search_pdfs':True}, start_urls=['https://www.giessen.de/buergerbeteiligung', 'https://www.giessen.de/Rathaus_und_Service/B%C3%BCrgerbeteiligung/'])
crawler.start_crawl()
while not crawler.finished():
    stats = crawler.report()
    time.sleep(2)
crawler.stop_crawl()
```

## Documentation:
For the full documentation see [docs.elpunkt.eu](http://docs.elpunkt.eu/MLCrawl)

## How to Contribute:
1. Test ML and open an issue to report a bug or discuss a feature idea.
2. Give general feedback on the code is appreciated.
3. Fork the repository and make your changes.






