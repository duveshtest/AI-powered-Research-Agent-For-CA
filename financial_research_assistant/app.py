# financial_research_assistant/app.py
import streamlit as st
import requests
import json # For parsing JSON if needed, though requests.json() handles it.

# FastAPI backend URL (ensure this matches where your FastAPI app is running)
# When running both locally, FastAPI might be on port 8000.
FASTAPI_BASE_URL = "http://127.0.0.1:8000"
REPORT_ENDPOINT = f"{FASTAPI_BASE_URL}/api/v1/generate_report"

# --- Page Configuration ---
st.set_page_config(
    page_title="Financial Research Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar ---
st.sidebar.title("About")
st.sidebar.info(
    "This is an AI-Powered Financial Research Assistant. "
    "Enter a company name or research query to generate a report. "
    "The system uses Tavily for web research, ChromaDB for vector storage, "
    "Alpha Vantage for financial data, and Google Gemini for report generation."
)
st.sidebar.markdown("---")
st.sidebar.subheader("API Status:")
try:
    # Check if FastAPI backend is reachable
    ping_url = f"{FASTAPI_BASE_URL}/" # Assuming your FastAPI root returns a simple message or 200 OK
    response = requests.get(ping_url, timeout=5)
    if response.status_code == 200:
        st.sidebar.success("Backend API is Online")
        # Optionally display a message from the root endpoint
        # api_message = response.json().get("message", "Connected")
        # st.sidebar.caption(f"API: {api_message}")
    else:
        st.sidebar.error(f"Backend API Error (Status: {response.status_code})")
except requests.exceptions.ConnectionError:
    st.sidebar.error("Backend API is Offline or Unreachable")
    st.sidebar.caption(f"Ensure FastAPI is running at: {FASTAPI_BASE_URL}")
except requests.exceptions.Timeout:
    st.sidebar.warning("Backend API connection timed out.")

st.sidebar.markdown("---")


# --- Main Application ---
st.title("💰 AI Financial Research Assistant")

# Input for company query
st.subheader("Enter Research Query")
company_query = st.text_input(
    "e.g., 'Financial performance of Apple Inc. in 2023', or 'MSFT', or 'Future of renewable energy stocks'",
    placeholder="Type your query here..."
)

# Report generation button
if st.button("Generate Report", type="primary", use_container_width=True):
    if not company_query:
        st.warning("Please enter a company name or research query.")
    else:
        with st.spinner(f"Generating report for: '{company_query}'... This may take a few minutes."):
            try:
                payload = {"company_query": company_query}
                response = requests.post(REPORT_ENDPOINT, json=payload, timeout=300) # 5 min timeout

                if response.status_code == 200:
                    report_data = response.json()
                    st.session_state.report_data = report_data # Store in session state to persist
                    st.success("Report generated successfully!")
                else:
                    st.error(f"Error generating report: {response.status_code} - {response.text}")
                    st.session_state.report_data = None # Clear previous report on error

            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend API: {e}")
                st.session_state.report_data = None
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.session_state.report_data = None

st.markdown("---")

# Display generated report (if available in session state)
if 'report_data' in st.session_state and st.session_state.report_data:
    report_output = st.session_state.report_data
    
    st.subheader(f"📄 Report for: {report_output.get('topic', 'N/A')}")
    
    # Using st.expander for collapsible sections
    with st.expander("Full Report Text", expanded=True):
        st.markdown(report_output.get('report', "No report content available."))

    st.subheader("🔗 Sources Consulted")
    sources = report_output.get('sources_consulted', [])
    if sources:
        for i, source in enumerate(sources):
            title = source.get('title', 'Source')
            url = source.get('url')
            if title and url and title != url:
                st.markdown(f"{i+1}. [{title}]({url})")
            elif url:
                st.markdown(f"{i+1}. {url}")
            else:
                st.markdown(f"{i+1}. Invalid source entry")
    else:
        st.info("No specific sources were listed for this report (this might indicate an issue or that the report is based on general financial data not tied to specific URLs).")

# Placeholder for future features like template upload
st.sidebar.markdown("---")
st.sidebar.subheader("Future Features (Placeholders)")
uploaded_file = st.sidebar.file_uploader("Upload Report Template (PDF, PPTX, XLSX)", type=["pdf", "pptx", "xlsx"], disabled=True)
if uploaded_file is not None:
    st.sidebar.success(f"Uploaded {uploaded_file.name} (Processing not implemented yet)")


# Instructions to run:
# 1. Make sure the FastAPI backend is running:
#    (from financial_research_assistant directory) uvicorn main:app --reload --port 8000
# 2. Run the Streamlit app:
#    (from financial_research_assistant directory) streamlit run app.py
