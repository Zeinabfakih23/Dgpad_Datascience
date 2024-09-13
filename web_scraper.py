import os
import requests
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import re
from tqdm import tqdm
from typing import List, Optional

# Define a data structure to store article information using a dataclass.
@dataclass
class Article:
    type: str  # Type of the content (e.g., "article").
    postid: str  # Unique identifier for the article.
    title: str  # Title of the article.
    url: str  # URL of the article.
    keywords: List[str]  # List of keywords associated with the article.
    thumbnail: str  # URL of the thumbnail image for the article.
    video_duration: Optional[str]  # Video duration, if available.
    word_count: str  # Word count of the article.
    lang: str  # Language of the article.
    published_time: str  # Published time of the article.
    last_updated: str  # Last updated time of the article.
    description: str  # Description of the article.
    author: str  # Author of the article.
    classes: List[dict]  # List of class mappings for posttype, category, etc.
    html: str  # HTML content of the article.
    lite_url: Optional[str]  # Lite version of the URL, if available.

# Define a class to handle sitemap parsing operations.
class SitemapParser:
    def __init__(self, sitemap_index_url):
        self.sitemap_index_url = sitemap_index_url  # Store the URL of the sitemap index.

    def get_monthly_sitemaps(self):
        response = requests.get(self.sitemap_index_url)  # Send an HTTP GET request to the sitemap index URL.
        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the XML content of the sitemap using BeautifulSoup.
        sitemap_urls = [loc.text for loc in soup.find_all('loc')]  # Extract all the URLs listed in the sitemap.
        return sitemap_urls  # Return a list of URLs for the monthly sitemaps.

    def get_article_urls(self, sitemap_url):
        response = requests.get(sitemap_url)  # Send an HTTP GET request to the monthly sitemap URL.
        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the XML content of the sitemap using BeautifulSoup.
        article_urls = [loc.text for loc in soup.find_all('loc')]  # Extract all the URLs listed in the sitemap.
        return article_urls  # Return a list of URLs for the articles.

# Define a class to handle article scraping operations.
class ArticleScraper:
    def __init__(self):
        pass  # The constructor doesn't need to do anything.

    def scrape_article(self, url):
        response = requests.get(url)  # Send an HTTP GET request to the article URL.
        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content of the article using BeautifulSoup.

        # Extract metadata from a <script> tag containing JSON data.
        script_tag = soup.find('script', id='tawsiyat-metadata')  # Find the specific script tag by ID.
        metadata = self.extract_metadata(script_tag.text) if script_tag else {}  # If the script tag is found, extract metadata.

        # Extract the main content of the article from <p> tags.
        paragraphs = soup.find_all('p')  # Find all <p> tags containing the article's content.
        content = '\n'.join([p.get_text() for p in paragraphs])  # Combine all <p> text into a single string.

        # Create an Article object using the extracted metadata.
        article = Article(
            type=metadata.get('type'),
            postid=metadata.get('postid'),
            title=metadata.get('title'),
            url=metadata.get('url'),
            keywords=metadata.get('keywords', '').split(','),  # Split keywords by comma.
            thumbnail=metadata.get('thumbnail'),
            video_duration=metadata.get('video_duration'),
            word_count=metadata.get('word_count'),
            lang=metadata.get('lang'),
            published_time=metadata.get('published_time'),
            last_updated=metadata.get('last_updated'),
            description=metadata.get('description'),
            author=metadata.get('author'),
            classes=metadata.get('classes', []),  # List of mappings like category, coverage, etc.
            html=metadata.get('html', ''),
            lite_url=metadata.get('lite_url')
        )
        return article

    def extract_metadata(self, script_content):
        try:
            json_data = re.search(r'{.*}', script_content, re.DOTALL)
            metadata = json.loads(json_data.group()) if json_data else {}
            return metadata
        except json.JSONDecodeError:
            return {}

# Define a utility class to handle saving data to JSON files.
class FileUtility:
    @staticmethod
    def save_to_json(data, year, month):
        filename = f'articles_{year}_{month}.json'  # Generate a filename based on the year and month.
        with open(filename, 'w', encoding='utf-8') as f:  # Open the file in write mode with UTF-8 encoding.
            json.dump([asdict(article) for article in data], f, ensure_ascii=False, indent=4)  # Write the data to the file as a JSON array.

# Define the main function that coordinates the entire process.
def main():
    sitemap_index_url = "https://www.almayadeen.net/sitemaps/all.xml"  # The URL of the main sitemap index.
    sitemap_parser = SitemapParser(sitemap_index_url)  # Create an instance of SitemapParser with the sitemap index URL.
    article_scraper = ArticleScraper()  # Create an instance of ArticleScraper.

    print("Retrieving monthly sitemaps...")
    monthly_sitemaps = sitemap_parser.get_monthly_sitemaps()  # Retrieve the list of monthly sitemap URLs.

    # Loop through each monthly sitemap URL.
    for sitemap_url in tqdm(monthly_sitemaps, desc="Processing Monthly Sitemaps"):
        # Extract the year and month from the sitemap URL using a regular expression.
        match = re.search(r'sitemap-(\d{4})-(\d{1,2})\.xml', sitemap_url)
        if match:
            year, month = match.groups()  # Extract the year and month as strings.

            print(f"\nProcessing articles for {year}-{month}...")
            article_urls = sitemap_parser.get_article_urls(sitemap_url)  # Retrieve the list of article URLs for the month.
            articles = []  # Initialize an empty list to store the scraped articles.

            # Loop through each article URL.
            i=0
            for url in tqdm(article_urls, desc=f"Scraping Articles for {year}-{month}", leave=False):
                if  i>10:
                   break
                try:
                    article = article_scraper.scrape_article(url)  # Scrape the article and store it in an Article object.
                    articles.append(article)  # Add the Article object to the list of articles.
                except Exception as e:
                    print(f"Failed to scrape {url}: {str(e)}")  # If there's an error, print the URL and error message.
                i=i+1

            FileUtility.save_to_json(articles, year, month)  # Save the list of articles to a JSON file.
            print(f"Saved articles for {year}-{month}.")  # Print a confirmation message after saving.

# The script starts executing from here when run as a standalone program.
if __name__ == "__main__":
    main()  # Call the main function to start the process.
