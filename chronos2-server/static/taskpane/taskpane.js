/* global Office, Excel, console */

// ====================================================================
// CHRONOS2 FORECASTING ADD-IN
// Office.js Task Pane Implementation
// ====================================================================

// URL del API en HuggingFace Spaces
const API_BASE_URL = 'https://ttzzs-chronos2-excel-forecasting-api.hf.space';

// Para desarrollo local, descomenta la siguiente línea:
// const API_BASE_URL = 'https://localhost:8000';

// Inicializar cuando Office esté listo
Office.onReady((info) => {
    if (info.host === Office.HostType.Excel) {
        console.log('Chronos2 Add-in loaded successfully');
        checkServerStatus();
        
        // Auto-check cada 30 segundos
        setInterval(checkServerStatus, 30000);
    }
});

// ====================================================================
// UTILIDADES
// ====================================================================

function log(message, type = 'info') {
    const resultsDiv = document.getElementById('results');
    const timestamp = new Date().toLocaleTimeString();
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    entry.innerHTML = `<span class="timestamp">${timestamp}</span> ${icon} ${message}`;
    
    resultsDiv.insertBefore(entry, resultsDiv.firstChild);
    
    // Limitar a 20 entries
    while (resultsDiv.children.length > 20) {
        resultsDiv.removeChild(resultsDiv.lastChild);
    }
}

async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            updateServerStatus(true, `Connected - ${data.model_id}`);
        } else {
            updateServerStatus(false, 'Server error');
        }
    } catch (error) {
        updateServerStatus(false, 'Server offline');
    }
}

function updateServerStatus(isOnline, message) {
    const statusEl = document.getElementById('serverStatus');
    const textEl = document.getElementById('statusText');
    
    statusEl.className = `status-indicator ${isOnline ? 'online' : 'offline'}`;
    textEl.textContent = message;
}

function showTab(tabName) {
    // Ocultar todos los tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    const buttons = document.querySelectorAll('.tab');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Mostrar el tab seleccionado
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.target.classList.add('active');
}

// ====================================================================
// FUNCIONES DE EXCEL (Office.js)
// ====================================================================

async function getSelectedRange() {
    return Excel.run(async (context) => {
        const range = context.workbook.getSelectedRange();
        range.load('values, address');
        await context.sync();
        
        return {
            values: range.values,
            address: range.address
        };
    });
}

async function writeToRange(data, startCell) {
    return Excel.run(async (context) => {
        try {
            console.log(`[writeToRange] Writing ${data?.length || 0} rows to ${startCell}`);
            console.log('[writeToRange] Data:', JSON.stringify(data).substring(0, 200));
            
            if (!data || data.length === 0) {
                throw new Error('No data to write');
            }
            
            if (!data[0] || data[0].length === 0) {
                throw new Error('Invalid data structure: empty first row');
            }
            
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            const numRows = data.length;
            const numCols = data[0].length;
            
            console.log(`[writeToRange] Creating range: ${numRows} rows x ${numCols} cols from ${startCell}`);
            
            const range = sheet.getRange(startCell).getResizedRange(numRows - 1, numCols - 1);
            
            range.values = data;
            range.format.autofitColumns();
            
            await context.sync();
            
            console.log('[writeToRange] ✅ Data written successfully');
        } catch (error) {
            console.error('[writeToRange] ❌ Error:', error);
            console.error('[writeToRange] Stack:', error.stack);
            throw error;
        }
    });
}

// ====================================================================
// COPY TO CLIPBOARD FUNCTIONALITY
// ====================================================================

/**
 * Format forecast results as TSV (Tab-Separated Values)
 * Excel automatically recognizes TSV and creates a table
 */
function formatForecastAsTSV(timestamps, median, q10, q90) {
    // Header row
    let tsv = 'Date\tForecast\tLower 10%\tUpper 90%\n';
    
    // Data rows
    for (let i = 0; i < timestamps.length; i++) {
        const date = timestamps[i] || `Period ${i + 1}`;
        const med = median[i]?.toFixed(2) || '';
        const lower = q10[i]?.toFixed(2) || '';
        const upper = q90[i]?.toFixed(2) || '';
        
        tsv += `${date}\t${med}\t${lower}\t${upper}\n`;
    }
    
    return tsv;
}

/**
 * Copy forecast results to clipboard
 */
async function copyForecastToClipboard(timestamps, median, q10, q90) {
    try {
        console.log('[copyToClipboard] Formatting data...');
        
        // Format as TSV
        const tsv = formatForecastAsTSV(timestamps, median, q10, q90);
        
        console.log('[copyToClipboard] TSV length:', tsv.length);
        console.log('[copyToClipboard] Preview:', tsv.substring(0, 200));
        
        // Copy to clipboard using Clipboard API
        await navigator.clipboard.writeText(tsv);
        
        console.log('[copyToClipboard] ✅ Copied successfully');
        
        // User feedback
        log('✅ Forecast copied to clipboard! Paste in Excel with Ctrl+V', 'success');
        showCopySuccessNotification();
        
        return true;
    } catch (error) {
        console.error('[copyToClipboard] ❌ Error:', error);
        
        // Fallback: Show modal with selectable text
        showCopyFallbackModal(formatForecastAsTSV(timestamps, median, q10, q90));
        log('⚠️ Please select and copy the text manually', 'warning');
        
        return false;
    }
}

/**
 * Show temporary success notification
 */
function showCopySuccessNotification() {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'copy-toast';
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">📋</span>
            <span class="toast-text">Copied to clipboard!</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Show fallback modal if clipboard API fails
 */
function showCopyFallbackModal(text) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'copy-fallback-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Copy Forecast Results</h3>
            <p>Select all text below and copy (Ctrl+C or Cmd+C):</p>
            <textarea readonly class="copy-textarea">${text}</textarea>
            <button onclick="this.parentElement.parentElement.remove()" class="btn btn-secondary">
                Close
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Auto-select text
    const textarea = modal.querySelector('.copy-textarea');
    textarea.focus();
    textarea.select();
}

/**
 * Show forecast preview with copy button
 */
function showForecastPreview(forecastData) {
    const { timestamps, median, q10, q90 } = forecastData;
    
    // Create preview HTML
    let previewHTML = `
        <div class="forecast-preview-card">
            <div class="preview-header">
                <h3>📊 Forecast Preview</h3>
                <span class="preview-count">${timestamps.length} periods</span>
            </div>
            <div class="preview-table-container">
                <table class="preview-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Forecast</th>
                            <th>Lower</th>
                            <th>Upper</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    // Show first 5 rows
    const displayRows = Math.min(5, timestamps.length);
    for (let i = 0; i < displayRows; i++) {
        previewHTML += `
            <tr>
                <td>${timestamps[i] || `P${i+1}`}</td>
                <td>${median[i].toFixed(2)}</td>
                <td>${q10[i].toFixed(2)}</td>
                <td>${q90[i].toFixed(2)}</td>
            </tr>
        `;
    }
    
    if (timestamps.length > 5) {
        previewHTML += `
            <tr class="preview-more">
                <td colspan="4">... and ${timestamps.length - 5} more rows</td>
            </tr>
        `;
    }
    
    previewHTML += `
                    </tbody>
                </table>
            </div>
            <div class="preview-actions">
                <button class="btn btn-primary btn-copy-forecast" onclick="copyLastForecast()">
                    📋 Copy to Clipboard
                </button>
                <div class="preview-hint">
                    💡 Click to copy, then paste in Excel with Ctrl+V
                </div>
            </div>
        </div>
    `;
    
    // Find or create preview container
    let previewContainer = document.getElementById('forecast-preview');
    if (!previewContainer) {
        previewContainer = document.createElement('div');
        previewContainer.id = 'forecast-preview';
        
        // Insert after results log
        const resultsCard = document.querySelector('.results-card');
        if (resultsCard) {
            resultsCard.parentNode.insertBefore(previewContainer, resultsCard);
        } else {
            document.querySelector('.container').appendChild(previewContainer);
        }
    }
    
    previewContainer.innerHTML = previewHTML;
    
    // Scroll to preview
    previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Copy last forecast (called from button)
 */
function copyLastForecast() {
    if (!window.lastForecastData) {
        log('⚠️ No forecast data available to copy', 'warning');
        return;
    }
    
    const { timestamps, median, q10, q90 } = window.lastForecastData;
    copyForecastToClipboard(timestamps, median, q10, q90);
}

async function writeForecastResults(timestamps, median, q10, q90, startRow) {
    return Excel.run(async (context) => {
        try {
            console.log('[writeForecastResults] Starting...');
            console.log(`[writeForecastResults] timestamps: ${timestamps?.length || 0} items`);
            console.log(`[writeForecastResults] median: ${median?.length || 0} items`);
            console.log(`[writeForecastResults] q10: ${q10?.length || 0} items`);
            console.log(`[writeForecastResults] q90: ${q90?.length || 0} items`);
            console.log(`[writeForecastResults] startRow: ${startRow}`);
            
            // VALIDACIÓN
            if (!timestamps || !median) {
                throw new Error('Invalid data: timestamps or median is undefined');
            }
            
            if (timestamps.length === 0) {
                throw new Error('No forecast data received (empty timestamps)');
            }
            
            if (timestamps.length !== median.length) {
                throw new Error(`Data mismatch: ${timestamps.length} timestamps vs ${median.length} median values`);
            }
            
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            
            // Preparar datos
            const data = [];
            data.push(['Timestamp', 'Median', 'Q10', 'Q90']); // Headers
            
            for (let i = 0; i < timestamps.length; i++) {
                data.push([
                    timestamps[i],
                    median[i],
                    q10 ? q10[i] : '',
                    q90 ? q90[i] : ''
                ]);
            }
            
            console.log(`[writeForecastResults] Prepared ${data.length} rows (including header)`);
            
            // Escribir en columnas D-G a partir de la fila especificada
            const startCell = `D${startRow}`;
            console.log(`[writeForecastResults] Writing to ${startCell}`);
            
            await writeToRange(data, startCell);
        
            // Aplicar formato
            const headerRange = sheet.getRange(`D${startRow}:G${startRow}`);
            headerRange.format.font.bold = true;
            headerRange.format.fill.color = '#4472C4';
            headerRange.format.font.color = 'white';
            
            await context.sync();
            
            console.log('[writeForecastResults] ✅ Forecast results written successfully');
        } catch (error) {
            console.error('[writeForecastResults] ❌ Error:', error);
            console.error('[writeForecastResults] Stack:', error.stack);
            throw error;
        }
    });
}

// ====================================================================
// FUNCIÓN 1: PRONÓSTICO UNIVARIANTE
// ====================================================================

async function forecastUnivariate() {
    log('Starting univariate forecast...');
    
    try {
        // Leer rango seleccionado
        const selection = await getSelectedRange();
        const values = selection.values.flat().filter(v => v !== '' && !isNaN(v));
        
        if (values.length < 3) {
            log('Error: Select at least 3 data points', 'error');
            return;
        }
        
        log(`Selected ${values.length} data points from ${selection.address}`);
        
        // Obtener parámetros
        const predictionLength = parseInt(document.getElementById('predictionLength').value);
        const frequency = document.getElementById('frequency').value;
        
        // Construir request
        const requestBody = {
            prediction_length: predictionLength,
            series: { values: values },
            start_timestamp: new Date().toISOString().split('T')[0],
            freq: frequency,
            quantile_levels: [0.1, 0.5, 0.9]
        };
        
        log('Sending request to API...');
        
        // Llamar a la API
        const response = await fetch(`${API_BASE_URL}/forecast_univariate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        log(`Received forecast for ${data.timestamps.length} periods`, 'success');
        
        // Store forecast data globally for copy function
        window.lastForecastData = {
            timestamps: data.timestamps,
            median: data.median,
            q10: data.quantiles['0.1'],
            q90: data.quantiles['0.9']
        };
        
        // Show preview with copy button
        showForecastPreview(window.lastForecastData);
        
        // Escribir resultados
        await Excel.run(async (context) => {
            const selection = context.workbook.getSelectedRange();
            selection.load('rowIndex, rowCount');
            await context.sync();
            
            const startRow = selection.rowIndex + selection.rowCount + 2;
            
            await writeForecastResults(
                data.timestamps,
                data.median,
                data.quantiles['0.1'],
                data.quantiles['0.9'],
                startRow
            );
        });
        
        log('✨ Forecast written to spreadsheet', 'success');
        
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        console.error(error);
    }
}

// ====================================================================
// FUNCIÓN 2: DETECCIÓN DE ANOMALÍAS
// ====================================================================

async function detectAnomalies() {
    log('Starting anomaly detection...');
    
    try {
        const selection = await getSelectedRange();
        const values = selection.values.flat().filter(v => v !== '' && !isNaN(v));
        
        const contextLength = parseInt(document.getElementById('contextLength').value);
        const recentPoints = parseInt(document.getElementById('recentPoints').value);
        
        if (values.length < contextLength + recentPoints) {
            log(`Error: Need at least ${contextLength + recentPoints} points`, 'error');
            return;
        }
        
        const context = values.slice(0, contextLength);
        const recent = values.slice(contextLength, contextLength + recentPoints);
        
        const requestBody = {
            context: { values: context },
            recent_observed: recent,
            prediction_length: recentPoints,
            quantile_low: 0.05,
            quantile_high: 0.95
        };
        
        log('Analyzing data...');
        
        const response = await fetch(`${API_BASE_URL}/detect_anomalies`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        const data = await response.json();
        const anomalyCount = data.anomalies.filter(a => a.is_anomaly).length;
        
        if (anomalyCount > 0) {
            log(`⚠️ Found ${anomalyCount} anomalies!`, 'error');
        } else {
            log('No anomalies detected ✓', 'success');
        }
        
        // Escribir resultados en Excel
        await Excel.run(async (context) => {
            const selection = context.workbook.getSelectedRange();
            selection.load('rowIndex, rowCount');
            await context.sync();
            
            const startRow = selection.rowIndex + selection.rowCount + 2;
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            
            // Preparar datos
            const tableData = [['Index', 'Value', 'Expected', 'Lower', 'Upper', 'Is Anomaly']];
            
            data.anomalies.forEach(a => {
                tableData.push([
                    a.index,
                    parseFloat(a.value.toFixed(2)),
                    parseFloat(a.predicted_median.toFixed(2)),
                    parseFloat(a.lower.toFixed(2)),
                    parseFloat(a.upper.toFixed(2)),
                    a.is_anomaly ? 'YES' : 'No'
                ]);
            });
            
            const range = sheet.getRangeByIndexes(startRow, 0, tableData.length, 6);
            range.values = tableData;
            range.format.autofitColumns();
            
            // Format header
            const headerRange = sheet.getRangeByIndexes(startRow, 0, 1, 6);
            headerRange.format.font.bold = true;
            headerRange.format.fill.color = '#4472C4';
            headerRange.format.font.color = 'white';
            
            // Highlight anomalies
            for (let i = 0; i < data.anomalies.length; i++) {
                if (data.anomalies[i].is_anomaly) {
                    const anomalyRange = sheet.getRangeByIndexes(startRow + i + 1, 0, 1, 6);
                    anomalyRange.format.fill.color = '#FFC7CE';
                }
            }
            
            await context.sync();
        });
        
        log('✨ Anomaly results written to spreadsheet', 'success');
        
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        console.error(error);
    }
}

// ====================================================================
// FUNCIÓN 3: BACKTEST
// ====================================================================

async function runBacktest() {
    log('Running backtest...');
    
    try {
        const selection = await getSelectedRange();
        const values = selection.values.flat().filter(v => v !== '' && !isNaN(v));
        
        const testLength = parseInt(document.getElementById('testLength').value);
        
        if (values.length <= testLength) {
            log('Error: Series must be longer than test length', 'error');
            return;
        }
        
        const requestBody = {
            series: { values: values },
            prediction_length: testLength,
            test_length: testLength
        };
        
        log('Evaluating model...');
        
        const response = await fetch(`${API_BASE_URL}/backtest_simple`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        const data = await response.json();
        const metrics = data.metrics;
        
        log(`📊 Backtest Results: MAE=${metrics.mae.toFixed(2)}, MAPE=${metrics.mape.toFixed(2)}%`, 'success');
        
        // Escribir resultados en Excel
        await Excel.run(async (context) => {
            const selection = context.workbook.getSelectedRange();
            selection.load('rowIndex, rowCount');
            await context.sync();
            
            const startRow = selection.rowIndex + selection.rowCount + 2;
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            
            // Tabla de métricas
            const metricsData = [
                ['Metric', 'Value'],
                ['MAE', parseFloat(metrics.mae.toFixed(2))],
                ['MAPE', metrics.mape.toFixed(2) + '%'],
                ['RMSE', parseFloat(metrics.rmse.toFixed(2))],
                ['WQL', parseFloat(metrics.wql.toFixed(3))]
            ];
            
            const metricsRange = sheet.getRangeByIndexes(startRow, 0, metricsData.length, 2);
            metricsRange.values = metricsData;
            metricsRange.format.autofitColumns();
            
            // Format header
            const headerRange = sheet.getRangeByIndexes(startRow, 0, 1, 2);
            headerRange.format.font.bold = true;
            headerRange.format.fill.color = '#70AD47';
            headerRange.format.font.color = 'white';
            
            // Forecast vs Actuals si están disponibles
            if (data.forecast_median && data.actuals) {
                const forecastData = [['Timestamp', 'Forecast', 'Actual', 'Error']];
                
                for (let i = 0; i < data.forecast_median.length; i++) {
                    const error = Math.abs(data.forecast_median[i] - data.actuals[i]);
                    forecastData.push([
                        data.forecast_timestamps[i] || `t+${i+1}`,
                        parseFloat(data.forecast_median[i].toFixed(2)),
                        parseFloat(data.actuals[i].toFixed(2)),
                        parseFloat(error.toFixed(2))
                    ]);
                }
                
                const forecastRange = sheet.getRangeByIndexes(
                    startRow + metricsData.length + 2, 
                    0, 
                    forecastData.length, 
                    4
                );
                forecastRange.values = forecastData;
                forecastRange.format.autofitColumns();
                
                const forecastHeaderRange = sheet.getRangeByIndexes(
                    startRow + metricsData.length + 2, 
                    0, 
                    1, 
                    4
                );
                forecastHeaderRange.format.font.bold = true;
                forecastHeaderRange.format.fill.color = '#4472C4';
                forecastHeaderRange.format.font.color = 'white';
            }
            
            await context.sync();
        });
        
        log('✨ Backtest results written to spreadsheet', 'success');
        
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        console.error(error);
    }
}

// ====================================================================
// FUNCIÓN 4: MULTI-SERIES
// ====================================================================

async function forecastMultiSeries() {
    log('Starting multi-series forecast...');
    
    try {
        const selection = await getSelectedRange();
        const data = selection.values;
        
        // Agrupar por series_id (columna A)
        const seriesMap = {};
        
        for (let i = 1; i < data.length; i++) { // Skip header
            const seriesId = data[i][0];
            const value = data[i][2]; // Columna C
            
            if (seriesId && value !== '' && !isNaN(value)) {
                if (!seriesMap[seriesId]) {
                    seriesMap[seriesId] = [];
                }
                seriesMap[seriesId].push(parseFloat(value));
            }
        }
        
        const seriesList = Object.entries(seriesMap).map(([id, values]) => ({
            series_id: id,
            values: values
        }));
        
        if (seriesList.length === 0) {
            log('Error: No valid series found', 'error');
            return;
        }
        
        log(`Found ${seriesList.length} series`);
        
        const predictionLength = parseInt(document.getElementById('multiPredLength').value);
        
        const requestBody = {
            prediction_length: predictionLength,
            series_list: seriesList,
            start_timestamp: new Date().toISOString().split('T')[0],
            freq: 'D',
            quantile_levels: [0.1, 0.5, 0.9]
        };
        
        log('Forecasting all series...');
        
        const response = await fetch(`${API_BASE_URL}/forecast_multi_id`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        log(`✨ Generated forecasts for ${result.forecasts.length} series`, 'success');
        
        // Escribir resultados en Excel
        await Excel.run(async (context) => {
            const selection = context.workbook.getSelectedRange();
            selection.load('rowIndex, rowCount');
            await context.sync();
            
            const startRow = selection.rowIndex + selection.rowCount + 2;
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            
            let currentRow = startRow;
            
            // Escribir cada serie
            result.forecasts.forEach(forecast => {
                // Header de la serie
                const seriesHeaderRange = sheet.getRangeByIndexes(currentRow, 0, 1, 1);
                seriesHeaderRange.values = [[`Series: ${forecast.series_id}`]];
                seriesHeaderRange.format.font.bold = true;
                seriesHeaderRange.format.fill.color = '#4472C4';
                seriesHeaderRange.format.font.color = 'white';
                currentRow++;
                
                // Datos de la serie
                const tableData = [['Timestamp', 'Median', 'Q10', 'Q90']];
                
                for (let i = 0; i < forecast.timestamps.length; i++) {
                    tableData.push([
                        forecast.timestamps[i],
                        parseFloat(forecast.median[i].toFixed(2)),
                        parseFloat(forecast.quantiles['0.1'][i].toFixed(2)),
                        parseFloat(forecast.quantiles['0.9'][i].toFixed(2))
                    ]);
                }
                
                const dataRange = sheet.getRangeByIndexes(
                    currentRow,
                    0,
                    tableData.length,
                    4
                );
                dataRange.values = tableData;
                dataRange.format.autofitColumns();
                
                // Format header
                const headerRange = sheet.getRangeByIndexes(currentRow, 0, 1, 4);
                headerRange.format.font.bold = true;
                headerRange.format.fill.color = '#D9E1F2';
                
                currentRow += tableData.length + 1; // +1 para separación
            });
            
            await context.sync();
        });
        
        log('✨ Multi-series forecasts written to spreadsheet', 'success');
        
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        console.error(error);
    }
}

// ====================================================================
// FUNCIÓN 5: COVARIABLES
// ====================================================================

async function forecastWithCovariates() {
    log('Starting forecast with covariates...');
    
    try {
        const selection = await getSelectedRange();
        const data = selection.values;
        
        if (data.length < 3) {
            log('Error: Need at least 3 rows of data', 'error');
            return;
        }
        
        // Obtener parámetros
        const predictionLength = parseInt(document.getElementById('covPredLength').value);
        const covariateNamesInput = document.getElementById('covariateNames').value;
        const covariateNames = covariateNamesInput.split(',').map(s => s.trim());
        
        log(`Reading data with ${covariateNames.length} covariates: ${covariateNames.join(', ')}`);
        
        // Estructura esperada:
        // Col A: Date/Timestamp
        // Col B: Target value
        // Col C+: Covariates
        
        const context = [];
        const future = [];
        
        for (let i = 1; i < data.length; i++) { // Skip header
            const timestamp = data[i][0] ? data[i][0].toString() : null;
            const target = data[i][1];
            
            // Leer covariables
            const covariates = {};
            for (let j = 0; j < covariateNames.length && j < data[i].length - 2; j++) {
                const covValue = data[i][j + 2];
                if (covValue !== '' && !isNaN(covValue)) {
                    covariates[covariateNames[j]] = parseFloat(covValue);
                }
            }
            
            // Si tiene target, es contexto histórico
            if (target !== '' && !isNaN(target)) {
                context.push({
                    timestamp: timestamp,
                    target: parseFloat(target),
                    covariates: covariates
                });
            } 
            // Si no tiene target pero sí covariables, son valores futuros
            else if (Object.keys(covariates).length > 0) {
                future.push({
                    timestamp: timestamp,
                    covariates: covariates
                });
            }
        }
        
        if (context.length === 0) {
            log('Error: No historical data found', 'error');
            return;
        }
        
        log(`Context: ${context.length} points, Future: ${future.length} points`);
        
        const requestBody = {
            context: context,
            future: future.length > 0 ? future : null,
            prediction_length: predictionLength,
            quantile_levels: [0.1, 0.5, 0.9]
        };
        
        log('Calling API with covariates...');
        
        const response = await fetch(`${API_BASE_URL}/forecast_with_covariates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.statusText} - ${errorText}`);
        }
        
        const result = await response.json();
        
        log(`✨ Forecast generated with ${result.pred_df.length} predictions`, 'success');
        
        // Escribir resultados en una nueva ubicación
        await Excel.run(async (context) => {
            const selection = context.workbook.getSelectedRange();
            selection.load('rowIndex, rowCount, columnCount');
            await context.sync();
            
            const startRow = selection.rowIndex + selection.rowCount + 2;
            const startCol = 0;
            
            // Crear tabla con los resultados
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            
            // Headers
            const headers = Object.keys(result.pred_df[0]);
            const tableData = [headers];
            
            // Data rows
            result.pred_df.forEach(row => {
                const rowData = headers.map(h => row[h]);
                tableData.push(rowData);
            });
            
            const outputRange = sheet.getRangeByIndexes(
                startRow, 
                startCol, 
                tableData.length, 
                headers.length
            );
            
            outputRange.values = tableData;
            outputRange.format.autofitColumns();
            
            // Format header
            const headerRange = sheet.getRangeByIndexes(startRow, startCol, 1, headers.length);
            headerRange.format.font.bold = true;
            headerRange.format.fill.color = '#4472C4';
            headerRange.format.font.color = 'white';
            
            await context.sync();
        });
        
        log('✨ Results written to spreadsheet', 'success');
        
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        console.error(error);
    }
}

// ====================================================================
// FUNCIÓN 6: ESCENARIOS
// ====================================================================

async function generateScenarios() {
    log('Starting scenario generation...');
    
    try {
        const selection = await getSelectedRange();
        const data = selection.values;
        
        if (data.length < 3) {
            log('Error: Need at least 3 rows of data', 'error');
            return;
        }
        
        const numScenarios = parseInt(document.getElementById('numScenarios').value);
        
        // Estructura esperada similar a covariates:
        // Col A: Date, Col B: Target, Col C+: Covariates
        // Para escenarios, generaremos variaciones de las covariables
        
        const context = [];
        const covariateNames = [];
        
        // Detectar nombres de covariables del header
        for (let j = 2; j < data[0].length; j++) {
            if (data[0][j]) {
                covariateNames.push(data[0][j].toString());
            }
        }
        
        log(`Detected covariates: ${covariateNames.join(', ')}`);
        
        // Leer contexto histórico
        for (let i = 1; i < data.length; i++) {
            const timestamp = data[i][0] ? data[i][0].toString() : null;
            const target = data[i][1];
            
            if (target !== '' && !isNaN(target)) {
                const covariates = {};
                for (let j = 0; j < covariateNames.length && j < data[i].length - 2; j++) {
                    const covValue = data[i][j + 2];
                    if (covValue !== '' && !isNaN(covValue)) {
                        covariates[covariateNames[j]] = parseFloat(covValue);
                    }
                }
                
                context.push({
                    timestamp: timestamp,
                    target: parseFloat(target),
                    covariates: covariates
                });
            }
        }
        
        if (context.length === 0) {
            log('Error: No historical data found', 'error');
            return;
        }
        
        // Generar escenarios automáticamente
        const predictionLength = 7;
        const scenarios = [];
        
        // Calcular valores promedio de covariables para generar variaciones
        const avgCovariates = {};
        covariateNames.forEach(name => {
            const values = context
                .map(p => p.covariates[name])
                .filter(v => v !== undefined);
            avgCovariates[name] = values.length > 0 
                ? values.reduce((a, b) => a + b, 0) / values.length 
                : 0;
        });
        
        // Escenario 1: Baseline (promedios)
        const baselineScenario = {
            name: 'Baseline',
            future_covariates: []
        };
        
        for (let i = 0; i < predictionLength; i++) {
            baselineScenario.future_covariates.push({
                timestamp: `future_${i+1}`,
                covariates: {...avgCovariates}
            });
        }
        scenarios.push(baselineScenario);
        
        // Escenario 2: Optimista (+20%)
        if (numScenarios >= 2) {
            const optimisticScenario = {
                name: 'Optimistic (+20%)',
                future_covariates: []
            };
            
            for (let i = 0; i < predictionLength; i++) {
                const covs = {};
                covariateNames.forEach(name => {
                    covs[name] = avgCovariates[name] * 1.2;
                });
                optimisticScenario.future_covariates.push({
                    timestamp: `future_${i+1}`,
                    covariates: covs
                });
            }
            scenarios.push(optimisticScenario);
        }
        
        // Escenario 3: Pesimista (-20%)
        if (numScenarios >= 3) {
            const pessimisticScenario = {
                name: 'Pessimistic (-20%)',
                future_covariates: []
            };
            
            for (let i = 0; i < predictionLength; i++) {
                const covs = {};
                covariateNames.forEach(name => {
                    covs[name] = avgCovariates[name] * 0.8;
                });
                pessimisticScenario.future_covariates.push({
                    timestamp: `future_${i+1}`,
                    covariates: covs
                });
            }
            scenarios.push(pessimisticScenario);
        }
        
        log(`Generated ${scenarios.length} scenarios`);
        
        const requestBody = {
            context: context,
            scenarios: scenarios,
            prediction_length: predictionLength,
            quantile_levels: [0.1, 0.5, 0.9]
        };
        
        log('Calling scenarios API...');
        
        const response = await fetch(`${API_BASE_URL}/forecast_scenarios`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.statusText} - ${errorText}`);
        }
        
        const result = await response.json();
        
        log(`✨ Generated ${result.scenarios.length} scenario forecasts`, 'success');
        
        // Escribir resultados
        await Excel.run(async (context) => {
            const selection = context.workbook.getSelectedRange();
            selection.load('rowIndex, rowCount');
            await context.sync();
            
            const startRow = selection.rowIndex + selection.rowCount + 2;
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            
            let currentRow = startRow;
            
            // Escribir cada escenario
            result.scenarios.forEach(scenario => {
                // Header del escenario
                const scenarioHeaderRange = sheet.getRangeByIndexes(currentRow, 0, 1, 1);
                scenarioHeaderRange.values = [[`Scenario: ${scenario.name}`]];
                scenarioHeaderRange.format.font.bold = true;
                scenarioHeaderRange.format.fill.color = '#70AD47';
                scenarioHeaderRange.format.font.color = 'white';
                currentRow++;
                
                // Datos del escenario
                if (scenario.pred_df && scenario.pred_df.length > 0) {
                    const headers = Object.keys(scenario.pred_df[0]);
                    const tableData = [headers];
                    
                    scenario.pred_df.forEach(row => {
                        tableData.push(headers.map(h => row[h]));
                    });
                    
                    const dataRange = sheet.getRangeByIndexes(
                        currentRow,
                        0,
                        tableData.length,
                        headers.length
                    );
                    dataRange.values = tableData;
                    dataRange.format.autofitColumns();
                    
                    currentRow += tableData.length + 1; // +1 para separación
                }
            });
            
            await context.sync();
        });
        
        log('✨ Scenarios written to spreadsheet', 'success');
        
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        console.error(error);
    }
}

// ====================================================================
// FUNCIÓN 7: MULTIVARIANTE
// ====================================================================

async function forecastMultivariate() {
    log('Starting multivariate forecast...');
    
    try {
        const selection = await getSelectedRange();
        const data = selection.values;
        
        if (data.length < 3) {
            log('Error: Need at least 3 rows of data', 'error');
            return;
        }
        
        // Obtener parámetros
        const predictionLength = parseInt(document.getElementById('multivarPredLength').value);
        const targetColumnsInput = document.getElementById('targetColumns').value;
        const targetColumns = targetColumnsInput.split(',').map(s => s.trim());
        
        log(`Forecasting ${targetColumns.length} target variables: ${targetColumns.join(', ')}`);
        
        // Estructura esperada:
        // Col A: Date/Timestamp
        // Col B+: Target variables (múltiples columnas que queremos predecir)
        
        const context = [];
        
        // Validar que hay suficientes columnas
        if (data[0].length < targetColumns.length + 1) {
            log(`Error: Expected ${targetColumns.length + 1} columns but found ${data[0].length}`, 'error');
            return;
        }
        
        // Leer datos
        for (let i = 1; i < data.length; i++) { // Skip header
            const timestamp = data[i][0] ? data[i][0].toString() : null;
            
            // Leer todos los targets
            const targets = {};
            let hasValidData = false;
            
            for (let j = 0; j < targetColumns.length && j < data[i].length - 1; j++) {
                const value = data[i][j + 1];
                if (value !== '' && !isNaN(value)) {
                    targets[targetColumns[j]] = parseFloat(value);
                    hasValidData = true;
                }
            }
            
            if (hasValidData) {
                context.push({
                    timestamp: timestamp,
                    targets: targets,
                    covariates: {} // Sin covariables por ahora
                });
            }
        }
        
        if (context.length === 0) {
            log('Error: No valid data found', 'error');
            return;
        }
        
        log(`Read ${context.length} data points`);
        
        const requestBody = {
            context: context,
            target_columns: targetColumns,
            prediction_length: predictionLength,
            quantile_levels: [0.1, 0.5, 0.9]
        };
        
        log('Calling multivariate forecast API...');
        
        const response = await fetch(`${API_BASE_URL}/forecast_multivariate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.statusText} - ${errorText}`);
        }
        
        const result = await response.json();
        
        log(`✨ Generated multivariate forecast with ${result.pred_df.length} predictions`, 'success');
        
        // Escribir resultados
        await Excel.run(async (context) => {
            const selection = context.workbook.getSelectedRange();
            selection.load('rowIndex, rowCount');
            await context.sync();
            
            const startRow = selection.rowIndex + selection.rowCount + 2;
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            
            // Crear tabla con resultados
            if (result.pred_df && result.pred_df.length > 0) {
                const headers = Object.keys(result.pred_df[0]);
                const tableData = [headers];
                
                result.pred_df.forEach(row => {
                    tableData.push(headers.map(h => row[h]));
                });
                
                const outputRange = sheet.getRangeByIndexes(
                    startRow,
                    0,
                    tableData.length,
                    headers.length
                );
                
                outputRange.values = tableData;
                outputRange.format.autofitColumns();
                
                // Format header
                const headerRange = sheet.getRangeByIndexes(startRow, 0, 1, headers.length);
                headerRange.format.font.bold = true;
                headerRange.format.fill.color = '#4472C4';
                headerRange.format.font.color = 'white';
                
                await context.sync();
            }
        });
        
        log('✨ Multivariate forecast written to spreadsheet', 'success');
        
    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        console.error(error);
    }
}
