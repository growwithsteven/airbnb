import sqlite3
import csv
import os
import sys

def normalize_row(row):
    """Convert all values to string, lowercase keys, strip whitespace"""
    normalized = {}
    for k, v in row.items():
        val = str(v) if v is not None else ""
        if val == "None" or val == "nan":
            val = ""
        normalized[str(k).lower()] = val.strip()
    return normalized

def main():
    db_path = "airbnb.db"
    sas_output_dir = "sas_output"

    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        sys.exit(1)

    if not os.path.exists(sas_output_dir):
        print(f"Directory '{sas_output_dir}' not found.")
        print(f"Please create '{sas_output_dir}' directory and place the exported SAS CSV files in it.")
        print(f"Example: {sas_output_dir}/HOST.csv, {sas_output_dir}/LISTING.csv")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = [row[0] for row in cursor.fetchall()]

    all_passed = True

    print("=" * 50)
    print("SAS vs Python (SQLite) Data Parity Check (Standard Library)")
    print("=" * 50)

    for table in tables:
        csv_path = os.path.join(sas_output_dir, f"{table}.csv")
        
        print(f"Checking table: {table.ljust(30)}", end="")
        
        if not os.path.exists(csv_path):
            csv_path_lower = os.path.join(sas_output_dir, f"{table.lower()}.csv")
            if os.path.exists(csv_path_lower):
                csv_path = csv_path_lower
            else:
                print("[SKIPPED] - CSV not found")
                continue

        try:
            # Load Python SQLite data
            cursor.execute(f"SELECT * FROM {table}")
            py_rows = [normalize_row(dict(row)) for row in cursor.fetchall()]
            
            # Load SAS CSV data
            sas_rows = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sas_rows.append(normalize_row(row))
            
            if len(py_rows) != len(sas_rows):
                print(f"[FAIL] - Row count mismatch: Python {len(py_rows)} vs SAS {len(sas_rows)}")
                all_passed = False
                continue

            # Sort both to ignore order differences
            # Sort by all keys values combined
            def sort_key(r):
                return tuple(r.get(k, "") for k in sorted(r.keys()))

            py_rows_sorted = sorted(py_rows, key=sort_key)
            sas_rows_sorted = sorted(sas_rows, key=sort_key)

            # Compare
            mismatch_found = False
            for i, (py_r, sas_r) in enumerate(zip(py_rows_sorted, sas_rows_sorted)):
                if py_r != sas_r:
                    print(f"\n[FAIL] - Data mismatch at sorted row {i}")
                    print(f"Python: {py_r}")
                    print(f"SAS   : {sas_r}")
                    mismatch_found = True
                    all_passed = False
                    break
            
            if not mismatch_found:
                print("[PASS]")
            
        except Exception as e:
            print(f"[ERROR] - {str(e)}")
            all_passed = False

    conn.close()

    print("=" * 50)
    if all_passed:
        print("All tested tables MATCH perfectly! 🎉")
    else:
        print("Some tables FAILED parity check. Please inspect the differences.")

if __name__ == "__main__":
    main()
