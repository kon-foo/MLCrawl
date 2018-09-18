from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey

Base = declarative_base()

class Crawl(Base):
    __tablename__ = 'crawls'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    base_url = Column(String)
    started = Column(Float)
    last_change = Column(Float)
    search_subdomains = Column(Boolean)
    search_singledomain = Column(Boolean)
    search_pdfs = Column(Boolean)
    charset = Column(String)

    relevant_docs = relationship('RelevantDocument')
    crawled_urls = relationship('CrawledUrl')
    queued_urls = relationship('QueuedUrl')


class RelevantDocument(Base):
    __tablename__ = 'relevant_documents'
    id = Column(Integer, primary_key=True)
    crawl_id = Column(Integer, ForeignKey('crawls.id'))
    url = Column(String)
    last_fetched = Column(Float)
    title = Column(String)
    type = Column(String)
    relevance = Column(Float)
    content = Column(Text)
    raw_content = Column(Text)
    follow = Column(Boolean)

class CrawledUrl(Base):
    __tablename__ = 'crawled_urls'
    id = Column(Integer, primary_key=True)
    crawl_id = Column(Integer, ForeignKey('crawls.id'))
    url = Column(String)
    last_fetched = Column(Float)

class QueuedUrl(Base):
    __tablename__ = 'queued_urls'
    id = Column(Integer, primary_key=True)
    crawl_id = Column(Integer, ForeignKey('crawls.id'))
    url = Column(String)
    priority = Column(Integer)
