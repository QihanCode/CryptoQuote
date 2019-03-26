import requests
import binance
import threading

symbol = "BTCUSDT"
expectVol = 10
marketDetail ={
    "mercado":{},
    "bitcoinTrade":{},
    "bitCambio":{},
    "binance":{},
}
class Quote:
    def __init__(self,currency):
        self.symbol = "BTCUSDT"
        self.marketDetail ={
            "mercado":{},
            "bitcoinTrade":{},
            "bitCambio":{},
            "binance":{},
        }

def get_mercado_ticker(currency):
    """
    get mercado ticker
    :param currency: the currency symbol of trading fiat trading pair , like 'btc'/'eth'
    :return: the full ticker data
    """
    mercadoTicker = requests.get("https://www.mercadobitcoin.net/api/%s/ticker/"%(currency)).json()
    marketDetail['mercado'] = mercadoTicker['ticker']

def get_bitcointrade_ticker(currency):
    """
    get bitcoinTrade ticker
    :param currency: the upcase fo currency symbol of trading fiat trading pair , like 'BTC'/'ETH'
    :return: the full ticker data
    """
    bitcoinTradeTicker = requests.get("https://api.bitcointrade.com.br/v2/public/BRL%s/ticker"%(currency.upper())).json()
    marketDetail['bitcoinTrade'] = bitcoinTradeTicker['data']

def get_bitcambio_ticker():
    """
    :return:
    """
    bitCambioTicker = requests.get("https://bitcambio_api.blinktrade.com/api/v1/BRL/ticker").json()
    marketDetail["bitCambio"] = bitCambioTicker

def get_binance_ticker(currency):
    binanceTicker = binance.ticker(currency.upper()+"USDT")
    marketDetail['binance'] = binanceTicker

def implied_fxrate(currency):

    t1 = threading.Thread(target= get_mercado_ticker,args=(currency,))
    t2 = threading.Thread(target=get_bitcointrade_ticker, args=(currency,))
    t3 = threading.Thread(target=get_bitcambio_ticker)
    t4 = threading.Thread(target=get_binance_ticker, args=(currency,))
    # bitCambioTicker = get_bitcambio_ticker()
    # bitcoinTradeTicker = get_bitcointrade_ticker(currency)
    # mercadoTicker = get_mercado_ticker(currency)
    # binanceTicker = binance.ticker(currency.upper()+"USDT")
    t1.start()
    t2.start()
    t3.start()
    t4.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    midPrice = float(marketDetail['binance']['askPrice'])/2 + float(marketDetail['binance']['bidPrice'])/2

    ask = marketDetail['bitCambio']['sell'] + float(marketDetail['bitcoinTrade']['sell']) + float(marketDetail['mercado']['sell'])
    bid = marketDetail['bitCambio']['buy'] + float(marketDetail['bitcoinTrade']['buy']) + float(marketDetail['mercado']['sell'])
    mid = (ask + bid) / 6

    inverseFX = mid/midPrice

    return{
        "usdt price ":round(midPrice,2),
          "brl price = ": round(mid,2),
          "implied fxrate =":round(inverseFX,4)
    }

# print(implied_fxrate("btc"))
print(implied_fxrate("btc"))
