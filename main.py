# coding=utf-8
import os
import re
import requests
from lxml import etree
from lxml import html
from io import StringIO
import time
import hashlib
import sys
import threading


from common_lib import MyArgParse, LogHandle


class ScrapLogin:
    def __init__(self):
        self.set_log_url = ''
        self.is_login = False
        self.set_cookie_file_name = 'cookie'
        self.set_domain = 'new'
        self.set_config_path = ''

        pass

    def do_login(self):
        pass

    def _save_cookie(self):
        pass

    def _get_config(self):
        pass


class ScrapContent2Data:
    def __init__(self):
        pass

    def load_urls(self):
        pass

    def run(self):
        pass

    def _save_data(self):
        pass


class ScrapContent2Urls:
    def __init__(self):
        pass

    def load_urls(self):
        pass

    def run(self, url):

        pass

    def _save_data(self):
        pass


class ScrapUrls2Content:
    def __init__(self):
        pass

    def load_urls(self):
        pass

    def run_parse(self, url=None):
        r = requests.get(url)
        return r.content
        pass


class ScrapMng:
    def __init__(self):
        pass

    def run(self):
        pass


class ScrapPengpaiNews:

    def __init__(self):
        pass

    def get_top_channels(self):
        pass

    def get_channel_lists(self):
        pass


class PPPageNode:
    def __init__(self):
        self.is_done = False
        self.content = ''
        self.sub_nodes = list()
        self.title = ''
        self.url = ''
        self.parent_node = None
        self.db_handler = None
        self.do_init()
        pass

    def do_init(self):
        pass


    def do_parse(self):
        pass

    def get_content(self):
        return self.content

    def get_sub_nodes(self):
        return self.sub_nodes
        pass

    def add_sub_node(self, node):
        node.set_parent_node(self)
        self.sub_nodes.append(node)

    def init_node(self, url, title):
        self.url = url
        self.title = self.filter_title(title)
        pass

    def get_info(self):
        return self.title + self.url

    def get_title(self):
        return self.title

    def set_title(self, title):
        self.title = self.filter_title(title)

    def get_url(self):
        return self.url

    def get_self_id(self):
        pass

    def set_parent_node(self, node):
        self.parent_node = node
        pass

    def get_parent_node(self):
        return self.parent_node
        pass

    def filter_title(self, title):
        valid_title = ''
        for idx, char in enumerate(title):
            if '0' <= char <= '9' or 'A' <= char <= 'Z' or 'a' <= char <= 'z' or 127 < char:
                valid_title += char
        if not len(valid_title):
            valid_title = 'buggytitle'
        return valid_title
        pass

from sqlite_util import DBRow, DBRowHuaBan, DBHandler


class PPFrontPageNode(PPPageNode):
    def do_init(self):
        self.db_handler = DBHandler()
        self.db_handler.load('sex.db')
        self.db_handler.add_table('sex')

        self.set_store_img_path = 'img'
        self.flag_quit = False
        self.log_handler = LogHandle('sex_srap.log')
        self.log = self.log_handler.log

        self.set_thread_cnt = 6

        self.info_run_thread_cnt = 0
        self.info_succeed_cnt = 0
        self.info_failed_cnt = 0

        self.task_row_list = list()
        self.task_update_row_list = list()
        self.lock = threading.RLock()
        if not os.path.exists(self.set_store_img_path):
            os.mkdir(self.set_store_img_path)
        pass

    def set_download_folder(self, folder_path):
        self.set_store_img_path = folder_path[:]
        self.log('Set Store Folder to [%s]' % self.set_store_img_path)

    def set_down_thread(self, thread_cnt):
        self.set_thread_cnt = thread_cnt
        self.log('Set thread num to [%s]' % self.set_thread_cnt)

    def do_parse(self, start_url=None):
        url2content_handle = ScrapUrls2Content()

        if not start_url:
            start_url = self.url
        self.content = url2content_handle.run_parse(start_url)
        write_content(self.content, 'start.html')

        tr = etree.HTML(self.content)
        channel_unit_tr_nodes = tr.xpath('//a[@class="image_wrapper"]/img[@class="image"]')
        for channel_unit_tr_node in channel_unit_tr_nodes:
            print channel_unit_tr_node.attrib['data-src']
            self.store_url_data(channel_unit_tr_node.attrib['data-src'])
            continue
            a_nodes = channel_unit_tr_node.xpath('a[@class="bn_a"]')
            if len(a_nodes):
                channel_unit_node = PPChannelUnitPageNode()
                url = start_url + a_nodes[0].attrib['href']
                title = a_nodes[0].text
                channel_unit_node.init_node(url, title)
                self.add_sub_node(channel_unit_node)
            else:
                continue
            sub_channel_tr_nodes = channel_unit_tr_node.xpath('div/ul[@class="clearfix"]/li/a')
            for sub_channel_tr_node in sub_channel_tr_nodes:
                channel_node = PPChannelPageNode()
                url = start_url + sub_channel_tr_node.attrib['href']
                title = sub_channel_tr_node.text
                channel_node.init_node(url, title)
                channel_unit_node.add_sub_node(channel_node)

    def do_auto_parse(self):
        max_page_id = self.get_last_page()
        start_url = self.url[:]
        for idx in range(1, max_page_id+1):
            cur_url = start_url + '?page=%d' % idx
            self.do_parse(cur_url)
            self.log(cur_url)
        pass

    def get_last_page(self):
        ret_page_id = 0
        url2content_handle = ScrapUrls2Content()

        start_url = 'http://www.sex.com/'
        start_url = self.url
        self.content = url2content_handle.run_parse(start_url)
        write_content(self.content, 'start.html')

        tr = etree.HTML(self.content)
        channel_unit_tr_nodes = tr.xpath('//div[@class="btn-group btn-group-lg"]/a[@class="btn btn-default"]')
        if channel_unit_tr_nodes:
            max_page_info = channel_unit_tr_nodes[len(channel_unit_tr_nodes)-1].attrib['href']
            pattern = u'page=(?P<page_id>\d+)'
            m = re.search(pattern, max_page_info)
            if m:
                self.log(m.group('page_id'))
                ret_page_id = int(m.group('page_id'))
            else:
                self.log('Not Found page id from %s' % max_page_info)
        else:
            self.log('Not found last page')
        return ret_page_id
        pass

    def get_store_file_path(self, row):
        img_path = os.path.join(self.set_store_img_path, row.item_list[2].value)
        file_tail = row.item_list[1].value.split('.')[-1]
        img_path += '.' + file_tail
        return img_path
        pass

    def store_url_data(self, img_url):
        db_row = DBRowHuaBan()
        # base_url
        db_row.item_list[0].value = self.url[:]
        # url
        db_row.item_list[1].value = img_url[:]
        # url_hash
        m = hashlib.md5()
        m.update(img_url)
        db_row.item_list[2].value =m.hexdigest()[:]
        # is_done
        db_row.item_list[3].value = 0
        self.db_handler.insert_row(db_row)
        # print db_row
        pass

    def do_login(self):
        pass

    def get_content(self, url=None):
        self.info_run_thread_cnt += 1
        while True:
            if self.flag_quit:
                self.log('thread quit..')
                self.info_run_thread_cnt -= 1
                return
            try:
                rows = self.db_handler.get_row(10)
                if not len(rows):
                    self.log('All done')
                    return
                headers = {'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0',
                           'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                           'accept-language': 'en-US,en;q=0.5',
                           'accept-encoding': 'gzip, deflate, br',
                           'referer': 'http://www.sex.com/',
                           }
                for row in rows:
                    url = row.item_list[1].value
                    self.log('start get download %s' % url)
                    try:
                        r = requests.get(url, headers=headers)
                    except KeyboardInterrupt:
                        self.log('Quit')
                        return
                    except ValueError:
                        'Request err'
                        continue
                        pass
                    if 200 == r.status_code:
                        self.log('Succeed get pic')
                        row.item_list[3].value = 1
                        self.db_handler.update_row(row)
                        # img_path = os.path.join(self.set_store_img_path, row.item_list[2].value)
                        img_path = self.get_store_file_path(row)
                        with open(img_path, 'wb+') as fd:
                            fd.write(r.content)
                        self.info_succeed_cnt += 1
                    else:
                        self.log('Failed to get pic')
                        self.info_failed_cnt += 1
            except KeyboardInterrupt:
                self.info_run_thread_cnt -= 1
                self.flag_quit = True
                self.log('Recv Ctrl-c thread quit..')
                return
            except ValueError:
                e_str = sys.exc_info()[0]
                self.log('Exception![%s]' % e_str)
                pass
        pass

    def download_thread(self, url=None):
        self.info_run_thread_cnt += 1
        headers = {'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0',
                   'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'accept-language': 'en-US,en;q=0.5',
                   'accept-encoding': 'gzip, deflate, br',
                   'referer': 'http://www.sex.com/',
                   }
        while True:
            if self.flag_quit:
                self.log('thread quit..')
                self.info_run_thread_cnt -= 1
                return
            try:
                row = self.get_one_row_task()
                if not row:
                    time.sleep(3)
                    self.log('No task to precess..')
                    continue
                url = row.item_list[1].value
                self.log('start get download %s' % url)
                try:
                    r = requests.get(url, headers=headers)
                except KeyboardInterrupt:
                    self.log('Quit')
                    return
                except ValueError:
                    'Request err'
                    continue
                    pass
                if 200 == r.status_code:
                    self.log('Succeed get pic')
                    row.item_list[3].value = 1
                    self.add_update_row(row)
                    img_path = self.get_store_file_path(row)
                    with open(img_path, 'wb+') as fd:
                        fd.write(r.content)
                    self.info_succeed_cnt += 1
                else:
                    self.log('Failed to get pic')
                    self.info_failed_cnt += 1
            except KeyboardInterrupt:
                self.info_run_thread_cnt -= 1
                self.flag_quit = True
                self.log('Recv Ctrl-c thread quit..')
                return
            except ValueError:
                e_str = sys.exc_info()[0]
                self.log('Exception![%s]' % e_str)
                pass
        pass

    def start_auto_download(self):
        set_period = 10
        for idx in range(self.set_thread_cnt):
            pro = threading.Thread(target=self.download_thread)
            pro.start()
        while True:
            try:
                self.get_task_from_db()
                self.do_update_row()
                succeed_cnt = self.info_succeed_cnt
                time.sleep(set_period)
                speed = (self.info_succeed_cnt - succeed_cnt) / set_period
                self.log('Thread[%d], succeed [%d], failed [%d], speed [%d]pic/s' %
                         (self.info_run_thread_cnt, self.info_succeed_cnt, self.info_failed_cnt,speed))
            except KeyboardInterrupt:
                e_str = sys.exc_info()[0]
                self.log('Exception![%s]' % e_str)
                return
        pass

    def set_store_path(self, path):
        self.set_store_img_path = path[:]
        if not os.path.exists(self.set_store_img_path):
            os.mkdir(self.set_store_img_path)
        pass

    def get_one_row_task(self):
        self.lock.acquire()
        ret_row = None
        if not len(self.task_row_list):
            ret_row = None
        else:
            ret_row = self.task_row_list.pop()
        self.lock.release()
        return ret_row
        pass

    def get_task_from_db(self):
        if len(self.task_row_list) > 50:
            return
        rows = self.db_handler.get_row(100)
        if not len(rows):
            self.log('Get zero row, maybe all task done, quit..')
            self.flag_quit = True
            return
        self.task_row_list.extend(rows)
        pass

    def do_update_row(self):
        if not len(self.task_update_row_list):
            return
        row = self.task_update_row_list.pop()
        self.db_handler.update_row(row)
        return
        pass

    def add_update_row(self, row):
        self.lock.acquire()

        self.task_update_row_list.append(row)

        self.lock.release()
        pass


class PPChannelUnitPageNode(PPPageNode):
    def get_self_id(self):
        m = re.match('.*channel_(?P<id>\d+)', self.url)
        if m:
            id = int(m.groupdict()['id'])
            return id
        return None
        pass
    pass


class PPChannelPageNode(PPPageNode):
    def do_parse(self):
        page_id = 0
        while True:
            channel_id = self.get_self_id()
            start_url = 'http://www.thepaper.cn/load_index.jsp?nodeids=%s&pageidx=%d' % (channel_id, page_id)
            print start_url
            url2content_handle = ScrapUrls2Content()
            content = url2content_handle.run_parse(start_url)
            if not len(content):
                print 'All article list get done, total article [%d]' % len(self.get_sub_nodes())
                break
            root = etree.HTML(content)
            nodes = root.xpath('//div[@class="news_li"]/h2/a')
            for node in nodes:
                article_node = PPArticlePageNode()
                url = 'http://www.thepaper.cn/' + node.attrib['href']
                title = node.text
                article_node.init_node(url, title)
                self.add_sub_node(article_node)
            page_id += 1
        pass

    def get_self_id(self):
        m = re.match('.*list_(?P<id>\d+)', self.url)
        if m:
            id = int(m.groupdict()['id'])
            return id
        return None
        pass

    pass


class PPArticlePageNode(PPPageNode):
    def do_parse(self):
        if check_if_exist(self.get_parent_node().get_parent_node(), self.get_parent_node(), self):
            print 'Already exist, skip [%s]' %self.url
            return True
        start_url = self.url
        #start_url = 'http://www.thepaper.cn/newsDetail_forward_1742361'
        print start_url
        url2content_handle = ScrapUrls2Content()
        self.content = url2content_handle.run_parse(start_url)
        if not len(self.content):
            print 'Empty content'
            return False
        root = etree.HTML(self.content)
        title_node = root.xpath('//div[@class="newscontent"]/h1[@class="news_title"]')
        news_about_node = root.xpath('//div[@class="newscontent"]/div[@class="news_about"]')
        news_txt_node = root.xpath('//div[@class="newscontent"]/div[@class="news_txt"]')

        self.title = self.filter_title(title_node[0].text)

        self.get_pic_from_content()
        store_new_article(self.get_parent_node().get_parent_node(), self.get_parent_node(), self)
        pass

    def get_self_id(self):
        m = re.match('.*newsDetail_forward_(?P<id>\d+)', self.url)
        if m:
            id = int(m.groupdict()['id'])
            return id
        return None
        pass

    def get_pic_from_content(self):
        root = etree.HTML(self.content)
        news_txt_nodes = root.xpath('//div[@class="newscontent"]/div[@class="news_txt"]')
        img_nodes = news_txt_nodes[0].xpath('.//img[@src]')
        for idx, img_node in enumerate(img_nodes):
            img_url = img_node.attrib['src']
            img_name = os.path.basename(img_url)
            url2content_handle = ScrapUrls2Content()
            img_content = url2content_handle.run_parse(img_url)
            if len(img_content):
                store_new_article_file(self.get_parent_node().get_parent_node(), self.get_parent_node(), self, img_name, img_content)
        pass
    pass


def write_content(content, file_name):
    with open(file_name, 'w+') as fd:
        fd.write(content)


def do_test_get_channels():
    ret_list = list()
    url2content_handle = ScrapUrls2Content()

    start_url = 'http://www.thepaper.cn/'
    content = url2content_handle.run_parse(start_url)
    write_content(content, 'start.html')

    tr = etree.HTML(content)
    nodes = tr.xpath('//div[@class="head_banner"]/div/a')
    for node in nodes:
        item = dict()
        item['title'] = node.text
        item['url'] = node.attrib['href']
        ret_list.append(item)
        list_nodes = node.xpath('//ul[@class="clearfix"]/li/a')
        item['subs'] = list()
        for list_node in list_nodes:
            sub_dict = dict()
            sub_dict['url'] = list_node.attrib['href']
            sub_dict['title'] = list_node.text
            item['subs'].append(sub_dict)
            print list_node.text, list_node.attrib['href']

    write_content(str(ret_list), 'items.txt')
    return ret_list


gLocalStoreFolder = 'PengPaiArticle'


def get_list(folder_path):
    items = os.listdir(folder_path)
    ret_list = list()
    for item in items:
        new_dict = dict()
        id = item.split('-')[0]
        new_dict['id'] = id
        new_dict['full_name'] = item
        ret_list.append(new_dict)
    return ret_list


def check_if_exist(channel_unit_node, channel_node, article_node):
    global gLocalStoreFolder
    if not os.path.exists(gLocalStoreFolder):
        os.mkdir(gLocalStoreFolder)
        return False
    items = get_list(gLocalStoreFolder)
    is_found = False
    channel_file_node = None
    for item in items:
        if item['id'] == str(channel_unit_node.get_self_id()):
            is_found = True
            channel_file_node = item
            break
    if not is_found:
        return False

    folder_path = os.path.join(gLocalStoreFolder, channel_file_node['full_name'])
    items = get_list(folder_path)
    list_file_node = None
    for item in items:
        if item['id'] == str(channel_node.get_self_id()):
            list_file_node = item
            break
    if not list_file_node:
        return False
    folder_path = os.path.join(folder_path, list_file_node['full_name'])
    items = get_list(folder_path)
    for item in items:
        if item['id'] == str(article_node.get_self_id()):
            return True
    return False
    pass


def store_new_article(channel_unit_node, channel_node, article_node):
    global gLocalStoreFolder
    try:
        if not os.path.exists(gLocalStoreFolder):
            os.mkdir(gLocalStoreFolder)

        folder_path = os.path.join(gLocalStoreFolder,  '%d-%s' % (channel_unit_node.get_self_id(), channel_unit_node.get_title()))
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        folder_path = os.path.join(folder_path, '%s-%s' % (channel_node.get_self_id(), channel_node.get_title()))
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        article_name = '%d-%s' % (article_node.get_self_id(), article_node.get_title())
        folder_path = os.path.join(folder_path, article_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        file_name = os.path.join(folder_path, article_name + '.html')

        with open(file_name, 'w+') as fd:
            fd.write(article_node.get_content())
    except :
        print 'ERROR: Failed to store new article'


def store_new_article_file(channel_unit_node, channel_node, article_node, file_name, content):
    global gLocalStoreFolder
    try:
        if not os.path.exists(gLocalStoreFolder):
            os.mkdir(gLocalStoreFolder)

        folder_path = os.path.join(gLocalStoreFolder,  '%d-%s' % (channel_unit_node.get_self_id(), channel_unit_node.get_title()))
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        folder_path = os.path.join(folder_path, '%s-%s' % (channel_node.get_self_id(), channel_node.get_title()))
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        article_name = '%d-%s' % (article_node.get_self_id(), article_node.get_title())
        folder_path = os.path.join(folder_path, article_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        full_file_path = os.path.join(folder_path, file_name)
        #print 'Create file [%s]' % full_file_path
        with open(full_file_path, 'wb+') as fd:
            fd.write(content)
    except :
        print 'ERROR: Failed to store new article file'


# front-page  channel-unit  channel  article-list-in-channel


def choose_node(node):
    sub_nodes = node.get_sub_nodes()
    for idx, sub_node in enumerate(sub_nodes):
        print str(idx) + ':' + sub_node.get_title()
    if not len(sub_nodes):
        print 'ERROR: no channel found...'
        return None
    while True:
        num = raw_input('choose channel unit-->')
        try:
            num = int(num)
            if num > len(sub_nodes):
                print 'wrong choice! try again.'
            break
        except ValueError:
            print 'Please input number..'
    return sub_nodes[num]
    pass


def arg_parser_init():
    arg_parse = MyArgParse()
    arg_parse.add_option('-parse', [0, 1], 'parse img url')
    arg_parse.add_option('-url', [0, 1], 'parse img url')
    arg_parse.add_option('-download', [0, 1], 'download imgs')
    arg_parse.add_option('-thread', [1], 'set thread count')
    arg_parse.add_option('-d', [1], 'set img store folder')
    arg_parse.add_option('-h', [0], 'print help')

    return arg_parse

gLogHandler = LogHandle('sex_scrap.log')


def main():
    arg_handler = arg_parser_init()
    if not arg_handler.parse(sys.argv) or arg_handler.check_option('-h'):
        print arg_handler
        return

    front_page_node = PPFrontPageNode()
    start_url = 'http://www.sex.com/'
    if arg_handler.check_option('-d'):
        front_page_node.set_download_folder(arg_handler.get_option_args('-d')[0])

    if arg_handler.check_option('-thread'):
        front_page_node.set_down_thread(int(arg_handler.get_option_args('-thread')[0]))

    if arg_handler.check_option('-parse'):
        if arg_handler.check_option('-url'):
            start_url = arg_handler.get_option_args('-url')[0]
        gLogHandler.log('Parse [%s]' % start_url)
        front_page_node.init_node(start_url, 'sex')
        front_page_node.do_auto_parse()
        gLogHandler.log('Parse [%s] Done' % start_url)
        return
    elif arg_handler.check_option('-download'):
        gLogHandler.log('Start download')
        # front_page_node.get_content()
        front_page_node.start_auto_download()
        gLogHandler.log('Download Done')
        return
    else:
        print arg_handler
        return
    # front_page_node.do_parse()
    # front_page_node.do_auto_parse()

    return

    channel_unit_node = choose_node(front_page_node)
    channel_node = choose_node(channel_unit_node)
    channel_node.do_parse()
    article_nodes = channel_node.get_sub_nodes()
    print len(article_nodes)
    for article_node in article_nodes:
        article_node.do_parse()


if __name__ == '__main__':
    main()
    exit(0)
    pass







