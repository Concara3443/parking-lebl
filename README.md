# LEBL Parking Assignment System
Sistema de asignación de parkings para el aeropuerto de Barcelona El Prat (LEBL) en IVAO.

---

## Requisitos
- **Python 3.8+** (sin dependencias externas — solo librería estándar)
- Windows: doble clic en `iniciar.bat`. Si Python no está instalado, abre la Microsoft Store automáticamente.

## Archivos a distribuir
```
parking_finder.py
iniciar.bat
data/
  airlines.json
  aircraft_wingspans.json
  parkings.json
```
La carpeta `dev/` es solo para regenerar las bases de datos (requiere `pdfplumber`) y **no hace falta enviarla**.

---

## Uso

### Modo sesión (recomendado)
```
python parking_finder.py
```
El script se queda abierto. Cada consulta acumula los parkings ocupados hasta que cierras el script.

### Consulta directa (una sola consulta y sale)
```
python parking_finder.py AEA B738 LFPO
```

---

## Sintaxis de consulta

```
AEROLINEA AERONAVE ORIGEN [modificadores]
```

| Modificador | Efecto |
|-------------|--------|
| `r` | Forzar solo stands remotos |
| `s` | Forzar vuelo Schengen (anula detección automática) |
| `ns` | Forzar vuelo Non-Schengen |
| `g` | Modo GA — solo aeronave necesaria, busca en stands 01-57 |
| `c` | Modo Cargo — solo aeronave necesaria, busca en stands 141-165 |

Los modificadores pueden ir en cualquier posición: `AEA B738 r LFPO s` es válido.

### Gestión de stands
| Comando | Efecto |
|---------|--------|
| `o 242 243` | Marcar stands como ocupados manualmente |
| `x 242` | Liberar stand de la lista de ocupados |
| `clear` | Liberar todos los stands ocupados |
| `?` | Mostrar ayuda |
| `q` | Salir |

Al asignar un stand (prompt tras los resultados), ese stand **y todos sus excludes** quedan ocupados automáticamente.

---

## Zonas de parkings

| Stands | Zona | Notas |
|--------|------|-------|
| 01–57 | GA | Aviación general — solo con modificador `g` |
| 71–87 | Mantenimiento | Excluidos siempre |
| 91–96 | EJU/EZY/EZS dedicados | T2. 91-94 remotos (mixed), 95-96 gates (Schengen only) |
| 141–165 | Cargo | Solo con modificador `c` o aerolínea cargo |
| 200, 202, 200R | IBE dedicados | T1. 200R remoto (mixed), 200/202 gates (Schengen only) |
| 200–223, 270+ | T1 comercial | Mixed (Schengen y Non-Schengen) |
| 224–268 | T1 Schengen | Solo vuelos Schengen |
| 260–268 | ANY dedicados | T1 Schengen only |
| 300–425 | T1 remotos | Mixed |
| T2 | T2 comercial | Stands numerados en 60-199 área gates + remotos propios |

---

## Detección Schengen
Se detecta automáticamente por el prefijo ICAO de 2 letras del aeropuerto de origen:
- **Schengen**: BI LB LD LE LF LG LH LI LJ LK LM LO LP LS LZ EB ED EF EH EK EL EN EP ES EV EY
- **Non-Schengen conocidos**: EG EI LQ LR LT LU LW LX LY
- **Resto**: si el prefijo no está en ninguna lista, pregunta interactivamente.

---

## Aerolíneas cargo
Las siguientes aerolíneas van automáticamente a stands de cargo (141-165) sin necesitar el modificador `c`:

`DHL SWT BCS UPS FDX TAY GTI MPH DHK BOX ACS RCF VDA`

Para añadir más, editar `data/airlines.json` y poner `"XYZ": "CARGO"`.

---

## Decisiones de diseño

Esta sección existe para poder revertir decisiones fácilmente si cambia el criterio.

### 1. Ordenación: wingspan ascendente como criterio principal
**Decisión**: los stands se ordenan primero por `max_wingspan` ascendente (fit más ajustado), luego por exclusiones, luego gate antes que remoto en caso de empate.

**Motivo**: un remoto con wingspan exacto (ej. stand 420 para CRJX 24.9m) es mejor opción que un gate sobredimensionado. Refleja el principio de "categoría mínima suficiente".

**Alternativa**: priorizar siempre gates sobre remotos y ordenar wingspan dentro de cada tipo.

---

### 2. Terminal único por consulta (sin mezcla de terminales)
**Decisión**: se muestran todos los stands del terminal propio (gates + remotos combinados). Solo si no hay ninguno, se hace fallback al otro terminal.

**Motivo**: el usuario pidió explícitamente el orden: mismo terminal → otro terminal, con fallback progresivo.

**Alternativa**: mostrar siempre los dos terminales y dejar elegir.

---

### 3. Stands 224–268 son Schengen only
**Decisión**: todos los stands 224-268 (T1) son `schengen_only`.

**Motivo**: confirmado explícitamente. Los stands 200-223 y 270+ son mixed.

---

### 4. Modificador `r` fuerza remotos pero mantiene el fallback de terminal
**Decisión**: con `r`, si no hay remotos en el terminal propio, se busca en el otro terminal.

**Motivo**: consistencia con el sistema de fallback. El `r` filtra el tipo de stand, no el terminal.

---

### 5. Al asignar un stand, sus excludes también se ocupan
**Decisión**: marcar el stand asignado + todos sus `excludes` como ocupados.

**Motivo**: los excludes son incompatibilidades físicas (el avión en X bloquea Y). No tiene sentido asignar Y si X está ocupado.

**Alternativa**: solo marcar el stand asignado y gestionar excludes manualmente.

---

### 6. Las aerolíneas cargo van directo a cargo, ignorando origen y Schengen
**Decisión**: aerolíneas con `"CARGO"` en airlines.json saltan directamente a `run_query_cargo()`, ignorando origen y estado Schengen.

**Motivo**: el cargo no opera en terminales comerciales ni le aplica Schengen de la misma forma.

---

## Añadir contenido

### Nueva aerolínea
Editar `data/airlines.json`:
```json
"XYZ": "T1"   // o "T2" o "CARGO"
```

### Nueva aerolínea con stands dedicados
Editar `parking_finder.py`, diccionarios al principio:
```python
DEDICATED['XYZ']          = {'101', '102', '103'}
DEDICATED_LABEL['XYZ']    = 'XYZ DEDICATED'
DEDICATED_TERMINAL['XYZ'] = 'T1'   # o 'T2'
```

### Nueva aeronave
Editar `data/aircraft_wingspans.json`:
```json
"B39M": 35.9
```

### Wingspan de un stand
Editar `data/parkings_enhanced.json`, campo `max_wingspan` del stand correspondiente.

---

## Carpeta dev (solo para desarrolladores)
Contiene los scripts para regenerar las bases de datos desde los PDFs oficiales de LEBL:

```
python dev/build_aircraft_db.py      # regenera aircraft_wingspans.json
python dev/build_parking_db.py       # regenera parkings.json (borra excludes manuales)
python dev/scrape_incompatibilities.py  # inyecta excludes desde el PDF
```

> ⚠️ `build_parking_db.py` sobreescribe parkings.json y pierde las modificaciones manuales.
