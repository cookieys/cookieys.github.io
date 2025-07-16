document.addEventListener('DOMContentLoaded', () => {
    const scriptUploader = document.getElementById('scriptUploader');

    scriptUploader.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const scriptContent = e.target.result;
                fetch('script_view_template.html')
                    .then(response => response.text())
                    .then(template => {
                        const newPageContent = template.replace(/{{SCRIPT_CONTENT}}/g, scriptContent);
                        const newPage = window.open();
                        newPage.document.write(newPageContent);
                        newPage.document.close();
                    });
            };
            reader.readAsText(file);
        }
    });
});
