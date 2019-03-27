import requests
import csv
import time
import json
import datetime
import threading
import traceback

import HuobiServices as Huobi
from priceOffer import Agent

class GetData:
    def __init__(self,currency = "btc", volume = 1, amount = 20):
        self.currency = currency
        self.volume = volume
        self.amount = amount
        self.mercado = {}
        self.bitcambio = {}
        self.bitcointrade = {}
        self.huobi = {}
        self.offer = {}

    def update_data(self):
        while(1):
            try:
                self.get_quote()

                headers = ["timestamp","mercado","bitcointrade","bitcambio","huobi"]

                data = {
                    "timestamp":time.time(),
                }

                data.update(mercado = json.dumps(self.mercado))
                data.update(bitcointrade = json.dumps(self.bitcointrade))
                data.update(bitcambio = json.dumps(self.bitcambio))
                data.update(huobi = json.dumps(self.huobi))

                with open('example.csv', 'a+', newline='') as f:
                    # 标头在这里传入，作为第一行数据
                    reader = csv.reader(f)
                    if reader == "":
                        writer = csv.DictWriter(f, headers)
                        writer.writeheader()
                        writer.writerow(data)
                    else:
                        writer = csv.DictWriter(f, headers)
                        writer.writerow(data)


            except Exception as e:
                print(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),"process error")
                print(traceback.print_exc())

            time.sleep(60)

    def get_quote(self):
        tick1 = time.time()
        t1 = threading.Thread(target=self.get_mercado_orderbook)
        t2 = threading.Thread(target=self.get_bitcointrade_orderbook)
        t3 = threading.Thread(target=self.get_bitcambio_orderbook)
        t4 = threading.Thread(target=self.get_huobi_orderboook)

        t1.start()
        t2.start()
        t3.start()
        t4.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()
        tick2 = time.time()
        print("requests time = %.2f s"%(tick2-tick1))

    def get_mercado_orderbook(self, currency="btc"):
        """get mercado orderbook"""
        mercadoOrderbook={
            "asks":[],
            "bids":[]
        }
        result = requests.get("https://www.mercadobitcoin.net/api/BTC/orderbook/").json()
        mercadoOrderbook['bids'] = result['bids'][:self.amount]
        mercadoOrderbook['asks'] = result['asks'][:self.amount]

        self.mercado = mercadoOrderbook

    def get_bitcointrade_orderbook(self, currency = "btc"):
        """get bitcoinTrade orderbook"""
        result = requests.get("https://api.bitcointrade.com.br/v2/public/BRLBTC/orders").json()['data']

        bitcoinTradeOrderbook={
            "asks":[],
            "bids":[]
        }
        for order in result['bids']:
            temp = []
            temp.append(order['unit_price'])
            temp.append(order['amount'])
            bitcoinTradeOrderbook['bids'].append(temp)

        for order in result['asks']:
            temp = []
            temp.append(order['unit_price'])
            temp.append(order['amount'])
            bitcoinTradeOrderbook['asks'].append(temp)

        bitcoinTradeOrderbook['bids'] = bitcoinTradeOrderbook['bids'][:self.amount]
        bitcoinTradeOrderbook['asks'] = bitcoinTradeOrderbook['asks'][:self.amount]

        self.bitcointrade = bitcoinTradeOrderbook

    def get_bitcambio_orderbook(self, currency = "btc"):
        """get bitCambio orderbook"""
        result = requests.get("https://bitcambio_api.blinktrade.com/api/v1/BRL/orderbook?crypto_currency=BTC")
        bitCambioOrderbook = {}
        bitCambioOrderbook.update(asks = result.json()["asks"])
        bitCambioOrderbook.update(bids = result.json()["bids"])
        bitCambioOrderbook['bids'] = bitCambioOrderbook['bids'][:self.amount]
        bitCambioOrderbook['asks'] = bitCambioOrderbook['asks'][:self.amount]
        for order in bitCambioOrderbook['bids']:
            order = order[:2]

        for order in bitCambioOrderbook['asks']:
            order = order[:2]

        self.bitcambio = bitCambioOrderbook

    def get_huobi_orderboook (self, currency ="btc"):
        huobiDepth = Huobi.get_depth(currency.lower() + "usdt", "step0")

        self.huobi = {}
        self.huobi.update(asks=huobiDepth['tick']['asks'][:self.amount])
        self.huobi.update(bids=huobiDepth['tick']['bids'][:self.amount])
        tick2 = time.time()

    def get_offer(self, testVol = ""):
        if testVol == "":
            testVol = self.volume
        case = Agent("btc", testVol)
        self.offer = case.offer_generate(testVol)


case = GetData(amount = 100)
case.update_data()