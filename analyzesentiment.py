from flask import Flask, jsonify
from pymongo import MongoClient
from textblob import TextBlob

app = Flask(__name__)

# MongoDB connection setup
client = MongoClient('your_mongodb_uri')  # Replace with your MongoDB URI
db = client['your_database_name']  # Replace with your database name
collection = db['your_collection_name']  # Replace with your collection name

# Function to analyze sentiment using TextBlob
def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity < 0:
        return 'negative'
    else:
        return 'neutral'

# API endpoint to analyze sentiment for all articles
@app.route('/analyze_sentiment', methods=['GET'])
def analyze_sentiment_for_articles():
    try:
        # Retrieve all articles from the collection
        articles = list(collection.find({}))  # Adjust query as necessary

        # Loop through articles to analyze sentiment
        for article in articles:
            sentiment = analyze_sentiment(article['text'])  # Assuming 'text' contains the article content
            collection.update_one({'_id': article['_id']}, {'$set': {'sentiment': sentiment}})

        return jsonify({"message": "Sentiment analysis complete and database updated."}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# Example API endpoint to get articles by sentiment
@app.route('/articles_by_sentiment/<string:sentiment>', methods=['GET'])
def articles_by_sentiment(sentiment):
    try:
        articles = list(collection.find({"sentiment": sentiment}, {"_id": 0, "title": 1, "url": 1}))
        return jsonify(articles), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

import spacy
nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]

@app.route('/articles_by_entity/<entity>', methods=['GET'])
def articles_by_entity(entity):
    try:
        result = list(collection.find({'entities': {'$elemMatch': {'$eq': entity}}}, {'title': 1, 'url': 1, '_id': 0}))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/sentiment_trends', methods=['GET'])
def sentiment_trends():
    try:
        pipeline = [
            {
                "$group": {
                    "_id": {"$month": "$published_time"},
                    "positive": {"$sum": {"$cond": [{"$eq": ["$sentiment", "positive"]}, 1, 0]}},
                    "negative": {"$sum": {"$cond": [{"$eq": ["$sentiment", "negative"]}, 1, 0]}},
                    "neutral": {"$sum": {"$cond": [{"$eq": ["$sentiment", "neutral"]}, 1, 0]}}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/most_positive_articles', methods=['GET'])
def most_positive_articles():
    try:
        result = list(collection.find({'sentiment': 'positive'}).sort('sentiment_score', -1).limit(10))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/most_negative_articles', methods=['GET'])
def most_negative_articles():
    try:
        result = list(collection.find({'sentiment': 'negative'}).sort('sentiment_score', 1).limit(10))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/articles_by_entity/<entity>', methods=['GET'])
def articles_by_entity(entity):
    try:
        result = list(collection.find({'entities': {'$elemMatch': {'$eq': entity}}}, {'title': 1, 'url': 1, '_id': 0}))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/trends/<keyword>', methods=['GET'])
def trends(keyword):
        # Implement trend analysis based on the keyword
        pass


if __name__ == '__main__':
    app.run(debug=True)
