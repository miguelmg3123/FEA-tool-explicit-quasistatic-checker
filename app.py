from flask import Flask, render_template, request, jsonify
import pandas as pd
import io # Para leer los archivos CSV en memoria
import numpy as np # Lo usaremos para 'inf' y algunas operaciones de array

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Nombres esperados para las columnas de tiempo y valor
# Asumimos que la primera columna es tiempo y la segunda el valor.
# Si los CSVs tienen cabeceras con nombres específicos, ajústalos aquí o en la lectura.
COL_TIME = 'Time' # O el nombre que uses, ej: 'Step Time', 'X-Time'
COL_VALUE = 'Value' # O el nombre que uses, ej: 'ALLKE', 'ALLIE', 'ALLWK'

def find_first_time_stable_condition(df, time_col, value_col, condition_func, look_from_end=True):
    """
    Encuentra el primer tiempo desde el cual una condición se cumple ESTABLEMENTE hasta el final (o inicio).
    
    Args:
        df (pd.DataFrame): DataFrame con columnas de tiempo y valor.
        time_col (str): Nombre de la columna de tiempo.
        value_col (str): Nombre de la columna de valor.
        condition_func (function): Función que toma un valor y devuelve True si la condición se cumple.
        look_from_end (bool): Si True, busca estabilidad desde el final hacia atrás. 
                              Si False, busca desde el inicio hacia adelante (para condiciones como >= X%).
    Returns:
        float or None: El tiempo si se encuentra, sino None.
    """
    if df.empty:
        return None

    if look_from_end:
        # Iterar desde el final para encontrar el primer punto donde la condición NO se cumple
        # El punto estable será el siguiente a ese.
        last_unstable_idx = -1
        for i in range(len(df) - 1, -1, -1):
            if not condition_func(df[value_col].iloc[i]):
                last_unstable_idx = i
                break
        
        if last_unstable_idx == -1: # Condición siempre cumplida
            return df[time_col].iloc[0]
        elif last_unstable_idx == len(df) - 1: # Condición nunca cumplida de forma estable al final
            return None 
        else: # Condición se cumple establemente desde el siguiente índice
            return df[time_col].iloc[last_unstable_idx + 1]
    else: # look_from_start (para condiciones como RET >= X%)
        for i in range(len(df)):
            if condition_func(df[value_col].iloc[i]):
                return df[time_col].iloc[i]
        return None


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
        # Leer CSVs. Asumimos que no tienen cabecera o que la primera fila es la cabecera.
        # Y que la primera columna es tiempo, la segunda es valor.
        # Si tus CSV tienen cabeceras con nombres fijos, usa:
        # df_allke = pd.read_csv(io.StringIO(file_allke.read().decode('utf-8')), names=[COL_TIME, 'ALLKE'], header=0 si hay cabecera o None si no)
        # Por simplicidad, asumiremos que podemos referirnos a las columnas por índice 0 y 1 si no tienen nombres estándar
        # O mejor, asignamos nombres al leer si no hay cabecera:
        
        # Intentar detectar si hay cabecera o no por el tipo de la primera fila, primera columna
        # Esto es una heurística, puede no ser perfecto
        # En app.py, reemplazar la función read_csv_with_optional_header con esta:
def read_csv_with_optional_header(file_stream, value_col_name):
    # Leer todo el contenido del stream como bytes
    file_content_bytes = file_stream.read()
    try:
        # Intentar decodificar como utf-8-sig para manejar BOM automáticamente
        file_content = file_content_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        # Fallback a utf-8 si utf-8-sig falla (ej. si no hay BOM o es otra codificación compatible con utf-8)
        file_content = file_content_bytes.decode('utf-8', errors='replace') # errors='replace' para evitar fallos por caracteres extraños

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
        # Leemos usando header=0 para que Pandas la use, pero solo tomamos las 2 primeras columnas
        # y luego les asignamos nuestros nombres estandarizados.
        df = pd.read_csv(s_io, sep=',', header=0, usecols=[0, 1], names=[COL_TIME, value_col_name],
                         on_bad_lines='skip') # Opcional: 'skip' para ignorar líneas malformadas
    else:
        # La primera línea son datos (o el archivo está vacío/formato inesperado).
        # Leemos sin cabecera desde el principio y asignamos nombres.
        df = pd.read_csv(s_io, sep=',', header=None, names=[COL_TIME, value_col_name],
                         on_bad_lines='skip')

    # Asegurarse de que las columnas de tiempo y valor sean numéricas
    df[COL_TIME] = pd.to_numeric(df[COL_TIME], errors='coerce')
    df[value_col_name] = pd.to_numeric(df[value_col_name], errors='coerce')
    
    # Eliminar filas donde la conversión a numérico falló para las columnas esenciales
    # o si alguna de estas columnas cruciales es NaN por otra razón (ej. línea vacía parseada).
    df.dropna(subset=[COL_TIME, value_col_name], inplace=True)
    
    # Ordenar por tiempo y resetear el índice
    return df.sort_values(by=COL_TIME).reset_index(drop=True)


        df_allke = read_csv_with_optional_header(file_allke.stream, 'ALLKE')
        df_allie = read_csv_with_optional_header(file_allie.stream, 'ALLIE')
        df_allwk = read_csv_with_optional_header(file_allwk.stream, 'ALLWK')
        
        if df_allke.empty or df_allie.empty or df_allwk.empty:
             return jsonify({"message": "Uno o más archivos CSV están vacíos o no se pudieron procesar."}), 400


        # --- 1. Alinear datos de ALLKE y ALLIE por tiempo y calcular RI ---
        # Usar merge externo para mantener todos los tiempos y luego interpolar
        df_energy = pd.merge(df_allke, df_allie, on=COL_TIME, how='outer').sort_values(by=COL_TIME)
        # Interpolar valores NaN que puedan surgir del merge
        df_energy['ALLKE'] = df_energy['ALLKE'].interpolate(method='linear')
        df_energy['ALLIE'] = df_energy['ALLIE'].interpolate(method='linear')
        df_energy.dropna(subset=['ALLKE', 'ALLIE'], inplace=True) # Eliminar si aún hay NaNs (ej. al principio/final)

        if df_energy.empty:
            return jsonify({"message": "No se pudieron alinear los datos de energía o resultaron vacíos."}), 400
        
        # Evitar división por cero o valores muy pequeños/negativos en ALLIE para RI
        df_energy['RI'] = np.where(df_energy['ALLIE'] > 1e-9, (df_energy['ALLKE'] / df_energy['ALLIE']) * 100, np.nan)
        # df_energy.dropna(subset=['RI'], inplace=True) # Opcional: quitar NaNs de RI si ALLIE fue 0


        # --- 2. Calcular RET ---
        if df_allwk.empty or df_allwk[COL_TIME].nunique() == 0: # Si no hay datos de trabajo
            allwk_final_value = 0
        else:
            allwk_final_value = df_allwk.iloc[-1]['ALLWK']
        
        if abs(allwk_final_value) < 1e-9: # Evitar división por cero si el trabajo final es casi nulo
            df_allwk['RET'] = 0.0
        else:
            df_allwk['RET'] = (df_allwk['ALLWK'] / allwk_final_value) * 100
        
        # --- 3. Determinar Tiempos Críticos ---
        # RI (Ratio Inercial)
        time_RI_estable_menor_5pct = find_first_time_stable_condition(df_energy, COL_TIME, 'RI', lambda x: x < 5.0 if pd.notna(x) else False)
        time_RI_estable_menor_1pct = find_first_time_stable_condition(df_energy, COL_TIME, 'RI', lambda x: x < 1.0 if pd.notna(x) else False)

        # RET (Ratio Evolución Trabajo)
        time_RET_mayor_igual_1pct = find_first_time_stable_condition(df_allwk, COL_TIME, 'RET', lambda x: x >= 1.0 if pd.notna(x) else False, look_from_end=False)
        time_RET_mayor_igual_5pct = find_first_time_stable_condition(df_allwk, COL_TIME, 'RET', lambda x: x >= 5.0 if pd.notna(x) else False, look_from_end=False)

        # --- 4. Lógica de Decisión ---
        final_decision_text = "NO ACEPTABLE (Condición inicial no cumplida). REESCALAR TIEMPO Y MASA." # Default
        porcentaje_tiempo_estable_RI_5pct_val = 0.0

        total_time_simulacion_energia = df_energy[COL_TIME].iloc[-1] if not df_energy.empty else 0

        if time_RI_estable_menor_5pct is not None and total_time_simulacion_energia > 0:
            tiempo_restante_RI_estable_5pct = total_time_simulacion_energia - time_RI_estable_menor_5pct
            porcentaje_tiempo_estable_RI_5pct_val = (tiempo_restante_RI_estable_5pct / total_time_simulacion_energia) * 100
            
            if porcentaje_tiempo_estable_RI_5pct_val >= 60:
                # Usar np.inf si un tiempo no se encontró para las comparaciones
                comp_time_RI_1pct = time_RI_estable_menor_1pct if time_RI_estable_menor_1pct is not None else np.inf
                comp_time_RET_1pct = time_RET_mayor_igual_1pct if time_RET_mayor_igual_1pct is not None else np.inf
                comp_time_RET_5pct = time_RET_mayor_igual_5pct if time_RET_mayor_igual_5pct is not None else np.inf
                
                # Asegurarse que time_RI_estable_menor_5pct (que sabemos que existe) no es None
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
            else: # porcentaje_tiempo_estable_RI_5pct_val < 60
                final_decision_text = "CÁLCULO NO ENTRA EN RÉGIMEN CUASI-ESTÁTICO EL TIEMPO SUFICIENTE (RI < 5% establemente por menos del 60% del tiempo total). REESCALAR TIEMPO Y MASA."
        else: # time_RI_estable_menor_5pct is None
            final_decision_text = "CÁLCULO NO ENTRA EN RÉGIMEN CUASI-ESTÁTICO NUNCA (RI siempre >= 5% o no se pudo determinar). REESCALAR TIEMPO Y MASA."


        # --- 5. Preparar Datos para la Respuesta JSON ---
        # Para la gráfica, enviaremos las series completas.
        # Convertir NaNs a None para que JSON no falle, y formatear números.
        def format_series_for_json(df, time_col, value_col):
            if df.empty or value_col not in df.columns:
                return {'x': [], 'y': []}
            # Rellenar NaN con None para Plotly y JSON. Plotly maneja 'null' para discontinuidades.
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

        # Para la tabla resumen, formatear los tiempos a string con decimales o "N/A"
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
        # Para depuración, imprime el error en la consola del servidor
        app.logger.error(f"Error inesperado durante el análisis: {e}", exc_info=True)
        return jsonify({"message": f"Error inesperado durante el análisis: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)