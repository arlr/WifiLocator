from flask import Flask, render_template, jsonify
import folium
from sqlalchemy import create_engine, text
import pandas as pd

app = Flask(__name__)

# Configure your database connection
DATABASE_URI = 'sqlite:///database.db'  # Replace with your DB URI
engine = create_engine(DATABASE_URI)

@app.route('/')
def index():
    """
    This route is the entry point of the application. It fetches data from the database and renders a map with markers.
    
    Returns:
        str: HTML content containing a folium map.
    """
    # Fetch data from the database
    query = text("SELECT id, bssid, latitude, longitude, ssid FROM wifilist")  # Modify your query
    df = pd.read_sql_query(query, engine)
    
    # Create a base map
    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=13)

    # Add markers to the map
    for index, row in df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"ID: {row['id']}<br>SSID: {row['ssid']}<br>BSSID: {row['bssid']}",
            icon=folium.Icon(icon='info-sign', prefix='glyphicon')
        ).add_to(m)
    
    # Render the map as an iframe in HTML
    return render_template('index.html', map=m._repr_html_())

@app.route('/card/<int:point_id>')
def card(point_id):
    """
    This route retrieves detailed information about a specific WiFi point based on its ID.
    
    Args:
        point_id (int): The ID of the WiFi point to retrieve details for.

    Returns:
        dict or tuple: JSON containing the WiFi point's details, or an error message with HTTP status code 404 if not found.
    """
    query = text("SELECT id, timestamp, bssid, frequency_mhz, ssid, channel_bandwidth_mhz, latitude, longitude, accuracy, provider FROM wifilist WHERE id = :id")  # Modify your query
    with engine.connect() as conn:
        result = conn.execute(query, {'id': point_id}).fetchone()
    
    if result:
        return jsonify({
            'id': result.id,
            'timestamp': result.timestamp,
            'bssid': result.bssid,
            'frequency_mhz': result.frequency_mhz,
            'ssid': result.ssid,
            'channel_bandwidth_mhz': result.channel_bandwidth_mhz,
            'latitude': result.latitude,
            'longitude': result.longitude,
            'accuracy': result.accuracy,
            'provider': result.provider
        })
    else:
        return jsonify({'error': 'Point not found'}), 404

@app.route('/data')
def data():
    """
    This route returns the entire dataset from the database as a JSON object.
    
    Returns:
        dict: JSON containing the entire dataset.
    """
    query = text("SELECT * FROM wifilist")  # Modify your query
    with engine.connect() as conn:
        result = conn.execute(query).fetchall()
    
    data = [dict(row) for row in result]
    return jsonify(data)

@app.route('/data_table')
def data_table():
    """
    This route renders the data table page.
    
    Returns:
        HTML: The rendered data_table.html template.
    """
    return render_template('data_table.html')

if __name__ == '__main__':
    app.run(debug=True)