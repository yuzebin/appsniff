#!/usr/bin/env python
#-*- coding: utf-8 -*-
import appstore2 as appstore
import copy
import re
import socks

def facade_buy(func):
    def facade_func(*args, **kargs):
        print "start func : " + func.__name__
        f = func(*args, **kargs)
        print "end func : " + func.__name__
        print
        return f
    return facade_func

@facade_buy
def buy_app(ac_list):
    buy_order_body = """as you know , you should put your app purchase order form in XML here ...
    """
    go_buy(buy_order_body,ac_list)

def go_buy(body,ac_list):
    k = 0
    for account in ac_list:
        k += 1
        print
        print "number: ", k
        try:
            asd = appstore.AppStore(*account)
            asd.gogogo(body)
            print account[0], account[2], "ok!"
        except:
            pass

if __name__ == '__main__':
    # store cn
    store_front = "143465-19,4"

    # account list
    cn_app_id = [
        ("your apple_id here", "your password here", "your guid here", store_front ),
    ]

    buy_app(cn_app_id)
