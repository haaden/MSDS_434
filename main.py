import os

#from flask import Flask, request, jsonify
#https://medium.datadriveninvestor.com/build-a-stock-sentiment-web-app-with-flask-and-deploy-it-online-3930e58a236c
import flask
from flask import Flask, render_template # for web app
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json # for graph plotting in website
# NLTK VADER for sentiment analysis
import nltk
from yaml import load
nltk.downloader.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import yfinance as yf
import datetime
import tweepy
import re
import json
from transformers import pipeline
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas_gbq

# set bigquery credential 

def gcpcred():
    KEY_PATH='model'

    CREDS = service_account.Credentials.from_service_account_file(KEY_PATH)

    client = bigquery.Client(credentials=CREDS, project=CREDS.project_id)
    
    return client

#get company name form bigquery
def getbigquerydata(ticker):

    client = gcpcred()
    Q2 = f"""\
        SELECT ticker, title \
        FROM  StockSentiment.compinfo \
            where ticker = '{ticker}' """
    compname= pandas_gbq.read_gbq(Q2, project_id=CREDS.project_id, credentials=CREDS)

    compname = compname['title'].to_list()[0]

    return compname





load_dotenv()
# set up tweepy authentication 
def tweepyauth():
    auth = tweepy.OAuth1UserHandler(os.getenv('api_key'), os.getenv('api_secret_key'))

    auth.set_access_token(os.getenv('access_token'), os.getenv('secret_access_token'))

    api = tweepy.API(auth, wait_on_rate_limit=True)

    #api.verify_credentials()

    try:
        api.verify_credentials()
        print ("cred ok")
    except:
        print("cred not working")
    
    return api



# parsing function to extract other relevant attributes from the json list and make  customised dictionary

def parse_tweets(status):
    parsedTweets = []
    for tweet in status:


        if 'full_text' in tweet._json:
            full_text = tweet._json['full_text']
        else:
            full_text = tweet._json['text']

        mydict = { "tweet_id": tweet._json["id_str"],
                       "date":tweet._json["created_at"],
                       "full_text": full_text,                    
                       "hyperlink": "https://twitter.com/twitter/status/" + tweet._json["id_str"]
              }
        parsedTweets.append(mydict) # Add Tweet to parsedTweets list
    return parsedTweets




def get_tweetdf(ticker):
    api = tweepyauth()
    # setupkeywords
    keywords= f'"{ticker}" "STOCK"'
   
    #https://twittercommunity.com/t/correct-syntax-for-an-exact-phrase-match-and-keyword-query/124617
    status = tweepy.Cursor(api.search_tweets,q = keywords, lang ='en', result_type= 'mixed', tweet_mode='extended', 
                          count=100).items(300)
    parsedTweets = parse_tweets(status)

    tweetdf = pd.DataFrame(parsedTweets)
    return tweetdf

#setting up hugging face model
model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
sentiment_task = pipeline("sentiment-analysis", model=model_path, tokenizer=model_path)

def get_tweet_sentiment(ticker):
    tweetdf = get_tweetdf(ticker)
    
    label = []
    score= []
    for i in tweetdf['full_text'].to_list():
        sentiment = sentiment_task(i)[0]
        #print(sentiment)
        label.append(sentiment['label'])
        score.append(sentiment['score'])
    tweetdf['label']= label
    tweetdf['score']= score

    tweetdf.date = tweetdf.date.astype('datetime64[ns]','%Y%m%d')
    tweet_date_min = tweetdf['date'].min()
    tweet_date_max = tweetdf['date'].max()
    

    return tweetdf,tweet_date_min,tweet_date_max

# for extracting data from finviz
finviz_url = 'https://finviz.com/quote.ashx?t='

def get_news(ticker):
    url = finviz_url + ticker
    req = Request(url=url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}) 
    response = urlopen(req)    
    # Read the contents of the file into 'html'
    html = BeautifulSoup(response)
    # Find 'news-table' in the Soup and load it into 'news_table'
    news_table = html.find(id='news-table')
    return news_table
	
# parse news into dataframe
def parse_news(news_table):
    parsed_news = []
    
    for x in news_table.findAll('tr'):
        # read the text from each tr tag into text
        # get text from a only
        text = x.a.get_text() 
        # splite text in the td tag into a list 
        date_scrape = x.td.text.split()
        # if the length of 'date_scrape' is 1, load 'time' as the only element

        if len(date_scrape) == 1:
            time = date_scrape[0]
            
        # else load 'date' as the 1st element and 'time' as the second    
        else:
            date = date_scrape[0]
            time = date_scrape[1]
        
        # Append ticker, date, time and headline as a list to the 'parsed_news' list
        parsed_news.append([date, time, text])
        
        # Set column names
        columns = ['date', 'time', 'headline']

        # Convert the parsed_news list into a DataFrame called 'parsed_and_scored_news'
        parsed_news_df = pd.DataFrame(parsed_news, columns=columns)
        
        # Create a pandas datetime object from the strings in 'date' and 'time' column
        parsed_news_df['datetime'] = pd.to_datetime(parsed_news_df['date'] + ' ' + parsed_news_df['time'])

        # get max and min date for yfinance 
        news_date_min = parsed_news_df['datetime'].min()
        news_date_max = parsed_news_df['datetime'].max()

        
    return parsed_news_df, news_date_min, news_date_max
        
def score_news(parsed_news_df):
    # Instantiate the sentiment intensity analyzer
    vader = SentimentIntensityAnalyzer()
    
    # Iterate through the headlines and get the polarity scores using vader
    scores = parsed_news_df['headline'].apply(vader.polarity_scores).tolist()

    # Convert the 'scores' list of dicts into a DataFrame
    scores_df = pd.DataFrame(scores)

    # Join the DataFrames of the news and the list of dicts
    parsed_and_scored_news = parsed_news_df.join(scores_df, rsuffix='_right')
    
            
    parsed_and_scored_news = parsed_and_scored_news.set_index('datetime')
    
    parsed_and_scored_news = parsed_and_scored_news.drop(['date', 'time'], 1)    
        
    parsed_and_scored_news = parsed_and_scored_news.rename(columns={"compound": "sentiment_score"})

    return parsed_and_scored_news

# def plot_hourly_sentiment(parsed_and_scored_news, ticker):
   
#     # Group by date and ticker columns from scored_news and calculate the mean
#     mean_scores = parsed_and_scored_news.resample('H').mean()

#     # Plot a bar chart with plotly
#     fig = px.bar(mean_scores, x=mean_scores.index, y='sentiment_score', title = ticker + ' Hourly Sentiment Scores')
#     return fig # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later

def plot_daily_sentiment(parsed_and_scored_news, ticker):

   
    # Group by date and ticker columns from scored_news and calculate the mean

    mean_scores = parsed_and_scored_news.resample('D').mean()

    # Plot a bar chart with plotly
    fig = px.bar(mean_scores, x=mean_scores.index, y='sentiment_score', title = ticker + ' Daily News Sentiment Scores')
    return fig # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later


def plot_daily_price(ticker, start= datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d'), \
     end = (datetime.datetime.now(datetime.timezone.utc)- datetime.timedelta(days=30)).strftime('%Y%m%d%H%M')):
   
   
    # Group by date and ticker columns from scored_news and calculate the mean
    data = yf.download(ticker, start ,end )
    # data =pd.data

    # Plot a bar chart with plotly
    fig = px.line(data, x=data.index, y='Adj Close', title = ticker +' Daily price')
    return fig # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later

def plot_daily_sentiment_tweet(tweetdf, ticker):

           
    # Group by date and ticker columns from scored_news and calculate the mean

    tweetdf_scores = tweetdf.resample('D').mean()

    # Plot a bar chart with plotly
    fig = px.bar(tweetdf_scores, x=tweetdf_scores.index, y='score', title = ticker + ' Daily twitter Sentiment Scores')
    return fig # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later


def plot_daily_price_tweet(ticker, start= datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d'), \
     end = (datetime.datetime.now(datetime.timezone.utc)- datetime.timedelta(days=7)).strftime('%Y%m%d')):
   
   
    # Group by date and ticker columns from scored_news and calculate the mean
    data = yf.download(ticker, start ,end )
    # data =pd.data

    # Plot a bar chart with plotly
    fig = px.line(data, x=data.index, y='Adj Close', title = ticker +' Daily price')
    return fig # instead of using fig.show(), we return fig and turn it into a graphjson object for displaying in web page later

app = Flask(__name__)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sentiment', methods = ['POST'])
def sentiment():
    #set up variable for get_twwet_sentiment()
   
    ticker = flask.request.form['ticker'].upper()

    tweetdf,tweet_date_min,tweet_date_max = get_tweet_sentiment(ticker)
    tweetdf = tweetdf[['date', 'full_text', 'label', 'score']]
    tweetdf.loc[tweetdf['label']=='Neutral', 'score']*=0.1
    tweetdf.loc[tweetdf['label']=='Negative', 'score']*=-1
    tweetdf.loc[tweetdf['label']=='Positive', 'score']*=1
    tweetdf = tweetdf.set_index('date')

    
    news_table = get_news(ticker)
    parsed_news_df, news_date_min, news_date_max = parse_news(news_table)
    parsed_and_scored_news = score_news(parsed_news_df)
    fig_news_daily = plot_daily_sentiment(parsed_and_scored_news, ticker)
    fig_price_daily = plot_daily_price(ticker, start= news_date_min, end = news_date_max)
    


    fig_price_daily_tweet = plot_daily_sentiment_tweet(tweetdf, ticker)
    fig_tweet_daily = plot_daily_price_tweet(ticker, start= tweet_date_min, end = tweet_date_max)
    company= getbigquerydata(ticker)


    graphJSON_hourly = json.dumps(fig_news_daily, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_daily = json.dumps(fig_price_daily, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_tweet = json.dumps(fig_price_daily_tweet, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_price = json.dumps(fig_tweet_daily, cls=plotly.utils.PlotlyJSONEncoder)

    header= f"Daily Sentiment of {company} : {ticker} Stock"
    description = """
    News for {}

    """.format(ticker)

    descriptionT = """
    Tweets for {}

    """.format(ticker)
    return render_template('sentiment.html',graphJSON_hourly=graphJSON_hourly, graphJSON_daily=graphJSON_daily,graphJSON_tweet=graphJSON_tweet,graphJSON_price=graphJSON_price,
     header=header,table=parsed_and_scored_news.to_html(classes='data'),description=description,
    table1=tweetdf.to_html(classes='data'),descriptionT=descriptionT
     )



# @app.route('/')
# def hello_world():
    
#     return jsonify({'Demo message': 'Hello World!'})


if __name__ == "__main__":
    # tweepyauth()
    app.run(debug=True ,port=8080, host='0.0.0.0')