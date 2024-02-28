async function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('http://192.168.1.165:8689/IDCard_Detection/predict', { // Replace 'API_ENDPOINT' with your actual API endpoint
            method: 'POST',
            body: formData,
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error uploading file:', error);
    }
}
let originalPhotoUrl = ''; // Global variable to hold the original photo URL

document.getElementById('file-input').addEventListener('change', function(event) {
    const file = event.target.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        originalPhotoUrl = e.target.result;
        // Optionally, display this photo immediately somewhere on the page if needed
    };
    
    reader.readAsDataURL(file);
});
function displayResults(data) {
    const { OCR, image } = data;
    populateTable(OCR.columns, OCR.data[0], image[0]);
    document.getElementById('results-container').style.display = 'block';
}

function populateTable(columns, rowData, imageData) {
    const table = document.getElementById('ocr-results');
    table.innerHTML = ''; // Clear existing table data
    
    // Define the mappings for column names
    const columnMappings = {
        'CName': 'Name (Chinese)',
        'EName': 'Name (English)',
        'SEX': 'Sex',
        'AUTH': 'Authority (English)',
        'ID': 'ID No.',
        'YB': 'Date of Birth',
        'YI': 'Date of Issue',
        'YE': 'Date of Expiry',
    };

    // Define the new column order and titles
    const newColumns = [
        'Original Photo', 'Name (Chinese)', 'Name (English)', 'Date of Birth', 'Sex', 'Authority (English)',
        'ID No.', 'Date of Issue', 'Date of Expiry', 'ID Photo', 'ID Signature'
    ];

    // Initialize the row data with placeholders for the new format
    let newRowData = new Array(newColumns.length).fill('');
    newRowData[0] = originalPhotoUrl;
    // Populate the new row data based on the original data and mappings
    columns.forEach((col, index) => {
        let newValue;
        switch(col) {
            case 'YB':
                newValue = `${rowData[index]}/${rowData[index + 1]}/${rowData[index + 2]}`; // Date of Birth
                newRowData[newColumns.indexOf(columnMappings[col])] = newValue;
                break;
            case 'YI':
                newValue = `${rowData[index]}/${rowData[index + 1]}/${rowData[index + 2]}`; // Date of Issue
                newRowData[newColumns.indexOf(columnMappings['YI'])] = newValue;
                break;
            case 'YE':
                newValue = `${rowData[index]}/${rowData[index + 1]}/${rowData[index + 2]}`; // Date of Expiry
                newRowData[newColumns.indexOf(columnMappings[col])] = newValue;
                break;
            case 'MB':
            case 'DB':
            case 'MI':
            case 'DI':
            case 'ME':
            case 'DE':
                // Skip as these are handled by their respective Y counterparts
                break;
            default:
                if(columnMappings[col]) {
                    newRowData[newColumns.indexOf(columnMappings[col])] = rowData[index];
                }
                break;
        }
    });

    // Add photo and signature
    newRowData[newColumns.length - 2] = imageData.photo; // ID Photo
    newRowData[newColumns.length - 1] = imageData.sig; // ID Signature

    // Create and append the header row
    const headerRow = document.createElement('tr');
    newColumns.forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Create and append the data row
    const dataRow = document.createElement('tr');
    newRowData.forEach((cell, index) => {
        const td = document.createElement('td');
        if (index === 0) { // Original Photo
            if (originalPhotoUrl) { // 确保有原始照片URL
                const img = document.createElement('img');
                img.src = originalPhotoUrl;
                img.style.width = '150px'; // 调整大小
                td.appendChild(img);
            }
        } else if (index >= newColumns.length - 2) { // ID Photo and ID Signature
            const img = document.createElement('img');
            img.src = `data:image/jpeg;base64,${cell}`;
            img.style.width = '100px'; // Adjust size as needed
            td.appendChild(img);
        } else {
            td.textContent = cell;
        }
        dataRow.appendChild(td);
    });
    table.appendChild(dataRow);
}
