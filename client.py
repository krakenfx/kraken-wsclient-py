#!/usr/bin/env python3

import simplejson

from decimal import Decimal
from operator import neg
from sortedcontainers.sorteddict import SortedDict

from kraken_wsclient_py import kraken_wsclient_py as client

class Orderbook(object):
    SIDE_ASK = "ask"
    SIDE_BID = "bid"
    def __init__(self):
        self.ask = SortedDict()
        self.bid = SortedDict(neg)
        self.lastupdate = None
    def copy(self):
        o = Orderbook()
        o.ask = self.ask.copy()
        o.bid = self.bid.copy()
        o.lastupdate = self.lastupdate
        return o
    def update(self, side, price, volume, timestamp = None):
        table = {
            self.SIDE_ASK : self.ask,
            self.SIDE_BID : self.bid,
        }[side]
        table[price] = volume
        if timestamp and (self.lastupdate is None or timestamp > self.lastupdate):
            self.lastupdate = timestamp
    def remove(self, side, price):
        table = {
            self.SIDE_ASK : self.ask,
            self.SIDE_BID : self.bid,
        }[side]
        del table[price]


book = Orderbook()

def my_handler(m):
    global book
    # Here you can do stuff with the messages
    #print(m)
    if list == type(m):
        updates = list(m[1].keys())
        pair = ('XBT', 'USD')
        #print("channel update:", updates, pair)
        for update in updates:
            if update in ('as', 'bs'):
                o = Orderbook()
                for side in ('as', 'bs'):
                    oside = {
                        'as' : o.SIDE_ASK,
                        'bs' : o.SIDE_BID,
                    }[side]
                    for e in m[1][side]:
                        o.update(oside, Decimal(e[0]), Decimal(e[1]), float(e[2]))
                book = o
            elif update in ('a', 'b'):
                o = book
                for side in ('a', 'b'):
                    oside = {
                        'a' : book.SIDE_ASK,
                        'b' : book.SIDE_BID,
                    }[side]
                    if side in m[1]:
                        for e in m[1][side]:
                            price = Decimal(e[0])
                            if '0.00000000' == e[1]:
                                try:
                                    book.remove(oside, price)
                                except KeyError as e:
                                    raise ValueError('asked to remove non-existing %s order %s' % (oside, price))
                            else:
                                volume = Decimal(e[1])
                                book.update(oside, price, volume, float(e[2]))
        askprice = book.ask.peekitem(0)
        bidprice = book.bid.peekitem(0)
        if askprice < bidprice:
            print("error: Improbable negative spread lastupdate=%s ask=%s bid=%s" %(book.lastupdate, askprice, bidprice))
            exit(1)
    return
    

my_client = client.WssClient()
my_client.start()

# Sample public-data subscription:

my_client.subscribe_public(
    subscription = {
        'name': 'book'
    },
    pair = ['XBT/USD'],
    callback = my_handler
)
