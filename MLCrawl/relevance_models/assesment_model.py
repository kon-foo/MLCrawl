import logging
import re
import io
from urllib import parse

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from bs4 import BeautifulSoup

pdf_logger = logging.getLogger('pdfminer')
pdf_logger.setLevel(logging.WARNING)
logger = logging.getLogger()

class RelAssesment():
    stopword_list = []
    BoilerPipe = None
    sentence_tokenizer = None
    word_tokenizer = None
    stemmer = None
    custom_regexs = []
    vectorizer = None
    classifier = None

    @classmethod
    def preprocess(cls, string):
        '''Apply custom regualar expressions.'''
        for rule in RelAssesment.custom_regexs:
            try:
                string = re.sub(rule[0], rule[1], string)
            except Exception as e:
                logger.error('Couldnt apply custom regular expression "{}" on "{}"'.format(rule, string))
        return string

    @classmethod
    def tokenize_word(cls, text):
        '''Remove punctuation, numbers and stopwords'''
        text = re.sub(r"[^a-zA-Z \öÖäÄüÜß]", r" ", text)
        text = re.sub(r"(^|\s+)(\S(\s+|$))+", r" ", text)
        text = ' '.join([word.lower() for word in text.split() if word.lower() not in RelAssesment.stopword_list])
        return RelAssesment.stem_word(RelAssesment.word_tokenizer(text))

    @classmethod
    def stem_word(cls, tokens):
        '''Stemming'''
        return [RelAssesment.stemmer.stem(item) for item in tokens]

    @classmethod
    def html_to_text(cls, full_html):
        extracted = cls.BoilerPipe(extractotr='LargestContentExtractor',  html=full_html).getText()
        return extracted

    @classmethod
    def pdf_to_text(cls, raw_pdf):
        pdf = io.BytesIO(raw_pdf)
        output = io.StringIO()
        manager = PDFResourceManager()
        converter = TextConverter(manager, output, laparams=LAParams())
        interpreter = PDFPageInterpreter(manager, converter)
        for page in PDFPage.get_pages(pdf, set()):
            interpreter.process_page(page)
        text = output.getvalue()
        output.close
        converter.close()
        return text

    @classmethod
    def classify_text(cls, text):
        cleaned_text = cls.preprocess(text)
        sentences = cls.sentence_tokenizer.tokenize(cleaned_text)
        as_vector = cls.vectorizer.transform(sentences)
        if as_vector.shape[0] == 0:
            return 0
        else:
            return cls.classifier.predict(as_vector).mean()

    @classmethod
    def extract_links(cls, html, source):
        parsed_uri = parse.urlparse(source)
        source_url_base = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        source_url_elements = parsed_uri.hostname.split('.')
        if source_url_elements[0] == 'www':
            source_url_elements.pop(0)
        internal = set()
        sub_domains = set()
        external = set()
        soup = BeautifulSoup(html, features="lxml")
        for link in soup.findAll('a'):
            try:
                link = cls.make_full_link(link.get('href'), source_url_base)
                if link == None:
                    continue
                linktype = cls.get_link_type(link, source_url_elements)
                if linktype == None:
                    continue
                if linktype == 'internal':
                    internal.add(link)
                elif linktype == 'external':
                    external.add(link)
                else:
                    sub_domains.add(link)
            except Exception as e:
                logger.error('Error while link extraction. Link: {} found on {}. Error: {}'.format(link, source, e))
                continue
        return internal, sub_domains, external


    @classmethod
    def make_full_link(cls, link, base):
        url = parse.urljoin(base, link)
        return url

    @classmethod
    def get_link_type(cls, link, base):
        elemnt_str = parse.urlparse(link).hostname
        if elemnt_str == None:
            return None
        elements = elemnt_str.split('.')
        if elements[0] == 'www':
            elements.pop(0)
        if elements[-2:] != base[-2:]:
            return 'external'
        elif elements[0] == base[0]:
            return 'internal'
        else:
            return 'subdomain'
