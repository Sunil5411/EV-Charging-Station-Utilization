import os
import requests
import mysql.connector
import random
import pandas as pd
from sqlalchemy import create_engine
from sklearn.cluster import KMeans
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Step 1: Fetch data from Open Charge Map API
def fetch_data_from_api():
    url = "https://api.openchargemap.io/v3/poi/"
    params = {"countrycode": "IN", "maxresults": 2000}
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Error: API key not found. Please set it in the .env file.")
        exit()
    headers = {"X-API-Key": api_key}
    
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            print("API call successful. Data fetched successfully.")
            return data
        except ValueError:
            print("Error: The response is not valid JSON.")
            print(f"Response Content: {response.text}")
            exit()
    else:
        print(f"Error: Received status code {response.status_code}.")
        print(f"Response Content: {response.text}")
        exit()
