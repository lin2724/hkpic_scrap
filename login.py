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
        self.http_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Referer': 'http://hkpic-forum.xyz/forum.php',
                        # 'Cookie': 'PHPSESSID=sq9oris1vovpvnou9rl603p5m0; Ovo6_2132_noticeTitle=1; Ovo6_2132_saltkey=MSTWVgAS; Ovo6_2132_lastvisit=1479612304; Ovo6_2132_lastact=1479615904%09forum.php%09',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        # 'Content-Length': '113',
                        # '': '',
                        }

        self.set_get_cookie = set_get_cookie
        self.do_init()
        pass

    def __str__(self):
        return 'username:%s,password:%s, login_url:%s' %(self.username, self.password, self.login_url)

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

    def do_login(self):
        login_data = dict()
        login_data['fastloginfield'] = 'username'
        login_data['username'] = r'lin2724'
        login_data['cookietime'] = '2592000'
        login_data['password'] = 'lin13721458201'
        login_data['quickfoward'] = 'yes'
        login_data['handlekey'] = 'ls'

        if self.set_get_cookie:
            cookie_jar2 = cookielib.LWPCookieJar()
            cookie_support2 = urllib2.HTTPCookieProcessor(cookie_jar2)
            opener2 = urllib2.build_opener(cookie_support2, urllib2.HTTPHandler)
            urllib2.install_opener(opener2)

            login_data = urllib.urlencode(login_data)
            req_login = urllib2.Request(
                url=self.login_url,
                data=login_data,
                headers=self.http_headers
            )
            data = urllib2.urlopen(req_login).read()
            with open('hk_login_resault.html', 'w+') as fd:
                fd.write(data)
                print ('login end')
        pass

if __name__ == '__main__':
    hk_login = LoginMethod(set_get_cookie=True)
    hk_login.get_config()
    hk_login.do_login()
    print hk_login