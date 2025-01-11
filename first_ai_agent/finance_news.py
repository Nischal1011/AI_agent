import os
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
import requests
from supabase import create_client
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import asyncio
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('finance_news.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
try:
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

# Configure Gemini
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    logger.info("Gemini API configured successfully")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")
    raise

# Define Brave Search function
search_news = FunctionDeclaration(
    name="search_financial_news",
    description="Search for latest financial news from reputable sources",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query for finding financial news"
            }
        },
        "required": ["query"]
    }
)

news_tool = Tool(function_declarations=[search_news])
model = genai.GenerativeModel('gemini-pro')

def execute_brave_search(query: str) -> list:
    """Execute Brave Search API call with error handling and filtering."""
    try:
        clean_query = " ".join(query.split())
        logger.info(f"Executing Brave search with query: {clean_query}")
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": os.getenv("BRAVE_API_KEY")
        }
        
        # Fix the site filter syntax
        params = {
            # Each site needs to be a separate site: operator
            "q": f"{clean_query} (site:bloomberg.com OR site:reuters.com OR site:cnbc.com OR site:ft.com)",
            "count": 10,
            "search_lang": "en",
            "freshness": "pd",
            "text_format": "raw"
        }
        
        # Add debug logging for the actual query
        logger.info(f"Search query: {params['q']}")
        
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=10
        )
        
        # Add delay to avoid rate limiting
        time.sleep(2)
        
        # Add debug logging
        logger.info(f"Brave Search API Response Status: {response.status_code}")
        logger.info(f"Brave Search API Response: {response.text[:500]}")  # First 500 chars
        
        response.raise_for_status()
        
        results = response.json().get("web", {}).get("results", [])
        logger.info(f"Found {len(results)} articles from Brave search")
        return [
            {
                "title": result.get("title"),
                "url": result.get("url"),
                "description": result.get("description")
            }
            for result in results
        ]
    
    except requests.RequestException as e:
        logger.error(f"Brave Search API error: {e}")
        return []

def get_article_content(url: str) -> str:
    """Fetch full article content."""
    try:
        logger.info(f"Fetching content from: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
            
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        if len(cleaned_text) < 100:  # Ensure meaningful content
            logger.warning(f"Extracted content too short from {url}")
            return ""
        
        logger.info(f"Successfully extracted {len(cleaned_text)} characters from {url}")
        return cleaned_text
    
    except Exception as e:
        logger.error(f"Error fetching article content: {e}")
        return ""

def store_article_in_supabase(article: dict) -> bool:
    """Store article in Supabase."""
    try:
        source = article.get("url", "").split("//")[-1].split("/")[0]
        
        # Update data structure to match your Supabase table
        data = {
            "title": article.get("title"),
            "url": article.get("url"),
            "finance_info": article.get("summary"),
            "source": source,
            "created_at": datetime.now().isoformat()
        }
        
        if not all([data["title"], data["url"], data["finance_info"], data["source"]]):
            logger.warning("Missing required fields in article data")
            return False
        
        logger.info(f"Storing article from {source}")
        supabase.table("finance_news").insert(data).execute()
        return True
    
    except Exception as e:
        logger.error(f"Error storing article in Supabase: {e}")
        return False

async def process_financial_news():
    """Process financial news using Gemini and Brave Search."""
    try:
        logger.info("Starting financial news processing")
        chat = model.start_chat()
        
        # Updated search queries to be more general
        search_queries = [
            "stock market news today",
            "financial markets update",
            "market analysis today",
            "trading stocks news",
            "market movers today"
        ]
        
        unique_urls = set()  # Track processed URLs
        unique_articles = []
        
        for query in search_queries:
            if len(unique_articles) >= 5:  # Increased target number
                break
                
            articles = execute_brave_search(query)
            
            for article in articles:
                url = article.get('url')
                
                # Skip if we've already processed this URL
                if url in unique_urls:
                    continue
                    
                if len(unique_articles) >= 5:
                    break
                
                unique_urls.add(url)
                content = get_article_content(url)
                
                if not content or len(content) < 500:  # Skip short content
                    continue
                
                # Fix the summarization prompt to be explicit about using the provided content
                analysis_prompt = f"""Based ONLY on the following article content, provide a concise 3-4 sentence summary of the key financial developments and market implications. 
                
                Article Title: {article['title']}
                
                Article Content:
                {content[:8000]}
                
                Provide your summary focusing on:
                1. The main financial news or development
                2. Key numbers or statistics mentioned
                3. Market impact or implications
                
                Summary:"""
                
                analysis = await chat.send_message_async(analysis_prompt)
                
                if analysis and analysis.text:
                    article['summary'] = analysis.text.strip()
                    if len(article['summary']) > 50:  # Basic quality check
                        unique_articles.append(article)
                        # Print summary to terminal
                        print("\n" + "="*80)
                        print(f"TITLE: {article['title']}")
                        print(f"SOURCE: {article['url']}")
                        print("-"*80)
                        print("SUMMARY:")
                        print(article['summary'])
                        print("="*80 + "\n")
                        
                        store_article_in_supabase(article)
                        logger.info(f"Article processed: {article['title']}")
    
    except Exception as e:
        logger.error(f"Error processing financial news: {e}", exc_info=True)

def main():
    """Main entry point of the script."""
    try:
        asyncio.run(process_financial_news())
        logger.info("Finished processing financial news")
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()