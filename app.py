import os
import json
import pandas as pd
import io
from datetime import datetime
from flask import Flask, request, render_template, jsonify, session, redirect, url_for, send_file
from services.log_service import registrar_log
from werkzeug.utils import secure_filename
from services.users_config import users
from models import db, TaskStatus


app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_super_segura'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

COMP_LIST_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'listas_comparacao')
if not os.path.exists(COMP_LIST_FOLDER):
    os.makedirs(COMP_LIST_FOLDER)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota de login.

    Se for uma requisição POST, verifica as credenciais do usuário e,
    se forem válidas, inicia uma sessão e redireciona para a página inicial.

    Retorna:
        - Em caso de sucesso: JSON com a URL de redirecionamento.
        - Em caso de erro: JSON com mensagem de erro e status 401.
    """
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        print(f"Tentativa de login: usuário={usuario}, senha={senha}")

        if usuario in users:
            print(f"Usuário encontrado: {usuario}, senha esperada: {users[usuario]}")
        else:
            print(f"Usuário {usuario} não encontrado!")

        if usuario in users and users[usuario] == senha:
            session['usuario'] = usuario
            print("Login bem-sucedido! Redirecionando para /")
            # Retorna JSON com a URL de redirecionamento
            return jsonify(redirect=url_for('index'))
        else:
            print("Usuário ou senha incorretos!")
            # Retorna JSON com a mensagem de erro e status 401
            return jsonify(error="Usuário ou senha inválidos"), 401

    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    Rota para logout.

    Remove o usuário da sessão e redireciona para a tela de login.
    """
    session.pop('usuario', None)
    return redirect(url_for('login'))


@app.route('/')
def index():
    """
    Página inicial.

    Se o usuário não estiver autenticado, redireciona para a página de login.
    Caso contrário, exibe a tela inicial.
    """
    if 'usuario' not in session:
        return redirect(url_for('login'))

    return render_template('index.html', usuario=session['usuario'])


@app.route('/upload', methods=['POST'])
def upload_files():
    """
    Rota para upload de arquivos.

    Recebe arquivos via requisição POST e os salva em diretórios específicos
    com base no usuário e setor selecionado. Também gera arquivos JSON contendo
    metadados sobre os arquivos e dispara um processamento assíncrono.

    Retorna:
        - Em caso de sucesso: JSON com status de sucesso e mensagem.
        - Em caso de erro: JSON com status de erro e mensagem apropriada.
    """
    try:
        print("Recebendo requisição de upload...")

        if 'files[]' not in request.files:
            return jsonify({"status": "erro", "mensagem": "Nenhum arquivo enviado."}), 400

        files = request.files.getlist('files[]')
        if not files:
            return jsonify({"status": "erro", "mensagem": "Nenhum arquivo válido recebido."}), 400

        usuario_web = session.get("usuario")
        opcao_setor = request.form.get("opcao_setor")
        usuario_dominio = request.form.get("login")
        senha_dominio = request.form.get("senha")
        senha_onvio = request.form.get("senha_onvio")
        # Para outros usuários, pode vir do form; para Eduardo será extraída do PDF
        data_vencimento = request.form.get("dataVencimento", None)

        print(f"Usuário: {usuario_web}, Setor: {opcao_setor}")

        arquivos_processados = []
        # Define a pasta e o nome do JSON conforme usuário e setor
        if usuario_web == "Fiscal":
            if opcao_setor:
                folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f"{usuario_web}_{opcao_setor}"))
                json_filename = f"arquivos_pendentes_{usuario_web}_{opcao_setor}.json"
            else:
                folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(usuario_web))
                json_filename = f"arquivos_pendentes_{usuario_web}.json"
        else:
            folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(opcao_setor if opcao_setor
                                                                               else usuario_web))
            json_filename = f"arquivos_pendentes_{usuario_web}.json"

        if not os.path.exists(folder):
            os.makedirs(folder)

        # Processa cada arquivo recebido
        for file in files:
            if file.filename == '':
                print("Arquivo sem nome ignorado.")
                continue

            file_name = file.filename.replace("/", "").replace("\\", "").strip()
            file_path = os.path.join(folder, file_name)
            file_path = os.path.abspath(os.path.normpath(file_path))
            file.save(file_path)

            # Se o usuário for Eduardo, extrai a data de vencimento do PDF
            if usuario_web.lower() == "eduardo":
                from services.file_service import extract_due_date_from_pdf
                vencimento_extraida = extract_due_date_from_pdf(file_path)
                print(f"[DEBUG] Data extraída para {file_name}: {vencimento_extraida}")
            else:
                vencimento_extraida = data_vencimento

            arquivo = {
                "nome_arquivo": file_name,
                "filepath": file_path,
                "setor": opcao_setor,
                "data_vencimento": vencimento_extraida
            }
            arquivos_processados.append(arquivo)

        if not arquivos_processados:
            return jsonify({"status": "erro", "mensagem": "Nenhum arquivo válido foi processado."}), 400

        print(f"Arquivos recebidos e salvos: {[arq['nome_arquivo'] for arq in arquivos_processados]}")

        # JSON para o robô
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_unique_filename = f"arquivos_pendentes_{usuario_web}_{opcao_setor}_{timestamp}.json" if opcao_setor else \
            f"arquivos_pendentes_{usuario_web}_{timestamp}.json"
        arquivos_json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_unique_filename)
        with open(arquivos_json_path, 'w', encoding="utf-8") as json_file:
            json.dump({
                "usuario": usuario_web,
                "login": usuario_dominio,
                "senha": senha_dominio,
                "senha_onvio": senha_onvio,
                "data_vencimento": data_vencimento,
                "arquivos": arquivos_processados
            }, json_file, indent=4)

        print(f"[DEBUG] JSON de organização criado: {arquivos_json_path}")

        # --- Json de envio mensal ---
        mes_atual = datetime.now().strftime("%Y%m")
        if usuario_web == "Fiscal":
            monthly_filename = f"lista_comparacao_{usuario_web}_{opcao_setor}_{mes_atual}.json"
        else:
            monthly_filename = f"lista_comparacao_{usuario_web}_{mes_atual}.json"

        monthly_filepath = os.path.join(COMP_LIST_FOLDER, monthly_filename)

        if os.path.exists(monthly_filepath):
            with open(monthly_filepath, 'r', encoding="utf-8") as mf:
                monthly_data = json.load(mf)
        else:
            monthly_data = {
                "usuario": usuario_web,
                "setor": opcao_setor,
                "mes": datetime.now().strftime("%Y-%m"),
                "envios": []
            }

        new_envio = {
            "timestamp": timestamp,
            "login": usuario_dominio,
            "senha": senha_dominio,
            "senha_onvio": senha_onvio,
            "data_vencimento": data_vencimento,
            "arquivos": arquivos_processados
        }

        monthly_data["envios"].append(new_envio)

        with open(monthly_filepath, 'w', encoding="utf-8") as mf:
            json.dump(monthly_data, mf, indent=4)
        # --- Fim da agregação mensal ---

        # Salva o JSON para a lista de comparação
        nome_json_comparacao = request.form.get("nome_json_comparacao", "").strip()

        comp_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if nome_json_comparacao:
            json_comp_filename = f"{secure_filename(nome_json_comparacao)}_{comp_timestamp}.json"
        else:
            json_comp_filename = (f"lista_comparacao_{usuario_web}_{opcao_setor}_{comp_timestamp}.json"
                                  if opcao_setor else f"lista_comparacao_{usuario_web}_{comp_timestamp}.json")

        json_comp_path = os.path.join(COMP_LIST_FOLDER, json_comp_filename)

        with open(json_comp_path, 'w', encoding="utf-8") as json_file:
            json.dump({
                "usuario": usuario_web,
                "login": usuario_dominio,
                "senha": senha_dominio,
                "senha_onvio": senha_onvio,
                "data_vencimento": data_vencimento,
                "arquivos": arquivos_processados
            }, json_file, indent=4)

        print(f"[DEBUG] JSON de organização criado: {json_comp_path}")

        # Registra a tarefa no banco com status "em_fila"
        nova_tarefa = TaskStatus(
            usuario=usuario_web,
            json_file_path=arquivos_json_path,
            status='em_fila'
        )
        db.session.add(nova_tarefa)
        db.session.commit()
        print(f"[DEBUG] Tarefa registrada no banco com ID: {nova_tarefa.id}")
        registrar_log(
            f"Usuário '{usuario_web}' subiu a lista '{json_unique_filename}' com {len(arquivos_processados)} arquivos.")

        return jsonify({"status": "sucesso", "mensagem": "Arquivos enviados para fila!"})
    except Exception as e:
        print(f"Erro geral no upload: {e}")
        registrar_log(f"Erro no upload por '{usuario_web}': {e}")
        return jsonify({"status": "erro", "mensagem": f"Erro ao processar os arquivos: {e}"}), 500


@app.route('/get-user')
def get_user():
    """
    Retorna o usuário logado na sessão atual.

    Retorna:
        - JSON com o nome do usuário autenticado.
    """
    if 'usuario' in session:
        return jsonify({"user": session['usuario']})
    return jsonify({"user": None})


@app.route('/listar-listas', methods=['GET'])
def listar_listas():
    usuario_web = session.get("usuario")
    if not usuario_web:
        return jsonify({"error": "Usuário não autenticado."}), 401

    listas = [
        filename for filename in os.listdir(COMP_LIST_FOLDER)
        if filename.startswith("lista_comparacao_")
        and usuario_web in filename
        and filename.lower().endswith('.json')
    ]
    listas.sort()
    return jsonify({"listas": listas})


@app.route('/comparar-listas', methods=['POST'])
def comparar_listas():
    """
    Compara a lista de arquivos enviados (salva no JSON) com a lista informada pelo usuário.
    Retorna:
        - JSON com os nomes dos arquivos que foram enviados mas que estão ausentes na lista do usuário.
    """
    usuario_web = session.get("usuario")
    if not usuario_web:
        return jsonify({"error": "Usuário não autenticado."}), 401

    lista_id = request.form.get("lista_id")
    if not lista_id:
        return jsonify({"error": "Identificador da lista (lista_id) não informado."}), 400

    json_comp_path = os.path.join(COMP_LIST_FOLDER, secure_filename(lista_id))
    if not os.path.exists(json_comp_path):
        return jsonify({"error": "Lista informada não existe."}), 400

    try:
        with open(json_comp_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except UnicodeDecodeError:
        return jsonify({"error": "Erro ao ler o arquivo JSON (codificação inválida)."}), 500

    arquivos_enviados = []
    if "arquivos" in dados:
        arquivos_enviados = [item["nome_arquivo"].strip().upper() for item in dados["arquivos"]]
    elif "envios" in dados:
        for envio in dados["envios"]:
            if "arquivos" in envio:
                arquivos_enviados.extend([item["nome_arquivo"].strip().upper() for item in envio["arquivos"]])
    else:
        return jsonify({"error": "Estrutura de lista desconhecida no arquivo selecionado."}), 400

    lista_texto = request.form.get("lista_texto", "").strip()
    if lista_texto:
        lista_usuario = [linha.strip().upper() for linha in lista_texto.splitlines() if linha.strip()]
    else:
        second_files = request.files.getlist("files[]")
        lista_usuario = [file.filename.strip().upper() for file in second_files]

    set_usuario = set(lista_usuario)

    faltantes = [nome for nome in arquivos_enviados if nome not in set_usuario]
    session['ultima_lista_usuario'] = lista_usuario

    registrar_log(
        f"Usuário '{usuario_web}' realizou comparação com lista '{lista_id}' contendo {len(lista_usuario)} itens.")
    return jsonify({"faltantes": faltantes})


@app.route('/baixar-lista-excel', methods=['GET'])
def baixar_lista_excel():
    usuario_web = session.get("usuario")
    if not usuario_web:
        return jsonify({"error": "Usuário não autenticado."}), 401

    lista_id = request.args.get("lista_id")
    if not lista_id:
        return jsonify({"error": "Lista não informada."}), 400

    json_comp_path = os.path.join(COMP_LIST_FOLDER, secure_filename(lista_id))
    if not os.path.exists(json_comp_path):
        return jsonify({"error": "Lista não existe."}), 400

    with open(json_comp_path, 'r', encoding='utf-8') as file:
        dados = json.load(file)

    arquivos = []

    if "arquivos" in dados:
        arquivos = dados["arquivos"]
    elif "envios" in dados:
        for envio in dados["envios"]:
            arquivos.extend(envio["arquivos"])
    else:
        return jsonify({"error": "Formato JSON não suportado."}), 400

    nomes_arquivos = [arquivo["nome_arquivo"].strip().upper() for arquivo in arquivos]

    lista_usuario = session.get('ultima_lista_usuario', [])
    set_usuario = set([nome.strip().upper() for nome in lista_usuario])

    dados_planilha = [
        {
            "Nome do Arquivo": nome,
            "Comparação": "Ok" if nome in set_usuario else "Não conferido"
        }
        for nome in nomes_arquivos
    ]

    df = pd.DataFrame(dados_planilha)

    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    excel_filename = f"{lista_id.replace('.json', '')}_comparado.xlsx"

    return send_file(
        output,
        download_name=excel_filename,
        as_attachment=True
    )


@app.route('/limpar-comparacao-sessao', methods=['POST'])
def limpar_comparacao_sessao():
    session.pop('ultima_lista_usuario', None)
    return jsonify({"status": "ok"})


@app.route('/excluir-lista', methods=['POST'])
def excluir_lista():
    usuario_web = session.get("usuario")
    if not usuario_web:
        return jsonify({"error": "Usuário não autenticado."}), 401

    lista_id = request.form.get("lista_id")
    if not lista_id:
        return jsonify({"error": "Identificador da lista não informado."}), 400

    json_comp_path = os.path.join(COMP_LIST_FOLDER, secure_filename(lista_id))
    if not os.path.exists(json_comp_path):
        return jsonify({"error": "Lista não existe."}), 400

    try:
        os.remove(json_comp_path)

        registrar_log(f"Usuário '{usuario_web}' excluiu a lista '{lista_id}'.")

        return jsonify({"status": "sucesso", "mensagem": "Lista excluída com sucesso."})
    except Exception as e:
        registrar_log(f"Erro ao excluir lista '{lista_id}' pelo usuário '{usuario_web}': {e}")
        return jsonify({"error": f"Erro ao excluir a lista: {e}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
