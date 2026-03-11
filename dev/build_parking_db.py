"""
build_parking_db.py
Parses LE_AD_2_LEBL_PDC_1_en.pdf and produces parkings.json
Uses aircraft_wingspans.json to resolve max_wingspan values.
"""
import json
import re
import os
import pdfplumber

_DEV  = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.join(_DEV, "..", "data")

PDF_PATH    = os.path.join(_DEV,  "LE_AD_2_LEBL_PDC_1_en.pdf")
WINGSPAN_DB = os.path.join(_DATA, "aircraft_wingspans.json")
OUTPUT      = os.path.join(_DATA, "parkings.json")


def get_numeric_id(pid):
    """Extract numeric part from parking ID string. '124A' -> 124, '200R' -> 200."""
    m = re.match(r'^(\d+)', str(pid))
    return int(m.group(1)) if m else -1


def classify_parking(pid):
    """
    Returns (terminal, schengen_type) for a parking ID.
    schengen_type: 'ga', 'maintenance', 'eju_ezy_ezs',
                   'schengen_only', 'non_schengen_only', 'mixed', 'ibe_dedicated'
    """
    pid = str(pid).strip()
    n = get_numeric_id(pid)

    # T2 (01–185)
    if (1 <= n <= 185) or pid in ('X1', 'X2', 'X3'):
        terminal = 'T2'
        if 1 <= n <= 57:
            return (terminal, 'ga')
        elif 71 <= n <= 87:
            return (terminal, 'maintenance')
        elif 91 <= n <= 95:
            return (terminal, 'eju_ezy_ezs')
        elif 124 <= n <= 129:
            return (terminal, 'non_schengen_only')
        elif 131 <= n <= 185:
            return (terminal, 'mixed')
        else:
            return (terminal, 'schengen_only')

    # T1 (200+)
    if n >= 200 or pid == '200R':
        terminal = 'T1'
        if pid in ('200', '202', '200R'):
            return (terminal, 'ibe_dedicated')
        elif 224 <= n <= 260:
            return (terminal, 'schengen_only')
        elif pid == '247' or (300 <= n <= 342) or (400 <= n <= 425):
            return (terminal, 'mixed')
        else:
            return (terminal, 'mixed')

    return ('unknown', 'mixed')


def find_max_acft_column(header_row):
    """Find the column index containing 'MAX ACFT' in a header row."""
    if not header_row:
        return None
    for i, cell in enumerate(header_row):
        if cell and re.search(r'MAX\s*ACFT', str(cell), re.IGNORECASE):
            return i
    return None


def find_prkg_column(header_row):
    """Find the column index containing 'PRKG' in a header row."""
    if not header_row:
        return None
    for i, cell in enumerate(header_row):
        if cell and re.search(r'PRKG', str(cell), re.IGNORECASE):
            return i
    return None


def clean_cell(val):
    """Strip and normalize a cell value."""
    if val is None:
        return None
    return str(val).strip().replace('\n', ' ').replace('  ', ' ').strip()


def parse_pdf(wingspan_db):
    """Parse PDF for parking data. Returns dict: pid -> {max_acft, max_wingspan}."""
    parkings = {}

    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            if 'MAX ACFT' not in text and 'PRKG' not in text:
                continue

            table = page.extract_table()
            if table:
                # Find header row (contains PRKG and MAX ACFT)
                header_idx = None
                prkg_col = None
                acft_col = None

                for i, row in enumerate(table):
                    if row is None:
                        continue
                    pc = find_prkg_column(row)
                    ac = find_max_acft_column(row)
                    if pc is not None and ac is not None:
                        header_idx = i
                        prkg_col = pc
                        acft_col = ac
                        break

                if header_idx is not None:
                    for row in table[header_idx + 1:]:
                        if not row or len(row) <= max(prkg_col, acft_col):
                            continue
                        pid = clean_cell(row[prkg_col])
                        max_acft = clean_cell(row[acft_col])

                        if not pid or pid in ('PRKG', '-', ''):
                            continue
                        if not max_acft or max_acft in ('-', ''):
                            continue

                        # Skip rows that look like headers or page notes
                        if re.search(r'[a-z]{4,}', pid):
                            continue

                        # Normalize: take first token if multi-value cell
                        max_acft_clean = max_acft.split()[0] if max_acft else max_acft

                        parkings[pid] = max_acft_clean
                    continue

            # Fallback: regex on raw text
            # Pattern: lines like "  101  ...  A332  ..."
            for line in text.split('\n'):
                # Match: starts with parking number, ends with ICAO type code
                m = re.match(
                    r'^\s*(\d{1,3}[A-Z]?)\s+.*?([A-Z][A-Z0-9]{2,3})\s*$',
                    line
                )
                if m:
                    pid_candidate = m.group(1)
                    acft_candidate = m.group(2)
                    if pid_candidate not in parkings:
                        parkings[pid_candidate] = acft_candidate

    return parkings


def main():
    if not os.path.exists(WINGSPAN_DB):
        print("ERROR: aircraft_wingspans.json not found. Run build_aircraft_db.py first.")
        return

    with open(WINGSPAN_DB, 'r', encoding='utf-8') as f:
        wingspan_db = json.load(f)

    raw = parse_pdf(wingspan_db)
    print(f"Raw parkings parsed from PDF: {len(raw)}")

    resolved = 0
    unknown = 0
    result = {}

    for pid, max_acft in sorted(raw.items(), key=lambda x: (get_numeric_id(x[0]), x[0])):
        terminal, schengen = classify_parking(pid)
        ws = wingspan_db.get(max_acft, None)

        if ws is not None:
            resolved += 1
        else:
            unknown += 1

        result[pid] = {
            "max_acft": max_acft,
            "max_wingspan": ws,
            "terminal": terminal,
            "schengen": schengen,
            "excludes": []
        }

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"parkings.json created.")
    print(f"  Total parkings  : {len(result)}")
    print(f"  Wingspan resolved: {resolved}")
    print(f"  Wingspan unknown : {unknown}")
    if unknown > 0:
        unknown_list = [p for p, d in result.items() if d['max_wingspan'] is None]
        print(f"  Unknown types   : {', '.join(unknown_list[:20])}")
    print()
    print("NEXT STEP: Manually fill 'excludes' arrays in parkings.json")
    print("  Each parking's 'excludes' lists other parking IDs that are blocked")
    print("  when this parking is occupied (adjacency conflicts).")


if __name__ == "__main__":
    main()
