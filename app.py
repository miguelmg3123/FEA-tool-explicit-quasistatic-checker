from flask import Flask, render_template, request, jsonify
import pandas as pd
import io # Para manejar los datos CSV en memoria

app = Flask(__name__)

# Configuración para evitar el caching durante el desarrollo
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_data():
    # --- Placeholder para la lógica de análisis ---
    # Aquí recibiremos los archivos, los procesaremos con Pandas
    # y aplicaremos la lógica de validación.

    # Ejemplo de datos de respuesta (temporal)
    analysis_result = {
        "message": "Procesamiento iniciado. Lógica aún no implementada.",
        "graph_data": None, # Aquí irían los datos para Plotly
        "summary_table": None, # Aquí irían los datos de la tabla resumen
        "final_decision_text": "PENDIENTE DE ANÁLISIS"
    }
    return jsonify(analysis_result)
    # --- Fin del Placeholder ---

if __name__ == '__main__':
    # En Codespaces, es común usar host='0.0.0.0' para que sea accesible externamente
    # y debug=True para desarrollo. El puerto 5000 es el predeterminado de Flask.
    app.run(host='0.0.0.0', port=5000, debug=True)