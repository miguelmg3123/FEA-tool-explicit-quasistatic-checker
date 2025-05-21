from flask import Flask, render_template, request, jsonify
import pandas as pd
import io # Para leer los archivos CSV en memoria
import numpy as np # Lo usaremos para 'inf' y algunas operaciones de array

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Nombres esperados para las columnas de tiempo y valor
COL_TIME = 'Time' # O el nombre que uses, ej: 'Step Time', 'X-Time'
COL_VALUE = 'Value' # O el nombre que uses, ej: 'ALLKE', 'ALLIE', 'ALLWK'


# --- Funciones Auxiliares ---

# En app.py, reemplazar la función read_csv_with_optional_header con esta:

# En app.py, dentro de la función read_csv_with_optional_header

# En app.py, reemplazar la función read_csv_with_optional_header con esta:

def read_csv_with_optional_header(file_stream, value_col_name):
    print(f"\n--- Procesando archivo para: {value_col_name} ---")
    file_content_bytes = file_stream.read()
    try:
        file_content = file_content_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        file_content = file_content_bytes.decode('utf-8', errors='replace')

    s_io_for_peek = io.StringIO(file_content)
    first_line_peek = s_io_for_peek.readline().strip()
    print(f"Primera línea detectada para heurística: '{first_line_peek}'")

    df = pd.DataFrame() # Inicializar df vacío
    
    # Intentar con separador ';' primero
    possible_separators = [';', ',']
    
    for sep_char in possible_separators:
        print(f"Intentando con separador: '{sep_char}'")
        s_io_for_pandas = io.StringIO(file_content) # Necesitamos un nuevo stream para cada intento de read_csv
        
        is_likely_text_header = False
        if first_line_peek:
            try:
                fields = first_line_peek.split(sep_char)
                if len(fields) >= 2:
                    float(fields[0]) 
                    # Para el segundo campo, tomar solo la parte antes de un posible ';' o ',' si es cabecera con descripción
                    # Esto es complicado porque el separador de descripción podría ser el mismo que el de datos
                    # Por simplicidad, si la conversión a float falla, es cabecera.
                    second_field_value_part = fields[1].split(';')[0].split(',')[0] # Tomar la parte numérica antes de cualquier descripción
                    float(second_field_value_part)
                else:
                    print(f"Heurística (sep='{sep_char}'): No hay suf. campos, asumiendo cabecera.")
                    is_likely_text_header = True
            except (ValueError, IndexError):
                print(f"Heurística (sep='{sep_char}'): Error convirtiendo primera línea, asumiendo cabecera.")
                is_likely_text_header = True
        
        print(f"Resultado heurística (sep='{sep_char}'): is_likely_text_header = {is_likely_text_header}")

        current_df = pd.DataFrame()
        try:
            if is_likely_text_header:
                print(f"Leyendo CSV con header=0, sep='{sep_char}'")
                current_df = pd.read_csv(s_io_for_pandas, sep=sep_char, header=0, usecols=[0, 1], 
                                         names=[COL_TIME, value_col_name], on_bad_lines='skip', engine='python')
            else:
                print(f"Leyendo CSV con header=None, sep='{sep_char}'")
                current_df = pd.read_csv(s_io_for_pandas, sep=sep_char, header=None, 
                                         names=[COL_TIME, value_col_name], on_bad_lines='skip', engine='python')
            
            # Verificar si el DataFrame tiene las columnas esperadas y no está completamente vacío
            if not current_df.empty and COL_TIME in current_df.columns and value_col_name in current_df.columns:
                # Intentar conversión a numérico
                temp_time_col = pd.to_numeric(current_df[COL_TIME], errors='coerce')
                temp_value_col = pd.to_numeric(current_df[value_col_name], errors='coerce')
                
                # Si la mayoría de los valores se pudieron convertir, este es probablemente el separador correcto
                if temp_time_col.notna().sum() > (len(current_df) / 2) and \
                   temp_value_col.notna().sum() > (len(current_df) / 2) and \
                   temp_time_col.notna().sum() > 0 : # Asegurarse que al menos una fila es válida
                    print(f"Separador '{sep_char}' parece correcto.")
                    df = current_df.copy() # Usar este df
                    # Aplicar las conversiones finales
                    df[COL_TIME] = temp_time_col
                    df[value_col_name] = temp_value_col
                    break # Salir del bucle de separadores
            print(f"DataFrame DESPUÉS de pd.read_csv (sep='{sep_char}'):\n{current_df.head()}")

        except Exception as e:
            print(f"Error en pd.read_csv (sep='{sep_char}'): {e}")
            continue # Probar con el siguiente separador

    if df.empty:
        print("No se pudo parsear el CSV con los separadores probados o resultó vacío.")
        return pd.DataFrame(columns=[COL_TIME, value_col_name]) # Devolver DF vacío estructurado

    print(f"DataFrame ANTES de dropna (primeras 5 filas):\n{df.head()}")
    print(f"Tipos de datos ANTES de dropna:\n{df.dtypes}")
    print(f"Número de NaNs en COL_TIME: {df[COL_TIME].isna().sum()}")
    print(f"Número de NaNs en {value_col_name}: {df[value_col_name].isna().sum()}")

    df.dropna(subset=[COL_TIME, value_col_name], inplace=True)
    print(f"DataFrame DESPUÉS de dropna (primeras 5 filas):\n{df.head()}")
    print(f"Tamaño del DataFrame final: {df.shape}")
    
    if df.empty: # Comprobación adicional por si dropna lo vació todo
        print("DataFrame vacío después de dropna.")
        return pd.DataFrame(columns=[COL_TIME, value_col_name])

    return df.sort_values(by=COL_TIME).reset_index(drop=True)
    print(f"\n--- Procesando archivo para: {value_col_name} ---") # NUEVO PRINT
    file_content_bytes = file_stream.read()
    try:
        file_content = file_content_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        file_content = file_content_bytes.decode('utf-8', errors='replace')

    s_io = io.StringIO(file_content)
    
    # NUEVO: Imprimir las primeras líneas del contenido del archivo tal como lo ve Python
    print("Primeras ~500 caracteres del archivo:")
    s_io.seek(0) # Asegurarse de estar al inicio para leer
    print(s_io.read(500))
    s_io.seek(0) # Resetear para la lógica de detección de cabecera

    first_line_peek = s_io.readline().strip()
    s_io.seek(0) 
    print(f"Primera línea detectada para heurística: '{first_line_peek}'") # NUEVO PRINT

    is_likely_text_header = False
    if first_line_peek:
        try:
            fields = first_line_peek.split(';')
            if len(fields) >= 2:
                float(fields[0]) 
                second_field_data_part = fields[1] 
                float(second_field_data_part) 
            else:
                print("Heurística: No hay suficientes campos en la primera línea, asumiendo cabecera.") # NUEVO PRINT
                is_likely_text_header = True
        except ValueError:
            print("Heurística: ValueError al convertir primera línea a float, asumiendo cabecera.") # NUEVO PRINT
            is_likely_text_header = True
        except IndexError:
            print("Heurística: IndexError en primera línea, asumiendo cabecera.") # NUEVO PRINT
            is_likely_text_header = True 
    
    print(f"Resultado de heurística de cabecera: is_likely_text_header = {is_likely_text_header}") # NUEVO PRINT

    df = pd.DataFrame() # Inicializar df vacío
    if is_likely_text_header:
        print("Intentando leer CSV con header=0, sep=';'") # NUEVO PRINT
        try:
            df = pd.read_csv(s_io, sep=';', header=0, usecols=[0, 1], names=[COL_TIME, value_col_name],
                             on_bad_lines='skip')
        except Exception as e:
            print(f"Error en pd.read_csv (con header): {e}") # NUEVO PRINT
    else:
        print("Intentando leer CSV con header=None, sep=';'") # NUEVO PRINT
        try:
            df = pd.read_csv(s_io, sep=';', header=None, names=[COL_TIME, value_col_name],
                             on_bad_lines='skip')
        except Exception as e:
            print(f"Error en pd.read_csv (sin header): {e}") # NUEVO PRINT

    print(f"DataFrame DESPUÉS de pd.read_csv (primeras 5 filas):\n{df.head()}") # NUEVO PRINT
    print(f"Tipos de datos DESPUÉS de pd.read_csv:\n{df.dtypes}") # NUEVO PRINT

    df[COL_TIME] = pd.to_numeric(df[COL_TIME], errors='coerce')
    df[value_col_name] = pd.to_numeric(df[value_col_name], errors='coerce')
    
    print(f"DataFrame DESPUÉS de to_numeric (primeras 5 filas):\n{df.head()}") # NUEVO PRINT
    print(f"Tipos de datos DESPUÉS de to_numeric:\n{df.dtypes}") # NUEVO PRINT
    print(f"Número de NaNs en COL_TIME: {df[COL_TIME].isna().sum()}") # NUEVO PRINT
    print(f"Número de NaNs en {value_col_name}: {df[value_col_name].isna().sum()}") # NUEVO PRINT

    df.dropna(subset=[COL_TIME, value_col_name], inplace=True)
    print(f"DataFrame DESPUÉS de dropna (primeras 5 filas):\n{df.head()}") # NUEVO PRINT
    print(f"Tamaño del DataFrame final: {df.shape}") # NUEVO PRINT
    
    return df.sort_values(by=COL_TIME).reset_index(drop=True)
    # Leer todo el contenido del stream como bytes
    file_content_bytes = file_stream.read()
    try:
        # Intentar decodificar como utf-8-sig (maneja BOM si está) o utf-8
        file_content = file_content_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        file_content = file_content_bytes.decode('utf-8', errors='replace')

    s_io = io.StringIO(file_content)
    
    first_line_peek = s_io.readline().strip()
    s_io.seek(0) 

    is_likely_text_header = False
    if first_line_peek:
        try:
            # Intentar convertir los dos primeros campos (separados por punto y coma) a float.
            fields = first_line_peek.split(';') # <--- CAMBIO AQUÍ: separador ;
            if len(fields) >= 2:
                float(fields[0]) 
                # Para el segundo campo, tomar solo la parte antes de un posible ';' adicional (si lo hubiera en la cabecera)
                # Aunque en este formato parece que el segundo campo de la cabecera es solo "Energy(J)"
                second_field_data_part = fields[1] # Asumimos que el segundo campo es directo
                float(second_field_data_part) 
            else:
                is_likely_text_header = True
        except ValueError:
            is_likely_text_header = True
        except IndexError:
            is_likely_text_header = True 

    if is_likely_text_header:
        # El separador es ';'
        df = pd.read_csv(s_io, sep=';', header=0, usecols=[0, 1], names=[COL_TIME, value_col_name],
                         on_bad_lines='skip') # <--- CAMBIO AQUÍ: sep=';'
    else:
        # El separador es ';'
        df = pd.read_csv(s_io, sep=';', header=None, names=[COL_TIME, value_col_name],
                         on_bad_lines='skip') # <--- CAMBIO AQUÍ: sep=';'

    df[COL_TIME] = pd.to_numeric(df[COL_TIME], errors='coerce')
    df[value_col_name] = pd.to_numeric(df[value_col_name], errors='coerce')
    
    df.dropna(subset=[COL_TIME, value_col_name], inplace=True)
    
    return df.sort_values(by=COL_TIME).reset_index(drop=True)
    # Leer todo el contenido del stream como bytes
    file_content_bytes = file_stream.read()
    try:
        # Intentar decodificar como utf-8-sig para manejar BOM automáticamente
        file_content = file_content_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        # Fallback a utf-8 si utf-8-sig falla (ej. si no hay BOM o es otra codificación compatible con utf-8)
        file_content = file_content_bytes.decode('utf-8', errors='replace')

    s_io = io.StringIO(file_content)
    
    # Leer la primera línea para inspección, luego resetear el stream para Pandas
    first_line_peek = s_io.readline().strip()
    s_io.seek(0) # Resetear para que Pandas pueda leer desde el inicio

    is_likely_text_header = False
    if first_line_peek:
        try:
            # Intentar convertir los dos primeros campos (separados por coma) a float.
            # Si esto falla, es probable que sea una cabecera de texto.
            fields = first_line_peek.split(',')
            if len(fields) >= 2:
                float(fields[0]) # Intenta convertir el primer campo (tiempo)
                # Para el segundo campo, tomar solo la parte antes de un posible ';'
                second_field_data_part = fields[1].split(';')[0]
                float(second_field_data_part) # Intenta convertir el segundo campo (valor)
            else:
                # No hay suficientes campos para ser datos típicos, asumir cabecera
                is_likely_text_header = True
        except ValueError:
            # La conversión a float falló, es una cabecera de texto
            is_likely_text_header = True
        except IndexError:
            # No hay suficientes campos (ej. línea vacía o solo un campo)
            is_likely_text_header = True # O podría ser un error de formato, pero tratémoslo como posible cabecera

    if is_likely_text_header:
        # La primera línea es una cabecera de texto.
        df = pd.read_csv(s_io, sep=',', header=0, usecols=[0, 1], names=[COL_TIME, value_col_name],
                         on_bad_lines='skip')
    else:
        # La primera línea son datos (o el archivo está vacío/formato inesperado).
        df = pd.read_csv(s_io, sep=',', header=None, names=[COL_TIME, value_col_name],
                         on_bad_lines='skip')

    # Asegurarse de que las columnas de tiempo y valor sean numéricas
    df[COL_TIME] = pd.to_numeric(df[COL_TIME], errors='coerce')
    df[value_col_name] = pd.to_numeric(df[value_col_name], errors='coerce')
    
    df.dropna(subset=[COL_TIME, value_col_name], inplace=True)
    
    return df.sort_values(by=COL_TIME).reset_index(drop=True)


def find_first_time_stable_condition(df, time_col, value_col, condition_func, look_from_end=True):
    """
    Encuentra el primer tiempo desde el cual una condición se cumple ESTABLEMENTE hasta el final (o inicio).
    """
    if df.empty:
        return None

    if look_from_end:
        last_unstable_idx = -1
        for i in range(len(df) - 1, -1, -1):
            if not condition_func(df[value_col].iloc[i]):
                last_unstable_idx = i
                break
        
        if last_unstable_idx == -1:
            return df[time_col].iloc[0]
        elif last_unstable_idx == len(df) - 1:
            return None 
        else:
            return df[time_col].iloc[last_unstable_idx + 1]
    else: 
        for i in range(len(df)):
            if condition_func(df[value_col].iloc[i]):
                return df[time_col].iloc[i]
        return None


# --- Rutas de Flask ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_data():
    if 'allke_csv' not in request.files or \
       'allie_csv' not in request.files or \
       'allwk_csv' not in request.files:
        return jsonify({"message": "Faltan uno o más archivos CSV."}), 400

    file_allke = request.files['allke_csv']
    file_allie = request.files['allie_csv']
    file_allwk = request.files['allwk_csv']

    if file_allke.filename == '' or file_allie.filename == '' or file_allwk.filename == '':
        return jsonify({"message": "Nombres de archivo vacíos."}), 400

    try:
        df_allke = read_csv_with_optional_header(file_allke.stream, 'ALLKE')
        df_allie = read_csv_with_optional_header(file_allie.stream, 'ALLIE')
        df_allwk = read_csv_with_optional_header(file_allwk.stream, 'ALLWK')
        
        if df_allke.empty or df_allie.empty or df_allwk.empty:
             return jsonify({"message": "Uno o más archivos CSV están vacíos o no se pudieron procesar."}), 400

        # --- 1. Alinear datos de ALLKE y ALLIE por tiempo y calcular RI ---
        df_energy = pd.merge(df_allke, df_allie, on=COL_TIME, how='outer').sort_values(by=COL_TIME)
        df_energy['ALLKE'] = df_energy['ALLKE'].interpolate(method='linear')
        df_energy['ALLIE'] = df_energy['ALLIE'].interpolate(method='linear')
        df_energy.dropna(subset=['ALLKE', 'ALLIE'], inplace=True)

        if df_energy.empty:
            return jsonify({"message": "No se pudieron alinear los datos de energía o resultaron vacíos."}), 400
        
        df_energy['RI'] = np.where(df_energy['ALLIE'] > 1e-9, (df_energy['ALLKE'] / df_energy['ALLIE']) * 100, np.nan)

        # --- 2. Calcular RET ---
        if df_allwk.empty or df_allwk[COL_TIME].nunique() == 0:
            allwk_final_value = 0
        else:
            allwk_final_value = df_allwk.iloc[-1]['ALLWK']
        
        if abs(allwk_final_value) < 1e-9:
            df_allwk['RET'] = 0.0
        else:
            df_allwk['RET'] = (df_allwk['ALLWK'] / allwk_final_value) * 100
        
        # --- 3. Determinar Tiempos Críticos ---
        time_RI_estable_menor_5pct = find_first_time_stable_condition(df_energy, COL_TIME, 'RI', lambda x: x < 5.0 if pd.notna(x) else False)
        time_RI_estable_menor_1pct = find_first_time_stable_condition(df_energy, COL_TIME, 'RI', lambda x: x < 1.0 if pd.notna(x) else False)

        time_RET_mayor_igual_1pct = find_first_time_stable_condition(df_allwk, COL_TIME, 'RET', lambda x: x >= 1.0 if pd.notna(x) else False, look_from_end=False)
        time_RET_mayor_igual_5pct = find_first_time_stable_condition(df_allwk, COL_TIME, 'RET', lambda x: x >= 5.0 if pd.notna(x) else False, look_from_end=False)

        # --- 4. Lógica de Decisión ---
        final_decision_text = "NO ACEPTABLE (Condición inicial no cumplida). REESCALAR TIEMPO Y MASA."
        porcentaje_tiempo_estable_RI_5pct_val = 0.0
        total_time_simulacion_energia = df_energy[COL_TIME].iloc[-1] if not df_energy.empty else 0

        if time_RI_estable_menor_5pct is not None and total_time_simulacion_energia > 0:
            tiempo_restante_RI_estable_5pct = total_time_simulacion_energia - time_RI_estable_menor_5pct
            porcentaje_tiempo_estable_RI_5pct_val = (tiempo_restante_RI_estable_5pct / total_time_simulacion_energia) * 100
            
            if porcentaje_tiempo_estable_RI_5pct_val >= 60:
                comp_time_RI_1pct = time_RI_estable_menor_1pct if time_RI_estable_menor_1pct is not None else np.inf
                comp_time_RET_1pct = time_RET_mayor_igual_1pct if time_RET_mayor_igual_1pct is not None else np.inf
                comp_time_RET_5pct = time_RET_mayor_igual_5pct if time_RET_mayor_igual_5pct is not None else np.inf
                comp_time_RI_5pct = time_RI_estable_menor_5pct 

                if comp_time_RI_1pct < comp_time_RET_1pct:
                    final_decision_text = "PERFECTO. El cálculo está completamente en régimen cuasi-estático (RI < 1% estable antes de que el trabajo alcance el 1%)."
                elif comp_time_RI_1pct < comp_time_RET_5pct:
                    final_decision_text = "MUY BUENO. El cálculo está lo suficiente en régimen cuasi-estático (RI < 1% estable antes de que el trabajo alcance el 5%)."
                elif comp_time_RI_5pct < comp_time_RET_1pct:
                    final_decision_text = (f"BUENO. El cálculo está en régimen cuasi-estático (RI < 5% estable antes de que el trabajo alcance el 1%). "
                                           f"REVISAR: Verificar que las variables de interés (tensión, deformación, contactos) no son relevantes antes del tiempo: {comp_time_RI_5pct:.3f} s.")
                elif comp_time_RI_5pct < comp_time_RET_5pct:
                    final_decision_text = (f"ACEPTABLE. El cálculo está ajustado en régimen cuasi-estático (RI < 5% estable antes de que el trabajo alcance el 5%). "
                                           f"REVISAR: Verificar que las variables de interés (tensión, deformación, contactos) no son relevantes antes del tiempo: {comp_time_RI_5pct:.3f} s.")
                else:
                    final_decision_text = "NO ACEPTABLE. Aunque el RI < 5% se mantiene más del 60% del tiempo, la relación con el inicio del trabajo no es adecuada. REESCALAR TIEMPO Y MASA."
            else: 
                final_decision_text = "CÁLCULO NO ENTRA EN RÉGIMEN CUASI-ESTÁTICO EL TIEMPO SUFICIENTE (RI < 5% establemente por menos del 60% del tiempo total). REESCALAR TIEMPO Y MASA."
        else: 
            final_decision_text = "CÁLCULO NO ENTRA EN RÉGIMEN CUASI-ESTÁTICO NUNCA (RI siempre >= 5% o no se pudo determinar). REESCALAR TIEMPO Y MASA."

        # --- 5. Preparar Datos para la Respuesta JSON ---
        def format_series_for_json(df, time_col, value_col):
            if df.empty or value_col not in df.columns:
                return {'x': [], 'y': []}
            return {
                'x': df[time_col].tolist(),
                'y': df[value_col].where(pd.notna(df[value_col]), None).tolist()
            }

        graph_data = {
            'ALLKE': format_series_for_json(df_energy, COL_TIME, 'ALLKE'),
            'ALLIE': format_series_for_json(df_energy, COL_TIME, 'ALLIE'),
            'RI': format_series_for_json(df_energy, COL_TIME, 'RI'),
            'ALLWK': format_series_for_json(df_allwk, COL_TIME, 'ALLWK'),
            'RET': format_series_for_json(df_allwk, COL_TIME, 'RET'),
        }

        def format_time_value(time_val):
            return f"{time_val:.3f} s" if time_val is not None and time_val != np.inf else "N/A"
        
        def format_percentage_value(perc_val):
             return f"{perc_val:.2f}%" if perc_val is not None else "N/A"

        summary_table_data = {
            "time_RI_estable_menor_5pct": format_time_value(time_RI_estable_menor_5pct),
            "time_RI_estable_menor_1pct": format_time_value(time_RI_estable_menor_1pct),
            "time_RET_mayor_igual_1pct": format_time_value(time_RET_mayor_igual_1pct),
            "time_RET_mayor_igual_5pct": format_time_value(time_RET_mayor_igual_5pct),
            "porcentaje_tiempo_estable_RI_5pct": format_percentage_value(porcentaje_tiempo_estable_RI_5pct_val if time_RI_estable_menor_5pct is not None else None),
        }

        return jsonify({
            "message": "Análisis completado.",
            "graph_data": graph_data,
            "summary_table": summary_table_data,
            "final_decision_text": final_decision_text
        })

    except pd.errors.EmptyDataError:
        return jsonify({"message": "Uno de los archivos CSV está vacío o tiene un formato incorrecto."}), 400
    except pd.errors.ParserError:
        return jsonify({"message": "Error al parsear uno de los archivos CSV. Verifica el formato."}), 400
    except KeyError as e:
        return jsonify({"message": f"Error: Falta una columna esperada en un CSV o nombre incorrecto: {e}"}), 400
    except Exception as e:
        app.logger.error(f"Error inesperado durante el análisis: {e}", exc_info=True)
        return jsonify({"message": f"Error inesperado durante el análisis: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)