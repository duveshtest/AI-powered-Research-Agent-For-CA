import requests
import json
from ..utils.config import TAVILY_API_KEY # Import API key from config

TAVILY_API_URL = "https://api.tavily.com/search"

def search_tavily(query: str, search_depth: str = "advanced", max_results: int = 10, include_domains: list = None, exclude_domains: list = None):
    """
    Performs a web search using the Tavily API.

    Args:
        query (str): The search query.
        search_depth (str, optional): The depth of the search. Can be "basic" or "advanced". Defaults to "advanced".
        max_results (int, optional): The maximum number of results to return. Defaults to 10.
        include_domains (list, optional): A list of domains to specifically include in the search.
        exclude_domains (list, optional): A list of domains to specifically exclude from the search.

    Returns:
        list: A list of search results (dictionaries with keys like 'title', 'url', 'content', 'score', etc.)
              Returns an empty list if an error occurs or TAVILY_API_KEY is not set.
    """
    if not TAVILY_API_KEY:
        print("Error: TAVILY_API_KEY is not set. Please set it in your .env file or environment variables.")
        return []

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": False, # True if you want Tavily to provide a summarized answer
        "include_raw_content": False, # True if you want raw HTML content (usually not needed if only extracting text later)
        "include_domains": include_domains if include_domains else [],
        "exclude_domains": exclude_domains if exclude_domains else []
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(TAVILY_API_URL, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        results = response.json()
        # We are interested in the 'results' part of the response, which contains a list of found sources.
        # Each item typically has 'title', 'url', 'content' (snippet), 'score', 'raw_content' (if requested).
        return results.get("results", [])

    except requests.exceptions.RequestException as e:
        print(f"Error during Tavily API request: {e}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from Tavily API. Response: {response.text}")
        return []

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    # Make sure to have a .env file with TAVILY_API_KEY in the root of the project
    # or have the TAVILY_API_KEY environment variable set.
    
    # To run this test, navigate to the 'financial_research_assistant' directory 
    # and run: python -m services.research_service

    from dotenv import load_dotenv
    import os
    # Load .env from the project root if it exists
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        # Re-import TAVILY_API_KEY if it was loaded from .env after initial module load
        from ..utils.config import TAVILY_API_KEY as TEST_TAVILY_API_KEY
        if not TEST_TAVILY_API_KEY:
             print("Test: TAVILY_API_KEY not found after loading .env. Make sure it's in your .env file.")
        else:
            print(f"Test: Loaded TAVILY_API_KEY successfully: {TEST_TAVILY_API_KEY[:5]}...") # Print first 5 chars for confirmation
    else:
        print("Test: .env file not found in project root. Ensure TAVILY_API_KEY is set as an environment variable for testing.")


    if TAVILY_API_KEY or os.getenv("TAVILY_API_KEY"): # Check again in case it was set globally
        sample_query = "financial performance of Apple Inc. in 2023"
        print(f"\nPerforming test search for: '{sample_query}'")
        search_results = search_tavily(sample_query, max_results=5)

        if search_results:
            print(f"\nFound {len(search_results)} results:")
            for i, result in enumerate(search_results):
                print(f"  Result {i+1}:")
                print(f"    Title: {result.get('title')}")
                print(f"    URL: {result.get('url')}")
                print(f"    Score: {result.get('score')}")
                # The 'content' from Tavily is a snippet/summary of the page relevant to the query.
                print(f"    Content Snippet: {result.get('content')[:200]}...") 
                print("-" * 20)
        else:
            print("No results returned or an error occurred.")
    else:
        print("\nSkipping test search as TAVILY_API_KEY is not available.")
