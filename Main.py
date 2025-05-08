import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import random

def simulate_session_data(num_sessions=1000):
    station_ids = [312269, 312240, 312152, 312151, 312150]
    charge_point_ids = [0, 32, 33, 34, 35]
    statuses = ['Available', 'Occupied', 'Faulted']
    
    sessions = []
    start_date = datetime(2023, 10, 1)
    end_date = datetime(2023, 10, 31)
    
    for _ in range(num_sessions):
        station_id = random.choice(station_ids)
        charge_point_id = random.choice(charge_point_ids)
        status = random.choice(statuses)
        start_time = start_date + timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))
        end_time = start_time + timedelta(hours=random.uniform(0.5, 4.0))
        energy_kwh = random.uniform(5.0, 20.0)
        
        sessions.append({
            'id': len(sessions) + 1,
            'station_id': station_id,
            'charge_point_id': charge_point_id,
            'start_time': start_time,
            'end_time': end_time,
            'energy_kwh': energy_kwh,
            'status': status
        })
    
    return pd.DataFrame(sessions)

def load_data_from_db(db_config):
    engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")
    query = "SELECT * FROM charging_sessions"
    df = pd.read_sql(query, engine)
    return df

def clean_data(df):
    # Convert 'start_time' and 'end_time' to datetime
    df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')
    
    # Handle missing values
    df.fillna({
        'charge_point_id': 'Unknown',
        'energy_kwh': 0.0,
        'status': 'Unknown'
    }, inplace=True)
    
    # Drop rows with invalid start_time or end_time
    df.dropna(subset=['start_time', 'end_time'], inplace=True)
    
    return df

def compute_metrics(df):
    # Calculate session duration in hours
    df['session_duration'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 3600
    
    # Calculate utilization rate (example)
    # Utilization rate = Total session duration / Total time period
    total_time_period = (df['end_time'].max() - df['start_time'].min()).total_seconds() / 3600
    
    df['utilization_rate'] = df.groupby('station_id')['session_duration'].transform('sum') / total_time_period * 24
    
    return df

def store_simulated_data_in_db(df, db_config):
    connection = create_connection(db_config['host'], db_config['user'], db_config['password'], db_config['database'])
    
    if connection is None:
        print("Failed to connect to the database.")
        return
    
    # Create table if not exists
    create_table_query = """
    CREATE TABLE IF NOT EXISTS charging_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        station_id VARCHAR(255),
        charge_point_id VARCHAR(255),
        start_time DATETIME,
        end_time DATETIME,
        energy_kwh FLOAT,
        status VARCHAR(255)
    )
    """
    execute_query(connection, create_table_query)
    
    # Insert data
    insert_query = """
    INSERT INTO charging_sessions (station_id, charge_point_id, start_time, end_time, energy_kwh, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = [tuple(row) for row in df.values]
    
    execute_query(connection, insert_query, values)
    
    connection.close()

def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL Database connection successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def execute_query(connection, query, values=None):
    cursor = connection.cursor()
    try:
        if values:
            cursor.executemany(query, values)
        else:
            cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as e:
        print(f"The error '{e}' occurred")

# Example usage
api_key = 'YOUR_API_KEY'
db_config = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': '5411',  # Replace with your MySQL password
    'database': 'ev_charging'
}

# Simulate session data
simulated_data = simulate_session_data()

# Store simulated data in the database
store_simulated_data_in_db(simulated_data, db_config)

# Load data from the database
df = load_data_from_db(db_config)
print("Loaded Data:")
print(df.head())

# Clean the data
df_cleaned = clean_data(df)
print("\nCleaned Data:")
print(df_cleaned.head())

# Compute metrics
df_metrics = compute_metrics(df_cleaned)
print("\nData with Metrics:")
print(df_metrics.head())