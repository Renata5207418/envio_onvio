import time
from datetime import datetime
from flask import Flask, request, render_template, jsonify
import os
import json
from utils import PostaDocumentos
from collections import defaultdict
import pyautogui

"""
Arquivo: app.py
Descrição: Aplicação Flask para upload e publicação automatizada de documentos no sistema Domínio.
Autor: Renata Scharf
Data: Dezembro/2024
Versão: 1.0.0

Funcionalidades:
- Recebe arquivos PDF enviados pelo usuário.
- Valida e organiza os arquivos por empresa.
- Publica os documentos no sistema Domínio usando automação com PyAutoGUI e PyWinAuto.
- Gera logs detalhados do processamento.

Dependências:
- Flask
- PyAutoGUI
- PyWinAuto
- JSON
- datetime
- os
"""

app = Flask(__name__)

# Diretório para salvar uploads temporariamente
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuração do Flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limitar upload a 16MB por arquivo

# Carregar o mapeamento de empresas
EMPRESAS_PATH = 'data/empresas.json'
if os.path.exists(EMPRESAS_PATH):
    with open(EMPRESAS_PATH, 'r') as f:
        EMPRESAS = json.load(f)
else:
    EMPRESAS = {}


# Página inicial (frontend)
@app.route('/')
def index():
    """
       Rota para carregar a página inicial do sistema (frontend).
       Renderiza o template HTML 'index.html'.
    """
    return render_template('index.html')


def formatar_data(data):
    """
        Remove caracteres não numéricos de uma data e retorna no formato DDMMYYYY.
    """
    return ''.join(filter(str.isdigit, data))


# Endpoint para upload
@app.route('/upload', methods=['POST'])
def upload_files():
    """
        Endpoint para realizar o upload de arquivos PDF e publicá-los no sistema Domínio.
    """
    try:
        files = request.files.getlist('files')
        arquivos_por_empresa = defaultdict(list)

        # Organizar os arquivos por empresa
        for file in files:
            nome_arquivo = file.filename
            if not nome_arquivo.endswith('.pdf'):
                print(f"Arquivo ignorado por não ser PDF: {nome_arquivo}")
                continue

            caminho_arquivo = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))
            file.save(caminho_arquivo)

            partes = nome_arquivo.split('-')
            if len(partes) < 2:
                print(f"Arquivo ignorado por nome inválido: {nome_arquivo}")
                continue

            codigo_empresa = partes[0]
            if not codigo_empresa.isdigit():
                print(f"Código da empresa inválido no arquivo: {nome_arquivo}")
                continue

            arquivos_por_empresa[codigo_empresa].append({
                "nome_arquivo": nome_arquivo,
                "caminho_arquivo": caminho_arquivo
            })

        # Salvar a organização em um arquivo JSON para rastreabilidade
        with open('arquivos_organizados.json', 'w') as f:
            json.dump(arquivos_por_empresa, f, indent=4, default=str)
        print("Organização salva no arquivo 'arquivos_organizados.json'")

        # Validação da Data de Vencimento
        data_vencimento = request.form.get('data_vencimento')
        if data_vencimento:
            try:
                # Valida a data diretamente no formato dd/mm/aaaa
                data_vencimento_formatada = datetime.strptime(data_vencimento, "%d/%m/%Y").date()

                # Valida se a data não é anterior a hoje
                if data_vencimento_formatada < datetime.now().date():
                    raise ValueError("A data de vencimento não pode ser anterior à data atual.")
                data_vencimento_formatada = data_vencimento_formatada.strftime("%d/%m/%Y")

            except ValueError as e:
                return jsonify({"status": "erro", "mensagem": f"Data inválida: {e}"}), 400
        else:
            data_vencimento_formatada = None

        # Processar os arquivos agrupados por empresa
        feedback = []
        processor = PostaDocumentos(
            caminho_executavel="CAMINHO_EXECUTAVEL.exe",
            usuario=request.form.get('login'),
            senha_dominio=request.form.get('senha'),
            senha_onvio=request.form.get('senha_onvio'),
            caminho_documento=None,
            nome_documento=None,
            ano=None,
            mes_ano=None,
            empresa=None,
            data_vencimento=data_vencimento_formatada
        )

        try:
            processor.abrir_sistema()
            processor.fazer_login()

            for codigo_empresa, arquivos in arquivos_por_empresa.items():
                print(f"Processando todos os arquivos para a empresa {codigo_empresa} de uma vez...")
                erros_empresa = []  # Lista para capturar erros individuais
                sucesso_empresa = []

                try:
                    processor.processar_multiplos(arquivos, codigo_empresa)

                    for arquivo in arquivos:
                        try:
                            # Aqui verificamos a publicação individual
                            sucesso_empresa.append({
                                "nome_arquivo": arquivo["nome_arquivo"],
                                "status": "sucesso"
                            })
                        except Exception as e:
                            erro_individual = {
                                "nome_arquivo": arquivo["nome_arquivo"],
                                "status": "erro",
                                "motivo": f"Erro individual no arquivo: {str(e)}"
                            }
                            erros_empresa.append(erro_individual)
                            print(erro_individual)

                except Exception as e:
                    print(f"Erro ao processar os arquivos da empresa {codigo_empresa}: {e}")
                    erros_empresa.append({
                        "empresa": codigo_empresa,
                        "status": "erro",
                        "motivo": str(e),
                        "arquivos": [arquivo["nome_arquivo"] for arquivo in arquivos]
                    })

                feedback.append({
                    "empresa": codigo_empresa,
                    "status": "sucesso" if not erros_empresa else "parcial",
                    "sucessos": sucesso_empresa,
                    "erros": erros_empresa
                })

                # Confirmar e reiniciar janela de upload
                processor.verificar_e_fechar_atencao()
                print(f"Concluído os arquivos da empresa {codigo_empresa}. Reiniciando janela de upload...")
                pyautogui.press("ESC")
                time.sleep(2)

        finally:
            processor.fechar_dominio()

        # Contagem de sucesso e erro
        total_arquivos = sum(len(arquivos) for arquivos in arquivos_por_empresa.values())
        sucesso = sum(1 for r in feedback if r['status'] == 'sucesso')
        erro = sum(1 for r in feedback
                   if r['status'] != 'sucesso')

        # Salvar log detalhado
        with open('logs_detalhados.json', 'w') as f:
            json.dump(feedback, f, indent=4)
        print("Logs detalhados salvos no arquivo 'logs_detalhados.json'")

        # Resposta JSON final
        return jsonify({
            "status": "sucesso" if erro == 0 else "parcial",
            "mensagem": f"{total_arquivos} recebido(s), {sucesso} processado(s) com sucesso, {erro} com erro.",
            "detalhes": feedback
        })

    except Exception as e:
        print(f"Erro no upload: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
