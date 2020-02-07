# -*- coding: utf-8 -*-
import scrapy
import json
import urllib
from copy import deepcopy
class JbbookSpider(scrapy.Spider):
    name = 'jbbook'
    allowed_domains = ['jd.com','p.3.cn']
    start_urls = ['https://book.jd.com/booksort.html']

    def parse(self, response):
        # 大分类dt
        b_sate_dts = response.xpath("//div[@class='mc']/dl/dt")
        for b_sate_dt in b_sate_dts:
            item = {}
            # 大分类
            item["b_state"] = b_sate_dt.xpath("./a/text()").extract_first()
            # 小分类em
            s_sate_ems = b_sate_dt.xpath("following-sibling::dd[1]//em")
            for s_sate_em in s_sate_ems:
                item["s_sate"] = s_sate_em.xpath("./a/text()").extract_first()
                s_sate_href = urllib.parse.urljoin(response.url,s_sate_em.xpath("./a/@href").extract_first())
                item["s_sate_href"] = s_sate_href
                if s_sate_href is not None:
                    yield scrapy.Request(
                    s_sate_href,
                    callback=self.parse_state_detail,
                    meta={"item":deepcopy(item)}
                    )

    # 小分类详情页面
    def parse_state_detail(self,response):
        next_page_url = response.xpath("//a[@class='pn-next'][1]/@href").extract_first()
        if next_page_url is not None:
            next_page_url = urllib.parse.urljoin(response.url,next_page_url)
            yield scrapy.Request(
                next_page_url,
                callback = self.parse_state_detail,
                meta={"item": item}
            )
        # 书籍列表
        book_lis = response.xpath("//div[@class='goods-list-v2 J-goods-list gl-type-4 ']/ul/li")
        item = response.meta["item"]
        for book_li in book_lis:
            div_container = book_li.xpath("./div[contains(@class,\"j-sku-item\")]")

            if div_container is None:
               print("*"*20)
            # 下单页面
            item["book_buy"] = urllib.parse.urljoin(response.url,div_container.xpath("./div[@class='p-img']/a/@href").extract_first())
            book_img = div_container.xpath("./div[@class='p-img']/a/img/@src").extract_first()
            book_img_url = ""
            if book_img is not None:
                book_img_url = div_container.xpath("./div[@class='p-img']/a/img/@src").extract_first()
            else:
                book_img_url = div_container.xpath("./div[@class='p-img']/a/img/@data-lazy-img").extract_first()
            item["book_img"] = urllib.parse.urljoin(response.url,book_img_url)
            item["book_name"] = div_container.xpath("./div[@class='p-name']/a/em/text()").extract_first()
            try:
                item["book_name"] = item["book_name"].strip()
            except :
                pass
                # print("book_name strip fail=>",item["book_name"])
                # print(div_container.xpath("./div[@class='p-name']/a/em/text()"))
            item["book_price_sku"] = div_container.xpath("@data-sku").extract_first()

            # 每本书的价格
            if item["book_price_sku"] is not None:
                yield scrapy.Request(
                    "https://p.3.cn/prices/mgets?skuIds=J_" + item["book_price_sku"],
                    callback=self.parse_book_price,
                    meta={"item": item}
                )


    def parse_book_price(self,response):
        item = response.meta["item"]
        item["book_price"] = json.loads(response.body.decode())[0]["op"]
        # print(item)
