import binance
import requests

# symbol = "BTCUSDT"
# marketDepth = binance.depth(symbol)
marketDepth = requests.get("https://api.huobi.pro/market/depth?symbol=btcusdt&type=step2").json()

def arbSlippage(expectVol):

    midPrice = float(marketDepth['bids'][0][0])/2 + float(marketDepth['asks'][0][0])/2

    acumVol = 0
    index = 0
    while(acumVol < expectVol):
        acumVol += float(marketDepth['bids'][index][1])
        index += 1
    # 单笔卖单滑点
    askArbSlippage = 1 - float(marketDepth['bids'][index][0])/midPrice

    acumVol = 0
    index = 0
    while(acumVol < expectVol):
        acumVol += float(marketDepth['asks'][index][1])
        index += 1
    # 单笔买单滑点
    bidsArbSlippage = float(marketDepth['asks'][index][0])/midPrice -1

    print("arbVolume = %d BTC"%(expectVol),"\nasksArbSlippage = %.4f %%"%(askArbSlippage*100),"\nbidsArbSlippage = %.4f %%"%(bidsArbSlippage*100))

arbSlippage(10)