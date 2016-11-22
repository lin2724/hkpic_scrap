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
            self.con.execute('CREATE TABLE url_record(\
              url CHAR PRIMARY KEY ,\
              count INT DEFAULT 0,\
              desciption CHAR ,\
              is_done INT DEFAULT 0,\
              record_time DATE )')
            self.con.commit()

    def add_record(self, url, count, description, is_done):
        now = datetime.datetime.now()
        try:
            self.con.execute('INSERT INTO url_record VALUES (?,?,?,?,?)', (url, count, description, 1, now))
            self.con.commit()
        except:
            e = sys.exc_info()[0]
            print e
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
        for url in m:
            (main_id, sub_url, title) = url
            print 'thread-' + main_id + sub_url + title
        print 'total:' + str(len(m))
        pass

    def generate_page_url(self):
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        'Referer':'http://hkpic-forum.xyz/forum.php?gid=1',
                        }
        min_page = 4271873
        for page in range(1, 3):
            page_url = 'http://hkpic-forum.xyz/forum-18-%d' % page + '.html'
            print page_url
            req_login = urllib2.Request(
                url=page_url,
                headers=http_headers
            )
            data = urllib2.urlopen(req_login, timeout=10).read()
            self.filter_page_urls(data)
        with open('page.html', 'w+') as fd:
            fd.write(data)

        pass

    def get_img_url(self, data):
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
    hk_login = LoginMethod()
    hk_login.get_config()
    hk_login.do_login()

    scrap = ScrapImg()

    #data = hk_login.get_url_data('http://hkpic-forum.xyz/thread-4244506-1-1.html')
    #with open('page.html', 'r') as fd:
    #    data = fd.read()
    #scrap.get_img_url(data)
    #with open('page.html', 'w+') as fd:
    #    fd.write(data)
    #scrap.filter_page_urls('xx')
    scrap.generate_page_url()
    #scrap.download_img('http://img.bipics.net/data/attachment/block/aa/aab8bb730c4e2c4dc489128235424dc9.jpg')
    #print hk_login