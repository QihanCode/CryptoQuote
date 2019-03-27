import requests
import csv
import time
import json
import datetime
import threading
import traceback

import HuobiServices as Huobi
from priceOffer import Agent

class Testdata:
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
                mercados = self.slippage_estimate(self.mercado)
                bitcointrades = self.slippage_estimate(self.bitcointrade)
                bitcambios = self.slippage_estimate(self.bitcambio)
                huobis = self.slippage_estimate(self.huobi)

                data = [time.time(),json.dumps(mercados),json.dumps(bitcointrades),json.dumps(bitcambios),json.dumps(huobis),json.dumps(self.offer)]

                print(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'), "process success")
                print(data)
                with open('testrecord.csv', 'a', newline='') as f:
                    # 标头在这里传入，作为第一行数据
                    writer = csv.writer(f)
                    writer.writerow(data)


            except Exception as e:
                print(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),"process error")
                print(traceback.print_exc())

            time.sleep(5)

    def get_quote(self):
        tick1 = time.time()
        t1 = threading.Thread(target=self.get_mercado_orderbook)
        t2 = threading.Thread(target=self.get_bitcointrade_orderbook)
        t3 = threading.Thread(target=self.get_bitcambio_orderbook)
        t4 = threading.Thread(target=self.get_huobi_orderboook)
        t5 = threading.Thread(target=self.get_offer)

        t1.start()
        t2.start()
        t3.start()
        t4.start()
        t5.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()
        t5.join()

        tick2 = time.time()
        print("total time cost", tick2 - tick1)

    def slippage_estimate(self, marketDepth, volume = "", side="all"):
        if volume == "":
            volume = self.volume


        midPrice = (float(marketDepth['asks'][0][0]) + float(marketDepth['bids'][0][0])) / 2

        slippage = {
            "midPrice": midPrice,
        }

        if side == "buy":

            tradeVol = 0
            index = 0
            cumVol = 0
            orders = []

            cumVol += float(marketDepth['asks'][index][1])
            orders.append(marketDepth['asks'][index])

            while cumVol < volume:
                index += 1
                cumVol += float(marketDepth['asks'][index][1])
                orders.append(marketDepth['asks'][index])

            for order in orders:
                tradeVol += float(order[0]) * float(order[1])

            tradeVol = tradeVol - float(marketDepth['asks'][index][0]) * (cumVol - volume)

            slippage['askAvgPrice'] = tradeVol / volume
            slippage['askSlippage'] = slippage['askAvgPrice'] / midPrice - 1

            return slippage

        elif side == 'sell':

            tradeVol = 0
            index = 0
            cumVol = 0
            orders = []

            cumVol += float(marketDepth['bids'][index][1])
            orders.append(marketDepth['bids'][index])

            while cumVol < volume:
                index += 1
                cumVol += float(marketDepth['bids'][index][1])
                orders.append(marketDepth['bids'][index])

            for order in orders:
                tradeVol += float(order[0]) * float(order[1])

            tradeVol = tradeVol - float(marketDepth['bids'][index][0]) * (cumVol - volume)

            slippage['bidAvgPrice'] = tradeVol / volume
            slippage['bidSlippage'] = 1 - slippage['bidAvgPrice'] / midPrice

            return slippage
        elif side == 'all':

            """initial settlement"""
            cumVol = {
                "asks": 0,
                "bids": 0,
            }

            orders = {
                "asks": [],
                "bids": [],
            }

            """calculating ask side"""
            tradeVol = 0
            index = 0

            cumVol['asks'] += float(marketDepth['asks'][index][1])
            orders['asks'].append(marketDepth['asks'][index])

            while cumVol['asks'] < volume:
                index += 1
                cumVol['asks'] += float(marketDepth['asks'][index][1])
                orders['asks'].append(marketDepth['asks'][index])

            for order in orders['asks']:
                tradeVol += float(order[0]) * float(order[1])

            tradeVol = tradeVol - float(marketDepth['asks'][index][0]) * (cumVol['asks'] - volume)

            slippage['askAvgPrice'] = tradeVol / volume
            slippage['askSlippage'] = slippage['askAvgPrice'] / midPrice - 1

            """calculating bid side"""
            tradeVol = 0
            index = 0

            cumVol['bids'] += float(marketDepth['bids'][index][1])
            orders['bids'].append(marketDepth['bids'][index])

            while cumVol['bids'] < volume:
                index += 1
                cumVol['bids'] += float(marketDepth['bids'][index][1])
                orders['bids'].append(marketDepth['bids'][index])

            for order in orders['bids']:
                tradeVol += float(order[0]) * float(order[1])

            tradeVol = tradeVol - float(marketDepth['bids'][index][0]) * (cumVol['bids'] - volume)

            slippage['bidAvgPrice'] = tradeVol / volume
            slippage['bidSlippage'] = 1 - slippage['bidAvgPrice'] / midPrice

            return slippage

    def get_mercado_orderbook(self, currency="btc"):
        tick1 = time.time()
        """get mercado orderbook"""
        mercadoOrderbook={
            "asks":[],
            "bids":[]
        }
        result = requests.get("https://www.mercadobitcoin.net/api/BTC/orderbook/").json()
        mercadoOrderbook['bids'] = result['bids'][:self.amount]
        mercadoOrderbook['asks'] = result['asks'][:self.amount]

        self.mercado = mercadoOrderbook
        tick2 = time.time()
        print("mercado",tick2-tick1)

    def get_bitcointrade_orderbook(self, currency = "btc"):
        """get bitcoinTrade orderbook"""
        tick1 = time.time()
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
        tick2 = time.time()
        print("bitcointrade", tick2 - tick1)

    def get_bitcambio_orderbook(self, currency = "btc"):
        """get bitCambio orderbook"""
        tick1 = time.time()
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
        tick2 = time.time()
        print("bitcambio", tick2 - tick1)

    def get_huobi_orderboook (self, currency ="btc"):
        tick1 = time.time()
        huobiDepth = Huobi.get_depth(currency.lower() + "usdt", "step0")

        self.huobi = {}
        self.huobi.update(asks=huobiDepth['tick']['asks'][:self.amount])
        self.huobi.update(bids=huobiDepth['tick']['bids'][:self.amount])
        tick2 = time.time()
        print("huobi", tick2 - tick1)

    def get_offer(self, testVol = ""):
        tick1 = time.time()
        if testVol == "":
            testVol = self.volume
        case = Agent("btc", testVol)
        self.offer = case.offer_generate(testVol)
        tick2= time.time()
        print("offer",tick2-tick1)


case = Testdata(amount = 100)
case.update_data()