# MSDS_434
# Stock Sentiment Analyzer 

[![Python application test with Github Actions](https://github.com/haaden/MSDS_434/actions/workflows/main.yml/badge.svg)](https://github.com/haaden/MSDS_434/actions/workflows/main.yml)

## Stock Sentiment Analyzer app overview

The purpose of this project was to create a Stock Price and Sentiment analyzer app that could be deployed via a CI/CD pipeline and hosted on Google Cloud Platform (GCP) via Google Cloud run. The app produces a time series visual of Stock price, News sentiment and Twitter sentiment and provides a table of recent News and Tweets with Sentiment scores.<br>
<br>
The stock price is acquired through yahoo finance API using the python library. News is acquired by web scraping finviz.com, Tweets by using  the twitter API and Company CIK and name information is acquired from SEC and saved on BigQuery and then sourced in the APP.<br>
<br>
The project is based in Flask app and uses Plotly to visualize the data. 

## Architecture Diagram

Data source Yahoo, finviz.com, twitter and SEC. 

Github to save source code.

Github Action for continuous integration and delivery.

Deploy App container on Google Cloud Run (production and test environment).

 ![Architecure](https://user-images.githubusercontent.com/19863921/172090604-5b41f72f-454d-4165-a400-3e7288b58447.jpg)



## Folder Structure

- Template folder contains the Index.html (landing page) and Sentiment.html file (display Graph and table).

- main.py contains the models, function to get data and Flask app.

- test_app.py is a test file to check if data source URLs  or API are broken.

- Dockerfile is used to execute all the commands to automatically build an image of the application.

- cloud-run-action.yml  deploys the app container in Google run platform.

- main.yml does testing and checks code format.

- requirements.txt list the  python libraries/modules required for the project.

- Makefile containing shell commands that are executed to automate installation, testing , linting and formatting the code.

- .flaskenv has Flask CLI configuration commands.


-- GCP credentials are stored as variables in github secrets. The credentials are required to deploy the container and access Big Query.



## Services and Tools used

-	Flask: Flask operates as the central point of data flow within the app . It serves out
an interactive website where users can submit a Stock symbol to get price and Sentiment data and charts.

-	Git/Github: Used to save the source code and version control

-	Github Actions: was used to incorporate continuous integration into the project. Any time code was pushed to the  GitHub repository, Github actions would be triggered to build and test the newest version of the app before deploying to Google Cloud Run.

-	BigQuery: was used to save company Name, CIK and Ticker symbol data from SEC.

-	Google Cloud Run: Cloud run was used to deploy Flask app container, which asks users to provide a Stock symbol and returns recent Price , news and news sentiment, tweets and tweet sentiment. 
 
-	Hugging Face and NLTK model:  NLTK sentiment Vader pretrained model was used to get sentiment scores for news and a pretrained hugging face model cardiffnlp/twitter-xlm-roberta-base-sentiment was used to get sentiment scores for Twitter data.

-	Google Cloud Monitoring: Cloud monitoring provides logging of any errors that may occur. Cloud monitoring was also used to set uptime checks.


## Data Source

- Python YFinance library to get Stock prices.
- Finviz.com for web scraping Stock news data.
- Twitter API to get Twitter data based on key word search.
- BigQuery  stored Sec.gov  Company identification data such as Name, CIK and Ticker symbol.

## Future Enhancements

- Use Amazon Sage Maker or Vertex AI to deploy Hugging Face models for efficiency. 

- Store stock price, news, and twitter data to BigQuery  for quick access and back testing. This will require paid subscription to get the data.

- Add stock price attribution data for additional insights.

## Demo

![ezgif com-gif-maker (1)](https://user-images.githubusercontent.com/19863921/172090275-cd17c42e-3d9a-4635-aac7-52a4861aaf42.gif)


### App URL

https://sentiment-kxd2g42gpa-uc.a.run.app/
