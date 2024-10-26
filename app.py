from flask import Flask, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import json_util
import json
from bson import ObjectId
from urllib.parse import unquote
import logging

app = Flask(__name__)

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["almayadeen"]
    collection = db["articles"]
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

def parse_json(data):
    return json.loads(json_util.dumps(data))

def convert_objectid(doc):
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

#  Root route with a welcome message
@app.route('/', methods=['GET'])
def welcome():
    return render_template('home.html')

# 1.Route for getting top keywords
@app.route('/top_keywords', methods=['GET'])
def top_keywords():

    try:
        pipeline = [
            {"$unwind": "$keywords"},
            {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 2.Route for getting top authors
@app.route('/top_authors', methods=['GET'])
def top_authors():
    try:
        pipeline = [
            {"$group": {"_id": "$author", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 3.Route for getting articles by publication date
@app.route('/articles_by_date', methods=['GET'])
def articles_by_date():
    try:
        pipeline = [
            {"$match": {"published_time": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$published_time"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        result = list(collection.aggregate(pipeline))
        if not result:
            return jsonify({"message": "No articles found or incorrect field type for 'published_time'."}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500


# 5.Route for getting articles by language
@app.route('/articles_by_language', methods=['GET'])
def articles_by_language():
    try:
        pipeline = [
            {"$group": {"_id": "$lang", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500


# 7.Route for getting recent articles
@app.route('/recent_articles', methods=['GET'])
def recent_articles():
    try:
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        result = list(collection.find(
            {"published_time": {"$exists": True, "$gte": week_ago}},
            {"title": 1, "published_time": 1}
        ).sort("published_time", -1).limit(10))

        # Convert ObjectId to string
        for article in result:
            article["_id"] = str(article["_id"])

        if not result:
            return jsonify({"message": "No recent articles found."}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500


# 9.Route for getting articles by author
@app.route('/articles_by_author/<author_name>', methods=['GET'])
def articles_by_author(author_name):
    try:
        result = list(collection.find({"author": author_name}, {"title": 1, "url": 1}))
        result =[convert_objectid(doc) for doc in result]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 10.Top classes
@app.route('/top_classes', methods=['GET'])
def top_classes():
    try:
        pipeline = [
            {
                "$match": {
                    "classes": {"$exists": True, "$ne": None}
                }
            },
            {
                "$unwind": "$classes"
            },
            {
                "$group": {
                    "_id": "$classes",
                    "article_count": {"$sum": 1}
                }
            },
            {
                "$sort": {
                    "article_count": -1  # Sort by article count in descending order
                }
            },
            {
                "$limit": 10  # Limit to top 10 classes
            }
        ]

        result = list(collection.aggregate(pipeline))

        # Format the result for better readability
        formatted_result = [{"class": item["_id"], "article_count": item["article_count"]} for item in result]

        if not formatted_result:
            return jsonify({"message": "No classes found."}), 404

        return jsonify(formatted_result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 11.articles details
@app.route('/article_details/<postid>', methods=['GET'])
def article_details(postid):
    try:
        # Find the article with the given postid
        result = collection.find_one({"postid": postid})

        if not result:
            return jsonify({"message": "Article not found."}), 404

        # Remove the ObjectId to make it JSON serializable
        result["_id"] = str(result["_id"])

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 12.articles with video
@app.route('/articles_with_video', methods=['GET'])
def articles_with_video():
    try:
        # Find articles where 'video_duration' field exists and is not None
        result = list(collection.find({"video_duration": {"$exists": True, "$ne": None}}, {"title": 1, "url": 1}))

        if not result:
            return jsonify({"message": "No articles with videos found."}), 404

        # Convert ObjectIds to strings
        for item in result:
            item["_id"] = str(item["_id"])

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 13.articles with publication year
from datetime import datetime
@app.route('/articles_by_year/<year>', methods=['GET'])
def articles_by_year(year):
    try:
        year_int = int(year)

        # Create start and end dates for the year
        start_date = datetime(year_int, 1, 1)
        end_date = datetime(year_int + 1, 1, 1)

        # Match articles within the specified year
        pipeline = [
            {
                "$match": {
                    "published_time": {
                        "$gte": start_date,
                        "$lt": end_date
                    }
                }
            },
            {
                "$group": {
                    "_id": year,
                    "article_count": {"$sum": 1}
                }
            }
        ]

        result = list(collection.aggregate(pipeline))

        if not result:
            return jsonify({"message": f"No articles found for the year {year}."}), 404

        return jsonify(result)
    except ValueError:
        return jsonify({"error": "Invalid year. Please provide a valid year in YYYY format."}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500



# 16.articles by keyword count
@app.route('/articles_by_keyword_count', methods=['GET'])
def articles_by_keyword_count():
    try:
        pipeline = [
            {"$match": {"keywords": {"$exists": True, "$type": "array"}}},  # Ensure keywords is an array
            {"$project": {"keyword_count": {"$size": "$keywords"}}},  # Calculate the size of the keywords array
            {"$group": {"_id": "$keyword_count", "article_count": {"$sum": 1}}},  # Group by keyword count
            {"$sort": {"_id": 1}}  # Sort by the keyword count
        ]
        result = list(collection.aggregate(pipeline))

        if not result:
            return jsonify({"message": "No articles found with keyword counts."}), 404

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 17.Route for articles with thumbnail
@app.route('/articles_with_thumbnail', methods=['GET'])
def articles_with_thumbnail():
    try:
        result = list(collection.find({"thumbnail": {"$exists": True, "$ne": None}}, {"title": 1, "url": 1}))
        result = [convert_objectid(doc) for doc in result]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 18.Articles Updated After Publication
@app.route('/articles_updated_after_publication', methods=['GET'])
def articles_updated_after_publication():
    try:
        pipeline = [
            {
                "$addFields": {
                    "published_date": {"$toDate": "$published_time"},
                    "last_updated_date": {"$toDate": "$last_updated"}
                }
            },
            {
                "$match": {
                    "$expr": {"$gt": ["$last_updated_date", "$published_date"]}
                }
            },
            {
                "$project": {
                    "title": 1,
                    "published_time": 1,
                    "last_updated": 1
                }
            }
        ]

        result = list(collection.aggregate(pipeline))

        # Convert ObjectId to string
        for article in result:
            if '_id' in article:
                article['_id'] = str(article['_id'])

        if not result:
            return jsonify({"message": "No articles updated after publication."}), 404

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 19.Route for getting articles by coverage
@app.route('/articles_by_coverage/<coverage>', methods=['GET'])
def articles_by_coverage(coverage):
    try:
        result = list(collection.find({"classes.value": coverage}, {"title": 1, "url": 1}))
        result = [convert_objectid(doc) for doc in result]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 20.Most Popular Keywords in the Last X Days
@app.route('/popular_keywords_last_X_days/<int:days>', methods=['GET'])
def popular_keywords_last_X_days(days):
    try:
        date_threshold = datetime.now() - timedelta(days=days)
        pipeline = [
            {"$match": {"published_time": {"$gte": date_threshold}}},
            {"$unwind": "$keywords"},
            {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify([{"keyword": doc['_id'], "occurrences": doc['count']} for doc in result])
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 21.Articles by Published Month
@app.route('/articles_by_month/<int:year>/<int:month>', methods=['GET'])
def articles_by_month(year, month):
    try:
        pipeline = [
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$eq": [{"$year": "$published_time"}, year]},
                            {"$eq": [{"$month": "$published_time"}, month]}
                        ]
                    }
                }
            },
            {"$group": {"_id": None, "count": {"$sum": 1}}}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify({"year": year, "month": month, "articles": result[0]['count'] if result else 0})
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 22.Route for getting articles by word count range
@app.route('/articles_by_word_count_range/<min>/<max>', methods=['GET'])
def articles_by_word_count_range(min, max):
    try:
        # Convert min and max to integers
        min_word_count = int(min)
        max_word_count = int(max)

        # MongoDB query with the word count forced to be an integer
        pipeline = [
            {
                "$addFields": {
                    "word_count_int": {
                        "$toInt": "$word_count"
                    }
                }
            },
            {
                "$match": {
                    "word_count_int": {
                        "$gte": min_word_count,
                        "$lte": max_word_count
                    }
                }
            },
            {
                "$project": {
                    "title": 1,
                    "word_count_int": 1
                }
            }
        ]

        result = list(collection.aggregate(pipeline))

        # Convert ObjectId to string for each document
        for doc in result:
            doc['_id'] = str(doc['_id'])

        # Check if the result is empty
        if not result:
            return jsonify({"message": "No articles found in the specified word count range."}), 404

        # Return the result
        return jsonify(result)
    except ValueError:
        return jsonify({"error": "Invalid word count range. Please provide integer values."}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500


# 24.Articles by Specific Date
@app.route('/articles_by_specific_date/<date>', methods=['GET'])
def articles_by_specific_date(date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        pipeline = [
            {
                "$match": {
                    "$expr": {
                        "$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$published_time"}}, date]
                    }
                }
            },
            {"$project": {"title": 1, "url": 1, "_id": 0}}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 25.Articles Containing Specific Text
# Set up logging

@app.route('/articles_containing_text/<text>', methods=['GET'])
def articles_containing_text(text):
    try:
        # Decode URL-encoded text
        decoded_text = unquote(text)
        logging.debug(f"Searching for text: {decoded_text}")

        result = list(collection.find(
            {"content": {"$regex": decoded_text, "$options": "i"}},
            {"title": 1, "url": 1, "_id": 0}
        ))

        if not result:
            return jsonify({"message": f"No articles found containing the text: {decoded_text}"}), 404

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 26.Articles with More than N Words
@app.route('/articles_with_more_than/<int:word_count>', methods=['GET'])
def articles_with_more_than(word_count):
    try:
        # Fetch articles with more than the specified word count
        result = list(collection.find(
            {"word_count": {"$gt": word_count, "$ne": None}},
            {"title": 1, "url": 1, "word_count": 1, "_id": 0}
        ))

        # If no articles are found, return a message
        if not result:
            return jsonify({"message": f"No articles found with more than {word_count} words."}), 404

        # Return the articles as JSON
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 27.Articles Grouped by Coverage
@app.route('/articles_grouped_by_coverage', methods=['GET'])
def articles_grouped_by_coverage():
    try:
        pipeline = [
            {"$unwind": "$classes"},
            {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify([{"coverage": doc['_id'], "articles": doc['count']} for doc in result])
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 28.Articles Published in Last X Hours
@app.route('/articles_last_X_hours/<int:hours>', methods=['GET'])
def articles_last_X_hours(hours):
    try:
        time_threshold = datetime.now() - timedelta(hours=hours)
        result = list(collection.find(
            {"published_time": {"$gte": time_threshold}},
            {"title": 1, "url": 1, "_id": 0}
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 29.Articles by Length of Title
@app.route('/articles_by_title_length', methods=['GET'])
def articles_by_title_length():
    try:
        pipeline = [
            {
                "$addFields": {
                    "title_length": {
                        "$strLenCP": { "$ifNull": ["$title", ""] }  # Handle null title with default empty string
                    }
                }
            },
            {
                "$group": {
                    "_id": "$title_length",
                    "article_count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}  # Sort by title length
            },
            {
                "$project": {
                    "title_length": "$_id",
                    "article_count": 1,
                    "_id": 0
                }
            }
        ]

        result = list(collection.aggregate(pipeline))
        if not result:
            return jsonify({"message": "No articles found by title length."}), 404

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

# 30.Most Updated Articles
@app.route('/most_updated_articles', methods=['GET'])
def most_updated_articles():
    try:
        pipeline = [
            {
                "$addFields": {
                    "last_updated_date": { "$toDate": "$last_updated" },
                    "published_time_date": { "$toDate": "$published_time" }
                }
            },
            {
                "$addFields": {
                    "update_difference": { "$subtract": ["$last_updated_date", "$published_time_date"] }
                }
            },
            { "$sort": { "update_difference": -1 } },
            { "$limit": 10 },
            {
                "$project": {
                    "title": 1,
                    "url": 1,
                    "update_difference": 1,
                    "last_updated": 1,
                    "published_time": 1,
                    "_id": 0
                }
            }
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500



###########################################################################################################################
@app.route('/keywords')
def keywords():
    try:
        # MongoDB pipeline to get the top 10 keywords
        pipeline = [
            {"$unwind": "$keywords"},
            {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        result = list(collection.aggregate(pipeline))

        # Prepare the data for Highcharts word cloud
        keywords = [{"name": doc["_id"], "weight": doc["count"]} for doc in result if doc["_id"].strip()]

        return jsonify(keywords)  # Send the keywords as JSON to be used by the frontend
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/wordcloud')
def wordcloud():
    # This route renders the template that contains the word cloud
    return render_template('wordcloud.html')


@app.route('/authors')
def authors():
    try:
        # MongoDB pipeline to get the top 10 authors
        pipeline = [
            {"$group": {"_id": "$author", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        result = list(collection.aggregate(pipeline))

        # Prepare data for amCharts
        authors = [{"name": doc["_id"] if doc["_id"] else "Unknown", "steps": doc["count"]} for doc in result]

        return jsonify(authors)  # Return the data as JSON for the frontend to process
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/barchart')
def barchart():
    return render_template('barchart.html')


@app.route('/languages')
def languages():
    try:
        # Example pipeline to get languages used in tweets
        pipeline = [
            {"$group": {"_id": "$language", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = list(collection.aggregate(pipeline))

        # Prepare the data for the pie chart
        languages = [{"country": doc["_id"], "sales": doc["count"]} for doc in result]

        return jsonify(languages)  # Send the data as JSON
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/piechart')
def piechart():
    return render_template('piechart.html')

@app.route('/articlesbydate')
def articlesbydate():
    return render_template('articlesbydate.html')

@app.route('/articlesbyclasses')
def articlesbyclasses():
    return render_template('articlesbyclasses.html')
@app.route('/articles_by_classes', methods=['GET'])
def articles_by_classes():
    try:
        pipeline = [
            {"$unwind": "$classes"},
            {"$group": {"_id": "$classes.value", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = list(collection.aggregate(pipeline))
        formatted_result = [{"class": item["_id"], "count": item["count"]} for item in result]
        return jsonify(formatted_result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/articles_by_word_count', methods=['GET'])
def articles_by_word_count():
        try:
            pipeline = [
                {"$match": {"word_count": {"$exists": True, "$ne": None, "$ne": 0}}},
                {"$project": {"word_count": {"$toInt": "$word_count"}}},
                {"$group": {"_id": "$word_count", "article_count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            result = list(collection.aggregate(pipeline))

            formatted_result = [{"word_count": item["_id"], "article_count": item["article_count"]} for item in result]
            return jsonify(formatted_result)
        except Exception as e:
            return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/articlesbywordcount')
def articlesbywordcount():
    return render_template('articlesbywordcount.html')

@app.route('/articles_by_keyword', methods=['GET'])
def articles_by_keyword():
    try:
        pipeline = [
            {"$unwind": "$keywords"},
            {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 30}  # Optional: limit to top 30 keywords
        ]
        result = list(collection.aggregate(pipeline))
        data = [{"keyword": item["_id"], "count": item["count"]} for item in result]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/articlesbykeyword')
def articlesbykeyword():
    return render_template('articlesbykeyword.html')




@app.route('/longest_articles', methods=['GET'])
def longest_articles():
    try:
        # Retrieve the top 10 longest articles by word count
        result = list(collection.find({"word_count": {"$exists": True, "$ne": None}})
                      .sort("word_count", -1)
                      .limit(10))

        if not result:
            return jsonify({"message": "No articles with word counts found."}), 404

        # Convert ObjectIds to strings
        for item in result:
            item["_id"] = str(item["_id"])

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/longestarticles')
def longestarticles():
    return render_template('longestarticles.html')

@app.route('/shortest_articles', methods=['GET'])
def shortest_articles():
    try:
        # Find the top 10 articles with the lowest word count
        result = list(collection.find({"word_count": {"$exists": True, "$ne": None}})
                      .sort("word_count", 1)  # Sort in ascending order
                      .limit(10))

        if not result:
            return jsonify({"message": "No articles with word counts found."}), 404

        # Convert ObjectIds to strings and prepare the data
        articles = []
        for item in result:
            item["_id"] = str(item["_id"])  # Convert ObjectId to string
            articles.append({
                "title": item.get("title", "Untitled"),  # Use a default title if not found
                "word_count": item.get("word_count", 0)  # Default to 0 if not found
            })

        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500


@app.route('/shortestarticles')
def shortestarticles():
    return render_template('shortestarticles.html')


@app.route('/articles_with_specific_keyword_count/<int:count>', methods=['GET'])
def articles_with_specific_keyword_count(count):
    try:
        result = list(collection.find(
            {"$expr": {"$eq": [{"$size": {"$ifNull": ["$keywords", []]}}, count]}},
            {"title": 1, "url": 1, "_id": 0}
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/articlesbykeywordcount')
def articlesbykeywordcount():
    return render_template('articlesbykeywordcount.html')

@app.route('/articlesbypublishedmonth')
def articlesbypublishedmonth():
    return render_template('articlesbypublishedmonth.html')







if __name__ == '__main__':
    app.run(debug=True)
