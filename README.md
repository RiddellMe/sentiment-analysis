# Sentiment analysis

#### Requirements:

* Written using Python3.8*

*TensorFlow not supported on Python3.9

#### Purpose:

Scrape subreddit(s) and aggregate the number of times a ticker was mentioned in a specified timeframe

#### Features:
* Can pull stock ticker names from NASDAQ
* Can provide own list of tickers
* Can specify a subreddit
* Can search through ALL subreddits
* Can specify a to date, and how many previous days to gather information
* Returns a DTO containing a list of tickers and their mention count in descending order, as well as a from date and to date
* Creates CSV with output data
* Utilizes the pushshift.io API
* Multi-threaded environment for speed
* Can conduct sentiment analysis using a Naive Bayes classifier. Weighting schemes supported:
    - raw word count
    - term frequency
    - tf-idf (term frequency-inverse document frequency)

#### TODO: 
* Implement other classification techniques (LSTM for example)
* Model the sentiment in terms of price movements/volatility/options prices/implied volatility within 1/3/5/14/30 days (correlation anaylsis/regression) and backtest
* Data visualization

