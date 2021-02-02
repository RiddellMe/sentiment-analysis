# Sentiment analysis

#### Purpose:

Scrape subreddit(s) and aggregate the number of times a ticker was mentioned in a specified timeframe

#### Features:
* Can pull stock ticker names from NASDAQ
* Can provide own list of tickers
* Can specify a subreddit
* Can search through ALL subreddits
* Can specify a to date, and how many previous days to gather information
* Returns a list of mentions and related ticker in descending order
* Creates CSV with output data
* Utilizes the pushshift.io API
* Multi-threaded environment to make API calls more efficient
* Includes a custom timer utility

#### TODO: 
* Keyword aggregation in top mentioned stocks to forecast price movements. Simple keyword search or ML techniques? porque no los dos?
* Data visualization
* Back-test and show impact of mentions on price movements/volatility/options prices/implied volatility within 1/3/5/14/30 days (correlation anaylsis/regression)

