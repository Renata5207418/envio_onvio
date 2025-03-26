# Postagem_onvio

Este projeto consiste em uma aplicação web em Flask para upload, gerenciamento e comparação de arquivos, contando também com um worker de processamento em background. A aplicação permite que usuários façam login, realizem upload de arquivos, comparem os arquivos enviados com listas fornecidas e acompanhem logs e status de tarefas em um banco de dados SQLite.

## Sumário

- [Estrutura de Pastas](#estrutura-de-pastas)
- [Principais Funcionalidades](#principais-funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Instalação e Configuração](#instalação-e-configuração)
  - [1. Criar ambiente virtual (opcional)](#1-criar-ambiente-virtual-opcional)
  - [2. Instalar dependências](#2-instalar-dependências)
  - [3. Configurar a aplicação](#3-configurar-a-aplicação)
- [Uso](#uso)
  - [Executando o servidor Flask](#executando-o-servidor-flask)
  - [Executando o worker em background](#executando-o-worker-em-background)
- [Endpoints Principais](#endpoints-principais)
  - [Login](#login-post-login)
  - [Upload de Arquivos](#upload-de-arquivos-post-upload)
  - [Comparação de Listas](#comparação-de-listas-post-comparar-listas)
  - [Geração de Relatório em Excel](#geração-de-relatório-em-excel-get-baixar-lista-excel)
- [Personalização](#personalização)
- [Logs e Histórico](#logs-e-histórico)
- [Como Contribuir](#como-contribuir)
- [Licença](#licença)

---

## Estrutura de Pastas

A estrutura de diretórios do projeto é a seguinte:

```
Postagem_onvio/
│── .venv/                   # Ambiente virtual do Python
│── instance/
│   └── tasks.db             # Banco de dados SQLite
│── logs/                    # Pasta para logs
│── services/                # Serviços do projeto
│   ├── config.py            # Configuração geral
│   ├── db_service.py        # Serviço de banco de dados
│   ├── file_service.py      # Serviço de arquivos
│   ├── log_service.py       # Serviço de logs
│   ├── teste_db.py          # Testes do banco de dados
│   └── users_config.py      # Configuração de usuários
│── static/                  # Arquivos estáticos (CSS, JS, imagens)
│── templates/               # Templates HTML (páginas)
│── uploads/                 # Pasta para uploads de arquivos
│── app.py                   # Arquivo principal da aplicação Flask
│── models.py                # Modelos de dados
│── README.md                # Documentação do projeto
│── requirements.txt         # Dependências do projeto
│── tasks.py                 # Lógica de processamento de tarefas
│── teste_file_service.py    # Testes do serviço de arquivos
│── utils.py                 # Funções utilitárias
│── worker.py                # Script de processamento em background
│── External Libraries/      # Bibliotecas externas (opcional)
└── Scratches and Consoles/  # Rascunhos e consoles (opcional)
```

---

## Principais Funcionalidades

1. **Sistema de Login**: Permite autenticação de usuários para acessar rotas protegidas.  
2. **Upload de Arquivos**: Os arquivos enviados são armazenados em diretórios específicos, baseados no setor ou no usuário logado.
3. **Geração Automática de JSON**: Sempre que arquivos são enviados, um arquivo JSON contendo metadados e informações (login, senha, data de vencimento etc.) é gerado.
4. **Comparação de Listas**: É possível comparar arquivos enviados com uma lista fornecida pelo usuário (digitada ou por arquivo).
5. **Exportação para Excel**: Depois da comparação, gera-se um relatório em `.xlsx` mostrando quais arquivos conferem ou não.
6. **Banco de Dados**: Usa SQLite (armazenado em `instance/tasks.db`) para gerenciar status de tarefas pendentes.
7. **Registro de Logs**: Todas as ações importantes são registradas em arquivos de log na pasta `logs/`.
8. **Processamento em Background**: Um _worker_ gerencia a fila de tarefas e, a cada dia, executa rotinas (como remoção de PDFs antigos).

---

## Tecnologias Utilizadas

- **[Python](https://www.python.org/)** (3.x)
- **[Flask](https://flask.palletsprojects.com/)** para a criação da aplicação web
- **[SQLAlchemy](https://www.sqlalchemy.org/)** para acesso ao banco de dados SQLite
- **[APScheduler](https://apscheduler.readthedocs.io/en/latest/)** para agendamento das tarefas em background
- **[pandas](https://pandas.pydata.org/)** para manipulação e geração de planilhas Excel
- **[Werkzeug](https://werkzeug.palletsprojects.com/)** para utilidades de WSGI e manipulação de arquivos

---

## Instalação e Configuração

### 1. Criar ambiente virtual (opcional)

No diretório do projeto, você pode (opcionalmente) criar um ambiente virtual:

```bash
python -m venv .venv
```

Em seguida, ative o ambiente:

- **Windows**: `.\.venv\Scripts\activate`
- **Linux/Mac**: `source .venv/bin/activate`

### 2. Instalar dependências

Instale as dependências listadas em `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Configurar a aplicação

- **Chave Secreta**: A chave usada para sessões Flask está definida em `app.py`:

  ```python
- app.secret_key = 'minha_chave_secreta_super_segura'
  ```

  Ajuste para um valor seguro em produção.

- **Banco de Dados**: Por padrão, a aplicação usa `sqlite:///tasks.db` dentro de `instance/`.  
  Se quiser usar outro banco ou alterar o caminho, modifique `app.config['SQLALCHEMY_DATABASE_URI']`.

- **Credenciais de Usuários**: Estão em `services/users_config.py`. Lá você pode ajustar ou incluir novos usuários e senhas.

---

## Uso

### Executando o servidor Flask

Na raiz do projeto, execute:

```bash
python app.py
```

Por padrão, o servidor Flask será iniciado em `http://0.0.0.0:4550` com `debug=True`.  
Para um ambiente de produção, considere utilizar um servidor WSGI (Gunicorn, Waitress etc.).

### Executando o worker em background

Abra outro terminal (ou use algum gerenciador de processos) e rode:

```bash
python worker.py
```

O _worker_ utiliza **APScheduler** para:
- Processar todas as tarefas em fila (`status='em_fila'`) diariamente às **19:00**.
- Limpar PDFs antigos (com mais de 30 dias) às **23:59**.

Você pode alterar esses horários dentro de `worker.py`:

```
python
 scheduler.add_job(func=processa_tarefas_pendentes, trigger='cron', hour=19, minute=0)
 scheduler.add_job(limpa_pdfs_antigos, 'cron', hour=23, minute=59, args=[UPLOAD_FOLDER, DIAS_MAXIMO])

```

---

## Endpoints Principais

Abaixo, alguns dos endpoints disponíveis:

### Login (`POST /login`)

- **Descrição**: Realiza autenticação do usuário.  
- **Campos de formulário**:  
  - `usuario`: nome do usuário  
  - `senha`: senha correspondente (definida em `users_config.py`)

Em caso de sucesso, retorna um JSON com a URL para redirecionamento.

### Upload de Arquivos (`POST /upload`)

- **Descrição**: Recebe um ou mais arquivos através do campo `files[]` e salva em `uploads/`.
- **Campos de formulário**:
  - `files[]`: lista de arquivos  
  - `opcao_setor`: nome do setor/diretório (usado na organização de pastas)  
  - `login`, `senha`, `senha_onvio`: informações de login do domínio e Onvio  
  - `dataVencimento`: data de vencimento dos documentos (pode ser extraída automaticamente caso o usuário seja "Eduardo")  
- **Retorno**: JSON indicando sucesso ou falha no upload e criação das tarefas no banco.

### Comparação de Listas (`POST /comparar-listas`)

- **Descrição**: Compara os arquivos enviados (armazenados em um JSON) com uma lista de arquivos provida pelo usuário (texto ou outro arquivo).
- **Campos de formulário**:
  - `lista_id`: nome do arquivo JSON que armazena as informações dos arquivos enviados
  - `lista_texto`: texto com nomes de arquivos (um por linha), opcional
  - `files[]`: arquivos para comparação, caso não seja fornecido `lista_texto`
- **Retorno**: JSON com a lista de arquivos "faltantes" (presentes no envio, mas ausentes na lista do usuário).

### Geração de Relatório em Excel (`GET /baixar-lista-excel`)

- **Descrição**: Gera um arquivo `.xlsx` comparando quais arquivos estão "Ok" e quais não foram conferidos.
- **Parâmetro de query**:
  - `lista_id`: identificador (nome) do JSON de comparação
- **Retorno**: Arquivo Excel para download.

---

## Personalização

- **Agendamentos**: Altere em `worker.py` a frequência de processamento das tarefas e limpeza de PDFs.
- **Logs**: Configure formatos e níveis de log em `services/log_service.py`.
- **Estrutura de Diretórios**: Se quiser separar ainda mais setores ou usuários, basta adaptar o código em `app.py` (função `upload_files`).
- **Arquivos de Template**: As páginas HTML (login, index etc.) ficam em `templates/`. Personalize conforme sua identidade visual.

---

## Logs e Histórico

- As ações de upload, comparação e processamento são salvas em arquivos na pasta `logs/`.
- Cada entrada de log contém timestamp e descrição da ação.  
- A pasta `logs/` pode ser limpa periodicamente, caso fique muito grande.

---

## Como Contribuir

1. **Fork** este repositório.  
2. Crie uma _branch_ com a nova feature ou correção de bug: `git checkout -b minha-feature`.  
3. Faça _commit_ das suas alterações: `git commit -m 'Adiciona nova feature'`.  
4. Faça _push_ para sua _branch_: `git push origin minha-feature`.  
5. Abra um _Pull Request_ no GitHub (ou plataforma que estiver usando).

---
