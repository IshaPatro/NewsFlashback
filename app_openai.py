import os
import streamlit as st
import openai
from dotenv import load_dotenv
from neo4j import GraphDatabase
import json
from config import CATEGORY_KEYWORDS

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URL")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

openai.api_key = OPENAI_API_KEY

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_relevant_categories(news_text, CATEGORY_KEYWORDS=CATEGORY_KEYWORDS):
    prompt = f"""
    Analyze this news article and select ONLY the most relevant categories and subcategories strictly from the Categories Keywords provided below:
    News: {news_text}
    Categories Keywords: {CATEGORY_KEYWORDS}
    
    Return strictly in this exact format without any markdown or code blocks:
    [("Category1", "Subcategory1"), ("Category2", "Subcategory2"), ...]
    
    Only include categories that are highly relevant to the content. The length of the response array should STRICTLY below 3.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a financial news categorization expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        response_text = response.choices[0].message.content.strip()
        
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
        st.write(f"Selected categories: {categories}")
        return categories
    except Exception as e:
        st.error(f"Error parsing categories: {str(e)}")
        return []

def fetch_all_articles_by_categories(categories):
    articles = []
    
    try:
        with driver.session() as session:
            for category, subcategory in categories:
                query = """
                MATCH (a:Article)-[r:BELONGS_TO]->(sc:Subcategory)
                WHERE toLower(sc.name) = toLower($subcategory)
                RETURN a.article_id AS article_id, a.heading AS heading, a.url AS url, 
                       a.full_text AS full_text, r.score AS score, a.last_updated AS last_updated
                """
                result = session.run(query, subcategory=subcategory)
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
                
            st.write(f"Found {len(articles)} total articles across all categories")
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
    
    Articles should be sorted by relevance (most relevant first) and a max of 10 articles. 
    Only include articles with STRONG topical relevance. Prioritize quality over quantity.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst expert at finding historical market patterns."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        result_text = response.choices[0].message.content
        
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
        st.error(f"Error filtering relevant articles: {str(e)}")
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

def generate_market_impact_data(news_text, relevant_articles):
    prompt = f"""
    Based on the breaking financial news and historical articles, identify:
    1. The most comparable historical event with exact date (YYYY-MM-DD format)
    2. The most relevant market index to track (e.g., S&P 500, Hang Seng, Nikkei 225)
    3. The approximate percentage impact on that index over 1 day, 1 week, and 1 month periods
    
    Current News:
    {news_text}
    
    Historical Articles:
    {json.dumps([{"heading": a["heading"], "date": str(a["last_updated"]), "content": a["full_text"][:300]} for a in relevant_articles[:5]])}
    
    Return ONLY a JSON object with these exact keys:
    {{
        "historical_event": "YYYY-MM-DD: Brief description of comparable event",
        "market_index": "Name of most relevant index",
        "impact_1d": percentage change as decimal (e.g., 0.02 for 2% gain, -0.03 for 3% loss),
        "impact_1w": percentage change as decimal,
        "impact_1m": percentage change as decimal
    }}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst specializing in market impact assessment."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        result_text = response.choices[0].message.content
        
        if '```json' in result_text:
            json_str = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            json_str = result_text.split('```')[1].split('```')[0].strip()
        else:
            json_str = result_text.strip()
            
        impact_data = json.loads(json_str)
        return impact_data
    except Exception as e:
        st.error(f"Error generating market impact data: {str(e)}")
        return {
            "historical_event": "Unable to determine comparable event",
            "market_index": "S&P 500",
            "impact_1d": 0,
            "impact_1w": 0,
            "impact_1m": 0
        }

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
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a senior financial analyst at a top investment bank."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating financial report: {str(e)}")
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
    
    with st.spinner("Generating market impact visualization..."):
        try:
            impact_data = generate_market_impact_data(news_text, relevant_articles)
            
            st.header("📈 Market Impact Projection")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("1-Day Impact", f"{impact_data['impact_1d']*100:.2f}%")
            with col2:
                st.metric("1-Week Impact", f"{impact_data['impact_1w']*100:.2f}%")
            with col3:
                st.metric("1-Month Impact", f"{impact_data['impact_1m']*100:.2f}%")
                
            st.caption(f"Based on historical comparison to: {impact_data['historical_event']}")
            st.caption(f"Reference index: {impact_data['market_index']}")
        except Exception as e:
            print(f"Error displaying market impact: {str(e)}")
    
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
                        st.info("Processing provided article IDs with reasoning...")
                        relevant_articles = process_article_ids_with_reasoning(article_data)
                        
                        with st.spinner("Generating market impact visualization..."):
                            try:
                                impact_data = generate_market_impact_data("Analysis of provided articles", relevant_articles)
                                
                                st.header("📈 Market Impact Projection")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("1-Day Impact", f"{impact_data['impact_1d']*100:.2f}%")
                                with col2:
                                    st.metric("1-Week Impact", f"{impact_data['impact_1w']*100:.2f}%")
                                with col3:
                                    st.metric("1-Month Impact", f"{impact_data['impact_1m']*100:.2f}%")
                                    
                                st.caption(f"Based on historical comparison to: {impact_data['historical_event']}")
                                st.caption(f"Reference index: {impact_data['market_index']}")
                            except Exception as e:
                                print(f"Error displaying market impact: {str(e)}")
                        
                        with st.spinner("Generating financial intelligence report..."):
                            try:
                                report = generate_financial_report("Analysis based on provided articles", relevant_articles)
                                st.header("🔍 Financial Intelligence Report")
                                st.markdown(report)
                            except Exception as e:
                                print(f"Error generating financial report: {str(e)}")
                                st.info("Unable to generate the financial report at this time.")
                        
                        st.header("📚 Provided Articles with Reasoning")
                        for i, article in enumerate(relevant_articles):
                            with st.expander(f"{i+1}. {article['heading']}"):
                                st.write(f"**Article ID:** {article['article_id']}")
                                st.write(f"**URL:** {article['url']}")
                                st.write(f"**Reasoning:** {article.get('reasoning', 'No reasoning provided')}")
                                st.write("**Content Preview:**")
                                st.write(article['full_text'][:500] + "..." if len(article['full_text']) > 500 else article['full_text'])
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