# services/report_service.py
import google.generativeai as genai
from ..utils.config import GOOGLE_API_KEY

# Configure the Gemini API key
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("Warning: GOOGLE_API_KEY is not set. Report generation will fail.")

# For now, we'll use gemini-1.5-flash, which is often available in free tiers and is faster.
# For higher quality, gemini-1.5-pro can be used if available and within budget/quota.
# The user's prompt mentioned "gemini-1.5-pro", so we can make this configurable or default to it.
DEFAULT_MODEL_NAME = "gemini-1.5-pro-latest" # Or "gemini-1.5-flash-latest"

def generate_report_from_context(topic: str, context_documents: list[dict], model_name: str = DEFAULT_MODEL_NAME):
    """
    Generates a financial report using the Google Gemini API based on provided context.

    Args:
        topic (str): The research topic or company name.
        context_documents (list[dict]): A list of context documents. Each document is a dictionary
                                       expected to have at least a 'text_content' key and optionally
                                       a 'source_url' or other metadata in a 'metadata' sub-dictionary.
                                       Example from vector_db_service:
                                       {'id': 'doc1', 'text_content': 'Text...', 'metadata': {'source_url': 'url1'}}
        model_name (str, optional): The name of the Gemini model to use. Defaults to DEFAULT_MODEL_NAME.

    Returns:
        str: The generated report text, or an error message if generation fails.
    """
    if not GOOGLE_API_KEY:
        return "Error: GOOGLE_API_KEY is not configured. Cannot generate report."
    if not context_documents:
        return "Error: No context documents provided. Cannot generate report."

    try:
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        return f"Error initializing Gemini model '{model_name}': {str(e)}"

    # Constructing the prompt
    # This is a critical part and may need significant iteration and refinement.
    
    context_str = "\n\n--- Start of Provided Context ---\n"
    sources_list = []
    for i, doc in enumerate(context_documents):
        text = doc.get('text_content', doc.get('document', '')) # ChromaDB might return 'document' key
        metadata = doc.get('metadata', {})
        source_url = metadata.get('source_url', 'N/A')
        
        context_str += f"Source {i+1} (URL: {source_url}):\n{text}\n---\n"
        if source_url not in sources_list and source_url != 'N/A':
            sources_list.append(source_url)
    context_str += "--- End of Provided Context ---\n\n"

    prompt = f"""
You are a specialized financial research assistant. Your task is to generate a comprehensive financial report on the following topic: "{topic}".

**IMPORTANT INSTRUCTIONS:**
1.  **Strictly use only the information provided in the 'Provided Context' section below.** Do NOT use any external knowledge or information you were pre-trained on.
2.  The report should be well-structured. Consider including sections like:
    *   Business Overview
    *   Financial Performance (if data is available in context)
    *   Investment Thesis (if inferable from context)
    *   Key Developments / Recent News (from context)
    *   Risk Factors (if mentioned in context)
    *   Outlook (if context provides future-looking statements)
3.  **Cite your sources meticulously.** After each piece of information or paragraph, indicate the source number(s) from the 'Provided Context' that support it. For example: [Source 1], [Source 1, Source 3].
4.  At the end of the report, include a dedicated "Sources" section listing all unique source URLs used.

Here is the context you MUST use:
{context_str}

Now, please generate the financial report on "{topic}" based ONLY on the provided context and following all instructions.
    """

    # Generation Configuration (optional, but can be useful)
    generation_config = genai.types.GenerationConfig(
        # temperature=0.7, # Controls randomness. Lower for more factual.
        # top_p=0.95,
        # top_k=40,
        # max_output_tokens=2048, # Adjust as needed
    )
    
    # Safety Settings (optional, adjust as needed)
    # Refer to Google AI documentation for details on these settings.
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]

    try:
        # print(f"\n--- Sending Prompt to Gemini ({model_name}) ---")
        # print(prompt[:1000] + "...") # Print beginning of prompt for debugging
        # print(f"--- Context string length: {len(context_str)} ---")
        # print(f"--- Full prompt length: {len(prompt)} ---")

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
            # stream=False # Set to True if you want to stream the response
        )
        
        # print(f"\n--- Gemini Response ---")
        # print(response) # For debugging the raw response object

        if response.candidates:
            # Accessing text from the first candidate
            # Check if parts exist and have text
            if response.candidates[0].content and response.candidates[0].content.parts:
                generated_text = "".join(part.text for part in response.candidates[0].content.parts)
                return generated_text
            else:
                # Fallback or error if no text parts are found
                # Check for prompt feedback if content is empty
                if response.prompt_feedback:
                    return f"Error: Report generation blocked. Feedback: {response.prompt_feedback}"
                return "Error: Gemini response did not contain text content."
        else:
            # This case might indicate the prompt was blocked entirely before candidates were generated.
            if response.prompt_feedback:
                 return f"Error: Report generation failed. Prompt feedback: {response.prompt_feedback}"
            return "Error: No candidates returned from Gemini model."

    except Exception as e:
        # Log the full error for debugging
        # import traceback
        # print(f"Error during Gemini API call: {e}\n{traceback.format_exc()}")
        return f"Error during Gemini API call: {str(e)}"

if __name__ == '__main__':
    # Example Usage:
    # To run this test, navigate to the 'financial_research_assistant' directory
    # and run: python -m services.report_service
    # Ensure GOOGLE_API_KEY is set in your .env file or environment.

    print("\n--- ReportService Test ---")
    if not GOOGLE_API_KEY:
        print("Skipping test as GOOGLE_API_KEY is not set.")
    else:
        print(f"Using Gemini model: {DEFAULT_MODEL_NAME}")
        sample_topic = "Apple Inc. Q1 2024 Performance"
        sample_context = [
            {
                'id': 'doc1',
                'text_content': "Apple announced record revenue in Q1 2024, driven by strong iPhone 15 sales. The services division also saw significant growth.",
                'metadata': {'source_url': 'https://apple.com/news/q1_2024_results'}
            },
            {
                'id': 'doc2',
                'text_content': "Analysts noted that Apple's expansion into new markets is paying off. However, there are concerns about supply chain stability affecting Mac production.",
                'metadata': {'source_url': 'https://financejournal.com/articles/apple_q1_analysis'}
            },
            {
                'id': 'doc3', # Document without a source URL in metadata for testing
                'text_content': "The wearables segment, including Apple Watch and AirPods, continued its upward trend.",
                'metadata': {} # No source_url
            }
        ]
        
        print(f"\nGenerating report for: '{sample_topic}'")
        print(f"With {len(sample_context)} context documents.")
        
        report = generate_report_from_context(sample_topic, sample_context)
        
        print("\n--- Generated Report ---")
        if report.startswith("Error:"):
            print(f"Report generation failed: {report}")
        else:
            print(report)
        print("--- Test End ---")
