#!/usr/bin/env python
"""
 Created by howie.hu at 25/02/2018.
 Target URI: https://www.qidian.com/all
        Param:?page=1
"""
from pymongo import MongoClient

from talonspider import Spider, Item, TextField, AttrField
from talospider.utils import get_random_user_agent


class MongoDb:
    _db = None
    MONGODB = {
        'MONGO_HOST': '127.0.0.1',
        'MONGO_PORT': '',
        'MONGO_USERNAME': '',
        'MONGO_PASSWORD': '',
        'DATABASE': 'owllook'
    }

    def client(self):
        # motor
        self.mongo_uri = 'mongodb://{account}{host}:{port}/'.format(
            account='{username}:{password}@'.format(
                username=self.MONGODB['MONGO_USERNAME'],
                password=self.MONGODB['MONGO_PASSWORD']) if self.MONGODB['MONGO_USERNAME'] else '',
            host=self.MONGODB['MONGO_HOST'] if self.MONGODB['MONGO_HOST'] else 'localhost',
            port=self.MONGODB['MONGO_PORT'] if self.MONGODB['MONGO_PORT'] else 27017)
        return MongoClient(self.mongo_uri)

    @property
    def db(self):
        if self._db is None:
            self._db = self.client()[self.MONGODB['DATABASE']]

        return self._db


class QidianNovelsItem(Item):
    target_item = TextField(css_select='ul.all-img-list>li')
    novel_url = AttrField(css_select='div.book-img-box>a', attr='href')
    novel_name = TextField(css_select='div.book-mid-info>h4')
    novel_author = TextField(css_select='div.book-mid-info>p.author>a.name')
    novel_author_home_url = AttrField(css_select='div.book-mid-info>p.author>a.name', attr='href')

    def tal_novel_url(self, novel_url):
        return 'http:' + novel_url

    def tal_novel_author(self, novel_author):
        if isinstance(novel_author, list):
            novel_author = novel_author[0].text
        return novel_author

    def tal_novel_author_home_url(self, novel_author_home_url):
        if isinstance(novel_author_home_url, list):
            novel_author_home_url = novel_author_home_url[0].get('href').strip()
        return 'http:' + novel_author_home_url


class QidianNovelsSpider(Spider):
    start_urls = ['https://www.qidian.com/all?page={i}'.format(i=i) for i in range(1, 41645)]
    headers = {
        "User-Agent": get_random_user_agent()
    }
    request_config = {
        'RETRIES': 3,
        'DELAY': 3,
        'TIMEOUT': 10
    }
    all_novels_col = MongoDb().db.all_novels

    def parse(self, res):
        items_data = QidianNovelsItem.get_items(html=res.html)
        for item in items_data:
            data = {
                'novel_url': item.novel_url,
                'novel_name': item.novel_name,
                'novel_author': item.novel_author,
                'novel_author_home_url': item.novel_author_home_url,
                'spider': 'qidian'
            }
            if self.all_novels_col.find_one({"novel_name": item.novel_name}) is None:
                self.all_novels_col.insert_one(data)
                print(item.novel_name + ' - 抓取成功')
            else:
                print(item.novel_name + ' - 已经抓取')


if __name__ == '__main__':
    # 其他多item示例：https://gist.github.com/howie6879/3ef4168159e5047d42d86cb7fb706a2f
    QidianNovelsSpider.start()