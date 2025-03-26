document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('senha');
    const togglePassword = document.getElementById('togglePassword');
    const logoutButton = document.getElementById('logoutButton');
    const form = document.getElementById('login-form');
    const feedback = document.getElementById('feedback');

    // Alternar exibir/ocultar senha
    if (togglePassword) {
        togglePassword.addEventListener('click', function() {
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                togglePassword.classList.remove('fa-eye');
                togglePassword.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                togglePassword.classList.remove('fa-eye-slash');
                togglePassword.classList.add('fa-eye');
            }
        });
    }

    // Envio do formulário com tratamento de erros via AJAX
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                // Se a resposta não for ok, lê o JSON e lança um erro
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Erro ao conectar com o servidor.');
                    });
                }
                // Se houver redirecionamento, a resposta JSON conterá a URL
                return response.json();
            })
            .then(data => {
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            })
            .catch(error => {
                console.error('Erro ao tentar fazer login:', error);
                if (feedback) {
                    feedback.style.color = 'red';
                    feedback.textContent = error.message;
                }
            });
        });
    }

    // Logout funcional
    if (logoutButton) {
        logoutButton.addEventListener("click", function () {
            window.location.href = "logout";
        });
    }
});
