import httpx
from fastapi import APIRouter, Request, HTTPException
import os

router = APIRouter()

# The URL for the hermes service, configurable via environment variable
HERMES_URL = os.getenv("HERMES_URL", "http://hermes:8000")

@router.post("/search")
async def search_proxy(request: Request):
    """
    Proxies search requests from the frontend to the hermes service,
    which handles the actual Elasticsearch query.
    """
    try:
        search_query = await request.json()
        hermes_search_url = f"{HERMES_URL}/api/v1/search"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                hermes_search_url,
                json=search_query,
                timeout=60.0,  # Setting a 60-second timeout for the search request
            )
            response.raise_for_status()  # Raises an exception for 4xx/5xx responses
            return response.json()

    except httpx.HTTPStatusError as e:
        # Forward the error response from the hermes service
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError as e:
        # Handle errors connecting to the hermes service
        raise HTTPException(status_code=502, detail=f"Error connecting to hermes service: {e}")
    except Exception as e:
        # Handle other potential errors, like JSON decoding
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
