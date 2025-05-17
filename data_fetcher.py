import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
from newspaper import Article
import time
import os
import torch
import scipy.special
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from keybert import KeyBERT
import OUTPUT_DIR, SENTIMENT_THRESHOLD, START_DATE, END_DATE, BASE_URL, BUSINESS_URL, FINANCIAL_KEYWORDS from config import *

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model_finbert = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
kw_model = KeyBERT(model="ProsusAI/finbert")

def is_financial_content(text, url, threshold=2):
    """Determine if content is financial based on keywords and URL."""
    financial_sections = ['business', 'money', 'finance', 'stock', 'market', 'invest']
    url_score = sum(1 for section in financial_sections if section in url.lower())
    keyword_count = sum(1 for keyword in FINANCIAL_KEYWORDS if keyword in text.lower())
    extracted_keywords = extract_keywords(text, num_keywords=8)
    extracted_keyword_matches = sum(1 for keyword in extracted_keywords if any(
        fin_keyword in keyword.lower() for fin_keyword in FINANCIAL_KEYWORDS))
    
    total_score = url_score + keyword_count + extracted_keyword_matches
    print(f"Financial content score: {total_score} (URL: {url_score}, Keywords: {keyword_count}, Extracted: {extracted_keyword_matches})")
    
    return total_score >= threshold

def fetch_guardian_links(date=None, section_url=BASE_URL):
    """Fetches article links from the specified section, optionally for a given date."""
    try:
        url = section_url
        if date:
            formatted_date = date.strftime("%Y/%b/%d").lower()
            url = f"{section_url}/{formatted_date}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('a', class_='u-faux-block-link__overlay')
        return [a['href'] for a in articles if a.has_attr('href')]
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return []

def scrape_full_article(url):
    """Extracts full article text using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {
            'text': article.text.strip(),
            'title': article.title,
            'publish_date': article.publish_date
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {'text': "", 'title': "", 'publish_date': None}

def analyze_sentiment(text):
    """Analyzes sentiment of text using FinBERT model."""
    try:
        tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}
        with torch.no_grad():
            input_sequence = tokenizer(text, return_tensors="pt", **tokenizer_kwargs)
            logits = model_finbert(**input_sequence).logits
            scores = {
                k: v
                for k, v in zip(
                    model_finbert.config.id2label.values(),
                    scipy.special.softmax(logits.numpy().squeeze()),
                )
            }
        sentiment = max(scores, key=scores.get)
        probability = max(scores.values())
        return sentiment, probability, scores
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return "neutral", 0.0, {}

def extract_keywords(text, num_keywords=5):
    """Extract keywords from text using KeyBERT with FinBERT model."""
    try:
        keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 3), stop_words='english', top_n=num_keywords)
        return [kw[0] for kw in keywords]
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []

def save_to_csv(data, year):
    """Saves data to a CSV file for the given year."""
    if not data: 
        print(f"No financial articles met the criteria for {year}.")
        return False
        
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    filename = f"{OUTPUT_DIR}/financial_news_{year}.csv"
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['Date', 'Headline', 'URL', 'Full Text', 'Sentiment', 'Sentiment Probability', 'Positive Score', 'Negative Score', 'Neutral Score', 'Keywords'])
        writer.writerows(data)
    
    print(f"Saved {len(data)} financial articles to {filename}")
    return True

def main():
    current_date = START_DATE
    
    while current_date <= END_DATE:
        year = current_date.year
        print(f"\nFetching articles for {current_date.strftime('%Y-%m-%d')}")
        
        # Get links from both stock market and general business sections
        stock_links = fetch_guardian_links(current_date)
        business_links = fetch_guardian_links(current_date, BUSINESS_URL)
        
        # Combine and remove duplicates
        all_links = list(set(stock_links + business_links))
        print(f"Found {len(all_links)} total articles to process")
        
        daily_articles = []
        filtered_sentiment_count = 0
        filtered_nonfinancial_count = 0
        
        for link in all_links:
            print(f"\nScraping: {link}")
            article_data = scrape_full_article(link)
            full_text = article_data['text']
            
            if full_text:
                # First check if the content is financial
                if is_financial_content(full_text, link):
                    sentiment, probability, scores = analyze_sentiment(full_text)
                    keywords = extract_keywords(full_text)
                    keywords_str = ", ".join(keywords)
                    
                    headline = article_data['title'] or link.split('/')[-1].replace('-', ' ')
                    
                    if probability >= SENTIMENT_THRESHOLD:
                        daily_articles.append([
                            current_date.strftime("%Y-%m-%d"),
                            headline, 
                            link,
                            full_text,
                            sentiment,
                            probability,
                            scores.get('positive', 0.0),
                            scores.get('negative', 0.0),
                            scores.get('neutral', 0.0),
                            keywords_str
                        ])
                        print(f"✓ Article added: {sentiment} sentiment with {probability:.4f} probability")
                    else:
                        filtered_sentiment_count += 1
                        print(f"✗ Article filtered out: sentiment probability {probability:.4f} below threshold {SENTIMENT_THRESHOLD}")
                else:
                    filtered_nonfinancial_count += 1
                    print(f"✗ Article filtered out: not financial content")
            time.sleep(2) 
        
        if daily_articles:
            save_to_csv(daily_articles, year)
            print(f"Results for {current_date.strftime('%Y-%m-%d')}:")
            print(f"- Saved {len(daily_articles)} financial articles")
            print(f"- Filtered out {filtered_nonfinancial_count} non-financial articles")
            print(f"- Filtered out {filtered_sentiment_count} financial articles below sentiment threshold")
        else:
            print(f"No articles met the criteria for {current_date.strftime('%Y-%m-%d')}")
        
        current_date += timedelta(days=1)
    
    print("\nScraping complete! Check the FinancialNewsData folder for financial articles.")

if __name__ == '__main__':
    main()