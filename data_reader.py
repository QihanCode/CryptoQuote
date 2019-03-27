import csv
import json
import pygal
import time, datetime

filename = 'testrecord.csv'

MarketData = [[[],[]],[[],[]],[[],[]],[[],[]],[[],[]]]
timeArray = []

with open(filename) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if reader.line_num % 5 == 0:
            timeArray.append(json.loads(row[0]))
            for index in range(1,4):
                # print(reader.line_num,json.loads(row[index]))
                MarketData[int(index-1)][0].append(json.loads(row[index])["askAvgPrice"])
                MarketData[int(index-1)][1].append(json.loads(row[index])["bidAvgPrice"])

            index = 4
            # fxrate = json.loads(row[index + 1])["FxRate"]
            fxrate = (json.loads(row[2])['askAvgPrice'] + json.loads(row[1])['askAvgPrice'] + json.loads(row[2])['bidAvgPrice'] + json.loads(row[1])['bidAvgPrice']) / json.loads(row[4])['askAvgPrice'] / 4
            MarketData[int(index - 1)][0].append(json.loads(row[index])["askAvgPrice"] * fxrate)
            MarketData[int(index - 1)][1].append(json.loads(row[index])["bidAvgPrice"] * fxrate)

            index = 5
            MarketData[int(index - 1)][0].append(json.loads(row[index])["AskOfferPrice"] / json.loads(row[index])["FxRate"] * fxrate)
            MarketData[int(index - 1)][1].append(json.loads(row[index])["BidOfferPrice"] / json.loads(row[index])["FxRate"] * fxrate)


price_chart = pygal.Line()
price_chart.x_labels =  map(str,timeArray)
price_chart.add("MercadoAsk",MarketData[0][0],color = 'green')
price_chart.add("MercadoBid",MarketData[0][1],color = 'green')
price_chart.add("BitcoinTradeAsk",MarketData[1][0],color = 'blue')
price_chart.add("BitcoinTradeBid",MarketData[1][1],color = 'blue')
# price_chart.add("BidCambioAsk",MarketData[2][0],color = 'yellow')
# price_chart.add("BitCambioBid",MarketData[2][1],color = 'yellow')
price_chart.add("HuobiAsk",MarketData[3][0],color = 'red')
price_chart.add("huobiBid",MarketData[3][1],color = 'red')
price_chart.add("NovaAsk",MarketData[4][0],color = 'purple')
price_chart.add("NovaBid",MarketData[4][1],color = 'purple')
price_chart.render_to_file("price_chart.svg")