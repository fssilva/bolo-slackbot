# coding=utf-8
import time
import json
import requests

from bs4 import BeautifulSoup, SoupStrainer
from slackclient import SlackClient
from yahoo_finance import Currency
from selenium import webdriver
from timeout import timeout


class BoloBot():

    UOL_URL = "http://economia.uol.com.br/cotacoes/cambio/dolar-turismo-estados-unidos"
    INFOMONEY_URL = "http://www.infomoney.com.br/mercados/cambio"
    BB_PERCENTAGE = 0.9862

    def __init__(self, token):
        self._sc = SlackClient(token)
        self._driver = webdriver.PhantomJS()
        self._currency_types = {"!dtc": self._get_tourist_exchange_rate,
                              "!dollar": self._get_dollar_exchange_rate,
                              "!bb": self._get_bb_exchange_rate,
                              "!bb2": self._get_bb_exchange_rate_faster,
                              "!dtc2": self._get_tourist_exchange_rate_faster}

    def _get_tourist_exchange_rate_faster(self):
        response = requests.get(self.INFOMONEY_URL)
        table_data = SoupStrainer('td')
        soup = BeautifulSoup(response.text, "lxml", parse_only=table_data)
        for td in soup:
            if td.string is not None and td.string.strip() == u"Dólar Turismo":
                return td.next_sibling.string.strip().replace(",", ".")

    def _get_tourist_exchange_rate(self):
        self._driver.get(self.UOL_URL)
        value = self._driver.find_element_by_css_selector(".bid").text
        return value.replace(',', '.')

    def _get_dollar_exchange_rate(self):
        usd_brl = Currency('USDBRL')
        return usd_brl.get_bid()

    def _get_bb_exchange_rate(self):
        return float(self._get_tourist_exchange_rate())*self.BB_PERCENTAGE

    def _get_bb_exchange_rate_faster(self):
        return float(self._get_tourist_exchange_rate_faster())*self.BB_PERCENTAGE

    def _get_euro_exchange_rate(self):
        eur_brl = Currency('EURBRL')
        return eur_brl.get_bid()

    def _get_user(self, id):
        member = json.loads(self._sc.api_call("users.info", user=id))["user"]
        return member["name"]

    def _send_message(self, user, channel, text):
        self._sc.api_call("chat.postMessage", as_user="true:",
                          channel=channel, text=text)

    def _send_rate(self, user, channel, rate_func, currency="USD"):
        user_name = self._get_user(user)
        rate = rate_func()
        message = "<@%s>: 1 %s = %.4f BRL" % (user_name, currency, float(rate))
        self._send_message(user, channel, message)

    @timeout(25)
    def _reply_message(self, message, user_id, channel):
        if message == "!euro":
            self._send_rate(user_id, channel, self._get_euro_exchange_rate, "EUR")
        elif message in self._currency_types.keys():
            func = self._currency_types.get(message)
            self._send_rate(user_id, channel, func)

    def run(self):
        if not self._sc.rtm_connect():
            exit("Failed to connect.")
        while True:
            new_events = self._sc.rtm_read()
            for evt in new_events:
                print(evt)
                if "type" in evt:
                    if evt["type"] == "message" and "text" in evt:
                        channel = evt["channel"]
                        message = evt["text"]
                        uid = evt["user"]
                        user_id = str(uid)
                        try:
                            self._reply_message(message, user_id, channel)
                        except Exception as e:
                            print str(e)
            #time.sleep(1)
