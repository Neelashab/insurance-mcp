from typing import Any
import os
import httpx
from mcp.server.fastmcp import FastMCP
from models import BusinessProfile, BioData
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
MONGODB_URI = os.getenv("MONGODB_URI")

mongo_client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
db = mongo_client['cigna_insurance']
collection = db['insurance_plans']

# Helper functions
def map_business_size_to_categories(employee_count: int) -> list[str]:
    """
    Map employee count to all applicable business size categories.
    Returns list of categories that the business size qualifies for.
    """
    categories = []
    
    if 2 <= employee_count <= 50:
        categories.append("2-50")
    if 2 <= employee_count <= 99:
        categories.append("2-99")
    if 51 <= employee_count <= 99:
        categories.append("51-99")
    if 100 <= employee_count <= 499:
        categories.append("100-499")
    if 500 <= employee_count <= 2999:
        categories.append("500-2,999")
    if employee_count >= 3000:
        categories.append("3,000+")
    
    # Also add "All sizes" as it matches any business
    categories.append("All sizes")
    
    return categories

async def retrieve_eligible_plans(plan_answers: BusinessProfile):
    """
    Search MongoDB for insurance plans that match user's business profile.
    Returns a dictionary where key is plan name and value is summary text.
    """
    print(f"  Coverage Preference: {plan_answers.coverage_preference}")
    
    # Build MongoDB query filters
    query_filters = {}
    
    # Coverage preference filter (Network Type)
    if plan_answers.coverage_preference:
        query_filters["Network Type"] = plan_answers.coverage_preference
    
    # Build list of filters to combine
    filters_list = []
    
    # Business size filter
    if plan_answers.business_size:
        size_categories = map_business_size_to_categories(plan_answers.business_size)
        filters_list.append({
            "$or": [
                {"Business Size Eligibility": {"$in": size_categories}},
                {"Business Size Eligibility": "All sizes"}
            ]
        })
    
    # Location filter
    if plan_answers.location:
        filters_list.append({
            "$or": [
                {"location_availability": {"$in": [plan_answers.location]}},
                {"location_availability": {"$in": ["All states"]}}
            ]
        })
    
    # Combine all filters
    if len(filters_list) > 1:
        query_filters["$and"] = filters_list
    elif len(filters_list) == 1:
        query_filters.update(filters_list[0])
    
    print(f"  MongoDB query: {query_filters}")
    
    # Query MongoDB
    try:
        cursor = collection.find(query_filters)
        matching_docs = list(cursor)
        print(f"  Found {len(matching_docs)} matching documents")
        
        # Create dictionary: plan_name -> summary
        plan_dict = {}
        for doc in matching_docs:
            plan_name = doc.get("Plan Type", "Unknown Plan")
            summary = doc.get("summary", "")
            
            if plan_name != "Unknown Plan" and summary:
                plan_dict[plan_name] = summary
                print(f"    Added plan: {plan_name}")
            else:
                print(f"    Skipped document with missing Plan Type or summary")
        
        print(f"  Returning {len(plan_dict)} unique plans")
        print(f"  Plan names: {list(plan_dict.keys())}")
        print(f"=== END PLAN SEARCH ===\n")
        
        return plan_dict
        
    except Exception as e:
        print(f"Error searching MongoDB: {e}")
        return {}

    return

async def get_claims_estimate():
    return