from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from yahoo_fin import stock_info as si
import pandas as pd
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

app = Flask(__name__)

def get_top_stocks():
    url = ("https://finviz.com/")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    ups = pd.read_html(str(html), attrs = {'class': 't-home-table'})[0]
    ups.columns = ['Ticker', 'Last', 'Change', 'Volume', '4', 'Signal']
    ups = ups.drop(columns = ['4'])
    ups = ups.iloc[1:]
    return ups

def get_bottom_stocks():
    url = ("https://finviz.com/")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    downs = pd.read_html(str(html), attrs = {'class': 't-home-table'})[1]
    downs.columns = ['Ticker', 'Last', 'Change', 'Volume', '4', 'Signal']
    downs = downs.drop(columns = ['4'])
    downs = downs.iloc[1:]
    return downs

def get_earnings():
    url = ("https://finviz.com/")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    earnings = pd.read_html(str(html), attrs = {'class': 't-home-table'})[7]
    earnings.columns = ['Date', 'Ticker', 'Ticker', 'Ticker', 'Ticker', 'Ticker', 'Ticker', 'Ticker', 'Ticker', 'Ticker', 'Ticker']
    earnings = earnings.iloc[1:]
    return earnings


def get_futures():
    url = ("https://finviz.com/")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    futures1 = pd.read_html(str(html), attrs = {'class': 't-home-table'})[8]
    futures1.columns = ['Index', 'Last', 'Change', 'Change (%)', '4']
    futures1 = futures1.drop(columns = ['4'])
    futures1 = futures1.iloc[1:]
    
    futures2 = pd.read_html(str(html), attrs = {'class': 't-home-table'})[9]
    futures2.columns = ['Index', 'Last', 'Change', 'Change (%)', '4']
    futures2 = futures2.drop(columns = ['4'])
    futures2 = futures2.iloc[1:]
    
    frames = [futures1, futures2]
    futures = pd.concat(frames)
    futures = futures.set_index('Index')
    futures = futures.dropna()
    return futures

def news():
    url = ("https://finviz.com/news.ashx")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    news = pd.read_html(str(html))[5]
    news.columns = ['0', 'Time', 'Headlines']
    news = news.drop(columns = ['0'])
    return news.head(10)

def long_buys():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_midover,fa_epsyoy1_o20,fa_salesqoq_o20,geo_usa,ind_stocksonly,sh_avgvol_o500,sh_insttrans_pos,sh_price_o10,ta_highlow52w_a30h,ta_perf_52w50o,ta_perf2_13wup,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa,targetprice_above&ft=4&o=change&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def long_shorts():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_smallover,geo_usa,ind_stocksonly,sh_avgvol_o300,sh_insidertrans_neg,sh_price_o5,ta_sma20_pb,ta_sma200_pa100,targetprice_below&ft=4&o=-change&ar=180&c=0,1,2,3,4,5,6,7,14,17,18,23,26,27,28,29,42,43,44,45,46,47,48,49,51,52,53,54,57,58,59,60,62,63,64,65,66,67,68,69")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def int_buys():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_midover,fa_epsyoy1_o20,fa_salesqoq_o20,geo_usa,ind_stocksonly,ipodate_prev3yrs,sh_avgvol_o500,sh_price_o15,ta_changeopen_u,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=change&ar=180&c=0,1,2,3,4,5,6,7,14,17,18,23,26,27,28,29,42,43,44,45,46,47,48,49,51,52,53,54,57,58,59,60,62,63,64,65,66,67,68,69")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def int_shorts():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_smallover,geo_usa,ind_stocksonly,sh_avgvol_o300,sh_insidertrans_neg,sh_insttrans_neg,sh_price_o7,ta_changeopen_d,ta_rsi_ob60,ta_sma200_pa100,targetprice_below&ft=4&o=-change&ar=180&c=0,1,2,3,4,5,6,7,14,17,18,23,26,27,28,29,42,43,44,45,46,47,48,49,51,52,53,54,57,58,59,60,62,63,64,65,66,67,68,69")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

@app.route('/', methods = ['POST'])
def screener():
    try:
        message_body = request.form['Body']
        resp = MessagingResponse()
        
        lb_matches1 = ["long", "buys"]
        lb_matches2 = ["long", "buy"]

        ls_matches1 = ["long", "shorts"]
        ls_matches2 = ["long", "short"]
        
        ib_matches1 = ["intraday", "buys"]
        ib_matches2 = ["intraday", "buy"]
        ib_matches3 = ["today", "buy"]
        ib_matches4 = ["today", "buys"]
        
        is_matches1 = ["intraday", "shorts"]
        is_matches2 = ["intraday", "short"]
        is_matches3 = ["today", "short"]
        is_matches4 = ["today", "shorts"]
        
        if ticker in si.tickers_sp500() or ticker in si.tickers_nasdaq() or si.tickers_other():
            stock = message_body
            
            # price
            price = si.get_live_price('{}'.format(message_body))
            price = round(price, 2)

            AvgGain= 15
            AvgLoss= 5

            maxStopBuy=round(price*((100-AvgLoss)/100), 2)
            Target1RBuy=round(price*((100+AvgGain)/100),2)
            Target2RBuy=round(price*(((100+(2*AvgGain))/100)),2)
            Target3RBuy=round(price*(((100+(3*AvgGain))/100)),2)

            maxStopShort=round(price*((100+AvgLoss)/100), 2)
            Target1RShort=round(price*((100-AvgGain)/100),2)
            Target2RShort=round(price*(((100-(2*AvgGain))/100)),2)
            Target3RShort=round(price*(((100-(3*AvgGain))/100)),2)

            change = str(round(((price-price)/price)*100, 4)) + '%'
            
            # Set up scraper
            url = (f"https://finviz.com/screener.ashx?v=152&ft=4&t={stock}&ar=180&c=1,2,3,4,5,6,7,14,17,18,23,26,27,28,29,42,43,44,45,46,47,48,49,51,52,53,54,57,58,59,60,62,63,64,67,68,69")
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            webpage = urlopen(req).read()
            html = BeautifulSoup(webpage, "html.parser")

            stocks = pd.read_html(str(html))[-2]
            stocks.columns = stocks.iloc[0]
            stocks = stocks[1:]
            stocks['Price'] = [f'{price}']
            stocks['Change'] = [f'{change}']
            stocks['Risk 1 Buy'] = [f'{Target1RBuy}']
            stocks['Risk 2 Buy'] = [f'{Target2RBuy}']
            stocks['Risk 3 Buy'] = [f'{Target3RBuy}']
            stocks['Max Stop Buy'] = [f'{maxStopBuy}']
            stocks['Risk 1 Short'] = [f'{Target1RShort}']
            stocks['Risk 2 Short'] = [f'{Target2RShort}']
            stocks['Risk 3 Short'] = [f'{Target3RShort}']
            stocks['Max Stop Short'] = [f'{maxStopShort}']
            # stocks['Resistance 1'] = [f'{}']
            # stocks['Resistance 2'] = [f'{}']
            # stocks['Resistance 3'] = [f'{}']
            # stocks['Pivot'] = [f'{}']
            # stocks['Support 1'] = [f'{}']
            # stocks['Support 2'] = [f'{}']
            # stocks['Support 3'] = [f'{}']
            message = "\n"
            for attr, val in zip(stocks.columns, stocks.iloc[0]):
                message=message + f"{attr} : {val}\n"

        elif message_body.lower() == 'news':
            df = news()
            headlines = df['Headlines'].tolist()
            times = df['Time'].tolist()

            message = "News:"
            for time, headline in zip(times, headlines):
                message += f"\n{time} : {headline}"

        elif message_body.lower() == 'gainers':
            df = get_top_stocks()
            tickers = df['Ticker'].tolist()
            prices = df['Last'].tolist()
            changes = df['Change'].tolist()

            message = "Top Gainers:"
            for ticker, price, change in zip(tickers, prices, changes):
                message += f"\n{ticker} : {price} : {change}"
        
        elif message_body.lower() == 'losers':
            df = get_bottom_stocks()
            tickers = df['Ticker'].tolist()
            prices = df['Last'].tolist()
            changes = df['Change'].tolist()

            message = "Top Losers:"
            for ticker, price, change in zip(tickers, prices, changes):
                message += f"\n{ticker} : {price} : {change}"

        elif message_body.lower() == 'futures':
            df = get_top_stocks()
            indices = df['Index'].tolist()
            prices = df['Last'].tolist()
            changes = df['Change'].tolist()

            message = "Futures:"
            for index, price, change in zip(indices, prices, changes):
                message += f"\n{index} : {price} : {change}"

        elif message_body.lower() == 'earnings':
            df = get_bottom_stocks()
            tickers = df['Ticker'].tolist()
            dates = df['Date'].tolist()

            message = "Earnings:"
            for date, ticker in zip(dates, tickers):
                message += f"\n{date} : {ticker}"

        elif all(x in message_body.lower() for x in lb_matches1) or all(x in message_body for x in lb_matches2):
            df = long_buys()
            tickers = df['Ticker'].tolist()
            
            message = "Stocks to Buy (Long Term):"
            for i in range(len(tickers)):
                message += f"\n{tickers[i]}"
        
        
        elif all(x in message_body.lower() for x in ls_matches1) or all(x in message_body for x in ls_matches2):
            df = long_shorts()
            tickers = df['Ticker'].tolist()
        
            message = "Stocks to Short (Long Term):"
            for i in range(len(tickers)):
                message += f"\n{tickers[i]}"
        
        
        elif all(x in message_body.lower() for x in ib_matches1) or all(x in message_body for x in ib_matches2) or all(x in message_body for x in ib_matches3)  or all(x in message_body for x in ib_matches4):
            df = int_buys()
            tickers = df['Ticker'].tolist()
            
            message = "Stocks to Buy Today:"
            for i in range(len(tickers)):
                message += f"\n{tickers[i]}"
            
        elif all(x in message_body.lower() for x in is_matches1) or all(x in message_body for x in is_matches2) or all(x in message_body for x in is_matches3) or all(x in message_body for x in is_matches4):
            df = int_shorts()
            tickers = df['Ticker'].tolist()
            
            message = "Stocks to Short Today:"
            for i in range(len(tickers)):
                message += f"\n{tickers[i]}"

        resp.message(message)
        return str(resp)
    
    except Exception as e:
        resp.message(f'\n{e}')
        return str(resp)
    
if __name__ == "__main__":
    app.run(port=5000, debug=True)