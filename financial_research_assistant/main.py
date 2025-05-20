# main.py
from fastapi import FastAPI
from .api import endpoints as api_endpoints # Ensure this import works based on your project structure

app = FastAPI(
    title="Financial Research Assistant API",
    description="API for generating financial research reports.",
    version="0.1.0"
)

# Include the router from api/endpoints.py
# It's good practice to prefix API routes, e.g., /api/v1
app.include_router(api_endpoints.router, prefix="/api/v1", tags=["Research Assistant"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Financial Research Assistant API. Visit /docs for API documentation."}

# To run this app: uvicorn financial_research_assistant.main:app --reload
# (Assuming 'financial_research_assistant' is in PYTHONPATH or you are in its parent directory)
# Or if you are in the 'financial_research_assistant' directory: uvicorn main:app --reload
