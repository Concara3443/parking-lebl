import csv
import json
import os

CSV_PATH = 'ALL_DATA.csv'
JSON_PATH = '../data/aircraft_wingspans.json'

def update_json():
    # Load current JSON
    try:
        with open(JSON_PATH, 'r') as f:
            wingspans = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # Count of changes
    added = 0
    updated = 0
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            icao = row['icao'].strip()
            csv_wingspan = row['wingspan'].strip()
            
            if not icao or not csv_wingspan:
                continue
                
            try:
                csv_val = float(csv_wingspan)
                # Ensure it's not zero or invalid
                if csv_val <= 0:
                    continue
            except ValueError:
                continue
            
            # If ICAO not in JSON, add it
            if icao not in wingspans:
                wingspans[icao] = csv_val
                added += 1
            else:
                # If already in JSON, check if value is different
                json_val = float(wingspans[icao])
                if abs(json_val - csv_val) > 0.01:
                    # Update with CSV value as requested
                    wingspans[icao] = csv_val
                    updated += 1
                    
    # Sort JSON by key before saving
    wingspans = dict(sorted(wingspans.items()))

    # Write back
    try:
        with open(JSON_PATH, 'w') as f:
            json.dump(wingspans, f, indent=2)
        print(f"Update complete: Added {added}, Updated {updated} ICAOs.")
    except Exception as e:
        print(f"Error saving JSON: {e}")

if __name__ == "__main__":
    update_json()
