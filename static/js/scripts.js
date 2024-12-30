/*
Arquivo: scripts.js
Descrição: Controla as interações do frontend para upload e envio de documentos no sistema Domínio.
Autor: Renata Scharf
Data: Dezembro/2024
Versão: 1.0.0
*/

// ==========================
// Alternar Visibilidade da Senha
// ==========================

// Função para alternar a visibilidade do campo de senha (mostrar/ocultar).
// Também troca o ícone (olho aberto/fechado) dinamicamente.
function toggleSenha(inputId, iconId) {
    console.log("Função chamada!");

    // Seleciona o campo de senha e o ícone correspondente
    const senhaInput = document.getElementById(inputId);
    const toggleIcon = document.getElementById(iconId);

    // Alterna entre os tipos 'text' e 'password'
    if (senhaInput.type === "password") {
        senhaInput.type = "text"; // Mostra o texto
        toggleIcon.classList.remove("fa-eye-slash"); // Remove o ícone de olho fechado
        toggleIcon.classList.add("fa-eye"); // Adiciona o ícone de olho aberto
    } else {
        senhaInput.type = "password"; // Oculta o texto
        toggleIcon.classList.remove("fa-eye"); // Remove o ícone de olho aberto
        toggleIcon.classList.add("fa-eye-slash"); // Adiciona o ícone de olho fechado
    }
}

// ==========================
// Exibir Arquivos Carregados
// ==========================

// Detecta a seleção de arquivos no campo de upload e exibe os nomes na interface.
document.getElementById("files").addEventListener("change", function () {
    // Seleciona o elemento onde será exibida a lista de arquivos
    const fileList = document.getElementById("file-list");
    fileList.innerHTML = ""; // Limpa a lista anterior

    // Captura os arquivos carregados
    const files = this.files;

    // Verifica se há arquivos carregados
    if (files.length > 0) {
        // Exibe a quantidade de arquivos e seus nomes
        fileList.innerHTML = `<strong>${files.length} documento(s) carregado(s):</strong>`;
        Array.from(files).forEach((file) => {
            fileList.innerHTML += `<p>- ${file.name}</p>`;
        });
    } else {
        // Caso nenhum arquivo seja carregado
        fileList.innerHTML = "<p style='color:red;'>Nenhum documento carregado.</p>";
    }
});

// ==========================
// Envio Assíncrono do Formulário
// ==========================

// Manipula o envio do formulário via AJAX, exibe mensagens de status e resultados do processamento.
document.getElementById("upload-form").addEventListener("submit", async function (e) {
    e.preventDefault(); // Evita o recarregamento da página

    // Captura os dados do formulário
    const form = e.target;
    const formData = new FormData(form);

    // Seleciona o elemento de feedback para exibir mensagens
    const feedback = document.getElementById("feedback");

    // ==========================
    // Formatação da Data de Vencimento
    // ==========================
    // Converte a data para o formato dd/mm/aaaa antes de enviar para o backend
    const dataVencimentoInput = document.getElementById("data_vencimento");
    if (dataVencimentoInput.value) {
        const [ano, mes, dia] = dataVencimentoInput.value.split("-");
        const dataFormatada = `${dia}/${mes}/${ano}`; // Converte para dd/mm/aaaa
        formData.set("data_vencimento", dataFormatada); // Atualiza o valor no formulário
    }

    // ==========================
    // Feedback Visual - Enviando
    // ==========================
    // Exibe o status de carregamento enquanto o envio está em andamento
    feedback.classList.add('carregando');
    feedback.innerHTML = "Enviando arquivos... <i class='fas fa-spinner fa-spin'></i>";

    try {
        // ==========================
        // Envio dos Dados para o Servidor
        // ==========================
        const response = await fetch(form.action, {
            method: form.method,
            body: formData,
        });

        // Verifica se houve erro na conexão
        if (!response.ok) {
            throw new Error("Falha ao conectar com o servidor.");
        }

        // Processa a resposta do servidor
        const result = await response.json();
        console.log("Resposta do backend:", result);

        // ==========================
        // Feedback Visual - Resultado
        // ==========================
        if (result.status === "sucesso" || result.status === "parcial") {
            feedback.classList.remove('carregando');
            feedback.classList.add('sucesso'); // Feedback para sucesso
            feedback.innerHTML = `<h3>${result.mensagem}</h3>`; // Mensagem geral

            // Exibe detalhes por empresa
            result.detalhes.forEach((detalhe) => {
                const statusIcon = detalhe.status === "sucesso" ? "✔️" : "❌";

                feedback.innerHTML += `
                    <p>${statusIcon} <strong>Empresa:</strong> ${detalhe.empresa}
                    - <strong>Status:</strong> ${detalhe.status}</p>`;

                // Exibe os erros, se houver
                if (detalhe.erros && detalhe.erros.length > 0) {
                    feedback.innerHTML += `<p style="margin-left: 20px; color: red;"><strong>Erros:</strong></p><ul>`;
                    detalhe.erros.forEach((erro) => {
                        feedback.innerHTML += `<li>${erro.nome_arquivo}: ${erro.motivo}</li>`;
                    });
                    feedback.innerHTML += "</ul>";
                }
            });
        } else {
            // Feedback para erro
            feedback.classList.remove('carregando');
            feedback.classList.add('erro');
            feedback.innerHTML = `<p><strong>Erro:</strong> ${result.mensagem}</p>`;
        }
    } catch (err) {
        // Tratamento de erro inesperado
        console.error("Erro ao enviar arquivos:", err);
        feedback.classList.remove('carregando');
        feedback.classList.add('erro');
        feedback.innerHTML = `<p><strong>Erro:</strong> ${err.message}</p>`;
    }
});
