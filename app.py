import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from neo4j import GraphDatabase
import json
from config import CATEGORY_KEYWORDS

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URL")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_relevant_categories(news_text, CATEGORY_KEYWORDS=CATEGORY_KEYWORDS):
    prompt = f"""
    Analyze this news article and select ONLY the most relevant categories and subcategories strictly from the Categories Keywords provided below:
    News: {news_text}
    Categories Keywords: {CATEGORY_KEYWORDS}
    
    Return strictly in this exact format without any markdown or code blocks:
    [("Category1", "Subcategory1"), ("Category2", "Subcategory2"), ...]
    
    Only include categories that are highly relevant to the content.
    """
    
    max_retries = 3
    retry_count = 0
    backoff_time = 2
    
    while retry_count < max_retries:
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith("```") and response_text.endswith("```"):
                clean_text = response_text.split("```")[1].strip()
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:].strip()
            elif response_text.startswith("[") and response_text.endswith("]"):
                clean_text = response_text
            else:
                lines = response_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith("[") and line.endswith("]"):
                        clean_text = line
                        break
                else:
                    clean_text = response_text
            
            categories = eval(clean_text)
            return categories
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                import time
                time.sleep(backoff_time)
                backoff_time *= 2
                continue
            else:
                print(f"Error parsing categories after {max_retries} attempts: {str(e)}")
                return []

def fetch_all_articles_by_categories(categories):
    articles = []
    
    try:
        with driver.session() as session:
            # Process only the first subcategory with top 10 highest score articles
            if categories and len(categories) > 0:
                first_category, first_subcategory = categories[0]
                query = """
                MATCH (a:Article)-[r:BELONGS_TO]->(sc:Subcategory)
                WHERE toLower(sc.name) = toLower($subcategory)
                RETURN a.article_id AS article_id, a.heading AS heading, a.url AS url, 
                       a.full_text AS full_text, r.score AS score, a.last_updated AS last_updated
                ORDER BY r.score DESC
                LIMIT 10
                """
                result = session.run(query, subcategory=first_subcategory)
                for record in result:
                    article_data = {
                        "article_id": record["article_id"],
                        "heading": record["heading"],
                        "url": record["url"],
                        "full_text": record["full_text"],
                        "score": record["score"],
                        "last_updated": record["last_updated"]
                    }
                    articles.append(article_data)
            
            return articles
    except Exception as e:
        st.error(f"Neo4j query error: {str(e)}")
        return []

def filter_relevant_articles(news_text, all_articles):
    articles_data = []
    
    for article in all_articles:
        articles_data.append({
            "article_id": article["article_id"],
            "heading": article["heading"],
            "url": article["url"],
            "preview": article["full_text"][:200] if article["full_text"] else "No content available"
        })
    
    prompt = f"""
    ACT as a senior financial analyst with expertise in market pattern recognition and historical comparison.
    
    1. ANALYZE this breaking financial news thoroughly:
    {news_text}
    
    2. From these historical articles, IDENTIFY ONLY those that are financial news and DIRECTLY RELEVANT to the breaking news and STRONGLY CORRELATED to it:
    {json.dumps(articles_data, indent=2)}
    
    3. RETURN ONLY the relevant articles in this exact format - an array of objects with article_id and reasoning:
    [
        {{
            "article_id": "id1",
            "reasoning": "Brief explanation of how this article relates to the breaking news"
        }},
        {{
            "article_id": "id2",
            "reasoning": "Brief explanation of how this article relates to the breaking news"
        }}
    ]
    
    Articles should be sorted by relevance (most relevant first).    
    Only include articles with STRONG topical relevance. Prioritize quality over quantity.
    """
    
    max_retries = 3
    retry_count = 0
    backoff_time = 2
    
    while retry_count < max_retries:
        try:
            response = model.generate_content(prompt)
            result_text = response.text
            
            if '```json' in result_text:
                json_str = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                json_str = result_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = result_text.strip()
                
            relevant_article_data = json.loads(json_str)
            
            relevant_ids = [item["article_id"] for item in relevant_article_data]
            relevant_articles = [article for article in all_articles if article["article_id"] in relevant_ids]
            
            sorted_articles = sorted(
                relevant_articles, 
                key=lambda x: relevant_ids.index(x["article_id"]) if x["article_id"] in relevant_ids else float('inf')
            )
            
            return sorted_articles
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                import time
                time.sleep(backoff_time)
                backoff_time *= 2
                continue
            else:
                print(f"Error filtering relevant articles after {max_retries} attempts: {str(e)}")
                return all_articles[:10]

def fetch_articles_by_ids(article_ids):
    articles = []
    
    try:
        with driver.session() as session:
            for article_id in article_ids:
                query = """
                MATCH (a:Article {article_id: $article_id})
                RETURN a.article_id AS article_id, a.heading AS heading, a.url AS url, 
                       a.full_text AS full_text, a.last_updated AS last_updated
                """
                result = session.run(query, article_id=article_id)
                record = result.single()
                if record:
                    article_data = {
                        "article_id": record["article_id"],
                        "heading": record["heading"],
                        "url": record["url"],
                        "full_text": record["full_text"],
                        "last_updated": record["last_updated"]
                    }
                    articles.append(article_data)
            
            return articles
    except Exception as e:
        st.error(f"Neo4j query error: {str(e)}")
        return []

def generate_financial_report(news_text, relevant_articles):
    formatted_articles = []
    for i, article in enumerate(relevant_articles[:10]):
        date = article.get("last_updated", "Unknown date")
        if isinstance(date, str):
            date_str = date
        else:
            date_str = date.strftime("%Y-%m-%d") if date else "Unknown date"
            
        formatted_articles.append(f"""
            ARTICLE {i+1} - {date_str}
            HEADING: {article.get("heading", "No heading")}
            URL: {article.get("url", "No URL")}
            CONTENT: {article.get("full_text", "No content")[:300]}...
        """)
    
    historical_context = "\n".join(formatted_articles)
    
    prompt = f"""
    ACT as a managing director at a top investment bank producing a formal financial report. You're analyzing breaking news in the context of historical events.

    CURRENT EVENT:
    {news_text}

    HISTORICAL CONTEXT:
    {historical_context}

    GENERATE a comprehensive financial analysis report with these EXACT SECTIONS:

    # FINANCIAL INTELLIGENCE REPORT
    ## Executive Summary
    [3-4 sentence summary of the current event and its likely market impact]

    ## Current Situation Analysis
    - **Key Market Entities**: [Companies, sectors, instruments affected]
    - **Primary Catalysts**: [Specific factors driving the current situation]
    - **Quantitative Assessment**: [Key financial metrics, changes, percentages]

    ## Historical Precedent Analysis
    - **Most Comparable Events**: [2-3 similar historical examples with exact dates]
    - **Market Response Patterns**: [Documented price movements, volatility metrics]
    - **Duration & Magnitude**: [Typical timelines of impact and percentage changes]

    ## Comparative Market Analysis
    | Factor | Current Event | Historical Precedent | Differential |
    |--------|--------------|---------------------|-------------|
    | [Factor 1] | [Current data] | [Historical data] | [Difference] |
    | [Factor 2] | [Current data] | [Historical data] | [Difference] |
    | [Factor 3] | [Current data] | [Historical data] | [Difference] |

    ## Risk Assessment
    - **Primary Risks**: [Rank-ordered risks]
    - **Mitigating Factors**: [Potential stabilizing forces]
    - **Probability Distribution**: [Most likely scenario and probability]

    ## Market Outlook
    - **Short-term Projection** (0-30 days): [Specific market predictions]
    - **Medium-term Outlook** (1-6 months): [Expected developments]
    - **Long-term Considerations**: [Structural impacts]

    ## Strategic Recommendations
    - **For Institutional Investors**: [2-3 specific actions]
    - **For Retail Investors**: [2-3 specific actions]
    - **Key Performance Indicators**: [Metrics to monitor]

    ENSURE all analysis is:
    - Grounded in referenced historical precedent
    - Quantitative where possible (specific percentages, timeframes, metrics)
    - Professional in tone appropriate for institutional clients
    - Free of speculative language without factual basis
    """
    
    max_retries = 3
    retry_count = 0
    backoff_time = 2
    
    while retry_count < max_retries:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                import time
                time.sleep(backoff_time)
                backoff_time *= 2
                continue
            else:
                print(f"Error generating financial report after {max_retries} attempts: {str(e)}")
                return "# FINANCIAL INTELLIGENCE REPORT\n\n## Notice\n\nWe're currently experiencing high demand on our analysis systems. Our team is working to generate your financial intelligence report as soon as possible.\n\nIn the meantime, please review the historical precedent articles below, which contain valuable insights related to your query.\n\nThank you for your patience."

st.set_page_config(page_title="Financial News Flashback", layout="wide")
st.title("📊 Financial News Flashback")
st.subheader("Historical Market Pattern Recognition System")

news_text = st.text_area("Paste breaking financial news article:", height=200)

def process_regular_news(news_text, categories):
    if categories:
        all_articles = fetch_all_articles_by_categories(categories)
    
    if not all_articles:
        st.info("No articles found for the selected categories. You might want to try a different news article.")
        return
    
    with st.spinner("Analyzing historical patterns and relevance..."):
        relevant_articles = filter_relevant_articles(news_text, all_articles)
    
    if not relevant_articles:
        st.info("No historically relevant articles found. Try a different news article with more specific financial details.")
        return
    
    with st.spinner("Generating financial intelligence report..."):
        try:
            report = generate_financial_report(news_text, relevant_articles)
            st.header("🔍 Financial Intelligence Report")
            st.markdown(report)
        except Exception as e:
            print(f"Error generating financial report: {str(e)}")
            st.info("Unable to generate the financial report at this time. You can still view the relevant historical articles below.")
    
    st.header("📚 Historical Precedent Articles")
    for i, article in enumerate(relevant_articles):
        with st.expander(f"{i+1}. {article['heading']}"):
            st.write(f"**Article ID:** {article['article_id']}")
            st.write(f"**URL:** {article['url']}")
            st.write("**Content Preview:**")
            st.write(article['full_text'][:500] + "..." if len(article['full_text']) > 500 else article['full_text'])


def process_article_ids_with_reasoning(article_data):
    article_ids = [item["article_id"] for item in article_data]
    
    reasoning_map = {item["article_id"]: item["reasoning"] for item in article_data}
    
    articles = fetch_articles_by_ids(article_ids)
    
    for article in articles:
        article["reasoning"] = reasoning_map.get(article["article_id"], "")
    
    return articles

if st.button("Generate Financial Intelligence Report") and news_text:
    with st.spinner("Processing..."):
        try:
            if news_text.strip().startswith("[") and news_text.strip().endswith("]"):
                try:
                    article_data = json.loads(news_text)
                    if isinstance(article_data, list) and all(isinstance(item, dict) and "article_id" in item and "reasoning" in item for item in article_data):
                        relevant_articles = process_article_ids_with_reasoning(article_data)
                    else:
                        categories = get_relevant_categories(news_text)
                        process_regular_news(news_text, categories)
                except json.JSONDecodeError:
                    categories = get_relevant_categories(news_text)
                    process_regular_news(news_text, categories)
            else:
                categories = get_relevant_categories(news_text)
                process_regular_news(news_text, categories)
        except Exception as e:
            print(f"Error processing input: {str(e)}")
            st.info("We're experiencing some technical difficulties. Please try again with a different news article or check back later.")

driver.close()