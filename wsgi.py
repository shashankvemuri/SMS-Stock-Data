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
yf.pdr_override()

app = Flask(__name__)

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

def quality():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=fa_epsqoq_o15,fa_epsyoy_pos,fa_epsyoy1_o25,fa_grossmargin_pos,fa_salesqoq_o25,ind_stocksonly,sh_avgvol_o300,sh_insttrans_pos,sh_price_o10,ta_perf_52w50o,ta_sma200_pa,ta_sma50_pa&ft=4&o=-change")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def long_buys():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=111&f=an_recom_holdbetter,cap_midover,fa_epsqoq_o20,fa_epsyoy_o20,fa_epsyoy1_o25,fa_grossmargin_pos,fa_roe_pos,fa_salesqoq_o25,ind_stocksonly,sh_avgvol_o300,sh_insttrans_pos,sh_price_o10,ta_perf_52w50o,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=change&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = BeautifulSoup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]
    
    return stocks

def long_shorts():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_smallover,fa_epsqoq_neg,fa_epsyoy_neg,fa_epsyoy1_neg,fa_salesqoq_neg,ind_stocksonly,sh_avgvol_o300,sh_price_o5,ta_sma20_pb,ta_sma200_pa100,targetprice_below&ft=4&o=-change&ar=180")
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
        
        lb_matches1 = ["long", "buys"]
        lb_matches2 = ["long", "buy"]

        ls_matches1 = ["long", "shorts"]
        ls_matches2 = ["long", "short"]
        
        q_matches1 = ['quality', 'buys']
        q_matches2 = ['quality', 'buys']
        q_matches3 = ['growth', 'buys']
        q_matches4 = ['growth', 'buys']
        
        if message_body in si.tickers_sp500() or message_body in si.tickers_nasdaq() or message_body in si.tickers_other():
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
            
            sma = 50
            limit = 10

            df = pdr.get_data_yahoo(stock, start_date, end_date).dropna()
            sma = 50
            limit = 10

            df['SMA'+str(sma)] = df.iloc[:,4].rolling(window=sma).mean() 
            df['PC'] = ((df["Adj Close"]/df['SMA'+str(sma)])-1)*100

            mean = round(df["PC"].mean(), 2)
            stdev= round(df["PC"].std(), 2)
            current = round(df["PC"][-1], 2)
            yday = round(df["PC"][-2], 2)

            last_close = df['Close'].tolist()[-2]
            change = str(round(((price-last_close)/last_close)*100, 4)) + '%'

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
            stocks['Last Green Line Value'] = [f'{round(lastGLV, 2)}']
            stocks['Mean Dev. from 50 SMA'] = [f'{mean}%']
            stocks['Stdev. from 50 SMA'] = [f'{stdev}%']
            stocks["Yday Dev. from 50 SMA"] = [f'{yday}%']
            stocks['Curr Dev. from 50 SMA'] = [f'{current}%']
            stocks['News Sentiment'] = [f'{sentiment}']
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

            message=message + "------------------------\n"
            message=message + "Recent News:\n"

            for new, time, date in zip(stock_headlines[:4], times[:4], dates[:4]):
                message=message + f"{date} {time} : {new}\n"

        elif message_body.lower() == 'functions':
            message = """
            Texting Functions:
            \n Enter a ticker to get its information
            \n Enter "news" to get recent market news
            \n Enter "gainers" to get today's top gainers
            \n Enter "losers" to get today's top losers
            \n Enter "futures" to get futures index data
            \n Enter "earnings" to get upcoming earning dates
            \n Enter "long buys" to get long term stock buys
            \n Enter "long shorts" to get long term stock shorts
            \n Enter "quality growth buys" to get quality growth stocks
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

        elif all(x in message_body.lower() for x in lb_matches1) or all(x in message_body for x in lb_matches2):
            df = long_buys()
            tickers = df['Ticker'].tolist()
            
            message = "Stocks to Buy (Long Term):\n[{0}]".format( ', '.join(map(str, tickers)))

        
        elif all(x in message_body.lower() for x in q_matches1) or all(x in message_body for x in q_matches2) or all(x in message_body for x in q_matches3) or all(x in message_body for x in q_matches4):
            df = quality()
            tickers = df['Ticker'].tolist()
        
            message = "Quality Growth Stocks (Long Term):\n[{0}]".format( ', '.join(map(str, tickers)))
        
        elif all(x in message_body.lower() for x in ls_matches1) or all(x in message_body for x in ls_matches2):
            df = long_shorts()
            tickers = df['Ticker'].tolist()
        
            message = "Stocks to Short (Long Term):\n[{0}]".format( ', '.join(map(str, tickers)))

        resp.message(message)
        return str(resp)
    
    except Exception as e:
        resp = MessagingResponse()
        resp.message(f'\n{e}')
        return str(resp)
    
if __name__ == "__main__":
    app.run(port=5000, debug=True)
