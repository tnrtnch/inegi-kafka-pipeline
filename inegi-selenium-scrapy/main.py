from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from inegi.spiders.inegi_spider import InegiSpider

process = CrawlerProcess(get_project_settings())
process.crawl(InegiSpider)
process.start()
