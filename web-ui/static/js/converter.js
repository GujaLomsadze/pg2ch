// web-ui/static/js/converter.js

let postgresEditor, clickhouseEditor;
let conversionTimeout;

// Initialize the converter
function initializeConverter() {
    // Initialize CodeMirror editors
    postgresEditor = CodeMirror.fromTextArea(document.getElementById('postgres-editor'), {
        mode: 'sql',
        theme: getTheme(),
        lineNumbers: true,
        lineWrapping: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        indentWithTabs: false,
        indentUnit: 2,
        placeholder: "Paste your PostgreSQL DDL here..."
    });

    clickhouseEditor = CodeMirror.fromTextArea(document.getElementById('clickhouse-editor'), {
        mode: 'sql',
        theme: getTheme(),
        lineNumbers: true,
        lineWrapping: true,
        readOnly: true,
        placeholder: "Converted ClickHouse DDL will appear here..."
    });

    // Add event listeners
    postgresEditor.on('change', debounce(convertDDL, 800));

    // Load theme preference
    loadThemePreference();

    console.log('🚀 pg2ch Converter initialized');
}

// Debounce function to limit API calls
function debounce(func, wait) {
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(conversionTimeout);
            func(...args);
        };
        clearTimeout(conversionTimeout);
        conversionTimeout = setTimeout(later, wait);
    };
}

// Convert PostgreSQL DDL to ClickHouse
async function convertDDL() {
    const ddl = postgresEditor.getValue().trim();

    if (!ddl) {
        clearResults();
        return;
    }

    // Show loading state
    showStatus('Converting...', 'info', true);

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ddl: ddl })
        });

        const data = await response.json();

        if (data.success) {
            // Update ClickHouse editor
            clickhouseEditor.setValue(data.clickhouse_ddl);

            // Show success status
            showStatus('✅ Conversion successful!', 'success');

            // Display metadata
            displayMetadata(data.metadata);

            // Enable action buttons
            enableButtons();

        } else {
            // Show error
            showStatus(`❌ Conversion failed: ${data.error}`, 'danger');
            clickhouseEditor.setValue('');
            clearMetadata();
            disableButtons();
        }

    } catch (error) {
        console.error('Conversion error:', error);
        showStatus(`❌ Network error: ${error.message}`, 'danger');
        clickhouseEditor.setValue('');
        clearMetadata();
        disableButtons();
    }
}

// Show status message
function showStatus(message, type, loading = false) {
    const statusArea = document.getElementById('status-area');
    const alertClass = `alert-${type}`;
    const loadingClass = loading ? 'loading' : '';

    statusArea.innerHTML = `
        <div class="alert ${alertClass} ${loadingClass}" role="alert">
            ${message}
        </div>
    `;
}

// Display conversion metadata
function displayMetadata(metadata) {
    const metadataArea = document.getElementById('metadata-area');
    const summaryDiv = document.getElementById('metadata-summary');
    const detailsDiv = document.getElementById('metadata-details');

    // Summary
    summaryDiv.innerHTML = `
        <div class="metadata-item">
            <strong>📊 Tables:</strong> ${metadata.tables_count}
        </div>
        <div class="metadata-item">
            <strong>📋 Total Columns:</strong> ${metadata.total_columns}
        </div>
    `;

    // Table details
    let detailsHTML = '';
    metadata.tables.forEach(table => {
        const primaryKeys = table.primary_keys.length > 0 ? table.primary_keys.join(', ') : 'None';
        detailsHTML += `
            <div class="metadata-table">
                <strong>🏷️ ${table.name}</strong><br>
                <small class="text-muted">
                    Columns: ${table.columns} | Primary Keys: ${primaryKeys}
                </small>
            </div>
        `;
    });

    detailsDiv.innerHTML = detailsHTML;
    metadataArea.style.display = 'block';
}

// Clear metadata display
function clearMetadata() {
    const metadataArea = document.getElementById('metadata-area');
    metadataArea.style.display = 'none';
}

// Clear all results
function clearResults() {
    clickhouseEditor.setValue('');
    clearMetadata();
    showStatus('Ready! Paste your PostgreSQL DDL above to start converting.', 'info');
    disableButtons();
}

// Enable action buttons
function enableButtons() {
    document.getElementById('downloadBtn').disabled = false;
    document.getElementById('validateBtn').disabled = false;
    document.getElementById('copyBtn').disabled = false;
}

// Disable action buttons
function disableButtons() {
    document.getElementById('downloadBtn').disabled = true;
    document.getElementById('validateBtn').disabled = true;
    document.getElementById('copyBtn').disabled = true;
}

// Validate ClickHouse DDL
async function validateClickHouse() {
    const ddl = clickhouseEditor.getValue().trim();

    if (!ddl) {
        showValidationResult(false, 'No ClickHouse DDL to validate');
        return;
    }

    showValidationResult(null, 'Validating...', true);

    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ddl: ddl })
        });

        const data = await response.json();
        showValidationResult(data.valid, data.message);

    } catch (error) {
        console.error('Validation error:', error);
        showValidationResult(false, `Validation error: ${error.message}`);
    }
}

// Show validation results
function showValidationResult(isValid, message, loading = false) {
    const validationArea = document.getElementById('validation-area');
    const resultsDiv = document.getElementById('validation-results');

    let alertClass = 'alert-info';
    if (isValid === true) alertClass = 'alert-success validation-success';
    if (isValid === false) alertClass = 'alert-danger validation-error';

    const loadingClass = loading ? 'loading' : '';

    resultsDiv.innerHTML = `
        <div class="alert ${alertClass} ${loadingClass}" role="alert">
            ${message}
        </div>
    `;

    validationArea.style.display = 'block';
}

// Copy to clipboard
async function copyToClipboard() {
    const text = clickhouseEditor.getValue();

    if (!text) {
        showStatus('❌ No content to copy', 'warning');
        return;
    }

    try {
        await navigator.clipboard.writeText(text);

        // Visual feedback
        const copyBtn = document.getElementById('copyBtn');
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✅ Copied!';
        copyBtn.classList.add('copy-success');

        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.classList.remove('copy-success');
        }, 2000);

    } catch (error) {
        console.error('Copy failed:', error);
        showStatus('❌ Failed to copy to clipboard', 'danger');
    }
}

// Download result as file
function downloadResult() {
    const content = clickhouseEditor.getValue();

    if (!content) {
        showStatus('❌ No content to download', 'warning');
        return;
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `clickhouse_ddl_${new Date().toISOString().slice(0, 10)}.sql`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
    showStatus('✅ File downloaded successfully!', 'success');
}

// Load file from upload
function loadFile(event) {
    const file = event.target.files[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.sql')) {
        showStatus('❌ Please select a .sql file', 'danger');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        postgresEditor.setValue(e.target.result);
        showStatus('✅ File loaded successfully!', 'success');
    };

    reader.onerror = function() {
        showStatus('❌ Failed to read file', 'danger');
    };

    reader.readAsText(file);
}

// Clear editors
function clearEditors() {
    postgresEditor.setValue('');
    clickhouseEditor.setValue('');
    clearResults();
    document.getElementById('validation-area').style.display = 'none';
}

// Load example DDL
async function loadExample() {
    try {
        const response = await fetch('/api/examples');
        const data = await response.json();

        showExamplesModal(data.examples);

    } catch (error) {
        console.error('Failed to load examples:', error);
        showStatus('❌ Failed to load examples', 'danger');
    }
}

// Show examples modal
function showExamplesModal(examples) {
    const examplesList = document.getElementById('examples-list');

    let examplesHTML = '';
    examples.forEach((example, index) => {
        examplesHTML += `
            <div class="example-card card p-3 mb-2" onclick="selectExample(${index})">
                <h6 class="mb-1">${example.name}</h6>
                <p class="text-muted mb-2">${example.description}</p>
                <code class="small">${example.ddl.substring(0, 100)}...</code>
            </div>
        `;
    });

    examplesList.innerHTML = examplesHTML;

    // Store examples for selection
    window.examplesData = examples;

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('examplesModal'));
    modal.show();
}

// Select example
function selectExample(index) {
    const example = window.examplesData[index];
    postgresEditor.setValue(example.ddl);

    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('examplesModal'));
    modal.hide();

    showStatus(`✅ Loaded example: ${example.name}`, 'success');
}

// Theme management
function getTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    return currentTheme === 'dark' ? 'dracula' : 'default';
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update editors theme
    const editorTheme = newTheme === 'dark' ? 'dracula' : 'default';
    if (postgresEditor) {
        postgresEditor.setOption('theme', editorTheme);
    }
    if (clickhouseEditor) {
        clickhouseEditor.setOption('theme', editorTheme);
    }

    // Update theme icon with smooth transition
    const themeIcon = document.getElementById('theme-icon');
    themeIcon.style.transform = 'scale(0)';

    setTimeout(() => {
        themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        themeIcon.style.transform = 'scale(1)';
    }, 150);
}

function loadThemePreference() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        themeIcon.style.transition = 'transform 0.3s ease';
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+Enter to convert
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        convertDDL();
    }

    // Ctrl+Shift+C to copy
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
        e.preventDefault();
        copyToClipboard();
    }

    // Ctrl+Shift+V to validate
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'V') {
        e.preventDefault();
        validateClickHouse();
    }
});

console.log('🚀 pg2ch Converter JavaScript loaded');
