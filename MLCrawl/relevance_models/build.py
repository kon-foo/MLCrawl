import logging
import os
import sys
import csv

from boilerpipe.extract import Extractor
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
import nltk

from .assesment_model import RelAssesment

logger = logging.getLogger(__name__)

def build_model(config, root_dir):
    # Boilerplate Extractor:
    _load_boilplate(config['TextProcessing']['boilerplate_extractor'])
    _load_customs_res(config['TextProcessing']['custom_regualar_expressions'])
    # Loading Toeknizers & Stemmer.
    _load_tokenizer(config['TextProcessing']['language'])
    _load_stemmer(config['TextProcessing']['language'])
    # Load Stopwords
    if config['General']['stopword_path'] != None:
        _load_stopwords(os.path.join(root_dir, config['General']['stopword_path']))
    # Reading traindata
    traindata = []
    with open(os.path.join(root_dir, config['General']['traindata']), 'r') as f:
        reader = csv.reader(f)
        for line in reader:
            sentence_list = RelAssesment.sentence_tokenizer.tokenize(RelAssesment.preprocess(line[2]))
            for sentence in sentence_list:
                traindata.append(sentence)
    logger.info("Loaded Traindata with {} sentences.".format(len(traindata)))
    # Building Vectorizer
    _build_vectorizer(config['TextProcessing'], None)
    tmp_vector = RelAssesment.vectorizer.fit_transform(traindata)
    logger.info("Created Vector with {} features.".format(tmp_vector.shape[1]))
    if config['SVM']['feature_percentage'] < 1:
        _build_vectorizer(config['TextProcessing'], int(tmp_vector.shape[1] * config['SVM']['feature_percentage']))
        tmp_vector = RelAssesment.vectorizer.fit_transform(traindata)
        logger.info("Reduced vector to top {} features.".format(tmp_vector.shape[1]))
    #Building classifier
    _build_svm(config['SVM'], tmp_vector)
    logger.info('Relevance Assesment Model build and trained sucessfully.')

def _load_boilplate(extractor_type):
    try:
        RelAssesment.BoilerPipe = Extractor
    except Exception as e:
        logger.error('Error loading boilerplate Extractor: {}'.format(e))

def _load_tokenizer(language):
    try:
        RelAssesment.sentence_tokenizer = nltk.data.load('tokenizers/punkt/{}.pickle'.format(language))
        RelAssesment.word_tokenizer = nltk.word_tokenize
    except Exception as e:
        logger.error('Error loading nltk tokenizer: {}'.format(e))
        sys.exit(1)

def _load_stemmer(language):
    try:
        RelAssesment.stemmer = nltk.stem.SnowballStemmer(language)
    except Exception as e:
        logger.error('Error loading nltk.stem.SnowballStemmer: {}'.format(e))
        logger.info('The following languages are supported: {}'.format(nltk.stem.SnowballStemmer.languages))

def _load_stopwords(path):
    try:
        with open(path, 'r') as f:
            for line in f:
                RelAssesment.stopword_list.append(line.split('\n')[0].lower())
    except Exception as e:
        logger.error("Couldn't load stopword list: {}".format(e))
        sys.exit(1)

def _load_customs_res(custom_res):
    for regex in custom_res:
        RelAssesment.custom_regexs.append(regex)

def _build_vectorizer(config, max_f):
    if config['vectorizer'] == 'count':
        RelAssesment.vectorizer = CountVectorizer(analyzer='word',
                                               tokenizer=RelAssesment.tokenize_word,
                                               ngram_range=config['ngramrange'],
                                               max_features=max_f)
    elif config['vectorizer'] == 'tfidf':
        RelAssesment.vectorizer = TfidfVectorizer(analyzer='word',
                                               tokenizer=RelAssesment.tokenize_word,
                                               ngram_range=config['ngramrange'],
                                               max_features=max_f)
    else:
        logger.error('Vectorizer "{}" unknown. Choose between "count" and "tfidf"'.format(config['TextProcessing']['vectorizer']))
        sys.exit(1)


def _build_svm(config, trainvector):
    RelAssesment.classifier = svm.OneClassSVM(nu=config['nu'],
                                           kernel=config['kernel'],
                                           gamma=config['gamma'],
                                           coef0=config['coef0'],
                                           degree=config['degree'],
                                           cache_size = config['cache_size'])
    RelAssesment.classifier.fit(trainvector)
