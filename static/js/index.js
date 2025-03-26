document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('indexForm');
  const dropzone = document.getElementById('dropzone');
  const fileListContainer = document.getElementById('fileListContainer');
  const fileInput = document.getElementById('anexos');
  const logoutButton = document.getElementById('logoutButton');
  const downloadIcon = document.getElementById('downloadIcon');
  const loginDominio = document.getElementById('loginDominio');
  const welcomeText = document.getElementById('welcomeText');
  const fiscalOpcaoElement = document.getElementById('fiscalOpcao');
  const fiscalOpcaoLabel = document.getElementById('fiscalOpcaoLabel');
  const dataVencimentoField = document.getElementById('dataVencimento');
  const dataVencimentoLabel = document.querySelector('label[for="dataVencimento"]');

  let currentUser = "";
  let uploadedFiles = [];

  fetch('/get-user')
    .then(response => response.json())
    .then(data => {
      if (data.user) {
        currentUser = data.user;
        welcomeText.textContent = `Bem-vindo, ${data.user}!`;
        if (data.user === "Fiscal") {
          fiscalOpcaoElement.style.display = 'block';
          fiscalOpcaoLabel.style.display = 'block';
        }
        if (data.user === "Eduardo" || data.user === "CND") {
          dataVencimentoField.style.display = 'none';
          dataVencimentoLabel.style.display = 'none';
          dataVencimentoField.value = "";
        }
      }
    })
    .catch(error => console.error('Erro ao buscar usuário logado:', error));

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.style.borderColor = '#333'; });
  dropzone.addEventListener('dragleave', () => dropzone.style.borderColor = '#bbb');
  dropzone.addEventListener('drop', function (e) {
    e.preventDefault();
    dropzone.style.borderColor = '#bbb';
    if (e.dataTransfer.files.length) {
      for (let file of e.dataTransfer.files) {
        uploadedFiles.push(file);
      }
      atualizarListaArquivos();
    }
  });
  fileInput.addEventListener('change', function (e) {
    for (let file of e.target.files) {
      uploadedFiles.push(file);
    }
    atualizarListaArquivos();
  });

  function atualizarListaArquivos() {
    dropzone.innerHTML = "<p>Arraste seus arquivos ou clique aqui</p>";
    // Se não houver arquivos, exibe "Nenhum arquivo adicionado ainda."
  if (uploadedFiles.length === 0) {
    fileListContainer.innerHTML = "<p>Nenhum arquivo adicionado ainda.</p>";
    fileInput.value = "";
    return;
  }
  // Exibe um título/contador com a quantidade de arquivos
  fileListContainer.innerHTML = `<p style="font-weight: bold;">Total de arquivos: ${uploadedFiles.length}</p>`;
  uploadedFiles.forEach((file, index) => {
      let fileItem = document.createElement("div");
      fileItem.style.display = "flex";
      fileItem.style.justifyContent = "space-between";
      fileItem.style.alignItems = "center";
      fileItem.style.padding = "5px";
      fileItem.style.borderBottom = "1px solid #ddd";
      fileItem.innerHTML = `<span>${file.name}</span> <span style="color:red; cursor:pointer;" onclick="removerArquivo(${index})">[X]</span>`;
      fileListContainer.appendChild(fileItem);
    });
    if (uploadedFiles.length > 0) {
      const dataTransfer = new DataTransfer();
      uploadedFiles.forEach(file => dataTransfer.items.add(file));
      fileInput.files = dataTransfer.files;
    } else {
      fileInput.value = "";
    }
      // Atualiza o valor do fileInput com os arquivos gerenciados em `uploadedFiles`
    const dataTransfer = new DataTransfer();
    uploadedFiles.forEach(file => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;

    console.log("Arquivos no input:");
    uploadedFiles.forEach((file, index) => {
      console.log(`Arquivo ${index + 1}: ${file.name}`);
    });
  }
  window.removerArquivo = function (index) {
    uploadedFiles.splice(index, 1);
    atualizarListaArquivos();
  };
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    console.log("Arquivos que serão enviados no FormData:");
    for (let i = 0; i < fileInput.files.length; i++) {
      console.log(`${fileInput.files[i].name}`);
    }
    if (form.classList.contains("sending")) {
      console.log("Formulário já está sendo enviado, ignorando novo envio.");
      return;
    }
    form.classList.add("sending");
    if (uploadedFiles.length === 0) {
      alert("Por favor, adicione arquivos antes de enviar.");
      form.classList.remove("sending");
      return;
    }
    const usuarioWeb = welcomeText.textContent.replace(/Bem-vindo,?\s*/i, "").replace(/[^\w\s]/g, "").trim();
    let opcaoSetor = fiscalOpcaoElement ? fiscalOpcaoElement.value : "";
    const formData = new FormData();
    formData.append("usuario_web", usuarioWeb);
    formData.append('opcao_setor', opcaoSetor);
    formData.append('login', loginDominio.value);
    formData.append('senha', document.getElementById('senhaDominio').value);
    formData.append('senha_onvio', document.getElementById('senhaOnvio').value);
    if (currentUser !== "Eduardo") {
      formData.append('dataVencimento', dataVencimentoField.value);
    }
    // Função para remover caracteres especiais do nome antes do envio
    function sanitizeFilename(nome) {
        return nome.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
            .replace(/[^a-zA-Z0-9-_]/g, "_");
    }
    // Nome do json criado pelo usuario
    const nomeJsonComparacao = document.getElementById('nomeJsonComparacao').value.trim();
    if (nomeJsonComparacao) {
        formData.append("nome_json_comparacao", sanitizeFilename(nomeJsonComparacao));
    }

    for (let i = 0; i < fileInput.files.length; i++) {
      formData.append('files[]', fileInput.files[i]);
    }
    console.log("Dados enviados no FormData:");
    for (let pair of formData.entries()) {
      console.log(pair[0], pair[1]);
    }
    console.log("Enviando FormData...");
    fetch('/upload', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      alert(data.mensagem);
      if (data.status === "sucesso") {
        uploadedFiles = [];
        atualizarListaArquivos();
        document.getElementById('nomeJsonComparacao').value = "";
      }
    })
    .catch(async error => {
      console.error('Erro ao enviar formulário:', error);
      if (error.response) {
        const errMessage = await error.response.text();
        console.error("Resposta do servidor:", errMessage);
        alert("Erro do servidor: " + errMessage);
      } else {
        alert("Erro ao enviar o arquivo. Verifique sua conexão.");
      }
    })
    .finally(() => {
      form.classList.remove("sending");
    });
  });
  if (logoutButton) {
    logoutButton.addEventListener('click', () => window.location.href = "/logout");
  }

  // ----- Novo código: Modal de Comparação de Listas -----
  // Abrir o modal ao clicar no downloadIcon (ícone de documento com lupa)
  if (downloadIcon) {
    console.log("Elemento downloadIcon encontrado.");
    downloadIcon.addEventListener('click', function(e) {
      e.preventDefault();
      fetch('/limpar-comparacao-sessao', { method: 'POST' }); // Limpa antes de abrir o modal
      console.log("Ícone clicado. Abrindo modal de comparação...");
      const comparisonModal = document.getElementById('comparisonModal');
      if (comparisonModal) {
        comparisonModal.style.display = 'block';
        carregarListas();
      } else {
        console.error("Modal de comparação não encontrado no DOM.");
      }
    });
  } else {
    console.error("downloadIcon não encontrado no DOM!");
  }

  // Função para carregar as listas disponíveis para comparação
function carregarListas() {
  const listaSelect = document.getElementById('listaSelect');

// Remover caracteres especiais
function removerCaracteresEspeciais(str) {
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, "");
}

// Função ajustada para formatar nomes corretamente
function formatarNomeComparacao(nomeArquivo) {
  nomeArquivo = nomeArquivo.normalize("NFC");

  let base = nomeArquivo
    .replace("lista_comparacao_", "")
    .replace(".json", "");

  let partes = base.split("_");

  if (partes.length === 2) {
    // Mensal sem setor: lista_comparacao_Fiscal_202503.json
    let [usuario, mesStr] = partes;
    let ano = mesStr.slice(0, 4);
    let mes = mesStr.slice(4, 6);
    return `${usuario} - Envio mensal (${mes}/${ano})`;
  } else if (partes.length === 3) {
    // Mensal com setor: lista_comparacao_Fiscal_Retenções_202503.json
    let [usuario, setor, mesStr] = partes;
    let ano = mesStr.slice(0,4);
    let mes = mesStr.slice(4,6);
    setor = removerCaracteresEspeciais(setor);
    return `${usuario} - Envio mensal ${setor} (${mes}/${ano})`;
  } else if (partes.length === 4) {
    // Envio único com setor: lista_comparacao_Fiscal_Retenções_20250325_202530.json
    let [usuario, setor, dataStr, horaStr] = partes;
    let ano = dataStr.slice(0,4);
    let mes = dataStr.slice(4,6);
    let dia = dataStr.slice(6,8);
    let hh = horaStr.slice(0,2);
    let mm = horaStr.slice(2,4);
    setor = removerCaracteresEspeciais(setor);
    return `${usuario} - ${setor} envio ${dia}.${mes}.${ano} ${hh}:${mm}`;
  } else {
    // fallback para outros casos
    return nomeArquivo.replace(".json", "");
  }
}

  fetch('/listar-listas')
    .then(response => response.json())
    .then(data => {
      listaSelect.innerHTML = "";
      if (data.listas && data.listas.length > 0) {
        data.listas.forEach(lista => {
          let option = document.createElement("option");
          option.value = lista; // valor real permanece original

          // Ajuste do texto exibido
          if (lista.startsWith("lista_comparacao_")) {
            option.text = formatarNomeComparacao(lista);
          } else {
            // Caso contrário, apenas remove .json
            option.text = lista.replace(".json", "");
          }

          listaSelect.appendChild(option);
        });
      } else {
        let option = document.createElement("option");
        option.value = "";
        option.text = "Nenhuma lista encontrada";
        listaSelect.appendChild(option);
      }
    })
    .catch(err => {
      console.error("Erro ao carregar listas:", err);
      listaSelect.innerHTML = "<option value=''>Erro ao carregar listas</option>";
    });
}


  // Fechar o modal de comparação ao clicar no X ou fora dele
  const comparisonModal = document.getElementById('comparisonModal');
  const closeComparisonModal = document.getElementById('closeComparisonModal');
  if (closeComparisonModal) {
    closeComparisonModal.addEventListener('click', () => {
      comparisonModal.style.display = 'none';
      document.getElementById('listaTexto').value = "";
      document.getElementById('comparisonResult').innerHTML = "";
    });
  }
  window.addEventListener('click', (event) => {
    if (event.target === comparisonModal) {
      comparisonModal.style.display = 'none';
      document.getElementById('listaTexto').value = "";
      document.getElementById('comparisonResult').innerHTML = "";
    }
  });

// Envio para comparação usando o texto colado no textarea
const compareButton = document.getElementById('compareButton');
const comparisonResult = document.getElementById('comparisonResult');
compareButton.addEventListener('click', function () {
  const listaSelect = document.getElementById('listaSelect');
  if (listaSelect.value === "") {
    alert("Por favor, selecione uma lista para comparação.");
    return;
  }
const listaTexto = document.getElementById("listaTexto").value.trim().toUpperCase();
  if (listaTexto === "") {
    alert("Por favor, cole a lista de documentos para comparação no campo.");
    return;
  }
  // Prepara o FormData com o identificador da lista e o texto do textarea
  const formData = new FormData();
  formData.append("lista_id", listaSelect.value);
  formData.append("lista_texto", listaTexto);

  fetch('/comparar-listas', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      let mensagem = "";
      if (data.error) {
        mensagem = "Erro: " + data.error;
      } else if (!data.faltantes || data.faltantes.length === 0) {
        mensagem = "As listas batem perfeitamente.";
      } else {
        mensagem = "Arquivos faltantes:<br><br>" + data.faltantes.join("<br>");
      }
      comparisonResult.innerHTML = mensagem;
    })
    .catch(err => {
      console.error(err);
      comparisonResult.innerHTML = "Erro ao comparar as listas.";
    });
});

// Baixar lista em excel
const downloadExcelBtn = document.getElementById('downloadExcelBtn');

if (downloadExcelBtn) {
  downloadExcelBtn.addEventListener('click', () => {
    const listaSelect = document.getElementById('listaSelect');
    if (!listaSelect.value) {
      alert("Selecione uma lista para baixar!");
      return;
    }

    const lista_id = encodeURIComponent(listaSelect.value);
    const downloadURL = `/baixar-lista-excel?lista_id=${lista_id}`;

    window.open(downloadURL, '_blank');
  });
}


  // Exclusão da lista selecionada
  const deleteListButton = document.getElementById('deleteListButton');
  if (deleteListButton) {
    deleteListButton.addEventListener('click', function () {
      const listaSelect = document.getElementById('listaSelect');
      if (listaSelect.value === "") {
        alert("Por favor, selecione uma lista para exclusão.");
        return;
      }
      const formData = new FormData();
      formData.append("lista_id", listaSelect.value);
      fetch('/excluir-lista', {
        method: 'POST',
        body: formData
      })
        .then(res => res.json())
        .then(data => {
          alert(data.mensagem || data.error);
          carregarListas();
        })
        .catch(err => {
          console.error(err);
          alert("Erro ao excluir a lista.");
        });
    });
  }
});
