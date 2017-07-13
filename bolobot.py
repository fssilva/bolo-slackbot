# coding=utf-8
import time
import json
import requests

from bs4 import BeautifulSoup, SoupStrainer
from yahoo_finance import Currency
from selenium import webdriver


class BoloBot():

    UOL_URL = 'http://economia.uol.com.br/cotacoes/cambio/dolar-turismo-estados-unidos'
    INFOMONEY_URL = 'http://www.infomoney.com.br/mercados/cambio'
    BB_PERCENTAGE = 0.9862

    def __init__(self):
        self._driver = webdriver.PhantomJS()
        self._currency_types = {'!dtc2': self._get_tourist_exchange_rate,
                              '!dollar': self._get_dollar_exchange_rate,
                              '!bb2': self._get_bb_exchange_rate,
                              '!bb': self._get_bb_exchange_rate_faster,
                              '!dtc': self._get_tourist_exchange_rate_faster}

    def _get_tourist_exchange_rate_faster(self):
        response = requests.get(self.INFOMONEY_URL)
        table_data = SoupStrainer('td')
        soup = BeautifulSoup(response.text, 'lxml', parse_only=table_data)
        for td in soup:
            if td.string is not None and td.string.strip() == u'Dólar Turismo':
                return td.next_sibling.next_sibling.string.strip().replace(',', '.')

    def _get_tourist_exchange_rate(self):
        self._driver.get(self.UOL_URL)
        value = self._driver.find_element_by_css_selector('.bid').text
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
    
    def _send_rate(self, channel, rate_func, currency='USD', quantity=1):
        try:
            rate = float(rate_func())
            total = '%.4f' % (rate * quantity)
            message = '%s %s = %s BRL' % (str(quantity), currency, total)
            return message
        except:
            return "Update nedded. Source has changed."

    def _reply_message(self, message, channel):
        message_list = message.split()
        command = message_list[0]
        quantity = 1
        if len(message_list) > 1:
            try:
                quantity = float(message_list[1])
            except ValueError as e:
                pass
        if command == '!euro':
            return self._send_rate(channel, self._get_euro_exchange_rate, 'EUR', quantity)
        elif command in self._currency_types.keys():
            func = self._currency_types.get(command)
            return self._send_rate(channel, func, quantity=quantity)
