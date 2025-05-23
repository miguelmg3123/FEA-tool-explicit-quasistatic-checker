// static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const checkButton = document.getElementById('check-button');
    const resultsSection = document.getElementById('results-section');
    
    // Elementos donde mostraremos los resultados
    const plotlyGraphDiv = document.getElementById('plotly-graph'); // Para la gráfica
    const summaryTableBody = document.querySelector('#summary-table tbody');
    const finalDecisionText = document.getElementById('final-decision-text');

    // Botones de la gráfica
    const graphButtons = document.querySelectorAll('.graph-btn');
    let currentGraphData = null; // <--- AÑADE ESTA LÍNEA AQUÍ

    // --- MANEJO DEL FORMULARIO DE CARGA ---
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Evitar el envío tradicional del formulario
            
            // Mostrar algún feedback de carga (opcional, se puede mejorar)
            checkButton.textContent = 'Procesando...';
            checkButton.disabled = true;

            const formData = new FormData(uploadForm);
            
            // Validar que los 3 archivos están seleccionados (HTML 'required' ya ayuda)
            const allkeFile = formData.get('allke_csv');
            const allieFile = formData.get('allie_csv');
            const allwkFile = formData.get('allwk_csv');

            if (!allkeFile || !allieFile || !allwkFile || allkeFile.size === 0 || allieFile.size === 0 || allwkFile.size === 0) {
                alert('Por favor, selecciona los tres archivos CSV.');
                checkButton.textContent = 'Check';
                checkButton.disabled = false;
                return;
            }

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData, // FormData se encarga del Content-Type (multipart/form-data)
                });

                if (!response.ok) {
                    // Si el servidor responde con un error (4xx, 5xx)
                    const errorData = await response.json().catch(() => ({ message: 'Error desconocido del servidor.' }));
                    throw new Error(errorData.message || `Error del servidor: ${response.status}`);
                }

                const result = await response.json();
                
                // Mostrar resultados
                displayResults(result);
                resultsSection.style.display = 'block'; // Mostrar la sección de resultados

            } catch (error) {
                console.error('Error al analizar los datos:', error);
                finalDecisionText.textContent = `Error: ${error.message}`;
                finalDecisionText.className = 'decision-rescale'; // Usar clase de error
                plotlyGraphDiv.innerHTML = '<p style="text-align:center; padding-top:50px; color: #721C24;">Error al procesar los datos.</p>';
                clearSummaryTable(); // Limpiar tabla si hubo error
                resultsSection.style.display = 'block'; // Mostrar la sección de resultados para ver el error
            } finally {
                // Restaurar botón
                checkButton.textContent = 'Check';
                checkButton.disabled = false;
            }
        });
    }

    // --- MANEJO DE BOTONES DE GRÁFICA ---
    graphButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Quitar clase 'active' de todos los botones
            graphButtons.forEach(btn => btn.classList.remove('active'));
            // Añadir clase 'active' al botón clicado
            button.classList.add('active');
            
            const seriesName = button.dataset.series;
            renderPlotlyGraph(seriesName); // Llamar a la función para actualizar la gráfica con la nueva serie
        });
    });

    // --- FUNCIÓN PARA MOSTRAR RESULTADOS ---
    function displayResults(data) {
        // 1. Actualizar texto de decisión final
        if (finalDecisionText) {
            finalDecisionText.textContent = data.final_decision_text || 'No hay decisión disponible.';
            // Aplicar clase CSS según la decisión (necesitaremos mapear esto)
            setDecisionClass(data.final_decision_text);
        }

        // 2. Actualizar tabla resumen
        if (summaryTableBody && data.summary_table) {
            updateSummaryTable(data.summary_table);
        } else if (summaryTableBody) {
            clearSummaryTable(); // Limpiar si no hay datos de tabla
        }


        // 3. Actualizar gráfica
        if (plotlyGraphDiv && data.graph_data) {
            currentGraphData = data.graph_data; // Guardar los datos completos
            const activeSeries = document.querySelector('.graph-btn.active')?.dataset.series || 'RI'; // Obtener la serie activa
            renderPlotlyGraph(activeSeries); // Renderizar la gráfica inicial con la serie activa
        } else if (plotlyGraphDiv) {
            currentGraphData = null; // No hay datos, limpiar
            plotlyGraphDiv.innerHTML = '<p style="text-align:center; padding-top:50px; color: #777;">No hay datos para la gráfica.</p>';
        }
    }

    function updateSummaryTable(summaryData) {
        // Asumimos que summaryData es un objeto como:
        // { time_RI_estable_menor_5pct: '1.2s', ... }
        // Y que los <td> en HTML tienen un atributo data-key que coincide
        for (const key in summaryData) {
            const cell = summaryTableBody.querySelector(`td[data-key="${key}"]`);
            if (cell) {
                cell.textContent = summaryData[key] !== null && summaryData[key] !== undefined ? summaryData[key] : 'N/A';
            }
        }
    }
    
    function clearSummaryTable() {
        const cells = summaryTableBody.querySelectorAll('td[data-key]');
        cells.forEach(cell => cell.textContent = 'N/A');
    }

    function setDecisionClass(decisionText) {
        if (!finalDecisionText || !decisionText) return;
        
        finalDecisionText.className = ''; // Limpiar clases previas
        decisionText = decisionText.toUpperCase(); // Para hacer la comparación insensible a mayúsculas

        if (decisionText.includes("PERFECTO")) {
            finalDecisionText.classList.add('decision-perfect');
        } else if (decisionText.includes("MUY BUENO")) {
            finalDecisionText.classList.add('decision-very-good');
        } else if (decisionText.includes("BUENO")) { // Asegúrate que "MUY BUENO" no lo capture antes
            finalDecisionText.classList.add('decision-good');
        } else if (decisionText.includes("ACEPTABLE")) {
            finalDecisionText.classList.add('decision-acceptable');
        } else if (decisionText.includes("NO ACEPTABLE") || decisionText.includes("REESCALAR") || decisionText.includes("NO ENTRA")) {
            finalDecisionText.classList.add('decision-rescale');
        } else {
            finalDecisionText.classList.add('decision-pending'); // Default o si no coincide
        }
    }


    // Nueva función para renderizar la gráfica con Plotly
    function renderPlotlyGraph(activeSeriesName) {
        if (!plotlyGraphDiv || !currentGraphData || !currentGraphData[activeSeriesName]) {
            plotlyGraphDiv.innerHTML = '<p style="text-align:center; padding-top:50px; color: #777;">Datos no disponibles para esta serie.</p>';
            return;
        }

        const series = currentGraphData[activeSeriesName];
        
        // Verificar que series.x y series.y existen y son arrays
        if (!series || !Array.isArray(series.x) || !Array.isArray(series.y)) {
            plotlyGraphDiv.innerHTML = '<p style="text-align:center; padding-top:50px; color: #777;">Formato de datos incorrecto para la gráfica.</p>';
            console.error("Datos incorrectos para Plotly:", series);
            return;
        }

        const trace = {
            x: series.x,
            y: series.y,
            mode: 'lines',
            type: 'scatter',
            name: activeSeriesName
        };

        const layout = {
            title: `Gráfica de ${activeSeriesName}`,
            xaxis: {
                title: 'Tiempo (s)'
            },
            yaxis: {
                title: getAxisTitle(activeSeriesName),
                // Considera type: 'log' para energías si los rangos son muy amplios
                // type: (activeSeriesName.includes('ALLKE') || activeSeriesName.includes('ALLIE')) ? 'log' : 'linear',
                // autorange: true // Asegura que el rango se ajuste bien, especialmente para log
            },
            margin: { l: 70, r: 30, b: 50, t: 50 }, // Ajustar márgenes (aumenté 'l' para el título del eje Y)
            autosize: true
        };
        
        // Usar Plotly.react para eficiencia en actualizaciones
        Plotly.react(plotlyGraphDiv, [trace], layout, {responsive: true});
    }

    // Nueva función para obtener el título del eje Y
    function getAxisTitle(seriesName) {
        if (seriesName.includes('RI') || seriesName.includes('RET')) {
            return 'Ratio (%)';
        }
        if (seriesName.includes('ALLKE') || seriesName.includes('ALLIE') || seriesName.includes('ALLWK')) {
            return 'Energía (J)'; // O la unidad que corresponda desde tu CSV
        }
        return 'Valor';
    }


    
    // Inicializar el texto de decisión con la clase correcta
    if(finalDecisionText) {
        setDecisionClass(finalDecisionText.textContent);
    }
});