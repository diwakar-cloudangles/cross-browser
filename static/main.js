document.addEventListener('DOMContentLoaded', () => {
    const browserOptions = document.querySelectorAll('.browser-option');
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');

    browserOptions.forEach(option => {
        option.addEventListener('click', async () => {
            const browserType = option.dataset.browser;
            loader.style.display = 'block';
            errorMessage.textContent = '';

            try {
                const response = await fetch('/api/sessions/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ browser_type: browserType }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to create session');
                }

                const session = await response.json();
                window.location.href = `/static/session.html?session_id=${session.session_id}`;

            } catch (error) {
                console.error('Error creating session:', error);
                errorMessage.textContent = `Error: ${error.message}`;
                loader.style.display = 'none';
            }
        });
    });
});