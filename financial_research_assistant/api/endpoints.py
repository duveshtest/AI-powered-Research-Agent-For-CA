# api/endpoints.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import asyncio # For concurrent execution if needed in future

# Import services
# Corrected import paths assuming 'financial_research_assistant' is the root package recognized by Python path
from ..services import research_service
from ..services import content_service # Main agent will use view_text_website
from ..services import vector_db_service
from ..services import report_service
from ..services import financial_data_service
# The main agent (Jules) will handle the actual calls to view_text_website

router = APIRouter()

class ReportRequest(BaseModel):
    company_query: str # e.g., "Apple Inc." or "latest financial news for Google"
    # include_financial_data: bool = True # Option to include financial data from Alpha Vantage
    # max_search_results: int = 10 # Option for number of search results for Tavily

class ReportResponse(BaseModel):
    topic: str
    report: str
    sources_consulted: list[dict] # List of {'url': str, 'title': str (optional)}
    # financial_data_summary: dict = None # Optional: summary of financial data used

@router.post("/generate_report", response_model=ReportResponse)
async def generate_report_endpoint(request: ReportRequest):
    """
    Endpoint to generate a financial research report.
    Orchestrates calls to various services:
    1. Search for relevant URLs (Tavily).
    2. Fetch content from URLs (Conceptually, main agent uses view_text_website here).
    3. Add content to Vector DB (ChromaDB).
    4. (Optional) Fetch financial data (Alpha Vantage).
    5. Query Vector DB for context relevant to the topic.
    6. Generate report from context (Gemini).
    """
    print(f"[API Endpoint] Received request to generate report for: {request.company_query}")

    # 1. Web Research (Tavily)
    print("[API Endpoint] Step 1: Performing web research...")
    try:
        # Using a smaller number for initial testing to avoid hitting API limits quickly
        # and to speed up the process. This can be made configurable.
        search_results = research_service.search_tavily(request.company_query, max_results=5) 
        if not search_results:
            # Allow continuing even if Tavily returns no results, maybe financial data alone is useful
            print("[API Endpoint] Warning: Tavily search returned no results.")
            # raise HTTPException(status_code=404, detail="No search results found from Tavily.")
            web_urls_for_content_extraction = []
            consulted_urls_for_report = []
        else:
            web_urls_for_content_extraction = [result['url'] for result in search_results if result.get('url')]
            consulted_urls_for_report = [{'url': r.get('url'), 'title': r.get('title', '')} for r in search_results if r.get('url')]
            print(f"[API Endpoint] Tavily search yielded {len(web_urls_for_content_extraction)} URLs.")

    except Exception as e:
        print(f"[API Endpoint] Error in Tavily search: {e}")
        raise HTTPException(status_code=500, detail=f"Error during web research: {str(e)}")

    # 2. Content Extraction (Simulated - Main agent uses 'view_text_website')
    # This step is crucial and involves the main agent's tool.
    # The `content_service.extract_text_from_url_list` is a placeholder for the agent's action.
    # For now, we'll create dummy content to proceed with the flow.
    print("[API Endpoint] Step 2: Simulating content extraction (Agent uses view_text_website)...")
    extracted_url_contents = []
    if web_urls_for_content_extraction:
        # In a real scenario, the agent would iterate through web_urls_for_content_extraction,
        # call `view_text_website(url)` for each, and collect the results.
        # This cannot be done directly by the worker here.
        # The following is a simulation of what the agent would provide to the next step.
        for url in web_urls_for_content_extraction:
            # SIMULATION: Replace this with actual call by the main agent
            # text_content = view_text_website(url) # This is what the agent would do
            text_content = f"This is simulated extracted text content for {url}. The actual content would be fetched by the agent using the view_text_website tool."
            # Simulate potential error from view_text_website
            error_message = None # or "Failed to fetch content."
            
            if text_content and not error_message:
                extracted_url_contents.append({
                    "url": url,
                    "text_content": text_content,
                    "error": None
                })
            else:
                 extracted_url_contents.append({
                    "url": url,
                    "text_content": "",
                    "error": error_message or "Unknown error during fetching by agent."
                })
        print(f"[API Endpoint] Simulated extraction for {len(extracted_url_contents)} URLs.")
    else:
        print("[API Endpoint] No URLs to extract content from.")
        
    # Filter out items where content extraction might have failed (in simulation)
    valid_extracted_contents = [item for item in extracted_url_contents if item.get("text_content") and not item.get("error")]

    # 3. Add content to Vector DB (ChromaDB)
    print("[API Endpoint] Step 3: Adding extracted content to Vector DB...")
    if valid_extracted_contents:
        texts_to_add = [item['text_content'] for item in valid_extracted_contents]
        metadatas_to_add = [{'source_url': item['url']} for item in valid_extracted_contents]
        # Generating unique IDs for ChromaDB
        ids_to_add = [f"doc_{i}_{request.company_query.replace(' ','_')}" for i in range(len(texts_to_add))]
        
        # Clear collection for this specific query to keep it relevant? Or accumulate?
        # For now, let's clear and add for simplicity in this example.
        # This behavior should be decided based on application requirements.
        vector_db_service.clear_collection() 
        success_add = vector_db_service.add_texts_to_collection(texts=texts_to_add, metadatas=metadatas_to_add, ids=ids_to_add)
        if not success_add:
            print("[API Endpoint] Warning: Failed to add some texts to Vector DB.")
            # Not necessarily a fatal error, could proceed with what was added.
        else:
            print(f"[API Endpoint] Added {len(texts_to_add)} items to Vector DB. Total in DB: {vector_db_service.count_collection_items()}")
    else:
        print("[API Endpoint] No valid content to add to Vector DB.")

    # 4. Fetch Financial Data (Alpha Vantage) - Optional based on request or always include for now
    # For simplicity, let's assume the company_query is often a company symbol or name
    # that can be used as a symbol. This might need refinement (e.g., mapping name to symbol).
    print("[API Endpoint] Step 4: Fetching financial data (Alpha Vantage)...")
    financial_context_str = ""
    # Try to use the query as a symbol. This is a simplification.
    # A more robust solution would involve symbol lookup.
    company_symbol_guess = request.company_query.split(" ")[0].upper() # e.g., "Apple Inc." -> "APPLE"
    try:
        overview = financial_data_service.get_company_overview(company_symbol_guess)
        if overview:
            financial_context_str += f"Company Overview for {overview.get('Name', company_symbol_guess)} ({overview.get('Symbol')}):\n"
            financial_context_str += f"Description: {overview.get('Description', 'N/A')}\n"
            financial_context_str += f"Industry: {overview.get('Industry', 'N/A')}\n"
            financial_context_str += f"Sector: {overview.get('Sector', 'N/A')}\n"
            financial_context_str += f"Market Capitalization: {overview.get('MarketCapitalization', 'N/A')}\n"
            financial_context_str += f"EBITDA: {overview.get('EBITDA', 'N/A')}\n"
            financial_context_str += f"PERatio: {overview.get('PERatio', 'N/A')}\n"
            financial_context_str += f"EPS: {overview.get('EPS', 'N/A')}\n"
            financial_context_str += "---\n"
            print(f"[API Endpoint] Fetched company overview for {company_symbol_guess}.")
        else:
            print(f"[API Endpoint] Could not fetch company overview for {company_symbol_guess}.")
    except Exception as e:
        print(f"[API Endpoint] Error fetching financial data for {company_symbol_guess}: {e}")
    
    # Add financial context to ChromaDB as well, so it can be retrieved by semantic search
    if financial_context_str:
        fin_metadata = {'source_url': f'alpha_vantage_overview_{company_symbol_guess}'}
        fin_id = f"financial_overview_{company_symbol_guess}"
        vector_db_service.add_texts_to_collection(
            texts=[financial_context_str], 
            metadatas=[fin_metadata], 
            ids=[fin_id]
        )
        print(f"[API Endpoint] Added financial overview to Vector DB. Total in DB: {vector_db_service.count_collection_items()}")


    # 5. Query Vector DB for context relevant to the topic
    print("[API Endpoint] Step 5: Querying Vector DB for relevant context...")
    # Query with the original request, and also with the financial data if fetched
    query_texts_for_rag = [request.company_query]
    # if financial_context_str: # Option: could also query with parts of financial data
    #    query_texts_for_rag.append(f"Financials for {company_symbol_guess}")
        
    # Get more results than perhaps strictly needed for the LLM, to have a broader context.
    # The LLM prompt will then contain these.
    num_rag_results = 10 # Number of documents to retrieve from ChromaDB for context
    context_from_db = vector_db_service.query_collection(
        query_texts=query_texts_for_rag, 
        n_results=num_rag_results
    )
    
    report_context_documents = []
    if context_from_db and context_from_db.get('documents') and context_from_db['documents'][0]:
        retrieved_docs = context_from_db['documents'][0]
        retrieved_metadatas = context_from_db['metadatas'][0]
        retrieved_ids = context_from_db['ids'][0]
        
        for i, doc_text in enumerate(retrieved_docs):
            report_context_documents.append({
                "id": retrieved_ids[i],
                "text_content": doc_text,
                "metadata": retrieved_metadatas[i]
            })
        print(f"[API Endpoint] Retrieved {len(report_context_documents)} documents from Vector DB for report context.")
    else:
        print("[API Endpoint] No relevant documents found in Vector DB for the query. Report might be less detailed.")
        # If no web content and no financial data, this could be an issue.
        if not valid_extracted_contents and not financial_context_str:
             raise HTTPException(status_code=404, detail="No content gathered from web search or financial APIs to generate a report.")


    # 6. Generate Report (Gemini)
    print("[API Endpoint] Step 6: Generating report via Gemini API...")
    if not report_context_documents: # Should not happen if the above check is in place.
        print("[API Endpoint] No context documents available for report generation. Aborting.")
        # This case should ideally be caught earlier.
        # If there were Tavily results but extraction failed for all, consulted_urls_for_report might still be populated.
        return ReportResponse(
            topic=request.company_query,
            report="Error: No context could be gathered to generate the report.",
            sources_consulted=consulted_urls_for_report 
        )

    try:
        # The report_service takes list of dicts with 'text_content' and 'metadata' (with 'source_url')
        generated_report_text = report_service.generate_report_from_context(
            topic=request.company_query,
            context_documents=report_context_documents # Pass the RAG results
        )
        if generated_report_text.startswith("Error:"):
            raise HTTPException(status_code=500, detail=f"Report generation failed: {generated_report_text}")
        
        print("[API Endpoint] Report generated successfully.")

    except Exception as e:
        print(f"[API Endpoint] Error during report generation: {e}")
        raise HTTPException(status_code=500, detail=f"Error during report generation: {str(e)}")

    # Prepare response
    # The sources_consulted should ideally come from the metadata of the actual context used by Gemini.
    # The `generate_report_from_context` prompt asks Gemini to list sources from the context.
    # For now, `consulted_urls_for_report` from Tavily is a good starting point.
    # A more robust way would be to extract source URLs from `report_context_documents`.
    final_sources = []
    seen_urls = set()
    for doc in report_context_documents:
        url = doc.get("metadata", {}).get("source_url")
        if url and url not in seen_urls and not url.startswith("alpha_vantage_overview_"): # Don't list AV as a clickable source unless desired
            # Try to find the title from original Tavily search if available
            title = next((t_url.get('title') for t_url in consulted_urls_for_report if t_url.get('url') == url), '')
            final_sources.append({'url': url, 'title': title})
            seen_urls.add(url)
    
    # If Tavily returned nothing, but we had financial data, consulted_urls_for_report would be empty.
    # Ensure final_sources reflects what was actually used.
    if not final_sources and consulted_urls_for_report: # Fallback if RAG context was empty but Tavily had results
         final_sources = consulted_urls_for_report


    return ReportResponse(
        topic=request.company_query,
        report=generated_report_text,
        sources_consulted=final_sources
    )

# Example of how to include this router in main.py:
# from fastapi import FastAPI
# from .api import endpoints as api_router
# app = FastAPI()
# app.include_router(api_router.router, prefix="/api/v1") # Example prefix
