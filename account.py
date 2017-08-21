import json
from collections import namedtuple

import requests
import time
import hmac
import hashlib


class Account(object):
    """
    An example of using Bittrex API
    Shows currencies I have, its price in USD and shows the total value
    """

    API       = "https://bittrex.com/api/v1.1/account/getbalances?apikey={}&nonce={}"
    BTC_USD   = "http://preev.com/pulse/units:btc+usd/sources:bittrex+bitstamp+btce"
    MARKET   = "https://bittrex.com/api/v1.1/public/getmarketsummary?market=btc-{}"
    DONT_CARE = ['USDT', 'BTC']
    DETAILS   = namedtuple('details', ['currency', 'have', 'value'])

    def __init__(self):
        """
        Reads the keys from a json file
        Two kind of keys are required: secret, key
        """

        self.balances     = None
        self.actual_price = 0
        self.actual_money = 0

        with open("keys") as keys:
            keys = json.loads(keys.read())
            self.key = keys.get("read_key", {}).get("key")
            self.secret = keys.get("read_key", {}).get("secret")

        self._get_btc_value_in_eur()

    def load_balances(self):
        """
        Sets up basic stuff that is required for using Bittrex API.
        After keys are ready, header is set up, got the hash, gets the balances from Bittrex

        :return: self
        """

        nonce = time.time()
        read_url = self.API.format(self.key, nonce)

        apisign = hmac.new(self.secret.encode(), msg=read_url.encode(), digestmod=hashlib.sha512).hexdigest()

        headers = {'apisign': apisign}
        resp = requests.get(read_url, headers=headers)

        self.balances = resp.json().get('result')

        return namedtuple('applicable_methods', ['show'])(self._show)

    def _show(self):
        """
        Shows currencies i have with its price in USD

        :return:
        """

        money = [self._get_price(x) for x in self.balances if x['Currency'] not in self.DONT_CARE]

        self.actual_money = 0
        for penny in money: self._get_my_wallet(penny)

        print("-"*50)
        print("I have: {:0.2f} $".format(float(self.actual_price) * float(self.actual_money)))

    def _get_btc_value_in_eur(self):
        """
        Gets the current value of BTC in USD

        :return: self
        """

        self.actual_price = requests.get(self.BTC_USD).json()['btc']['usd']['bitstamp']['last']

        return self

    def _get_my_wallet(self, penny):
        """
        Calculates and prints the currencies' value in USD i have

        :param penny: Account.DETAILS
        :return:
        """

        value = penny.have * penny.value
        self.actual_money += value
        print("{}: {:0.2f}$".format(penny.currency, value * float(self.actual_price)))

    def _get_price(self, crypto):
        """
        Gets `crypto` market i am interested in

        :param crypto: dict - currency details
        :return: Account.DETAILS
        """

        url = self.MARKET.format(crypto.get('Currency').lower())
        resp = requests.get(url).json().get("result").pop()

        return Account.DETAILS(crypto.get('Currency'), crypto.get('Balance', 1), resp.get('Last', 1))


if __name__ == '__main__':
    account = Account()
    account.load_balances().show()
