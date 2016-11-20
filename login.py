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
thread_number = 30')

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
        data = urllib2.urlopen(req_test).read()
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
        login_data['username'] = r'lin2724'
        login_data['cookietime'] = '2592000'
        login_data['password'] = 'lin13721458201'
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


class ScrapImg:
    def __init__(self):
        pass


if __name__ == '__main__':
    hk_login = LoginMethod()
    hk_login.get_config()
    hk_login.do_login()
    print hk_login