const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');
const body = document.body;
const output = document.getElementById('output');
const resetButton = document.getElementById('resetButton');

themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-theme');
    if (body.classList.contains('dark-theme')) {
        themeIcon.textContent = 'brightness_7'; // Light icon
    } else {
        themeIcon.textContent = 'brightness_4'; // Dark icon
    }
});

document.getElementById('myButton').addEventListener('click', function() {
    output.textContent += 'Hi ';
});

resetButton.addEventListener('click', function() {
    output.textContent = ''; // Clear the output
});
