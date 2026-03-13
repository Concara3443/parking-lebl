import csv
import json
import os

CSV_PATH = 'ALL_DATA.csv'
JSON_PATH = '../data/aircraft_wingspans.json'

def verify_wingspans():
    # Load JSON
    # Since read_file failed, I'll use the content I saw from 'cat'
    # but to be safe and autonomous, I'll read it via shell again if needed.
    # Actually I have the content in the history.
    
    # Let's try to get it via python directly since I'm running a script
    try:
        with open(JSON_PATH, 'r') as f:
            wingspans = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    missing_in_json = []
    different_value = []
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            icao = row['icao'].strip()
            csv_wingspan = row['wingspan'].strip()
            
            if not icao or not csv_wingspan:
                continue
                
            try:
                csv_val = float(csv_wingspan)
            except ValueError:
                continue
                
            if icao not in wingspans:
                missing_in_json.append(icao)
            else:
                json_val = float(wingspans[icao])
                if abs(json_val - csv_val) > 0.1: # 10cm tolerance
                    different_value.append((icao, csv_val, json_val))
                    
    # Unique missing
    missing_in_json = sorted(list(set(missing_in_json)))
    
    print(f"ICAOs missing in JSON: {len(missing_in_json)}")
    if missing_in_json:
        print(f"Example missing: {missing_in_json[:10]}")
        
    print(f"\nICAOs with different values: {len(different_value)}")
    if different_value:
        print("Example differences (ICAO, CSV, JSON):")
        for diff in different_value[:10]:
            print(diff)

if __name__ == "__main__":
    verify_wingspans()
