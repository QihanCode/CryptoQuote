import binance, requests

# 获取Binance中间价
symbol = "BTCUSDT"
marketDepth = binance.depth(symbol)
midPrice = float(marketDepth['bids'][0][0])/2 + float(marketDepth['asks'][0][0])/2

def fxrate(localPrice, globalPrice):

    fxRate = localPrice/globalPrice
    print(round(fxRate,4))

# mercado行情对应汇率
print("mercado's implied fx :")
mercadoTicker = requests.get("https://www.mercadobitcoin.net/api/btc/ticker/").json()
fxrate(float(mercadoTicker['ticker']['buy']),midPrice)
fxrate(float(mercadoTicker['ticker']['sell']),midPrice)

#bitcoinTrade
print("\nbitcoinTrade's implied fx :")
bitcoinTradeTicker = requests.get("https://api.bitcointrade.com.br/v2/public/BRLBTC/ticker").json()
fxrate(bitcoinTradeTicker["data"]['buy'],midPrice)
fxrate(bitcoinTradeTicker["data"]['sell'],midPrice)

# bitCambio对应汇率
print("\nbitCambio's implied fx :")
bitCambioTicker = requests.get("https://bitcambio_api.blinktrade.com/api/v1/BRL/ticker").json()
fxrate(float(bitCambioTicker['buy']),midPrice)
fxrate(float(bitCambioTicker['sell']),midPrice)