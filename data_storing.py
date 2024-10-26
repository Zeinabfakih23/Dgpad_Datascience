import pymongo
import json
import os
# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["almayadeen"]
collection = db["articles"]


def load_json_files(directory_path):
    """
    Loads and inserts all JSON files from the specified directory into MongoDB.
    """
    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            file_path = os.path.join(directory_path, filename)
            print(f"Processing file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        collection.insert_many(data)
                        print(f"Inserted data from {filename} into MongoDB.")
                    else:
                        print(f"File {filename} does not contain a list of documents.")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file {filename}.")
            except Exception as e:
                print(f"An error occurred while processing {filename}: {e}")
if __name__ == '__main__':
    directory_path =r'C:\Users\zeinab\PycharmProjects\Dgpad'  # Adjust this path to your directory containing JSON files
    if os.path.exists(directory_path):
        load_json_files(directory_path)
        print("Data inserted successfully!")
    else:
        print(f"Directory {directory_path} does not exist.")
