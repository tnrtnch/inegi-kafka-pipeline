import scrapy

class InegiItem(scrapy.Item):
    Entity_name = scrapy.Field()
    Sanction_numbers = scrapy.Field()

