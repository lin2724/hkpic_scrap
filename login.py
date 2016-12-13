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
import socket
import mutex
import Queue
from multiprocessing import Process, Pipe

Config_Path = 'config.ini'
Cookie_Path = 'cookie'


class LoginMethod:
    def __init__(self, set_get_cookie = False):
        self.login_url = 'http://hkbbcc.net/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1'
        #http://hkpic-forum.xyz/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1
        self.status_url = 'http://hkbbcc.net/forum.php'#http://hkpic-forum.xyz/forum.php
        self.config_file_path = Config_Path
        self.cookie_file_path = Cookie_Path
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

    def get_status(self):
        return True
        http_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
                        '(Request-Line)':'GET /forum.php HTTP/1.1',
                        'Host':'hkbbcc.net',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                    }
        req_test = urllib2.Request(
            url=self.status_url,
            headers=http_headers
        )
        try_count = 0
        while True:
            try:
                data = urllib2.urlopen(req_test, timeout=10).read()
            except socket.timeout:
                if try_count >= 3:
                    print 'get login status timeout %d times' % try_count
                    return False
                print 'get login status timeout try again %d..' % try_count
                try_count += 1
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
                             'Referer': self.status_url,
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
            try_count = 0
            while True:
                try:
                    data = urllib2.urlopen(req_login, timeout=10).read()
                except socket.timeout as e:
                    print 'error occurred %s' % e
                    if try_count>3:
                        exec 1
                    else:
                        try_count += 1
                        continue
                break

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


class MyUrlOpenErr(Exception):
    pass

class ScrapImg:
    def __init__(self):
        self.db_path = 'record.db'
        self.img_store_path = 'img'
        self.max_thread = 20
        self.img_download_trytime = 5
        self.page_download_trytime = 3

        self.cookie_file_path = Cookie_Path
        self.do_init()
        pass

    def do_init(self):
        self.data_base_init()
        if not os.path.exists(self.img_store_path):
            os.mkdir(self.img_store_path)

    def build_openner_with_cookie(self):
        cookie_jar = cookielib.LWPCookieJar(self.cookie_file_path)
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        cookie_support = urllib2.HTTPCookieProcessor(cookie_jar)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)

    def data_base_init(self):
        print 'ScrapImg instance init'
        if not os.path.exists(self.db_path):
            self.con = sqlite3.connect(self.db_path)
            self.con.execute('CREATE TABLE page_record(\
              page_id INT PRIMARY KEY ,\
              url char,\
              count INT DEFAULT 0,\
              description CHAR ,\
              is_done INT DEFAULT 0,\
              record_time DATE )')
            self.con.commit()
            self.con.execute('CREATE TABLE img_record(\
              img_url CHAR PRIMARY KEY ,\
              page_id INT,\
              description CHAR ,\
              is_done INT DEFAULT 0,\
              record_time DATE ,\
              foreign key (page_id) references page_record(page_id) on delete cascade on update cascade)')
            self.con.commit()
        else:
            self.con = sqlite3.connect(self.db_path)

    def add_page_record(self, page_id, url, description):
        now = datetime.datetime.now()
        con = sqlite3.connect(self.db_path)
        try:
            con.execute('INSERT INTO page_record VALUES (?,?,?,?,?,?)', (page_id, url, 0, description.decode('utf-8'), 0, now,))
            con.commit()
        except:
            e = sys.exc_info()[0]
            #print 'add_page_record except:' + str(e)
        con.close()
        pass

    def add_img_record(self, img_url, page_id, description):
        now = datetime.datetime.now()
        con = sqlite3.connect(self.db_path)
        decode_utf8 = True
        try:
            description.decode('utf-8')
        except UnicodeEncodeError:
            decode_utf8 = False
        try:
            if decode_utf8:
                con.execute('INSERT INTO img_record VALUES (?,?,?,?,?)',
                            (img_url, page_id, description.decode('utf-8'), 0, now))
            else:
                con.execute('INSERT INTO img_record VALUES (?,?,?,?,?)',
                            (img_url, page_id, description, 0, now))

            con.commit()
        except:
            e = sys.exc_info()[0]
            #print 'add_img_record except:' + str(e)
            debug_info(3, e)
        con.close()
        pass

    def check_page_record(self,page_id):
        con = sqlite3.connect(self.db_path)
        try:
            con.execute('update page_record set is_done=1\
            where page_id=(?)', ( page_id, ))
            con.commit()
        except:
            e = sys.exc_info()[0]
            #print 'check_page_record except:' + str(e)
            debug_info(3, 'check_page_record except:' + str(e))
        con.close()
        pass

    def uncheck_page_record(self,page_id):
        con = sqlite3.connect(self.db_path)
        con.execute('update page_record set is_done=0\
        where page_id=(?)', ( page_id, ))
        con.commit()
        con.close()
        pass

    def check_img_record(self, img_url):
        con = sqlite3.connect(self.db_path)
        try:
            con.execute('update img_record set is_done=1\
            where img_url=(?)', ( img_url, ))
            con.commit()
        except:
            e = sys.exc_info()[0]
            #print 'check_img_record except:' + str(e)
            debug_info(3, 'check_img_record except:' + str(e))
        con.close()
        pass

    def uncheck_img_record(self, img_url):
        con = sqlite3.connect(self.db_path)
        con.execute('update img_record set is_done=0\
        where img_url=(?)', ( img_url, ))
        con.commit()
        con.close()
        pass

    def get_page_record(self, page_id):
        now = datetime.datetime.now()
        con = sqlite3.connect(self.db_path)
        try:
            con.execute('select * from page_record where page_record.page_id=(?)',(page_id, ))
            con.commit()

        except:
            e = sys.exc_info()[0]
            print 'get_page_record except:' + str(e)
            debug_info(3, e)
        con.close()
        pass

    def get_imgurl_of_page_record(self, page_id):
        now = datetime.datetime.now()
        con = sqlite3.connect(self.db_path)
        try:
            con.execute('select * from img_record where img_record.page_id=(?)', (page_id,))
            con.commit()
        except:
            e = sys.exc_info()[0]
            print 'get_imgurl_of_page_record except:' + str(e)
            debug_info(3, e)
        con.close()
        pass

    def get_page_records_from_data(self, data):
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
            #print 'thread-' + main_id + sub_url + title
            tmp_dict = dict()
            tmp_dict['page_id'] = int(main_id)
            tmp_dict['url'] = 'http://hkbbcc.net/thread-'+ main_id + sub_url
            tmp_dict['description'] = title
            ret_list.append(tmp_dict)
        print 'pageurl total:' + str(len(m))
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
            page_url = 'http://hkbbcc.net/forum-18-%d' % page + '.html'
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
                        debug_info(1, 'page parse timeout fail url:' + page_url)
                        break
                    else:
                        print 'url parse timeout, try again %d:%s' %(try_count, page_url)
                        try_count += 1
                else:
                    break

            page_records =  self.get_page_records_from_data(data)
            for page_record in page_records:
                #print 'store page %s' % str(page)
                self.add_page_record(page_record['page_id'], page_record['url'], page_record['title'])
            #e = sys.exc_info()[0]
            #print e
        #with open('page.html', 'w+') as fd:
        #    fd.write(data)
        pass

    def parse_pages_task(self, task_queue, db_queue):
        self.build_openner_with_cookie()
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        'Referer': 'http://hkpic-forum.xyz/forum.php?gid=1',
                        }
        while True:
            page_index = task_queue.get()  # prints "[42, None, 'hello']"
            if type(page_index) == str and page_index == 'quit':
                print "parse_pages_task done quit"
                break
            page_url = 'http://hkbbcc.net/forum-18-%d' % page_index + '.html'
            #print page_url
            req_login = urllib2.Request(
                url=page_url,
                headers=http_headers
            )
            try_count = 0
            while True:
                try:
                    data = urllib2.urlopen(req_login, timeout=10).read()
                    page_records = self.get_page_records_from_data(data)
                    if len(page_records) == 0:
                        with open('page_data.html', 'w+') as fd:
                            fd.write(data)
                        print 'homepage done:%s' % page_url
                    else:
                        db_queue.put(page_records)
                except socket.timeout:
                    if try_count >= 3:
                        print 'page parse fail : %s' % page_url
                        debug_info(1, 'page parse timeout fail url:' + page_url)
                        break
                    else:
                        print 'url parse timeout, try again %d:%s' % (try_count, page_url)
                        try_count += 1
                        continue
                except:
                    e = sys.exc_info()[0]
                    print 'ERROR:urlopen fail %s' % str(e)
                    debug_info(0, e)
                break
            pass


    def parse_single_page_data(self, page_url):
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        'Referer': 'http://hkpic-forum.xyz/forum.php?gid=1',
                        }

        debug_info(5, page_url)
        req_login = urllib2.Request(
            url=page_url,
            headers=http_headers,
        )
        try_count = 0
        data = None
        while True:
            try:
                data = urllib2.urlopen(req_login, timeout=10).read()
                try_count = 0
                break
            except socket.timeout:
                try_count += 1
                if try_count >self.page_download_trytime:
                    print 'detail page parse fail : %s' % page_url
                    debug_info(1, 'detail page parse timeout fail url:' + page_url)
                    break
                else:
                    print 'url parse timeout, try again %d:%s' % (try_count, page_url)
                    continue
            except:
                e = sys.exc_info()[0]
                print 'ERROR:open url fail %s' % str(e)
                debug_info(0, e)
                raise MyUrlOpenErr('ERROR:open url fail %s' % str(e))
        return data
        pass

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
        print 'imgurl total count : %d' % count
        return ret
        pass

    def get_img_tail(self, url):
        m = re.search('.\w{3,4}$', url)
        return m.group(0)
        pass

    def give_imgfile_name(self, page_id, img_tail):
        for i in range(1000):
            img_name = str(page_id)+ '_' + str(i) + img_tail
            file_path = os.path.join(self.img_store_path, img_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w+') as fd:
                    pass#occupied this file
                return img_name

    def delete_imgfile(self, img_name):
        file_path = os.path.join(self.img_store_path, img_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    def download_img(self, urls, img_name=None):
        title = time.strftime('%Y_%m_%d_%H_%M_%S_')
        http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        }
        count = 0
        #print type(urls)
        if type(urls) != 'list':
            tmp = urls[:]
            urls = list()
            urls.append(tmp)
        ret = False
        for url in urls:
            try_count = 0
            while True:
                print 'url: %s' % url
                req_login = urllib2.Request(
                    url=url,
                    headers=http_headers
                )
                try:
                    data = urllib2.urlopen(req_login, timeout=20).read()
                    if not img_name:
                        img_name = title + str(count) + self.get_img_tail(url)
                    file_path = os.path.join(self.img_store_path, img_name)
                    print 'filename: %s' % img_name
                    with open(file_path, 'wb+') as fd:
                        fd.write(data)
                    ret = True
                    break
                except socket.timeout:
                    if try_count >= self.img_download_trytime:
                        print 'download img fail %s' % url
                        debug_info(5, 'download img fail %s' % url)
                        return False
                    else:
                        try_count += 1
                        print 'try again to download %s' % url
                except:
                    e = sys.exc_info()[0]
                    print 'ERROR:download img fail %s' % str(e)
                    debug_info(0, e)
                    raise MyUrlOpenErr('ERROR:download img fail %s' % str(e))
        return ret
        pass

    def download_img_task(self, task_queue, db_uncheck_queue, filename_mutex):
        self.build_openner_with_cookie()
        while True:
            img_records = task_queue.get()  # prints "[42, None, 'hello']"
            if type(img_records) == str and img_records == 'quit':
                print "done"
                break
            for img_record in img_records:
                (img_url, page_id, description, id_done, record_time) = img_record
                with filename_mutex:
                    img_name = self.give_imgfile_name(page_id=page_id,img_tail=self.get_img_tail(img_url))
                try:
                    ret = self.download_img(urls=img_url, img_name=img_name)
                    print 'img download done %s' % img_name
                except MyUrlOpenErr:
                    continue #unexpect err has happend,pass this url
                if not ret:
                    img_record_dict = dict()
                    img_record_dict['img_url'] = img_url
                    db_uncheck_queue.put(img_record_dict)
                    self.delete_imgfile(img_name)#delete occupied file
            time.sleep(3)#wait for datebase check complete
        pass

    def parse_imgurls_task(self, task_queue, db_store_queue, db_uncheck_queue):
        #print 'parse_imgurls_task'
        self.build_openner_with_cookie()
        while True:
            page_records = task_queue.get()  # prints "[42, None, 'hello']"
            #print page_records
            if type(page_records) == str and page_records == 'quit':
                break
            for page_record in page_records:
                (page_id,url,_,description,_,record_time) = page_record
                try:
                    data = self.parse_single_page_data(url)
                except MyUrlOpenErr:
                    continue #pass this url as if it has been done
                    pass
                if data:
                    img_urls = self.get_imgurls_from_data(data)
                    print 'page get imgurls done %s' % url
                    for img_url in img_urls:
                        imgurl_record = dict()
                        imgurl_record['img_url'] = img_url
                        imgurl_record['page_id'] = page_id
                        imgurl_record['description'] = description
                        db_store_queue.put(imgurl_record)
                else:
                    page_record_dict = dict()
                    page_record_dict['page_id'] = page_id
                    db_uncheck_queue.put(page_record_dict)
            time.sleep(3)#wait for database check complete

    def parse_imgdata_from_imgurl_pipe(self, con):
        while True:
            if con.poll(3):
                img_record = con.recv()  # prints "[42, None, 'hello']"
                if type(img_record) == str and img_record == 'quit':
                    #print "done"
                    break
                self.download_img(img_record['url'])
            else:
                print 'parse_imgdata_from_imgurl_pipe need more task'
                con.send('ask')

    def get_pages_to_process(self, max_pages):
        con = sqlite3.connect(self.db_path)
        cur = con.execute("select * from page_record where page_record.is_done=0 limit ?", (max_pages,))
        ret_list =cur.fetchall()
        con.close()
        return ret_list
        pass

    def get_imgs_to_process(self, max_imgs=20):
        con = sqlite3.connect(self.db_path)
        cur = con.execute("select * from img_record where img_record.is_done=0 limit ?", (max_imgs,))
        ret_list = cur.fetchall()
        con.close()
        return ret_list
        pass

    def pipe_handle_imgurls_store(self, task_queue):
        while True:
            img_records = task_queue.get()
            if type(img_records) == str and img_records == 'quit':
                print 'pipe_single_handle_pageurl_store received command to quit!'
                return
            if type(img_records) == list:
                for img_record in img_records:
                    self.add_img_record( img_record['img_url'], img_record['page_id'], img_record['description'])
            else:
                self.add_img_record(img_records['img_url'], img_records['page_id'], img_records['description'])
        pass

    def pipe_handle_imgurls_check(self, task_queue):
        while True:
            img_records = task_queue.get()
            if type(img_records) == str and img_records == 'quit':
                print 'pipe_single_handle_pageurl_store received command to quit!'
                return
            if type(img_records) == list:
                for img_record in img_records:
                    self.check_img_record( img_record['img_url'])
            else:
                self.check_img_record(img_records['img_url'])
        pass

    def pipe_handle_imgurls_uncheck(self, task_queue):
        while True:
            img_records = task_queue.get()
            if type(img_records) == str and img_records == 'quit':
                print 'pipe_single_handle_pageurl_store received command to quit!'
                return
            if type(img_records) == list:
                for img_record in img_records:
                    self.uncheck_img_record( img_record['img_url'])
            else:
                self.uncheck_img_record(img_records['img_url'])
        pass


    def pipe_handle_pages_store(self, task_queue):
        print 'page-store process start'
        while True:
            page_records = task_queue.get()
            if type(page_records) == str and page_records == 'quit':
                print 'pipe_single_handle_pageurl_store received command to quit!'
                return
            if type(page_records) == list:
                for page_record in page_records:
                    #print page_record
                    self.add_page_record(page_record['page_id'], page_record['url'], page_record['description'])
            else:
                self.add_page_record(page_records['page_id'], page_records['url'], page_records['description'])

    def pipe_handle_pages_check(self, task_queue):
        print 'page-store process start'
        while True:
            page_records = task_queue.get()
            if type(page_records) == str and page_records == 'quit':
                print 'pipe_single_handle_pageurl_store received command to quit!'
                return
            if type(page_records) == list:
                for page_record in page_records:
                    #print page_record
                    self.check_page_record(page_record['page_id'])
            else:
                self.check_page_record(page_records['page_id'])

    def pipe_handle_pages_uncheck(self, task_queue):
        print 'page-store process start'
        while True:
            page_records = task_queue.get()
            if type(page_records) == str and page_records == 'quit':
                print 'pipe_single_handle_pageurl_store received command to quit!'
                return
            if type(page_records) == list:
                for page_record in page_records:
                    #print page_record
                    self.uncheck_page_record(page_record['page_id'])
            else:
                self.uncheck_page_record(page_records['page_id'])

    def start_pages_parse_task(self):
        task_queue = multiprocessing.Queue(50)
        db_queue = multiprocessing.Queue(50)
        p = multiprocessing.Process(target=self.pipe_handle_pages_store, args=(db_queue,))
        p.start()
        for i in range(self.max_thread):
            p = multiprocessing.Process(target=self.parse_pages_task, args=(task_queue, db_queue))
            p.start()
        for i in range(1000):
            task_queue.put(i)
        for i in range(self.max_thread):
            task_queue.put('quit')
        pass

    def start_imgurl_parse_task(self):
        max_queue = 50
        task_queue = multiprocessing.Queue(max_queue)
        db_store_queue = multiprocessing.Queue(max_queue)
        db_uncheck_queue = multiprocessing.Queue(max_queue)
        p = multiprocessing.Process(target=self.pipe_handle_imgurls_store, args=(db_store_queue,))
        p.start()
        p = multiprocessing.Process(target=self.pipe_handle_pages_uncheck, args=(db_uncheck_queue,))
        p.start()
        for i in range(self.max_thread):
            p = multiprocessing.Process(target=self.parse_imgurls_task,
                                        args=(task_queue, db_store_queue, db_uncheck_queue))
            p.start()
        while True:
            page_records = self.get_pages_to_process(1)
            if len(page_records) == 0:
                print 'no more page to parse imgurls..'
                break
            print 'put one page_record'
            task_queue.put(page_records)
            for page_record in page_records:
                (page_id, url, _, description, _, record_time) = page_record
                self.check_page_record(page_id=page_id)
        for i in range(self.max_thread):
            task_queue.put('quit')
        pass

    def start_img_download_task(self):
        max_queue = 50
        task_queue = multiprocessing.Queue(max_queue)
        db_uncheck_queue = multiprocessing.Queue(max_queue)
        filename_mutex = multiprocessing.Lock()
        p = multiprocessing.Process(target=self.pipe_handle_imgurls_uncheck, args=(db_uncheck_queue,))
        p.start()
        for i in range(self.max_thread):
            p = multiprocessing.Process(target=self.download_img_task, args=(task_queue, db_uncheck_queue, filename_mutex))
            p.start()
        while True:
            img_records = self.get_imgs_to_process(1)
            if len(img_records) == 0:
                print 'no more imgurl to parse img..'
                break
            print 'put one img_record'
            task_queue.put(img_records)
            for img_record in img_records:
                (img_url, page_id, description, id_done, record_time) = img_record
                self.check_img_record(img_url=img_url)
        for i in range(self.max_thread):
            task_queue.put('quit')

    def start_parse(self):
        p = multiprocessing.Process(target=self.start_pages_parse_task )
        p.start()
        time.sleep(20)
        p = multiprocessing.Process(target=self.start_imgurl_parse_task )
        p.start()
        time.sleep(20)
        p = multiprocessing.Process(target=self.start_img_download_task )
        p.start()
        pass


def debug_info(level, information):
    debug_level = 1
    if level > debug_level:
        return
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
    scrap.start_parse()
    #page_records = scrap.get_pages_to_process(20)
    #print page_records
    #scrap.download_img('http://img.bipics.net/data/attachment/forum/201612/09/202911u9dil762u67h0u69.png.thumb.jpg')
    #scrap.get_pages_to_process()
    #scrap.get_pages_to_process(max=10)
    #scrap.get_imgs_to_process()
    #scrap.add_page_record(1,'fuckxxx', '你好')
    #scrap.add_img_record(1,'url', 'http://', '你好')
    #data = hk_login.get_url_data('http://hkpic-forum.xyz/thread-4244506-1-1.html')
    #with open('page.html', 'r') as fd:
    #    data = fd.read()
    #scrap.get_img_url(data)
    #with open('page.html', 'w+') as fd:
    #    fd.write(data)
    #scrap.generate_page_url()
    #scrap.start_parse()
    #scrap.download_img('http://img.bipics.net/data/attachment/block/aa/aab8bb730c4e2c4dc489128235424dc9.jpg')
    #print hk_login