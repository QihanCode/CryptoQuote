import requests
import csv
import time
import json
import datetime
import threading
import traceback
import HuobiServices as Huobi

from priceOffer import Agent

testVol = 1
currency = "btc"

def slippage_estimate(marketDepth, volume = 1, side="all"):

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

def get_mercado_orderbook(currency="btc", amount = 20):
    """get mercado orderbook"""
    mercadoOrderbook={
        "asks":[],
        "bids":[]
    }
    result = requests.get("https://www.mercadobitcoin.net/api/BTC/orderbook/").json()
    mercadoOrderbook['bids'] = result['bids'][:amount]
    mercadoOrderbook['asks'] = result['asks'][:amount]

    global mercado
    mercado = mercadoOrderbook

def get_bitcointrade_orderbook(currency = "btc", amount = 20):
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

    bitcoinTradeOrderbook['bids'] = bitcoinTradeOrderbook['bids'][:amount]
    bitcoinTradeOrderbook['asks'] = bitcoinTradeOrderbook['asks'][:amount]

    global bitcointrade
    bitcointrade = bitcoinTradeOrderbook

def get_bitcambio_orderbook(currency = "btc", amount = 20):
    """get bitCambio orderbook"""
    result = requests.get("https://bitcambio_api.blinktrade.com/api/v1/BRL/orderbook?crypto_currency=BTC")
    bitCambioOrderbook = {}
    bitCambioOrderbook.update(asks = result.json()["asks"])
    bitCambioOrderbook.update(bids = result.json()["bids"])
    bitCambioOrderbook['bids'] = bitCambioOrderbook['bids'][:amount]
    bitCambioOrderbook['asks'] = bitCambioOrderbook['asks'][:amount]
    for order in bitCambioOrderbook['bids']:
        order = order[:2]

    for order in bitCambioOrderbook['asks']:
        order = order[:2]

    global bitcambio
    bitcambio = bitCambioOrderbook

def get_huobi_orderboook (currency ="btc", amount = 20):
    huobiDepth = Huobi.get_depth(currency.lower() + "usdt", "step0")

    global huobi
    huobi = {}
    huobi.update(asks=huobiDepth['tick']['asks'][:amount])
    huobi.update(bids=huobiDepth['tick']['bids'][:amount])

def get_offer(volume = testVol):
    case = Agent("btc", testVol)

    global offer
    offer = case.offer_generate(testVol)

while(1):

    try:

        t1 = threading.Thread(target=get_mercado_orderbook())
        t2 = threading.Thread(target=get_bitcointrade_orderbook())
        t3 = threading.Thread(target=get_bitcambio_orderbook())
        t4 = threading.Thread(target=get_huobi_orderboook())
        t5 = threading.Thread(target=get_offer())

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

        mercados = slippage_estimate(mercado)
        bitcointrades = slippage_estimate(bitcointrade)
        bitcambios = slippage_estimate(bitcambio)
        huobis = slippage_estimate(huobi)

        data = [time.time(),json.dumps(mercados),json.dumps(bitcointrades),json.dumps(bitcambios),json.dumps(huobis),json.dumps(offer)]

        print(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'), "process success")
        print(data)
        with open('testrecord.csv', 'a', newline='') as f:
            # 标头在这里传入，作为第一行数据
            writer = csv.writer(f)
            writer.writerow(data)


    except Exception as e:
        print(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),"process error")
        print(traceback.print_exc())

    time.sleep(15)