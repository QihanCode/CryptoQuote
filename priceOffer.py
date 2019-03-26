# -*- coding: utf-8 -*-
import requests
import binance
import HuobiServices as huobi
import threading
import time

adjustParams = {
            "BTC":2,
            "ETH":2,
            "EOS":2,
            "XLM":1.5,
            "TRX":1.5,
            "XRP":1.5,
            "BTT":1.5,
        }

exFeeRate = 0.0004
initialSpread = exFeeRate + 0.0004

class Agent:
    def __init__(self, currency, tradeVol = 1, clientSide="all", initialSpread = initialSpread, adjustParams = adjustParams, exchange = "huobi", exFeeRate = exFeeRate):
        """
        :param currency:
        :param spread:
        :param tradeVol:用户交易币数量
        :param clientSide:用户交易方向，"buy"/"sell"/"all"
        """
        self.symbol = "%sUSDT"%(currency.upper())
        self.btcQuote = {
            "mercado": {},
            "bitcoinTrade": {},
            "bitCambio": {},
            "global": {
                "ticker":{},
            },
        }
        self.marketDepth = {
            "asks":[],
            "bids":[],
        }
        self.currency = currency
        self.initialSpread = initialSpread
        self.tradeVol = tradeVol
        self.clientSide = clientSide
        self.adjustParams = adjustParams
        self.exchange = exchange
        self.exFeeRate = exFeeRate

    def get_btc_quote(self):
        t1 = threading.Thread(target=self.get_mercado_ticker)
        t2 = threading.Thread(target=self.get_bitcointrade_ticker)
        t3 = threading.Thread(target=self.get_bitcambio_ticker)
        if self.exchange.lower() == "binance":
            t4 = threading.Thread(target=self.get_binance_ticker, args=("btc",))
            t5 = threading.Thread(target=self.get_binance_depth())
        elif self.exchange.lower() == "huobi":
            t4 = threading.Thread(target=self.get_huobi_ticker, args=("btc",))
            t5 = threading.Thread(target=self.get_huobi_depth())

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

        return self.btcQuote

    def get_depth(self):
        if self.exchange.lower() == "binance":
            self.get_binance_depth()
        elif self.exchange.lower() == "huobi":
            self.get_huobi_depth()

        return self.marketDepth

    def get_mercado_ticker(self):
        """
        get mercado ticker
        :param currency: the currency symbol of trading fiat trading pair , like 'btc'/'eth'
        :return: the full ticker data
        """
        mercadoTicker = requests.get("https://www.mercadobitcoin.net/api/%s/ticker/" % ("btc")).json()
        self.btcQuote['mercado'] = mercadoTicker['ticker']

    def get_bitcointrade_ticker(self):
        """
        get bitcoinTrade ticker
        :param currency: the upcase fo currency symbol of trading fiat trading pair , like 'BTC'/'ETH'
        :return: the full ticker data
        """
        bitcoinTradeTicker = requests.get(
            "https://api.bitcointrade.com.br/v2/public/BRL%s/ticker" % ("BTC")).json()
        self.btcQuote['bitcoinTrade'] = bitcoinTradeTicker['data']

    def get_bitcambio_ticker(self):
        """
        :return:
        """
        bitCambioTicker = requests.get("https://bitcambio_api.blinktrade.com/api/v1/BRL/ticker").json()
        self.btcQuote["bitCambio"] = bitCambioTicker

    def get_binance_ticker(self, currency=""):
        if currency == "":
            currency = self.currency
        binanceTicker = binance.ticker(currency.upper() + "USDT")
        self.btcQuote['global']['ticker'] = binanceTicker

    def get_binance_depth(self, currency=""):
        if currency == "":
            currency = self.currency

        binanceDepth = binance.depth(currency.upper() + "USDT")
        self.marketDepth['asks'] = binanceDepth['asks']
        self.marketDepth['bids'] = binanceDepth['bids']


    def get_huobi_ticker(self, currency = ""):
        if currency == "":
            currency = self.currency

        huobiTicker = huobi.get_ticker(currency.lower()+"usdt")['tick']
        huobiTicker['askPrice'] = huobiTicker['ask'][0]
        huobiTicker['bidPrice'] = huobiTicker['bid'][0]
        self.btcQuote['global']['ticker'] = huobiTicker


    def get_huobi_depth(self,currency = ""):
        if currency == "":
            currency = self.currency

        huobiDepth = huobi.get_depth(currency.lower()+"usdt","step0")
        self.marketDepth['asks'] = huobiDepth['tick']['asks']
        self.marketDepth['bids'] = huobiDepth['tick']['bids']


    def get_fxrate(self):
        self.get_btc_quote()

        globalBTCPrice = float(self.btcQuote['global']['ticker']['askPrice']) / 2 + float(
            self.btcQuote['global']['ticker']['bidPrice']) / 2

        brazilBTCAsk = (self.btcQuote['bitCambio']['sell'] + float(
            self.btcQuote['bitcoinTrade']['sell']) + float(
            self.btcQuote['mercado']['sell'])) / 3

        brazilBTCBid=(self.btcQuote['bitCambio']['buy'] + float(
            self.btcQuote['bitcoinTrade']['buy']) + float(
            self.btcQuote['mercado']['buy'])) / 3
        brazilBTCPrice=(brazilBTCAsk + brazilBTCBid) / 2

        inverseFxRate = brazilBTCPrice / globalBTCPrice

        return round(inverseFxRate,4)

    def offer_generate(self, volume = ""):
        if volume == "":
            volume = self.tradeVol

        offer = {
            "FxRate" : self.get_fxrate(),
        }
        spread = self.spreadPoint(volume)
        offer.update(spread)

        midPrice = (float(self.marketDepth['asks'][0][0]) + float(self.marketDepth['bids'][0][0]))/ 2
        askPrice = float(self.marketDepth['asks'][0][0])
        bidPrice = float(self.marketDepth['bids'][0][0])

        self.get_depth()
        offer.update(ReferencePrice= (midPrice * offer['FxRate']))
        offer.update(AskOfferPrice = askPrice * offer['FxRate'] * (1 + offer['askSpread']))
        offer.update(BidOfferPrice = bidPrice * offer['FxRate'] * (1 - offer['bidSpread']))

        return offer

    def spreadPoint(self, volume = ""):
        if volume == "":
            volume = self.tradeVol

        slippage = self.slippage_estimate(volume, "all")

        askSpread = self.initialSpread + slippage['askSlippage']* self.adjustParams[self.currency.upper()]
        bidSpread = self.initialSpread + slippage['bidSlippage']* self.adjustParams[self.currency.upper()]

        return {
            "askSpread":askSpread,
            "bidSpread":bidSpread,
        }

    def slippage_estimate(self, volume = "", side = ""):
        if volume == "":
            volume = self.tradeVol
        if side == "":
            side = self.clientSide

        if self.marketDepth['asks'] == []:
            self.get_depth()

        midPrice = (float(self.marketDepth['asks'][0][0]) + float(self.marketDepth['bids'][0][0]))/2

        slippage = {
            "midPrice":midPrice,
        }

        if side == "buy":

            tradeVol = 0
            index = 0
            cumVol = 0
            orders = []

            cumVol += float(self.marketDepth['asks'][index][1])
            orders.append(self.marketDepth['asks'][index])

            while cumVol < volume:
                index += 1
                cumVol += float(self.marketDepth['asks'][index][1])
                orders.append(self.marketDepth['asks'][index])

            for order in orders:
                tradeVol += float(order[0])*float(order[1])

            tradeVol = tradeVol - float(self.marketDepth['asks'][index][0])*(cumVol-volume)

            slippage['askAvgPrice'] = tradeVol / volume
            slippage['askSlippage'] = slippage['askAvgPrice'] / midPrice - 1

        elif side == 'sell':

            tradeVol = 0
            index = 0
            cumVol = 0
            orders = []

            cumVol += float(self.marketDepth['bids'][index][1])
            orders.append(self.marketDepth['bids'][index])

            while cumVol < volume:
                index += 1
                cumVol += float(self.marketDepth['bids'][index][1])
                orders.append(self.marketDepth['bids'][index])

            for order in orders:
                tradeVol += float(order[0]) * float(order[1])

            tradeVol = tradeVol - float(self.marketDepth['bids'][index][0]) * (cumVol - volume)

            slippage['bidAvgPrice'] = tradeVol / volume
            slippage['bidSlippage'] = 1 - slippage['bidAvgPrice'] / midPrice

        elif side == 'all':

            """initial settlement"""
            cumVol = {
                "asks": 0,
                "bids": 0,
            }

            orders = {
                "asks":[],
                "bids":[],
            }

            """calculating ask side"""
            tradeVol = 0
            index = 0

            cumVol['asks'] += float(self.marketDepth['asks'][index][1])
            orders['asks'].append(self.marketDepth['asks'][index])

            while cumVol['asks'] < volume:
                index += 1
                cumVol['asks'] += float(self.marketDepth['asks'][index][1])
                orders['asks'].append(self.marketDepth['asks'][index])

            for order in orders['asks']:
                tradeVol += float(order[0]) * float(order[1])

            tradeVol = tradeVol - float(self.marketDepth['asks'][index][0]) * (cumVol['asks'] - volume)

            slippage['askAvgPrice'] = tradeVol / volume
            slippage['askSlippage'] = slippage['askAvgPrice'] / midPrice - 1

            """calculating bid side"""
            tradeVol = 0
            index = 0

            cumVol['bids'] += float(self.marketDepth['bids'][index][1])
            orders['bids'].append(self.marketDepth['bids'][index])

            while cumVol['bids'] < volume:
                index += 1
                cumVol['bids'] += float(self.marketDepth['bids'][index][1])
                orders['bids'].append(self.marketDepth['bids'][index])

            for order in orders['bids']:
                tradeVol += float(order[0]) * float(order[1])

            tradeVol = tradeVol - float(self.marketDepth['bids'][index][0]) * (cumVol['bids'] - volume)

            slippage['bidAvgPrice'] = tradeVol / volume
            slippage['bidSlippage'] = 1 - slippage['bidAvgPrice'] / midPrice

        return slippage

    def revenue_estimate(self,volume = "", side = ""):
        if volume == "":
            volume = self.tradeVol
        if side == "":
            side = self.clientSide

        detail = {}

        offer = self.offer_generate()
        detail.update(self.btcQuote)

        slippage = self.slippage_estimate(side="all")

        detail.update(offer)
        detail.update(slippage)

        detail.update(askProfit = (detail["AskOfferPrice"] - detail['askAvgPrice'] * detail['FxRate'] * (1 + self.exFeeRate))*volume)
        detail.update(askProfitRatio=detail['askProfit'] / detail["AskOfferPrice"] / volume)
        detail.update(bidProfit = (detail['bidAvgPrice'] * detail['FxRate']* (1 - self.exFeeRate) - detail["BidOfferPrice"])*volume)
        detail.update(bidProfitRatio=detail['bidProfit'] / detail["BidOfferPrice"] / volume)

        return detail


# currency = "btc"
# testVol = 1
#
# case = Agent(currency,testVol,'all')
# for value,item in case.revenue_estimate().items():
#     print(value,item)
