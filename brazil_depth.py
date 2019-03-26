import requests

bitCambioDepth = requests.get("https://bitcambio_api.blinktrade.com/api/v1/BRL/orderbook?crypto_currency=BTC").json()
print('mid Price = %d'%(bitCambioDepth['bids'][0][0]/2 + bitCambioDepth['asks'][0][0]/2))

def spread(testVol):
    vol = 0
    bidsIndex = 0
    while(vol<testVol):
        vol += bitCambioDepth['bids'][bidsIndex][1]
        bidsIndex += 1
    # print(bitCambioDepth['bids'][bidsIndex][0])

    vol = 0
    asksIndex = 0
    while(vol<testVol):
        vol += bitCambioDepth['asks'][asksIndex][1]
        asksIndex += 1
    print("order volume = %d BTC\t"%(testVol),"buy price = %d\t"%bitCambioDepth['bids'][bidsIndex][0],"sell price = %d\t"%bitCambioDepth['asks'][asksIndex][0])

for n in range(1,11):
    spread(n)