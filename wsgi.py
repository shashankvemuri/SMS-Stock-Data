from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from yahoo_fin import stock_info as si
import pandas as pd
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import yfinance as yf
import datetime as dt
from pandas_datareader import data as pdr

import talib
import requests
from bs4 import BeautifulSoup as bs

yf.pdr_override()

app = Flask(__name__)

# Metrics of data needed from finviz.com
metrics = ['Sales Q/Q', 'EPS Q/Q', 'EPS next Y', 'EPS this Y', 'Gross Margin', 'ROE', 'Rel Volume']

# Using beautifulsoup to find finviz metrics specifified
def fundamental_metrics(soup, metrics):
    return soup.find(text = metrics).find_next(class_='snapshot-td2').text
   
# Using beautifulsoup to get/clean finviz metrics specifified
def get_finviz_data(ticker):
    try:
        url = (f"http://finviz.com/quote.ashx?t={ticker}")
        headers_dictionary = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}
        soup = bs(requests.get(url,headers=headers_dictionary).content, features="lxml")
        
        finviz_dict = {}        
        for m in metrics:   
            finviz_dict[m] = fundamental_metrics(soup,m)
        
        for key, value in finviz_dict.items():
            # replace percentages
            if (value[-1]=='%'):
                finviz_dict[key] = float(value[:-1])
            try:
                finviz_dict[key] = float(finviz_dict[key])
            except:
                finviz_dict[key] = 0 

    except Exception as e:
        print (f'the following error has occured while retrieving finviz data \n{e}')        
    
    return finviz_dict

def buy_rating(ticker):
    try:
        start = dt.date.today() - dt.timedelta(days = 365)
        end = dt.date.today()
        
        price = si.get_live_price(ticker)
        buy_rating = 0
        
        df = pdr.get_data_yahoo(ticker, start, end)
        
        df['% Change'] = df['Adj Close'].pct_change()
        df['EMA_4_H'] = talib.EMA(df['High'], timeperiod=4)
        
        sma = [10, 30, 50, 150, 200]
        for x in sma:
            df["SMA_"+str(x)] = round(df['Adj Close'].rolling(window=x).mean(), 2)
            
        ema = [2, 3, 4, 5, 8, 21, 30]
        for x in ema:
            df["EMA_"+str(x)] = talib.EMA(df['Adj Close'], timeperiod=x)
        
        # Storing required values
        moving_average_50 = df["SMA_50"][-1]
        moving_average_150 = df["SMA_150"][-1]
        moving_average_200 = df["SMA_200"][-1]
        low_of_52week = round(min(df["Low"][-260:]), 2)
        high_of_52week = round(max(df["High"][-260:]), 2)
        
        # retrieving finviz values
        finviz_data = get_finviz_data(ticker)
        sales_q = finviz_data['Sales Q/Q']
        eps_q = finviz_data['EPS Q/Q']                  
        eps_next_year = finviz_data['EPS next Y']
        eps_this_year = finviz_data['EPS this Y']
        gross_margin = finviz_data['Gross Margin']
        roe = finviz_data['ROE']
        rel_volume = finviz_data['Rel Volume']
    
        upper, middle, lower = talib.BBANDS(df["Adj Close"], 15, 2, 2)
    
        dcr = 100*(price - df["Low"][-1])/(df["High"][-1] - df["Low"][-1])
        wcr = (100*(price - df['Low'].rolling(window=5).min())/(df['High'].rolling(window=5).max() - df['Low'].rolling(window=5).min()))[-1]
        volatility = ((((df['High'].rolling(window=10).max())/(df['Low'].rolling(window=10).min()))-1)*100)[-1]
        avg_dollar_volume = df['Adj Close'].rolling(window=20).mean()[-1] * df['Volume'].rolling(window=20).mean()[-1]
        macd, macdsignal, macdhist = talib.MACD(df["Adj Close"], fastperiod=12, slowperiod=26, signalperiod=9)
        
        df_50 = df.tail(50)
        up_vol = df_50.loc[df['% Change'] > 0, 'Volume'].sum()
        down_vol = df_50.loc[df['% Change'] < 0, 'Volume'].sum()
        up_down_vol = up_vol/down_vol
        
        slowk_104, slowd_104 = talib.STOCH(df["High"], df['Low'], df['Adj Close'], fastk_period=10, slowk_period=4, slowk_matype=0, slowd_period=4, slowd_matype=0)
        slowk_5221, slowd_5221 = talib.STOCH(df["High"], df['Low'], df['Adj Close'], fastk_period=5, slowk_period=2, slowk_matype=0, slowd_period=2, slowd_matype=0)
        
        try:
            moving_average_200_20 = df["SMA_200"][-20]
        except Exception:
            moving_average_200_20 = 0
    
        # Condition 1: Current Price > 150 SMA and > 200 SMA
        condition_1 = price > moving_average_150 > moving_average_200
        
        # Condition 2: 150 SMA and > 200 SMA
        condition_2 = moving_average_150 > moving_average_200
    
        # Condition 3: 200 SMA trending up for at least 1 month
        condition_3 = moving_average_200 > moving_average_200_20
        
        # Condition 4: 50 SMA> 150 SMA and 50 SMA> 200 SMA
        condition_4 = moving_average_50 > moving_average_150 > moving_average_200
           
        # Condition 5: Current Price > 50 SMA
        condition_5 = price > moving_average_50
           
        # Condition 6: Current Price is at least 30% above 52 week low
        condition_6 = price >= (1.3*low_of_52week)
           
        # Condition 7: Current Price is within 25% of 52 week high
        condition_7 = price >= (.75*high_of_52week)
        
        # Condition 8: Current Price > 10
        condition_8 = price >= 10
        
        # Condition 9: DCR is greater than 40
        condition_9 = dcr > 40
        
        # Condition 10: WCR is greater than 50
        condition_10 = wcr > 50
        
        # Condition 11: Volatility less than 80
        condition_11 = volatility < 80
        
        # Condition 12: Average daily dollar volume
        condition_12 = avg_dollar_volume > 30000000
        
        # Condition 13: Up/Down Volume > 1
        condition_13 = up_down_vol > 1
    
        # Condition 14: Stochastic 10.4 < 80
        condition_14 = slowk_104[-1] < 80
        
        # Condition 15: Slingshot
        condition_15 = price > df['EMA_4_H'][-1] and df['Adj Close'][-2] < df['EMA_4_H'][-2] and df['Adj Close'][-3] < df['EMA_4_H'][-3] and df['Adj Close'][-4] < df['EMA_4_H'][-4]
    
        # Condition 16: 50SMA bounce
        condition_16 = df["Low"][-2] < df["SMA_50"][-2] and df["High"][-2] > df["SMA_50"][-2] and price > df["SMA_50"][-1]
    
        # Condition 17: 15.2BBANDS bounce
        condition_17 = df["Low"][-2] < lower[-2] and df["High"][-2] > lower[-2] and price > lower[-1]
    
        # Condition 18: Power of three
        condition_18 = price > 0.98*df['EMA_21'][-1] and price < 1.02*df['EMA_21'][-1] and price > 0.98*df['SMA_10'][-1] and price <1.02*df['SMA_10'][-1] and price > 0.98*df['SMA_50'][-1] and price < 1.02*df['SMA_50'][-1]
    
        # Condition 19: 3 Weeks tight
        logic = {'Open'  : 'first',
             'High'  : 'max',
             'Low'   : 'min',
             'Adj Close' : 'last',
             'Volume': 'sum'}
        offset = dt.timedelta(days = 6)
        df_week = df.resample('W', loffset=offset).apply(logic)
        condition_19 = df_week['Adj Close'][-2]/df_week['Adj Close'][-3] < 1.015 and df_week['Adj Close'][-2]/df_week['Adj Close'][-3] >.985 and df_week['Adj Close'][-1]/df_week['Adj Close'][-2] < 1.015 and df_week['Adj Close'][-1]/df_week['Adj Close'][-2] >.985 and df_week['Adj Close'][-1]/df_week['Adj Close'][-3] < 1.015 and df_week['Adj Close'][-1]/df_week['Adj Close'][-3] >.985
    
        # Condition 20: PGO
        condition_20 = (price > df["SMA_30"][-1]) and (slowk_104[-2] < slowd_104[-2]) and (slowk_104[-2] < 60) and (slowk_104[-1] > slowd_104[-2]) and (price > df["Adj Close"][-2]) and (price > df["Adj Close"][-3]) and (price > df["Adj Close"][-4]) and (rel_volume > 0.9) and (df["EMA_2"][-1] > df["EMA_8"][-1]) and ((df["EMA_3"][-1] / df["EMA_5"][-1]) < 1.5) and ((df["EMA_4"][-1] / df["EMA_8"][-1]) > 0.7) and ((df["EMA_5"][-1] / df["EMA_30"][-1]) > .95) and (macdhist[-1]>macdhist[-2])
    
        # Condition 21: Green Dot
        condition_21 = (price > df["SMA_30"][-1]) and (slowk_104[-2] < slowd_104[-2]) and (slowk_104[-2] < 60) and (slowk_104[-1] > slowd_104[-2])
        
        # Condition 22: Teal Dot
        condition_22 = (price > df["Open"][-1]) and (dcr > 40) and (slowk_5221[-2] < 60) and (slowk_5221[-2] < slowd_5221[-2]) and (slowk_5221[-1] > slowd_5221[-1])
        
        # Condition 23: 3BBU
        condition_23 = price > df["High"][-2] and price > df["High"][-3] and price > df["High"][-4] and df["High"][-2] < df["High"][-4]
        
        # Condition 24: 21EMA bounce
        condition_24 = df["Low"][-2] < df["EMA_21"][-2] and df["High"][-2] > df["EMA_21"][-2] and price > df["EMA_21"][-1]
    
        # Condition 25: Upside Reversal
        condition_25 = dcr > 60 and ((price-df["Low"][-1])/(df["High"][-1]-df["Low"][-1])) > 0.6 and (df["Low"][-1] < df["Low"][-2]) and (slowk_5221[-2] < 85)
    
        # Condition 26: Oops Reversal
        condition_26 =  df["Open"][-1] < df["Low"][-2] and price > df["Low"][-2]
    
        # Condition 27: EPS Growth Q/Q
        condition_27 = eps_q > 0
    
        # Condition 28: Sales Growth Q/Q
        condition_28 = sales_q > 0
        
        # Condition 29: Return on Equity
        condition_29 = roe > 0
        
        # Condition 30: Gross Margin
        condition_30 = gross_margin > 0
    
        # Condition 31: EPS Growth Next Year
        condition_31 = eps_next_year > 0
    
        # Condition 32: EPS Growth This Year
        condition_32 = eps_this_year > 0
    
        # Condition 33: Relative Volume > 1 & Change from Open > 0
        condition_33 = rel_volume > 1 and price > df["Open"][-1]
    
        message = '\nReqs Passed:'
        
        if (condition_8):
            buy_rating += 1
            message += "\nPrice > 10"
            
        if (condition_9):
            buy_rating += 2
            message += "\nDCR > 40"
            
        if (condition_10):
            buy_rating += 2
            message += "\nWCR > 50"
            
        if (condition_11):
            buy_rating += 2
            message += "\nVolatility < 80"
            
        if (condition_14):
            buy_rating += 2
            message += "\nStochastic 10.4 < 80"
            
        if (condition_13):
            buy_rating += 5
            message += "\nUp/Down Vol > 1"
            
        if (condition_12):
            buy_rating += 4
            message += "\nAverage Daily Dollar Volume > 30M"
            
        if (condition_29):
            buy_rating += 3
            message += "\nReturn on Equity"
            
        if (condition_30):
            buy_rating += 3
            message += "\nGross Margin"
            
        if (condition_32):
            buy_rating += 4
            message += "\nEPS Growth This Year"

        if (condition_31):
            buy_rating += 5
            message += "\nEPS Growth Next Year"

        if (condition_27):
            buy_rating += 6
            message += "\nEPS Growth Q/Q"
            
        if (condition_28):
            buy_rating += 6
            message += "\nSales Growth Q/Q"
            
        if (condition_1 and condition_2 and condition_3 and condition_4 and condition_5 and condition_6 and condition_7):
            buy_rating += 10
            message += "\nMinervini Trend Template"
            
        if (condition_33):
            buy_rating += 4
            message += "\nRelative Volume > 1 & Change From Open > 0"
            
        if (condition_16):
            buy_rating += 5
            message += "\n50SMA Bounce"
    
        if (condition_19):
            buy_rating += 5
            message += "\n3 Weeks Tight"

        if (condition_15):
            buy_rating += 4
            message += "\nSlingshot"

        if (condition_17):
            buy_rating += 4
            message += "\n15.2BBANDS Bounce"
    
        if (condition_18):
            buy_rating += 4
            message += "\nPower of Three"
            
        if (condition_20):
            buy_rating += 4
            message += "\nPGO"
            
        if (condition_21):
            buy_rating += 4
            message += "\nGreen Dot"
            
        if (condition_22):
            buy_rating += 3
            message += "\nTeal Dot"
            
        if (condition_23):
            buy_rating += 3
            message += "\n3BBU"
            
        if (condition_24):
            buy_rating += 2
            message += "\n21EMA Bounce"
            
        if (condition_25):
            buy_rating += 1
            message += "\nUpside Reversal"
            
        if (condition_26):
            buy_rating += 1
            message += "\nOops Reversal"
        
        return buy_rating, message
        
    except:
        buy_rating = 0
        message = 'None'
        return buy_rating, message

def get_sell_rating(ticker):
    try:
        sell_rating = 0
        start = dt.date.today() - dt.timedelta(days = 365)
        end = dt.date.today()
        
        df = pdr.get_data_yahoo(ticker, start, end)
        price = df["Adj Close"][-1]
        df['% Change'] = df['Adj Close'].pct_change()
        
        sma = [10, 30, 50, 150, 200]
        for x in sma:
            df["SMA_"+str(x)] = round(df['Adj Close'].rolling(window=x).mean(), 2)
            
        ema = [2, 3, 4, 5, 8, 21, 30, 65]
        for x in ema:
            df["EMA_"+str(x)] = talib.EMA(df['Adj Close'], timeperiod=x)
        
        # Storing required values
        moving_average_50 = df["SMA_50"][-1]
        moving_average_150 = df["SMA_150"][-1]
        moving_average_200 = df["SMA_200"][-1]
        low_of_52week = round(min(df["Low"][-260:]), 2)
        high_of_52week = round(max(df["High"][-260:]), 2)
        
        mcr = (100*(price - df['Low'].rolling(window=21).min())/(df['High'].rolling(window=21).max() - df['Low'].rolling(window=21).min()))[-1]
        dcr = (100*(price - df['Low'].rolling(window=1).min())/(df['High'].rolling(window=1).max() - df['Low'].rolling(window=1).min()))[-1]
        
        volatility = ((((df['High'].rolling(window=10).max())/(df['Low'].rolling(window=10).min()))-1)*100)[-1]

        df_50 = df.tail(50)
        up_vol = df_50.loc[df['% Change'] > 0, 'Volume'].sum()
        down_vol = df_50.loc[df['% Change'] < 0, 'Volume'].sum()
        up_down_vol = up_vol/down_vol
        
        slowk_104, slowd_104 = talib.STOCH(df["High"], df['Low'], df['Adj Close'], fastk_period=10, slowk_period=4, slowk_matype=0, slowd_period=4, slowd_matype=0)
        
        finviz_data = get_finviz_data(ticker)
        rel_volume = finviz_data['Rel Volume']
        
        try:
            moving_average_200_20 = df["SMA_200"][-20]
        except Exception:
            moving_average_200_20 = 0
    
        # Condition 1: Current Price > 150 SMA and > 200 SMA
        condition_1 = price > moving_average_150 > moving_average_200
        
        # Condition 2: 150 SMA and > 200 SMA
        condition_2 = moving_average_150 > moving_average_200
    
        # Condition 3: 200 SMA trending up for at least 1 month
        condition_3 = moving_average_200 > moving_average_200_20
        
        # Condition 4: 50 SMA> 150 SMA and 50 SMA> 200 SMA
        condition_4 = moving_average_50 > moving_average_150 > moving_average_200
           
        # Condition 5: Current Price > 50 SMA
        condition_5 = price > moving_average_50
           
        # Condition 6: Current Price is at least 30% above 52 week low
        condition_6 = price >= (1.3*low_of_52week)
           
        # Condition 7: Current Price is within 25% of 52 week high
        condition_7 = price >= (.75*high_of_52week)

        # Condition 8: Heavy Volume On Selling
        condition_8 = rel_volume > 1.3 and price < df["Open"][-1]

        # Condition 9: MCR is less than 40
        condition_9 = mcr < 40
        
        # Condition 10: Volatility greater than 80
        condition_10 = volatility > 80

        # Condition 11: Up/Down Volume < 1
        condition_11 = up_down_vol < 1
    
        # Condition 12: Stochastic 10.4 > 80
        condition_12 = slowk_104[-1] > 80
        
        # Condition 13: Price < 21EMA for 2 closes
        condition_15 = price < df["EMA_21"][-1] and df["Adj Close"][-2] < df["EMA_21"][-2]

        # Condition 14: Price < 65EMA for 2 closes
        condition_14 = price < df["EMA_65"][-1] and df["Adj Close"][-2] < df["EMA_65"][-2]

        # Condition 15: Price < 50SMA for 2 closes
        condition_13 = price < df["SMA_50"][-1] and df["Adj Close"][-2] < df["SMA_50"][-2]

        # Condition 16: Price < 200SMA for 2 closes
        condition_16 = price < df["SMA_200"][-1] and df["Adj Close"][-2] < df["SMA_200"][-2]
                                                                    
        # Condition 17: 3BBD
        condition_17 = price < df["Low"][-2] and price < df["Low"][-3] and price < df["Low"][-4]
        
        # Condition 18: Downside Reversal
        condition_18 = df["High"][-1]<df["High"][-2] and df["Adj Close"][-1]<df["Adj Close"][-2] and dcr<40

        message = '\nSell Reqs Passed:'
            
        if not(condition_1 and condition_2 and condition_3 and condition_4 and condition_5 and condition_6 and condition_7):
            sell_rating += 15
            message += "\nNo Minervini Trend Template"
        
        if (condition_8):
            sell_rating += 20
            message += "\nHeavy Volume On Selling"
            
        if (condition_9):
            sell_rating += 5
            message += "\nMCR < 40"
            
        if (condition_10):
            sell_rating += 10
            message += "\nVolatility > 80"
            
        if (condition_11):
            sell_rating += 18
            message += "\nUp/Down Vol < 1"

        if (condition_12):
            sell_rating += 5
            message += "\nStochastic 10.4 > 80"
            
        if (condition_13):
            sell_rating += 7
            message += "\nPrice < 21EMA (2x)"
            
        if (condition_14):
            sell_rating += 12
            message += "\nPrice < 65EMA (2x)"
        
        if (condition_15):
            sell_rating += 12
            message += "\nPrice < 50SMA (2x)"
            
        if (condition_16):
            sell_rating += 20
            message += "\nPrice < 200SMA (2x)"
        
        if (condition_17):
            sell_rating += 7
            message += "\n3BBD"
            
        if (condition_18):
            sell_rating += 7
            message += "\nDownside Reversal"
            
        rating = round(100 * (sell_rating / 80))
        
        return rating, message
        
    except:
        buy_rating = 0
        message = 'None'
        return buy_rating, message

def recently_priced():
    url = ("https://www.marketwatch.com/tools/ipo-calendar")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    ipo = pd.read_html(str(html), attrs = {'class': 'table table--primary ranking table--overflow tool-table'})[0]
    return ipo.head(20)

def this_week_ipos():
    url = ("https://www.marketwatch.com/tools/ipo-calendar")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    ipo = pd.read_html(str(html), attrs = {'class': 'table table--primary ranking table--overflow tool-table'})[1]
    return ipo

def next_week_ipos():
    url = ("https://www.marketwatch.com/tools/ipo-calendar")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    ipo = pd.read_html(str(html), attrs = {'class': 'table table--primary ranking table--overflow tool-table'})[2]
    return ipo

def future_ipos():
    url = ("https://www.marketwatch.com/tools/ipo-calendar")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    ipo = pd.read_html(str(html), attrs = {'class': 'table table--primary ranking table--overflow tool-table'})[3]
    return ipo.columns

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
    futures = futures.reset_index()
    return futures

def news():
    url = ("https://finviz.com/news.ashx")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")

    news = pd.read_html(str(html))[5]
    news.columns = ['0', 'Time', 'Headlines']
    news = news.drop(columns = ['0'])
    return news.head(17)

def universe():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_smallover,fa_epsqoq_o20,fa_epsyoy_o20,fa_epsyoy1_pos,fa_grossmargin_pos,fa_roe_pos,fa_salesqoq_o20,sh_avgvol_o200,sh_price_o10,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=-high52w&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def long_buys():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_midover,fa_epsqoq_o25,fa_epsyoy_o20,fa_epsyoy1_o25,fa_grossmargin_pos,fa_roe_o15,fa_salesqoq_o25,ind_stocksonly,sh_avgvol_o200,sh_price_o10,ta_perf_52wup,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=-relativevolume&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def strength():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=fa_epsqoq_o25,fa_epsyoy_o25,fa_epsyoy1_o25,fa_salesqoq_o25,ind_stocksonly,sh_avgvol_o200,sh_float_u50,ta_highlow52w_b0to10h&ft=4&o=-high52w&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def alpha():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_midover,fa_epsyoy1_o20,fa_salesqoq_o20,ind_stocksonly,ipodate_prev3yrs,sh_avgvol_o500,sh_price_o15,ta_changeopen_u,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=-relativevolume&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def squeeze():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=fa_epsyoy_o20,ind_stocksonly,sh_avgvol_o300,sh_float_u20,sh_price_o15,sh_short_o10,ta_changeopen_u,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=-shortinterestratio&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def leaps():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_smallover,fa_epsqoq_o20,fa_epsyoy_o20,fa_epsyoy1_o25,fa_grossmargin_pos,fa_roe_o15,fa_salesqoq_o25,sh_avgvol_o200,sh_instown_o30,sh_price_o5,ta_perf_52wup&ft=4&o=high52w&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def new_highs():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_smallover,fa_epsqoq_pos,fa_epsyoy_pos,fa_epsyoy1_pos,fa_roe_pos,fa_salesqoq_pos,sh_avgvol_o200,sh_price_o10,ta_change_u,ta_changeopen_u,ta_highlow20d_nh,ta_highlow50d_nh,ta_highlow52w_nh,ta_perf_dup,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=-relativevolume&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def get_top_stocks():
    ups = si.get_day_gainers()
    return ups.head(15)

def get_bottom_stocks():
    downs = si.get_day_losers()
    return downs.head(15)

@app.route('/', methods = ['GET','POST'])
def screener():
    try:
        message_body = request.form['Body']
        resp = MessagingResponse()
        
        if message_body in si.tickers_sp500() or message_body in si.tickers_nasdaq() or message_body in si.tickers_other():
            stock = message_body
            
            # price
            price = si.get_live_price('{}'.format(message_body))
            price = round(price, 2)

            finwiz_url = 'https://finviz.com/quote.ashx?t='
            news_tables = {}
            
            url = finwiz_url + stock
            req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'})
            response = urlopen(req)
            html = BeautifulSoup(response, features="lxml")
            news_table = html.find(id='news-table')
            news_tables[stock] = news_table
            
            parsed_news = []
            
            # Iterate through the news
            for file_name, news_table in news_tables.items():
                for x in news_table.findAll('tr'):
                    text = x.a.get_text()
                    date_scrape = x.td.text.split()
            
                    if len(date_scrape) == 1:
                        time = date_scrape[0]
                        
                    else:
                        date = date_scrape[0]
                        time = date_scrape[1]
            
                    ticker = file_name.split('_')[0]
                    
                    parsed_news.append([ticker, date, time, text])
                    
            vader = SentimentIntensityAnalyzer()
            
            columns = ['ticker', 'date', 'time', 'headline']
            dataframe = pd.DataFrame(parsed_news, columns=columns)
            scores = dataframe['headline'].apply(vader.polarity_scores).tolist()
            
            scores_df = pd.DataFrame(scores)
            dataframe = dataframe.join(scores_df, rsuffix='_right')

            dataframe = dataframe.set_index('ticker')
            
            sentiment = round(dataframe['compound'].mean(), 2)
            stock_headlines = dataframe['headline'].tolist()
            times = dataframe['time'].tolist()
            dates = dataframe['date'].tolist()

            num_of_years = 40
            start_date = dt.datetime.now() - dt.timedelta(int(365.25 * num_of_years))
            end_date = dt.datetime.now()

            df = pdr.get_data_yahoo(stock, start_date, end_date).dropna()
            
            df.drop(df[df["Volume"]<1000].index, inplace=True)
            
            avg_volume = df['Volume'].head(50).mean()
            avg_volume = round(avg_volume)
            avg_volume = '{:,}'.format(avg_volume)

            current_volume = df['Volume'].tolist()
            current_volume = round(current_volume[-1])
            current_volume = '{:,}'.format(current_volume)

            dfmonth=df.groupby(pd.Grouper(freq="M"))["High"].max()

            glDate=0
            lastGLV=0
            currentDate=""
            curentGLV=0
            for index, value in dfmonth.items():
                if value > curentGLV:
                    curentGLV=value
                    currentDate=index
                    counter=0
                if value < curentGLV:
                    counter=counter+1

                    if counter==3 and ((index.month != end_date.month) or (index.year != end_date.year)):
                        if curentGLV != lastGLV:
                            glDate=currentDate
                            lastGLV=curentGLV
                            counter=0
            
            df = pdr.get_data_yahoo(stock, start_date, end_date).dropna()
            sma = 50

            df['SMA'+str(sma)] = df.iloc[:,4].rolling(window=sma).mean() 
            df['PC'] = ((df["Adj Close"]/df['SMA'+str(sma)])-1)*100

            mean = round(df["PC"].mean(), 2)
            stdev= round(df["PC"].std(), 2)
            current = round(df["PC"][-1], 2)
            yday = round(df["PC"][-2], 2)

            last_close = df['Close'].tolist()[-2]
            change = str(round(((price-last_close)/last_close)*100, 4)) + '%'

            # Set up scraper
            url = (f"https://finviz.com/screener.ashx?v=152&ft=4&t={stock}&ar=180&c=1,2,3,4,5,6,10,16,17,18,22,23,25,27,28,29,31,33,39,42,43,46,47,53,54,57,58,60,63,64,65,66,67,68,69")
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            webpage = urlopen(req).read()
            html = BeautifulSoup(webpage, "html.parser")

            stocks = pd.read_html(str(html))[-2]
            stocks.columns = stocks.iloc[0]
            stocks = stocks[1:]
            stocks['Price'] = [f'{price}']
            stocks['Change'] = [f'{change}']
            stocks['Mean Dev. from 50 SMA'] = [f'{mean}%']
            stocks['Stdev. from 50 SMA'] = [f'{stdev}%']
            stocks["Yday Dev. from 50 SMA"] = [f'{yday}%']
            stocks['Curr Dev. from 50 SMA'] = [f'{current}%']
            stocks['News Sentiment'] = [f'{sentiment}']
            message = "\n"
            for attr, val in zip(stocks.columns, stocks.iloc[0]):
                message=message + f"{attr} : {val}\n"
            
            rating, buy_message = buy_rating(message_body)
            rate = round(100 * (rating / 80))
            message=message + "------------------------\n"
            message=message + f"Buy Rating for {ticker} is {rate}"
            
            if rate >= 86:
                action = "Strong Buy"
            elif rate >= 75:
                action = "Buy"
            else:
                action = "N/A"
            
            message=message + ('\nBuy Action: ' + action)
            message=message + buy_message
            
            
            s_rating, sell_message = get_sell_rating(message_body)
            message=message + "\n------------------------\n"
            message=message + f"Sell Rating for {ticker} is {s_rating}"
            
            if rating >= 100:
                action = "STRONG Sell"
            elif rating >= 80 and rating < 100:
                action = "Strong Sell"
            elif rating >= 68 and rating < 80:
                action = "Sell"
            else:
                action = "N/A"
            
            message=message + ('\nSell Action: ' + action)
            message=message + sell_message

        elif message_body.lower() == 'functions':
            message = """
            Texting Functions:
            \n Enter a ticker to get its information
            \n Enter "news" to get recent market news
            \n Enter "gainers" to get today's top gainers
            \n Enter "losers" to get today's top losers
            \n Enter "futures" to get futures index data
            \n Enter "earnings" to get upcoming earning dates
            \n Enter "buys" to get long term stock buys
            \n Enter "universe" to get quality growth stocks
            \n Enter "strength" to get stocks showing RS
            \n Enter "alpha" to get potential setups
            \n Enter "squeeze" to get potential short squeezes
            \n Enter "future ipos" to get future ipos
            \n Enter "this week ipos" to get the ipos for this week
            \n Enter "next week ipos" to get the ipos for next week
            \n Enter "recent ipos" to get recently ipo'd stocks
                    """

        elif message_body.lower() == 'news':
            df = news()
            headlines = df['Headlines'].tolist()
            times = df['Time'].tolist()

            message = "Market News:"
            for time, headline in zip(times, headlines):
                message += f"\n{time} : {headline}"

        elif message_body.lower() == 'future ipos':
            df = future_ipos()
            symbols = df['Proposed Symbol'].tolist()
            prices = df['Price Range'].tolist()
            shares = df['Shares'].tolist()

            message = "Future IPOS:"
            for symbol, price, share in zip(symbols, prices, shares):
                message += f"\n{symbol} | {price} | {share}"

        elif message_body.lower() == 'this week ipos':
            df = this_week_ipos()
            symbols = df['Proposed Symbol'].tolist()
            prices = df['Price Range'].tolist()
            shares = df['Shares'].tolist()

            message = "This Week IPOS:"
            for symbol, price, share in zip(symbols, prices, shares):
                message += f"\n{symbol} | {price} | {share}"

        elif message_body.lower() == 'next week ipos':
            df = next_week_ipos()
            symbols = df['Proposed Symbol'].tolist()
            prices = df['Price Range'].tolist()
            shares = df['Shares'].tolist()

            message = "Next Week IPOS:"
            for symbol, price, share in zip(symbols, prices, shares):
                message += f"\n{symbol} | {price} | {share}"
                
        elif message_body.lower() == 'recent ipos':
            df = next_week_ipos()
            symbols = df['Symbol'].tolist()
            prices = df['Price'].tolist()
            shares = df['Shares'].tolist()
            dates = df['IPO Date'].tolist()

            message = "Recent IPOS:"
            for symbol, price, share, date in zip(symbols, prices, shares, dates):
                message += f"\n{symbol} | {price} | {share} | {date}"

        elif message_body.lower() == 'gainers':
            df = get_top_stocks()
            tickers = df['Symbol'].tolist()
            prices = df['Price (Intraday)'].tolist()
            changes = df['% Change'].tolist()

            message = "Top Gainers:"
            for ticker, price, change in zip(tickers, prices, changes):
                message += f"\n{ticker} : {price} : {change}"
        
        elif message_body.lower() == 'losers':
            df = get_bottom_stocks()
            tickers = df['Symbol'].tolist()
            prices = df['Price (Intraday)'].tolist()
            changes = df['% Change'].tolist()

            message = "Top Losers:"
            for ticker, price, change in zip(tickers, prices, changes):
                message += f"\n{ticker} : {price} : {change}"

        elif message_body.lower() == 'futures':
            df = get_futures()
            indices = df['Index'].tolist()
            prices = df['Last'].tolist()
            changes = df['Change (%)'].tolist()

            message = "Futures:"
            for index, price, change in zip(indices, prices, changes):
                message += f"\n{index} | {price} | {change}"

        elif message_body.lower() == 'earnings':
            df = get_earnings()

            message = "Earnings:"
            for i in range(len(df)):
                message += f"\n{df.iloc[i]}"

        elif all(x in message_body.lower() for x in ['buy']) or all(x in message_body.lower() for x in ['buys']):
            df = long_buys()
            tickers = df['Ticker'].tolist()
            
            message = "Stocks to Buy (Long Term):\n{0}".format( ', '.join(map(str, tickers)))
            
        elif message_body.lower() == 'new highs':
            df = new_highs()
            tickers = df['Ticker'].tolist()
            
            message = "Stocks Making New Highs:\n{0}".format( ', '.join(map(str, tickers)))
            
        elif message_body.lower() == 'leaps':
            df = leaps()
            tickers = df['Ticker'].tolist()
            
            message = "LEAPS:\n{0}".format( ', '.join(map(str, tickers)))
            
        elif all(x in message_body.lower() for x in ['rs']) or all(x in message_body.lower() for x in ['strength']):
            df = strength()
            tickers = df['Ticker'].tolist()
            
            message = "Stocks Showing RS:\n{0}".format( ', '.join(map(str, tickers)))
            
        elif all(x in message_body.lower() for x in ['alpha']):
            df = alpha()
            tickers = df['Ticker'].tolist()
            
            message = "Alpha Setup:\n{0}".format( ', '.join(map(str, tickers)))
            
        elif all(x in message_body.lower() for x in ['squeeze']) or all(x in message_body.lower() for x in ['squeezes']):
            df = squeeze()
            tickers = df['Ticker'].tolist()
            
            message = "Short Squeeze Setup:\n{0}".format( ', '.join(map(str, tickers)))
        
        elif all(x in message_body.lower() for x in ['universe']):
            df = universe()
            tickers = df['Ticker'].tolist()
        
            message = "Universe Growth Stocks:\n{0}".format( ', '.join(map(str, tickers)))

        resp.message(message)
        return str(resp)
    
    except Exception as e:
        resp = MessagingResponse()
        resp.message(f'\n{e}')
        return str(resp)
    
if __name__ == "__main__":
    app.run(port=5000, debug=True)
