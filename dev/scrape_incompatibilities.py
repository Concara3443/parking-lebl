"""
scrape_incompatibilities.py
Extrae todas las incompatibilidades (INCOMP.) del PDF y las inyecta
en el campo 'excludes' de parkings.json.
"""
import json
import re
import os
import pdfplumber

_DEV     = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(_DEV, "LE_AD_2_LEBL_PDC_1_en.pdf")
PKG_JSON = os.path.join(_DEV, "..", "data", "parkings.json")

# Regex: inicio de fila de parking  →  "101 R2 ..."  o  "101A R2 ..."  o  "X1 R2 ..."
ROW_START = re.compile(r'^(X[123]|\d{1,3}[A-Z]?)\s+R\d+\s+\d{6}')

# Regex: extrae los IDs tras "INCOMP."
#   "INCOMP. 113, 114, X3"  →  ['113', '114', 'X3']
INCOMP_RE = re.compile(r'INCOMP\.\s*([0-9A-Z][0-9A-Z,\s]*)', re.IGNORECASE)


def extract_incompatibilities():
    """
    Devuelve dict  { parking_id: [incompatible_id, ...] }
    """
    result = {}
    current_pid = None

    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            # Solo páginas con tabla de parkings
            if 'MAX ACFT' not in text and 'PRKG' not in text:
                continue

            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # ¿Empieza una nueva fila de parking?
                m_row = ROW_START.match(line)
                if m_row:
                    current_pid = m_row.group(1).strip()

                # ¿Hay INCOMP. en esta línea?
                m_inc = INCOMP_RE.search(line)
                if m_inc and current_pid:
                    raw = m_inc.group(1)
                    # Separar por coma, limpiar espacios y caracteres raros
                    ids = [
                        x.strip()
                        for x in re.split(r'[,\s]+', raw)
                        if re.match(r'^[0-9A-Z]+$', x.strip())
                    ]
                    if ids:
                        if current_pid not in result:
                            result[current_pid] = []
                        for pid in ids:
                            if pid not in result[current_pid]:
                                result[current_pid].append(pid)

    return result


def main():
    with open(PKG_JSON, 'r', encoding='utf-8') as f:
        parkings = json.load(f)

    incomp = extract_incompatibilities()

    print(f"Incompatibilidades encontradas: {len(incomp)} parkings afectados")
    print()

    # Mostrar lo encontrado antes de aplicar
    for pid in sorted(incomp, key=lambda x: (len(x), x)):
        print(f"  {pid:6} -> INCOMP. {', '.join(incomp[pid])}")

    print()

    # Inyectar en parkings.json
    applied = 0
    not_found = []
    for pid, excl_list in incomp.items():
        if pid in parkings:
            parkings[pid]['excludes'] = excl_list
            applied += 1
        else:
            not_found.append(pid)

    with open(PKG_JSON, 'w', encoding='utf-8') as f:
        json.dump(parkings, f, indent=2)

    print(f"Aplicados : {applied} parkings actualizados en parkings.json")
    if not_found:
        print(f"No encontrados en JSON: {not_found}")


if __name__ == "__main__":
    main()
