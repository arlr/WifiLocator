import json
import subprocess
import shlex
import platform
import os
import sys
import time
import threading
import sqlite3

def print_environment_info():
    """
    Prints information about the Python environment and the system.
    """
    print("-" * 80)
    print("Python Environment Information")
    print("-" * 80)
    print(f"Python Version: {sys.version}")
    print(f"Python Implementation: {platform.python_implementation()}")
    print(f"Operating System: {platform.system()}")
    print(f"Operating System Release: {platform.release()}")
    print(f"Operating System Version: {platform.version()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Current Working Directory: {os.getcwd()}")
    try:
        import psutil
        print(f"CPU Count: {psutil.cpu_count()}")
        print(f"Available Memory: {psutil.virtual_memory().available // (1024 * 1024)} MB")
    except ImportError:
        print("psutil library not found. Skipping CPU and memory information.")
    print("-" * 80)

def run_cmd(cmd):
        """
        Runs the given command and captures its output.
        Args:
                cmd (str): The command to execute, including arguments.

        Returns:
                str: The output of the command, or an error message if the command fails.
        """
        try:
                # Split the command string into a list of arguments
                        args = shlex.split(cmd)
                        # Run the command
                        #print("CMD: " + str(args))
                        result = subprocess.run(args, capture_output=True, text=True, check=True)
                        output = result.stdout.strip()
                        #print("CMD Results:\n" + output)
                        return output

        except subprocess.CalledProcessError as e:
                return f"Error executing command: {e}"

        except FileNotFoundError:
                return "Command not found."

def create_database_if_not_exists(db_file):
        """
        Creates an SQLite database file if it doesn't already exist.

        Args:
        db_file: Path to the desired SQLite database file.
        """
        try:
                conn = sqlite3.connect(db_file)
                conn.close()
                print(f"Database '{db_file}' already exists.")
        except sqlite3.Error as e:
                if e.args[0] == 'no such file or directory':
                        conn = sqlite3.connect(db_file)
                        conn.close()
                        print(f"Database '{db_file}' created successfully.")
                else:
                        print(f"Error creating database: {e}")

def create_table(db_file):
        """
        Creates a table named 'Wifilist' in the given database connection.

        Args:
                db_file: Path to the desired SQLite database file.
        """
        try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS wifilist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DEFAULT CURRENT_TIMESTAMP,
                        bssid CHAR(17) NOT NULL,
                        frequency_mhz SMALLINT NOT NULL,
                        rssi SMALLINT NOT NULL,
                        ssid TEXT,
                        channel_bandwidth_mhz TINYINT NOT NULL,
                        latitude FLOAT NOT NULL,
                        longitude FLOAT NOT NULL,
                        accuracy INT NOT NULL,
                        provider TINYTEXT NOT NULL
        )
                """)
                conn.commit()
                conn.close()
                print("Tables created successfully.")
        except sqlite3.OperationalError as e:
                print("Failed to create tables:", e)

def insert_data(db_file, json_location, json_wifi):
        """
        Inserts sample data into the 'wifilist' table.

        Args:
        db_file: Path to the desired SQLite database file.
        json_location: Json object carrying location data
        json_wifi: Json object carry wifis data
        """
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        data = []
        for item in json_wifi:

                bssid = item["bssid"]
                frequency_mhz = item["frequency_mhz"]
                rssi = item["rssi"]
                ssid = item["ssid"]
                channel_bandwidth_mhz = item["channel_bandwidth_mhz"]

                latitude = json_location["latitude"]
                longitude = json_location["longitude"]
                accuracy = json_location["accuracy"]
                provider = json_location["provider"]

                data_line = (bssid, frequency_mhz, rssi, ssid, channel_bandwidth_mhz, latitude, longitude, accuracy, provider)
                data.append(data_line)
        #print("-"*80)
        #print(data)
        cursor.executemany("INSERT INTO wifilist (bssid, frequency_mhz, rssi, ssid, channel_bandwidth_mhz, latitude, longitude, accuracy, provider) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        conn.commit()
        conn.close()

def looking(db_file, wait_in_second):
        print(time.ctime())
        cmd_out = run_cmd("termux-location -p gps -r once")
        if cmd_out == "":
                cmd_out = run_cmd("termux-location -p gps -r updates")
                if cmd_out == "":
                        cmd_out = run_cmd("termux-location -p network -r once")
                        if cmd_out == "":
                                print("No location")
                                return
        json_out_gps = json.loads(cmd_out)
        cmd_out = run_cmd("termux-wifi-scaninfo")
        json_out_wifiscan = json.loads(cmd_out)
        insert_data(db_file, json_out_gps, json_out_wifiscan)

if __name__ == "__main__":
        db_file = "database.db"
        wait_in_second = 60*1
        create_database_if_not_exists(db_file)
        create_table(db_file)
        print_environment_info()
        ticker = threading.Event()
        looking(db_file, wait_in_second)
        while not ticker.wait(wait_in_second):
                looking(db_file, wait_in_second)
