document.addEventListener('DOMContentLoaded', () => {
    const scriptEditor = document.getElementById('scriptEditor');
    const scriptUploader = document.getElementById('scriptUploader');
    const saveButton = document.getElementById('saveButton');
    const clearButton = document.getElementById('clearButton');

    // Load saved script from local storage
    const savedScript = localStorage.getItem('userScript');
    if (savedScript) {
        scriptEditor.value = savedScript;
    }

    // Handle file upload
    scriptUploader.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                scriptEditor.value = e.target.result;
            };
            reader.readAsText(file);
        }
    });

    // Save script to local storage
    saveButton.addEventListener('click', () => {
        localStorage.setItem('userScript', scriptEditor.value);
        alert('Script saved!');
    });

    // Clear script from editor and local storage
    clearButton.addEventListener('click', () => {
        scriptEditor.value = '';
        localStorage.removeItem('userScript');
        alert('Script cleared!');
    });
});
