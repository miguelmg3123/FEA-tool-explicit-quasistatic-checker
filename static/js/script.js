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
            // Aquí llamaremos a la función que actualiza la gráfica de Plotly
            console.log(`Se debe mostrar la serie: ${seriesName}`);
            // Por ahora, solo un placeholder en la gráfica
            if (plotlyGraphDiv) {
                plotlyGraphDiv.innerHTML = `<p style="text-align:center; padding-top:50px; color: #777;">Gráfica para ${seriesName} aparecerá aquí.</p>`;
            }
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

        // 3. Actualizar gráfica (esto se hará más adelante con Plotly)
        if (plotlyGraphDiv && data.graph_data) {
            // Ejemplo: renderPlotlyGraph(data.graph_data, graphButtons.find(btn => btn.classList.contains('active')).dataset.series);
            const activeSeries = document.querySelector('.graph-btn.active')?.dataset.series || 'RI';
            plotlyGraphDiv.innerHTML = `<p style="text-align:center; padding-top:50px; color: #777;">Datos recibidos. Gráfica para ${activeSeries} se mostrará aquí.</p>`;
        } else if (plotlyGraphDiv) {
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
    
    // Inicializar el texto de decisión con la clase correcta
    if(finalDecisionText) {
        setDecisionClass(finalDecisionText.textContent);
    }
});