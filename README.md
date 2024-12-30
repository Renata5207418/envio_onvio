# 🚀 Sistema de Upload e Publicação de Documentos no Domínio  

Este projeto automatiza o processo de upload e publicação de documentos no sistema **Domínio**, utilizado em escritórios contábeis.  

Ele oferece uma interface web simples para que os usuários possam enviar arquivos PDF, validá-los e publicá-los automaticamente na plataforma. O sistema também exibe feedback detalhado sobre os resultados do processamento.  

## 🛠️ Funcionalidades  

- ✅ **Upload de Arquivos PDF:** Validação automática do formato e organização por empresa.  
- 🔎 **Extração de Informações:** Identifica o código da empresa e data a partir do nome do arquivo.  
- 📤 **Publicação Automática:** Envia os documentos diretamente para o sistema Domínio.  
- 🔐 **Integração com Onvio:** Realiza login e sincronização automática (caso necessário).  
- 📊 **Feedback Visual:** Mostra o status do envio (sucesso, parcial ou erro) diretamente na interface.  
- 📝 **Logs Detalhados:** Gera arquivos JSON com o histórico do processamento.  

---

## 🚀 Como Executar
    python app.py

## ⚙️ Pré-requisitos  

- Python 3.12 ou superior instalado.  
- Sistema operacional **Windows** (necessário para integração com o sistema Domínio).  
- Sistema **Domínio** instalado e configurado no caminho especificado no código.  
- Conexão estável com a internet para integração com o Onvio (opcional).  

### 🧩 Instalação  

1. **Clone este repositório:**  
   ```bash
   git clone https://github.com/seu-usuario/sistema-upload-dominio.git
   cd sistema-upload-dominio

### 📋 Logs e Feedback
  - Arquivos de Logs:
  - O sistema gera logs detalhados no formato JSON para rastrear os arquivos processados. Eles são armazenados nos arquivos:
   
  - logs_detalhados.json – Registra sucessos e falhas durante o processamento.
  - arquivos_organizados.json – Exibe a organização dos arquivos por empresa antes do envio.
  - Proteção de Dados nos Logs:
  - Informações sensíveis como nomes de arquivos são mascaradas antes do armazenamento.

  - Interface Visual:
  - A interface web exibe em tempo real o status de cada envio, incluindo erros e confirmações.

### 🔐 Segurança
 - Credenciais Seguras:
 - Nenhuma senha ou informação sensível é armazenada no código.
 - Utilize variáveis de ambiente para gerenciar credenciais de forma segura.
 
 - Validação de Arquivos:
 -  Apenas arquivos PDF com formato válido são aceitos.
 -  Arquivos maliciosos são bloqueados por validação MIME automática.
   
 -  Configuração HTTPS:
 -  Para ambientes de produção, recomenda-se configurar HTTPS e adicionar autenticação adicional para acesso ao sistema.

### 🧑‍💻 Tecnologias Utilizadas
 - Backend: Flask, PyAutoGUI, PyWinAuto.
 - Frontend: HTML, CSS, JavaScript.
 - Automação: Integração com o sistema Domínio.

### 🧩 Observações
 - Somente para Uso Interno
 - Este sistema foi projetado para funcionar em redes internas com acesso restrito.
   
 - Testes e Validações
 - Teste o ambiente em máquinas de homologação antes de implantar em produção.
   


pip install -r requirements.txt
