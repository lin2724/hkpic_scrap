# coding=utf-8
import os
import sys
import urllib
import urllib2
import cookielib
import base64
import re
import hashlib
import json
import binascii
import time
import imghdr
import sys
import platform
import multiprocessing
import sqlite3
import datetime
import ConfigParser
import multiprocessing
from multiprocessing import Process, Pipe


class LoginMethod:
    def __init__(self, set_get_cookie = False):
        self.login_url = 'http://hkpic-forum.xyz/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1'
        self.status_url = 'http://hkpic-forum.xyz/forum.php'
        self.config_file_path = 'config.ini'
        self.cookie_file_path = 'cookie'
        self.username = ''
        self.password = ''

        self.set_get_cookie = set_get_cookie
        self.do_init()
        pass

    def __str__(self):
        return 'username:%s, login_url:%s' %(self.username, self.login_url)

    def do_init(self):
        if not os.path.exists(self.config_file_path):
            print 'config file not exist, create it'
            with open(self.config_file_path, 'w+') as file_fd:
                file_fd.write('[login_account_info]\
#account info for login\n\
login_username =\n\
login_password =\n\
#all pic urls will be stroed in this file\n\
link_file = board_link.txt\n\
[scrapy_settings]\n\
#how many threads do u want when scrap pic\n\
thread_number = 30\n\
img_folder = img')

        if not os.path.exists(self.cookie_file_path) or self.set_get_cookie:
            with open(self.cookie_file_path, 'w+') as fd:
                pass

    def get_status(self):
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                              }
        req_test = urllib2.Request(
            url=self.status_url,
            headers=http_headers
        )
        data = urllib2.urlopen(req_test, timeout=10).read()
        with open('hk_check_login_result.html', 'w+') as fd:
            fd.write(data)
            print ('get satus end')
        m = re.search('lin2724', data)
        if m:
            return True
        else:
            return False
        pass

    def get_config(self):
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.config_file_path, 'r'))
        try:
            self.username = config.get('login_account_info', 'login_username')
            self.password = config.get('login_account_info', 'login_password')
            if not self.username or not self.password:
                print '###warning! username or password not found!'
            return True
        except ConfigParser.NoOptionError:
            print ('ERROR: config file not complete!')
            return None
        pass

    def check_cookie_exist(self):
        if os.path.exists(self.cookie_file_path):
            return True
        return False

    def do_login(self):
        login_data = dict()
        login_data['fastloginfield'] = 'username'
        login_data['username'] = self.username
        login_data['cookietime'] = '2592000'
        login_data['password'] = self.password
        login_data['quickfoward'] = 'yes'
        login_data['handlekey'] = 'ls'

        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                             'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                             'Accept-Encoding': 'gzip, deflate',
                             'DNT': '1',
                             'Referer': 'http://hkpic-forum.xyz/forum.php',
                             'Content-Type': 'application/x-www-form-urlencoded;text/html; charset=utf-8',
                             }

        if self.set_get_cookie or not self.check_cookie_exist():
            cookie_jar2 = cookielib.LWPCookieJar()
            cookie_support2 = urllib2.HTTPCookieProcessor(cookie_jar2)
            opener2 = urllib2.build_opener(cookie_support2, urllib2.HTTPHandler)
            urllib2.install_opener(opener2)

            login_data = urllib.urlencode(login_data)
            req_login = urllib2.Request(
                url=self.login_url,
                data=login_data,
                headers=http_headers
            )
            data = urllib2.urlopen(req_login).read()
            with open('hk_login_result.html', 'w+') as fd:
                fd.write(data)
                print ('login end')
            if self.get_status():
                print 'login succeed!'
                cookie_jar2.save(self.cookie_file_path, ignore_discard=True, ignore_expires=True)
            else:
                print 'login fail'
            pass
        else:
            print ('cookie already exist, try login with cookie')
            cookie_jar = cookielib.LWPCookieJar(self.cookie_file_path)
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            cookie_support = urllib2.HTTPCookieProcessor(cookie_jar)
            opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
            urllib2.install_opener(opener)
            if self.get_status():
                print 'login succeed!'
            else:
                print 'login with cookie fail, try login with password'
                self.set_get_cookie = True
                self.do_login()

    def get_url_data(self, url):
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        }
        req_test = urllib2.Request(
            url=url,
            headers=http_headers
        )
        data = urllib2.urlopen(req_test, timeout=10).read()
        return data


class ScrapImg:
    def __init__(self):
        self.db_path = 'record.db'
        self.img_store_path = 'img'
        self.do_init()
        pass

    def do_init(self):
        self.data_base_init()
        if not os.path.exists(self.img_store_path):
            os.mkdir(self.img_store_path)

    def data_base_init(self):
        if not os.path.exists(self.db_path):
            self.con = sqlite3.connect(self.db_path)
            self.con.execute('CREATE TABLE page_record(\
              page_id INT PRIMARY KEY ,\
              url char,\
              count INT DEFAULT 0,\
              desciption CHAR ,\
              is_done INT DEFAULT 0,\
              record_time DATE )')
            self.con.commit()
            self.con.execute('CREATE TABLE img_record(\
              img_url CHAR PRIMARY KEY ,\
              page_id INT,\
              desciption CHAR ,\
              is_done INT DEFAULT 0,\
              record_time DATE ,\
              foreign key (page_id) references page_record(page_id) on delete cascade on update cascade)')
            self.con.commit()
        else:
            self.con = sqlite3.connect(self.db_path)

    def add_page_record(self, page_id,url, description):
        now = datetime.datetime.now()
        try:
            self.con.execute('INSERT INTO page_record VALUES (?,?,?,?,?,?)', (page_id, url, 0, description.decode('utf-8'), 0, now))
            self.con.commit()
        except:
            e = sys.exc_info()[0]
            print 'add_check_record except:' + str(e)
            debug_info(e)
        pass

    def add_img_record(self, img_url, page_id, description):
        now = datetime.datetime.now()
        try:
            self.con.execute('INSERT INTO img_record VALUES (?,?,?,?,?,?)', (img_url, page_id, 0, description.decode('utf-8'), 0, now))
            self.con.commit()
        except:
            e = sys.exc_info()[0]
            print 'add_img_record except:' + str(e)
            debug_info(e)
        pass

    def check_page_record(self,page_id):
        try:
            self.con.execute('update page_record set is_done=1\
            where page_id=(?)', ( page_id, ))
            self.con.commit()
        except:
            e = sys.exc_info()[0]
            print 'check_page_record except:' + str(e)
            debug_info('check_page_record except:' + str(e))
        pass

    def check_img_record(self, page_url):
        try:
            self.con.execute('update img_record set is_done=1\
            where img_url=(?)', ( page_url, ))
            self.con.commit()
        except:
            e = sys.exc_info()[0]
            print 'add_img_record except:' + str(e)
            debug_info('check_img_record except:' + str(e))
        pass

    def get_page_record(self, page_id):
        now = datetime.datetime.now()
        try:
            self.con.execute('select * from page_record where page_record.page_id=(?)',(page_id, ))
            self.con.commit()

        except:
            e = sys.exc_info()[0]
            print 'add_check_record except:' + str(e)
            debug_info(e)
        pass

    def get_imgurl_of_page_record(self, page_id):
        now = datetime.datetime.now()
        try:
            self.con.execute('select * from img_record where img_record.page_id=(?)', (page_id,))
            self.con.commit()
        except:
            e = sys.exc_info()[0]
            print 'add_check_record except:' + str(e)
            debug_info(e)
        pass

    def filter_page_urls(self, data):
        #for page in range(1000):
        #    page_url = 'http://hkpic-forum.xyz/forum-18-%d' % page + '.html'
        #with open('page.html') as fd:
        #    data = fd.read()
            #prog = re.compile('a href="thread-\d{4,9}-1-1.html" .*?title=".*?" class="z"')
        m = re.findall('a href="thread-(?P<main_id>\d{4,9})(?P<sub_url>-\d{1,6}-\d{1,6}.html)" .*?title="(?P<title>.*?)" class="z"', data)
            #m = prog.findall(data)
            #print data
        ret_list = list()
        for url in m:
            (main_id, sub_url, title) = url
            print 'thread-' + main_id + sub_url + title
            tmp_dict = dict()
            tmp_dict['page_id'] = int(main_id)
            tmp_dict['url'] = 'http://hkpic-forum.xyz/thread-'+ main_id + sub_url
            tmp_dict['description'] = title
            ret_list.append(tmp_dict)
        print 'total:' + str(len(m))
        return ret_list
        pass

    def generate_page_url(self):
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        'Referer':'http://hkpic-forum.xyz/forum.php?gid=1',
                        }
        min_page = 4271873
        try_count = 0
        err_flag = 0
        for page in range(1, 1000):
            page_url = 'http://hkpic-forum.xyz/forum-18-%d' % page + '.html'
            print page_url
            req_login = urllib2.Request(
                url=page_url,
                headers=http_headers
            )
            while True:
                try:
                    data = urllib2.urlopen(req_login, timeout=10).read()
                    err_flag = 0
                except:
                    err_flag = 1
                if err_flag:
                    if try_count > 10:
                        try_count = 0
                        print 'page parse fail : %s' % page_url
                        debug_info('page parse fail url:' + page_url)
                        break
                    else:
                        print 'url parse timeout, try again %d:%s' %(try_count, page_url)
                        try_count += 1
                else:
                    break

            page_list =  self.filter_page_urls(data)
            for page in page_list:
                print 'store page %s' % str(page)
                self.add_page_record(page['page_id'], page['url'], page['title'])
            #e = sys.exc_info()[0]
            #print e
        #with open('page.html', 'w+') as fd:
        #    fd.write(data)
        pass

    def parse_single_page_pipe(self, index, con):
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        'Referer': 'http://hkpic-forum.xyz/forum.php?gid=1',
                        }
        min_page = 4271873
        try_count = 0
        err_flag = 0
        page_url = 'http://hkpic-forum.xyz/forum-18-%d' % index + '.html'
        print page_url
        req_login = urllib2.Request(
            url=page_url,
            headers=http_headers
        )
        while True:
            try:
                data = urllib2.urlopen(req_login, timeout=10).read()
                err_flag = 0
            except:
                err_flag = 1
            if err_flag:
                if try_count > 10:
                    try_count = 0
                    print 'page parse fail : %s' % page_url
                    debug_info('page parse fail url:' + page_url)
                    break
                else:
                    print 'url parse timeout, try again %d:%s' % (try_count, page_url)
                    try_count += 1
            else:
                break
        page_list = self.filter_page_urls(data)
        con.send(page_list)
        pass

    def parse_single_page_data(self, page_url):
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        'Referer': 'http://hkpic-forum.xyz/forum.php?gid=1',
                        }
        try_count = 0
        print page_url
        req_login = urllib2.Request(
            url=page_url,
            headers=http_headers
        )
        while True:
            try:
                data = urllib2.urlopen(req_login, timeout=10).read()
                err_flag = 0
            except:
                err_flag = 1
            if err_flag:
                if try_count > 10:
                    try_count = 0
                    print 'detail page parse fail : %s' % page_url
                    debug_info('detail page parse fail url:' + page_url)
                    return None
                else:
                    print 'url parse timeout, try again %d:%s' % (try_count, page_url)
                    try_count += 1
            else:
                break
        return data
        pass

    def parse_pages_imgurls_from_pageurl_pipe(self, con, record_con):
        while True:
            if con.poll(3):
                page_record = con.recv()  # prints "[42, None, 'hello']"
                if type(page_record) == str and page_record == 'quit':
                    print "done"
                    break
                data = self.parse_single_page_data(page_record['url'])
                if data:
                    img_urls = self.get_imgurls_from_data(data)
                for imgurl in img_urls:
                    record_con.send(imgurl)
            else:
                print 'parse_pages_imgurls_from_pageurl_pipe need more task'
                con.send('ask')

    def parse_imgdata_from_imgurl_pipe(self, con):
        while True:
            if con.poll(3):
                img_record = con.recv()  # prints "[42, None, 'hello']"
                if type(img_record) == str and img_record == 'quit':
                    print "done"
                    break
                self.download_img(img_record['url'])
            else:
                print 'parse_imgdata_from_imgurl_pipe need more task'
                con.send('ask')

    def get_imgurls_from_data(self, data):
        # http://img.bipics.net/data/attachment/forum/201610/14/101421bvx3f83jvq4xyyo3.jpg"
        img_names = re.findall('http://img.bipics.net/data/attachment/forum/(?P<time>\d{4,6}/\d{1,2}/)(?P<img_name>.*?)"', data)
        count = 0
        ret = list()
        for img_name in img_names:
            (folde, name) = img_name
            if 'thumb' not in name:
                ret.append('http://img.bipics.net/data/attachment/forum/' + folde + name)
                count += 1
        print 'total count : %d' % count
        return ret
        pass

    def get_img_tail(self, url):
        m = re.search('.\w{3,4}$', url)
        return m.group(0)
        pass

    def download_img(self, urls):
        title = time.strftime('%Y_%m_%d_%H_%M_%S_')
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        }
        count = 0
        print type(urls)
        if type(urls) != 'list':
            tmp = urls[:]
            urls = list()
            urls.append(tmp)
        print type(urls)
        for url in urls:
            print 'url: %s' % url
            req_login = urllib2.Request(
                url=url,
                headers=http_headers
            )
            try:
                data = urllib2.urlopen(req_login).read()
                img_name = title + str(count) + self.get_img_tail(url)
                file_path = os.path.join(self.img_store_path, img_name)
                print 'filename: %s' % img_name
                with open(file_path, 'wb+') as fd:
                    fd.write(data)
                count += 1
            except urllib2.HTTPError:
                e = sys.exc_info()[0]
                print e
                debug_info(e)
        pass

    def ask_pages_to_process(self, con):
        while True:
            if con.poll(3):
                tmp = con.recv()  # prints "[42, None, 'hello']"
                if type(tmp) == str and tmp == 'quit':
                    print "done"
                    break
                print tmp
                time.sleep(1)
            else:
                print 'timeout'
                con.send('ask')
        pass

    def ask_imgs_to_process(self, con):
        while True:
            if con.poll(3):
                tmp = con.recv()  # prints "[42, None, 'hello']"
                if type(tmp) == str and tmp == 'quit':
                    print "done"
                    break
                print tmp
                time.sleep(1)
            else:
                print 'timeout'
                con.send('ask')
        pass

    def pipe_single_handle_imgurl_store(self, con):
        while True:
            img_record = con.recv()
            self.add_img_record( img_record['img_url'], img_record['page_id'], img_record['description'])
        pass

    def pipe_single_handle_imgurl_store_check(self, con):
        while True:
            img_record = con.recv()
            self.check_page_record(img_record['img_url'])
        pass

    def pipe_single_handle_pageurl_store(self, con):
        while True:
            page_record = con.recv()
            self.check_page_record(page_record['page_id'])

    def start_parse(self):
        parent_conn, child_conn = Pipe()
        p = multiprocessing.Process(target=self.ask_pages_to_process, args=(child_conn,) )
        p.start()
        p = multiprocessing.Process(target=self.ask_pages_to_process, args=(child_conn,) )
        p.start()
        for y in range(10):
            for i in range(10):
                parent_conn.send(i)
            tmp = parent_conn.recv()
            print 'give more'
        parent_conn.send('quit')
        parent_conn.send('quit')
        parent_conn.close()
        pass


def debug_info(information):
    debug_file = 'debug.log'
    if not os.path.exists('debug.log'):
        with open(debug_file, 'w+') as fd:
            pass
    with open(debug_file, 'a') as fd:
        if callable(information):
            fd.write(str(information) + time.strftime('     %H:%M:%S %d %b') + '\n')
        else:
            fd.write(information + time.strftime('     %H:%M:%S %d %b') + '\n')
    pass


if __name__ == '__main__':
    #hk_login = LoginMethod()
    #hk_login.get_config()
    #hk_login.do_login()

    scrap = ScrapImg()
    #scrap.add_page_record(1,'url', '你好'.decode('utf-8'))
    #scrap.add_img_record(1,'url', 'http://', '你好')
    #data = hk_login.get_url_data('http://hkpic-forum.xyz/thread-4244506-1-1.html')
    #with open('page.html', 'r') as fd:
    #    data = fd.read()
    #scrap.get_img_url(data)
    #with open('page.html', 'w+') as fd:
    #    fd.write(data)
    #scrap.filter_page_urls('xx')
    #scrap.generate_page_url()
    scrap.start_parse()
    #scrap.download_img('http://img.bipics.net/data/attachment/block/aa/aab8bb730c4e2c4dc489128235424dc9.jpg')
    #print hk_login