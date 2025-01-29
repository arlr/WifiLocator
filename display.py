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

if __name__ == '__main__':
    app.run(debug=True)