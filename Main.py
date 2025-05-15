import requests
import mysql.connector
import random
import pandas as pd
from sqlalchemy import create_engine
from sklearn.cluster import KMeans

# Step 1: Fetch data from Open Charge Map API
def fetch_data_from_api():
    url = "https://api.openchargemap.io/v3/poi/ "
    params = {"countrycode": "IN", "maxresults": 2000}  # Fetch data for India
    headers = {"X-API-Key": "fb5f3e54-8755-410c-bf1d-ab46b5b10cde"}  # Replace with your actual API key
    response = requests.get(url, params=params, headers=headers)

    # Check if the request was successful
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

# Step 2: Simulate usage counts between 1 and 100
def simulate_usage_counts(data):
    for station in data:
        station['UsageCount'] = random.randint(1, 100)  # Simulate random usage counts
    return data

# Step 3: Insert data into MySQL database
def insert_data_into_mysql(data):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="5411",
            database="ev_charging"
        )
        cursor = conn.cursor()
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        exit()

    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stations (
        station_id INT PRIMARY KEY,
        name VARCHAR(255),
        latitude DECIMAL(10, 6),
        longitude DECIMAL(10, 6),
        usage_count INT
    )
    """)

    # Insert data into the stations table
    for station in data:
        query = """
        INSERT INTO stations (station_id, name, latitude, longitude, usage_count)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            latitude = VALUES(latitude),
            longitude = VALUES(longitude),
            usage_count = VALUES(usage_count)
        """
        values = (
            station['ID'],
            station['AddressInfo']['Title'],
            station['AddressInfo']['Latitude'],
            station['AddressInfo']['Longitude'],
            station.get('UsageCount', 0)  # Use simulated usage count
        )
        cursor.execute(query, values)

    conn.commit()
    cursor.close()
    conn.close()
    print("Data successfully inserted into the database.")

# Step 4: Perform geospatial clustering and identify low/high-performing stations
def analyze_stations():
    # Connect to MySQL using SQLAlchemy
    engine = create_engine("mysql+pymysql://root:password@localhost/ev_charging")
    query = "SELECT * FROM stations"
    df = pd.read_sql(query, engine)

    # Perform geospatial clustering
    coords = df[['latitude', 'longitude']]
    kmeans = KMeans(n_clusters=5, random_state=42)  # Adjust n_clusters as needed
    df['cluster'] = kmeans.fit_predict(coords)

    # Calculate utilization metrics per cluster
    cluster_metrics = df.groupby('cluster').agg({
        'usage_count': ['mean', 'sum']
    }).reset_index()
    cluster_metrics.columns = ['cluster', 'avg_usage', 'total_usage']

    print("\nCluster Metrics:")
    print(cluster_metrics)

    # Identify low-performing and high-performing stations
    avg_usage = df['usage_count'].mean()
    low_performing_stations = df[df['usage_count'] < avg_usage]
    high_performing_stations = df[df['usage_count'] > avg_usage]

    print("\nLow-Performing Stations:")
    print(low_performing_stations[['station_id', 'name', 'usage_count']])

    print("\nHigh-Performing Stations:")
    print(high_performing_stations[['station_id', 'name', 'usage_count']])

# Main function
if __name__ == "__main__":
    # Step 1: Fetch data from API
    data = fetch_data_from_api()

    # Step 2: Simulate usage counts
    data = simulate_usage_counts(data)

    # Step 3: Insert data into MySQL
    insert_data_into_mysql(data)

    # Step 4: Analyze stations
    analyze_stations()