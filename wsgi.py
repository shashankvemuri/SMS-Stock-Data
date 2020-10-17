from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from yahoo_fin import stock_info as si
import pandas as pd
from bs4 import BeautifulSoup as soup
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer

app = Flask(__name__)

def long_buys():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_midover,fa_epsyoy1_o20,fa_salesqoq_o20,geo_usa,ind_stocksonly,sh_avgvol_o500,sh_insttrans_pos,sh_price_o10,ta_highlow52w_a30h,ta_perf_52w50o,ta_perf2_13wup,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa,targetprice_above&ft=4&o=change&ar=180")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = soup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]

    tickers = stocks['Ticker'].tolist()[:5]
    
    # Get Data
    finviz_url = 'https://finviz.com/quote.ashx?t='
    news_tables = {}
    
    for ticker in tickers:
        url = finviz_url + ticker
        req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'}) 
        resp = urlopen(req)    
        html = BeautifulSoup(resp, features="lxml")
        news_table = html.find(id='news-table')
        news_tables[ticker] = news_table
    
    try:
        for ticker in tickers:
            df = news_tables[ticker]
            df_tr = df.findAll('tr')
            
            for i, table_row in enumerate(df_tr):
                a_text = table_row.a.text
                td_text = table_row.td.text
                td_text = td_text.strip()
                if i == 2:
                    break
    except KeyError:
        pass
    
    # Iterate through the news
    parsed_news = []
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
            
    # Sentiment Analysis
    analyzer = SentimentIntensityAnalyzer()
    
    columns = ['Ticker', 'Date', 'Time', 'Headline']
    news = pd.DataFrame(parsed_news, columns=columns)
    scores = news['Headline'].apply(analyzer.polarity_scores).tolist()
    
    df_scores = pd.DataFrame(scores)
    news = news.join(df_scores, rsuffix='_right')
    
    # View Data 
    news['Date'] = pd.to_datetime(news.Date).dt.date
    
    unique_ticker = news['Ticker'].unique().tolist()
    news_dict = {name: news.loc[news['Ticker'] == name] for name in unique_ticker}
    
    values = []
    for ticker in tickers: 
        dataframe = news_dict[ticker]
        dataframe = dataframe.set_index('Ticker')
        dataframe = dataframe.drop(columns = ['Headline'])
        
        mean = round(dataframe['compound'].mean(), 2)
        values.append(mean)
        
    df = pd.DataFrame(list(zip(tickers, values)), columns =['Ticker', 'Mean Sentiment']) 
    df = df.sort_values('Mean Sentiment', ascending=False)
    
    return df

def long_shorts():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_smallover,geo_usa,ind_stocksonly,sh_avgvol_o300,sh_insidertrans_neg,sh_price_o5,ta_sma20_pb,ta_sma200_pa100,targetprice_below&ft=4&o=-volume&ar=180&c=0,1,2,3,4,5,6,7,14,17,18,23,26,27,28,29,42,43,44,45,46,47,48,49,51,52,53,54,57,58,59,60,62,63,64,65,66,67,68,69")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = soup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]

    tickers = stocks['Ticker'].tolist()
    
    # Get Data
    finviz_url = 'https://finviz.com/quote.ashx?t='
    news_tables = {}
    
    for ticker in tickers:
        url = finviz_url + ticker
        req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'}) 
        resp = urlopen(req)    
        html = BeautifulSoup(resp, features="lxml")
        news_table = html.find(id='news-table')
        news_tables[ticker] = news_table
    
    try:
        for ticker in tickers:
            df = news_tables[ticker]
            df_tr = df.findAll('tr')
            
            for i, table_row in enumerate(df_tr):
                a_text = table_row.a.text
                td_text = table_row.td.text
                td_text = td_text.strip()
                if i == 2:
                    break
    except KeyError:
        pass
    
    # Iterate through the news
    parsed_news = []
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
            
    # Sentiment Analysis
    analyzer = SentimentIntensityAnalyzer()
    
    columns = ['Ticker', 'Date', 'Time', 'Headline']
    news = pd.DataFrame(parsed_news, columns=columns)
    scores = news['Headline'].apply(analyzer.polarity_scores).tolist()
    
    df_scores = pd.DataFrame(scores)
    news = news.join(df_scores, rsuffix='_right')
    
    # View Data 
    news['Date'] = pd.to_datetime(news.Date).dt.date
    
    unique_ticker = news['Ticker'].unique().tolist()
    news_dict = {name: news.loc[news['Ticker'] == name] for name in unique_ticker}
    
    values = []
    for ticker in tickers: 
        dataframe = news_dict[ticker]
        dataframe = dataframe.set_index('Ticker')
        dataframe = dataframe.drop(columns = ['Headline'])
        
        mean = round(dataframe['compound'].mean(), 2)
        values.append(mean)
        
    df = pd.DataFrame(list(zip(tickers, values)), columns =['Ticker', 'Mean Sentiment']) 
    df = df.sort_values('Mean Sentiment', ascending=True)
    
    return df

def int_buys():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_midover,fa_epsyoy1_o20,fa_salesqoq_o20,geo_usa,ind_stocksonly,ipodate_prev3yrs,sh_avgvol_o500,sh_price_o15,ta_changeopen_u,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume&ar=180&c=0,1,2,3,4,5,6,7,14,17,18,23,26,27,28,29,42,43,44,45,46,47,48,49,51,52,53,54,57,58,59,60,62,63,64,65,66,67,68,69")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = soup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]

    tickers = stocks['Ticker'].tolist()
    
    # Get Data
    finviz_url = 'https://finviz.com/quote.ashx?t='
    news_tables = {}
    
    for ticker in tickers:
        url = finviz_url + ticker
        req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'}) 
        resp = urlopen(req)    
        html = BeautifulSoup(resp, features="lxml")
        news_table = html.find(id='news-table')
        news_tables[ticker] = news_table
    
    try:
        for ticker in tickers:
            df = news_tables[ticker]
            df_tr = df.findAll('tr')
            
            for i, table_row in enumerate(df_tr):
                a_text = table_row.a.text
                td_text = table_row.td.text
                td_text = td_text.strip()
                if i == 2:
                    break
    except KeyError:
        pass
    
    # Iterate through the news
    parsed_news = []
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
            
    # Sentiment Analysis
    analyzer = SentimentIntensityAnalyzer()
    
    columns = ['Ticker', 'Date', 'Time', 'Headline']
    news = pd.DataFrame(parsed_news, columns=columns)
    scores = news['Headline'].apply(analyzer.polarity_scores).tolist()
    
    df_scores = pd.DataFrame(scores)
    news = news.join(df_scores, rsuffix='_right')
    
    # View Data 
    news['Date'] = pd.to_datetime(news.Date).dt.date
    
    unique_ticker = news['Ticker'].unique().tolist()
    news_dict = {name: news.loc[news['Ticker'] == name] for name in unique_ticker}
    
    values = []
    for ticker in tickers: 
        dataframe = news_dict[ticker]
        dataframe = dataframe.set_index('Ticker')
        dataframe = dataframe.drop(columns = ['Headline'])
        
        mean = round(dataframe['compound'].mean(), 2)
        values.append(mean)
        
    df = pd.DataFrame(list(zip(tickers, values)), columns =['Ticker', 'Mean Sentiment']) 
    df = df.sort_values('Mean Sentiment', ascending=False)
    
    return df

def int_shorts():
    # Set up scraper
    url = ("https://finviz.com/screener.ashx?v=151&f=cap_smallover,geo_usa,ind_stocksonly,sh_avgvol_o300,sh_insidertrans_neg,sh_insttrans_neg,sh_price_o7,ta_changeopen_d,ta_rsi_ob60,ta_sma200_pa100,targetprice_below&ft=4&o=-volume&ar=180&c=0,1,2,3,4,5,6,7,14,17,18,23,26,27,28,29,42,43,44,45,46,47,48,49,51,52,53,54,57,58,59,60,62,63,64,65,66,67,68,69")
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    html = soup(webpage, "html.parser")
    
    stocks = pd.read_html(str(html))[-2]
    stocks.columns = stocks.iloc[0]
    stocks = stocks[1:]

    tickers = stocks['Ticker'].tolist()
    
    # Get Data
    finviz_url = 'https://finviz.com/quote.ashx?t='
    news_tables = {}
    
    for ticker in tickers:
        url = finviz_url + ticker
        req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'}) 
        resp = urlopen(req)    
        html = BeautifulSoup(resp, features="lxml")
        news_table = html.find(id='news-table')
        news_tables[ticker] = news_table
    
    try:
        for ticker in tickers:
            df = news_tables[ticker]
            df_tr = df.findAll('tr')
            
            for i, table_row in enumerate(df_tr):
                a_text = table_row.a.text
                td_text = table_row.td.text
                td_text = td_text.strip()
                if i == 2:
                    break
    except KeyError:
        pass
    
    # Iterate through the news
    parsed_news = []
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
            
    # Sentiment Analysis
    analyzer = SentimentIntensityAnalyzer()
    
    columns = ['Ticker', 'Date', 'Time', 'Headline']
    news = pd.DataFrame(parsed_news, columns=columns)
    scores = news['Headline'].apply(analyzer.polarity_scores).tolist()
    
    df_scores = pd.DataFrame(scores)
    news = news.join(df_scores, rsuffix='_right')
    
    # View Data 
    news['Date'] = pd.to_datetime(news.Date).dt.date
    
    unique_ticker = news['Ticker'].unique().tolist()
    news_dict = {name: news.loc[news['Ticker'] == name] for name in unique_ticker}
    
    values = []
    for ticker in tickers: 
        dataframe = news_dict[ticker]
        dataframe = dataframe.set_index('Ticker')
        dataframe = dataframe.drop(columns = ['Headline'])
        
        mean = round(dataframe['compound'].mean(), 2)
        values.append(mean)
        
    df = pd.DataFrame(list(zip(tickers, values)), columns =['Ticker', 'Mean Sentiment']) 
    df = df.sort_values('Mean Sentiment', ascending=True)
    
    return df

@app.route('/sms', methods = ['POST'])
def sms():
    try:
        message_body = request.form['Body']
        resp = MessagingResponse()
        
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
        html = soup(webpage, "html.parser")

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

        resp.message(message)
        return str(resp)
    
    except Exception as e:
        resp.message(f'\n{e}')
        return str(resp)

@app.route('/screener', methods = ['POST'])
def screener():
    try:
        message_body = request.form['Body']
        resp = MessagingResponse()
        
        if message_body.lower() == 'long buys':
            df = long_buys()
            tickers = df['Ticker'].tolist()
            
            message = "Long Stocks to Buy:"
            for i in range(len(tickers)):
                message += f"\n{tickers[i]}"
        
        
        elif message_body.lower() == 'long shorts':
            df = long_shorts()
            tickers = df['Ticker'].tolist()
        
            message = "Long Stocks to Short:"
            for i in range(len(tickers)):
                message += f"\n{tickers[i]}"
        
        
        elif message_body.lower() == 'intraday buys':
            df = int_buys()
            tickers = df['Ticker'].tolist()
            
            message = "Intraday Stocks to Buy:"
            for i in range(len(tickers)):
                message += f"\n{tickers[i]}"
            
        elif message_body.lower() == 'intraday shorts':
            df = int_shorts()
            tickers = df['Ticker'].tolist()
            
            message = "Intraday Stocks to Short:"
            for i in range(len(tickers)):
                message += f"\n{tickers[i]}"
        
        else:
            message = "Include (long or intraday) and (buys or shorts) in your message!"
        
        resp.message(message)
        return str(resp)
    
    except Exception as e:
        resp.message(f'\n{e}')
        return str(resp)
    
if __name__ == "__main__":
    app.run(port=5000, debug=True)