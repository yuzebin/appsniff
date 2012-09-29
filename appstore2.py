#!/usr/bin/env python
#-*- coding: utf-8 -*-
import pycurl
import cStringIO as StringIO
import urllib
import re
import copy

"""thanks for @feisan to write this file , you can find his code on https://github.com/feisan
"""

class AppStore(object):
    def __init__(self, apple_id, password, guid, store, verbose=False):
        self.apple_id = apple_id
        self.password = password
        self.guid = guid
        self.store = store
        self.verbose = verbose
        http = pycurl.Curl()
        #http.setopt(pycurl.PROXY, "172.16.0.40")
        #http.setopt(pycurl.PROXYPORT, 8888)
        #http.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)
        http.setopt(pycurl.SSL_VERIFYHOST,0)
        http.setopt(pycurl.SSL_VERIFYPEER,0)
        http.setopt(pycurl.FOLLOWLOCATION, 1)
        http.setopt(pycurl.MAXREDIRS, 5)
        http.fp = StringIO.StringIO()
        http.setopt(pycurl.WRITEFUNCTION, http.fp.write)
        http.setopt(pycurl.COOKIEFILE, "")
        http.setopt(pycurl.COOKIEJAR, "")
        http.setopt(pycurl.USERAGENT, "iTunes-iPhone/5.1.1 (6; 16GB; dt:73)")
        http.setopt(pycurl.TCP_NODELAY, 1)
        http.setopt(pycurl.ENCODING, 'gzip, deflate')
        self.http = http

        self.headers = [
            "User-Agent: iTunes-iPhone/5.1.1 (6; 16GB; dt:73)",
            "X-Apple-Client-Application: Software",
            "X-Apple-Client-Versions: iBooks/2.1.1; iTunesU/1.1.1; GameCenter/2.0",
            "X-Apple-Connection-Type: WiFi",
            "X-Apple-Store-Front: " + self.store,
            "Expect:",
        ]

        self.passwordToken = None
        self.clearToken = None
        self.dsPersonId = None
        self.buyProduct_url = None
        self.songDownloadDone_url = None
        self.Pod = None

    def login(self):
        login_url = "https://p49-buy.itunes.apple.com/WebObjects/MZFinance.woa/wa/authenticate"
        body = {
            "appleId" : self.apple_id,
            "rmp" : 0,
            "password" : self.password,
            "attempt" : 0,
            "accountKind" : 0,
            "guid" : self.guid,
            "createSession" : "ture",
            "why" : "signin"
        }
        url = login_url + "?" + urllib.urlencode(body)
        headers = copy.deepcopy(self.headers)
        self.http.setopt(pycurl.HTTPHEADER, headers)
        self.http.setopt(pycurl.URL, url)
        self.http.setopt(pycurl.POST, 1)
        self.http.setopt(pycurl.POSTFIELDS,  urllib.urlencode(body))
        self.http.perform()

        content = self.http.fp.getvalue()

        p1 = "<key>passwordToken</key><string>(.+?)</string>"
        m1 = re.search(p1, content)
        if m1:
            self.passwordToken = m1.group(1)
            self.headers.append("X-Token: " + self.passwordToken)
        p2 = "<key>dsPersonId</key><string>(.+?)</string>"
        m2 = re.search(p2, content)
        if m2:
            self.dsPersonId = m2.group(1)
            self.headers.append("X-Dsid: " + self.dsPersonId)
        print self.apple_id, "Dsid:", self.dsPersonId

    def get_bag(self):
        headers = copy.deepcopy(self.headers)
        url = "http://ax.init.itunes.apple.com/bag.xml?ix=2&dsid=" + self.dsPersonId
        self.http.setopt(pycurl.HTTPHEADER, headers)
        self.http.setopt(pycurl.URL, url)
        self.http.setopt(pycurl.HTTPGET, 1)
        self.http.fp.seek(0)
        self.http.fp.truncate()
        self.http.perform()
        content = self.http.fp.getvalue()
        p1 = "<key>bag</key><data>(.+?)</data>"
        m1 = re.search(p1, content)
        if not m1:
            raise RuntimeError("can't find bag data")
        bag_data = m1.group(1).decode("base64")
        p2 = "<key>buyProduct</key><string>(.+?)</string>"
        m2 = re.search(p2, bag_data)
        if not m2:
            raise RuntimeError("can't find buyProduct url")
        self.buyProduct_url = m2.group(1)
        p3 = "<key>songDownloadDone</key><string>(.+?)</string>"
        m3 = re.search(p3, bag_data)
        if not m3:
            raise RuntimeError("can't find songDownloadDone url")
        self.songDownloadDone_url = m3.group(1)
        p4 = "/p(.+?)-buy\.itunes"
        m4 = re.search(p4, self.songDownloadDone_url)
        if not m4:
            raise RuntimeError("can't find Pod")
        self.Pod = m4.group(1)
        print self.apple_id, "Pod:", self.Pod

    def buy(self, buy_order_body):
        # 这个不一定有用
        headers = copy.deepcopy(self.headers)
        url = "https://se.itunes.apple.com/WebObjects/MZStoreElements.woa/wa/buyButtonMetaData?cc=cn"
        p = "<key>salableAdamId</key>(\s+?)<string>(.+?)</string>"
        m = re.search(p, buy_order_body)
        body = "ids=" + m.group(2) +"%3Asoftware&version=2"
        self.http.setopt(pycurl.HTTPHEADER, headers)
        self.http.setopt(pycurl.URL, url)
        self.http.setopt(pycurl.POST, 1)
        self.http.setopt(pycurl.POSTFIELDS, body)
        self.http.perform()

        buy_url = self.buyProduct_url
        url = buy_url + "?guid=" + self.guid
        body = buy_order_body.replace("{{guid}}", self.guid)
        headers = copy.deepcopy(self.headers)
        headers.append("Content-Type: application/x-www-form-urlencoded")
        self.http.setopt(pycurl.HTTPHEADER, headers)
        self.http.setopt(pycurl.URL, url)
        self.http.setopt(pycurl.POST, 1)
        self.http.setopt(pycurl.POSTFIELDS, body)
        self.http.fp.seek(0)
        self.http.fp.truncate()
        self.http.perform()
        content = self.http.fp.getvalue()

        p0 = "<key>customerMessage</key><string>(.+?)</string>"
        m0 = re.search(p0, content)
        if m0:
            print "customerMessage:", m0.group(1)

        p1 = r"<key>pings</key>(\s+?)<array>(\s+?)<string>(.+?)</string>"
        m1 = re.search(p1, content)
        if not m1:
            raise RuntimeError("can't find ping url")
        ping_url = m1.group(3).replace("&amp;", "&")
        headers = copy.deepcopy(self.headers)
        self.http.setopt(pycurl.HTTPHEADER, headers)
        self.http.setopt(pycurl.URL, ping_url)
        self.http.setopt(pycurl.HTTPGET, 1)
        self.http.fp.seek(0)
        self.http.fp.truncate()
        self.http.perform()

        p2 = "<key>download-id</key><string>(.+?)</string>"
        m2 = re.search(p2, content)
        if not m2:
            raise RuntimeError("can't find download-id")
        download_id = m2.group(1)
        download_url = self.songDownloadDone_url + "?download-id=" + download_id + "&guid=" + self.guid
        headers = copy.deepcopy(self.headers)
        self.http.setopt(pycurl.HTTPHEADER, headers)
        self.http.setopt(pycurl.URL, download_url)
        self.http.setopt(pycurl.HTTPGET, 1)
        self.http.fp.seek(0)
        self.http.fp.truncate()
        self.http.perform()

    def enableMedia(self):
        url = "https://p" + self.Pod + "-buy.itunes.apple.com/WebObjects/MZFinance.woa/wa/registerMediaTypes"
        headers = copy.deepcopy(self.headers)
        headers.append("Content-Type: application/x-www-form-urlencoded")
        body = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>guid</key>
    <string>{{guid}}</string>
</dict>
</plist>"""
        body = body.replace("{{guid}}", self.guid)
        self.http.setopt(pycurl.HTTPHEADER, headers)
        self.http.setopt(pycurl.URL, url)
        self.http.setopt(pycurl.POST, 1)
        self.http.setopt(pycurl.POSTFIELDS, body)
        self.http.fp.seek(0)
        self.http.fp.truncate()
        self.http.perform()
        headers = copy.deepcopy(self.headers)
        url = "https://p" + self.Pod + "-buy.itunes.apple.com/WebObjects/MZFinance.woa/wa/enabledMediaTypes?guid=" + self.guid
        self.http.setopt(pycurl.HTTPHEADER, headers)
        self.http.setopt(pycurl.URL, url)
        self.http.setopt(pycurl.HTTPGET, 1)
        self.http.perform()
        print self.apple_id, "enableMedia ok."

    def gogogo(self, buy_order_body):
        self.login()
        self.get_bag()
        #self.enableMedia()
        self.buy(buy_order_body)
