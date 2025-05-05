document.addEventListener('DOMContentLoaded', () => {
    const inputCodeEl = document.getElementById('inputCode');
    const outputCodeEl = document.getElementById('outputCode');
    const removeButton = document.getElementById('removeButton');
    const copyButton = document.getElementById('copyButton');

    removeButton.addEventListener('click', () => {
        const inputCode = inputCodeEl.value;
        const outputCode = removeComments(inputCode);
        outputCodeEl.value = outputCode;
    });

     copyButton.addEventListener('click', () => {
        if (outputCodeEl.value) {
            navigator.clipboard.writeText(outputCodeEl.value)
                .then(() => {
                    // Optional: Give user feedback (e.g., change button text)
                    const originalText = copyButton.textContent;
                    copyButton.textContent = 'Copied!';
                    setTimeout(() => {
                        copyButton.textContent = originalText;
                    }, 1500); // Reset after 1.5 seconds
                })
                .catch(err => {
                    console.error('Failed to copy text: ', err);
                    alert('Failed to copy text. Your browser might not support this feature or permissions are denied.');
                });
        }
    });

    function removeComments(code) {
        if (!code) {
            return '';
        }

        let result = code;

        // --- Multi-line Comments ---

        // 1. C-style block comments: /* ... */
        //    Uses [\s\S] to match any character including newlines.
        //    *? makes the asterisk non-greedy, matching the shortest possible block.
        result = result.replace(/\/\*[\s\S]*?\*\//g, '');

        // 2. HTML comments: <!-- ... -->
        result = result.replace(/<!--[\s\S]*?-->/g, '');

        // --- Single-line Comments ---
        // Process these after multi-line comments.
        // The 'gm' flags are important: g = global (all occurrences), m = multiline (^/$ match start/end of line)

        // 3. C++/Java/JavaScript style: // ...
        //    Matches // followed by any characters until the end of the line.
        //    We add a check `(?<!:)` to avoid matching URLs like http://, although this is
        //    a negative lookbehind and might not be supported in all *very* old browsers.
        //    A simpler version without lookbehind: result = result.replace(/\/\/.*$/gm, '');
        //    Let's use a slightly safer version that requires space or start of line before //
        //    to reduce false positives in URLs.
        result = result.replace(/(^|[^:])\/\/.*$/gm, '$1'); // Keep the character before // if it wasn't ':'


        // 4. Python/Ruby/Shell style: # ...
        //    Matches # followed by any characters until the end of the line.
        result = result.replace(/#.*$/gm, '');

        // 5. SQL/Ada/Haskell style: -- ...
        //    Matches -- followed by any characters until the end of the line.
        result = result.replace(/--.*$/gm, '');

        // 6. Lisp/Assembly style: ; ...
        //    Matches ; followed by any characters until the end of the line.
        result = result.replace(/;.*$/gm, '');

         // 7. BASIC style: REM ... (case insensitive)
        //    Matches REM at the start of a line (possibly indented) followed by anything.
        result = result.replace(/^\s*REM\s+.*$/gmi, '');

        // 8. VB/VBScript style: ' ...
        //    Matches ' at the start of a line (possibly indented) followed by anything.
        //    This is potentially problematic if ' is used for strings at line start in other languages,
        //    but common for VB style comments.
        result = result.replace(/^\s*'.*$/gm, '');


        // --- Cleanup ---

        // 9. Remove lines that are now empty or contain only whitespace.
        //    Matches start of line, optional whitespace, and then newline.
        result = result.replace(/^\s*[\r\n]/gm, '');


        return result.trim(); // Trim leading/trailing whitespace from the final result
    }
});
