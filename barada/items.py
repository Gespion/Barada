# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BaradaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    job_site        = scrapy.Field()
    job_url         = scrapy.Field()
    job_date        = scrapy.Field()
    job_expire_date = scrapy.Field()
    job_title       = scrapy.Field()
    job_company     = scrapy.Field()
    job_domain      = scrapy.Field()
    job_experience  = scrapy.Field()
    job_level_num   = scrapy.Field()
    job_level_txt   = scrapy.Field()
    job_active      = scrapy.Field()
    job_scrape_date = scrapy.Field()