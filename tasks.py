import os
import json
import shutil
import time
from utils import PostaDocumentos
from services.config import USERS_CONFIG
from services.log_service import registrar_log
from models import db, TaskStatus

# Definições de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_PATH = os.path.join(BASE_DIR, "uploads")
PROCESSED_PATH = os.path.join(UPLOADS_PATH, "processados")
os.makedirs(PROCESSED_PATH, exist_ok=True)


def processa_fila(json_file_path):
    registrar_log(f"Processando arquivos a partir do JSON: {json_file_path}")

    if not os.path.exists(json_file_path):
        registrar_log(f"Arquivo JSON de pendências não encontrado: {json_file_path}")
        return f"[ERROR] Arquivo JSON de pendências não encontrado: {json_file_path}"

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError:
        registrar_log("JSON corrompido! Criando um novo arquivo vazio.")
        return "[ERROR] JSON corrompido."

    usuario_web = dados.get("usuario")
    usuario_dominio = dados.get("login")
    senha_dominio = dados.get("senha")
    senha_onvio = dados.get("senha_onvio")
    data_vencimento = dados.get("data_vencimento")
    arquivos = dados.get("arquivos", [])

    if not arquivos:
        registrar_log(f"Nenhum arquivo pendente para o usuário {usuario_web}.")
        return f"[ERROR] Nenhum arquivo pendente para o usuário {usuario_web}."

    registrar_log(f"Organizando {len(arquivos)} arquivos para o usuário: {usuario_web}")

    # Processa os arquivos e posta os documentos
    resultado = processar_postagem(arquivos, usuario_web, usuario_dominio, senha_dominio, senha_onvio, data_vencimento)

    # Move o JSON processado para a pasta de processados
    user_processed_folder = os.path.join(PROCESSED_PATH, usuario_web)
    os.makedirs(user_processed_folder, exist_ok=True)
    shutil.move(json_file_path, os.path.join(user_processed_folder, os.path.basename(json_file_path)))
    registrar_log(f"Arquivo {os.path.basename(json_file_path)} movido para {user_processed_folder}.")

    return f"Arquivos organizados e enviados para postagem para o usuário {usuario_web}."


def processar_postagem(arquivos, usuario_web, usuario_dominio, senha_dominio, senha_onvio, data_vencimento):
    postagem = None
    try:
        if isinstance(arquivos, dict):
            arquivos = [arquivos]

        if not arquivos:
            registrar_log(f"[ERRO] Nenhum arquivo para processar para o usuário {usuario_web}.")
            return f"ERRO: Nenhum arquivo para processar para o usuário {usuario_web}."

        primeiro_arquivo = arquivos[0]
        nome_arquivo = primeiro_arquivo.get("nome_arquivo")
        if not nome_arquivo:
            registrar_log(f"[ERRO] Nome do arquivo inválido ou ausente para {usuario_web}.")
            return "ERRO: Nome do arquivo inválido."

        caminho_executavel = USERS_CONFIG.get(usuario_web, {}).get("caminho_executavel")
        if not caminho_executavel:
            registrar_log(f"[ERRO] Caminho executável não definido para o usuário {usuario_web}.")
            return "ERRO: Caminho executável não definido."

        postagem = PostaDocumentos(
            config_usuario=USERS_CONFIG.get(usuario_web),
            usuario_web=usuario_web,
            usuario_dominio=usuario_dominio,
            senha_dominio=senha_dominio,
            senha_onvio=senha_onvio,
            caminho_documento="",
            nome_documento="",
            ano="",
            mes_ano="",
            empresa="",
            data_vencimento=data_vencimento,
            opcao=""
        )

        postagem.abrir_sistema()
        postagem.fazer_login()

        for arquivo in arquivos:
            current_nome = arquivo.get("nome_arquivo")
            if not current_nome:
                registrar_log("Nome do arquivo inválido ou ausente.")
                continue

            start_time = time.time()
            registrar_log(f"Iniciando processamento do arquivo {current_nome} em {time.strftime('%H:%M:%S')}")

            ano = None
            mes_ano = None
            codigo_empresa = None
            opcao = arquivo.get("setor", "")
            data_vencimento_final = data_vencimento

            if usuario_web.lower() == "eduardo":
                partes = current_nome.split('_')
                if len(partes) < 4:
                    registrar_log("Formato de nome de arquivo inválido para Eduardo.")
                    continue

                cnpj = partes[0]
                doc_type = partes[1].upper()

                from services.db_service import get_empresa_codigo
                codigo_empresa = get_empresa_codigo(cnpj)
                if not codigo_empresa:
                    registrar_log(f"[ERRO] Código da empresa não encontrado para o CNPJ {cnpj}.")
                    continue

                data_vencimento_final = arquivo.get("data_vencimento")

                ano_str = partes[-1]
                if ano_str.lower().endswith('.pdf'):
                    ano_str = ano_str[:-4]

                ano = "20" + ano_str if len(ano_str) == 2 else ano_str
                mes_ano = partes[2]

                # Se for NF, verificar correspondência de HONORARIO antes
                if doc_type == "NF":
                    arquivo_honorario_esperado = f"{cnpj}_HONORARIO_{mes_ano}_{ano_str}.pdf"

                    nomes_arquivos_enviados = {arq["nome_arquivo"].upper() for arq in arquivos}

                    if arquivo_honorario_esperado.upper() not in nomes_arquivos_enviados:
                        registrar_log(f"[IGNORADO] NF'{current_nome}' "
                                      f"sem correspondente HONORARIO '{arquivo_honorario_esperado}'")
                        continue
                    else:
                        registrar_log(
                            f"[OK] NF '{current_nome}' possui HONORARIO correspondente '{arquivo_honorario_esperado}'.")

                elif doc_type == "HONORARIO":
                    if not data_vencimento_final:
                        registrar_log(
                            f"[ERRO] HONORARIO '{current_nome}' sem data de vencimento definida.")
                        continue

            elif usuario_web.lower() == "cnd":
                partes = current_nome.split('-')
                codigo_empresa = partes[0].strip()
                from datetime import datetime
                now = datetime.now()
                ano = now.strftime("%Y")
                mes_ano = now.strftime("%m.%Y")

            else:
                partes_data = current_nome.split('-')[-1].split('.')[0]
                mes_ano = f"{partes_data[:2]}.{partes_data[2:]}"
                ano = partes_data[2:]
                codigo_empresa = current_nome.split('-')[0]
                data_vencimento_final = data_vencimento
                registrar_log(f"[INFO] Data de vencimento final utilizada: {data_vencimento_final}")

            ignored_codes = ["3025", "3026", "3027", "3028", "3029", "3030", "3031", "3032"]
            if codigo_empresa in ignored_codes:
                registrar_log(f"[INFO] Documentos ignorados, empresa {codigo_empresa} está na lista de exclusão.")
                continue

            if usuario_web.lower() == "fiscal":
                if not opcao:
                    registrar_log("[ERRO] Setor não definido para o usuário Fiscal.")
                    continue
                else:
                    registrar_log(f"[INFO] Setor definido para Fiscal: {opcao}")
            else:
                registrar_log(f"[INFO] Usuário {usuario_web} não precisa de setor. Valor recebido: '{opcao}'")

            postagem.caminho_documento = arquivo.get("filepath", "")
            postagem.nome_documento = current_nome
            postagem.ano = ano
            postagem.mes_ano = mes_ano
            postagem.empresa = codigo_empresa
            postagem.data_vencimento = data_vencimento_final
            postagem.opcao = opcao

            postagem.entrar_no_campo_upload()
            registrar_log(f"Arquivo {current_nome} postado com sucesso para a empresa {codigo_empresa}.")

            end_time = time.time()
            duration = end_time - start_time
            registrar_log(f"Processamento do arquivo {current_nome} finalizado em {duration:.2f} segundos.")

        registrar_log(f"[SUCESSO] Processamento do lote finalizado para o usuário {usuario_web}.")

        return "Postagem concluída com sucesso. Task finalizada corretamente."

    except Exception as e:
        registrar_log(f"[ERRO] Falha ao postar para o usuário {usuario_web}: {e}")
        return f"ERRO: {e}"
    finally:
        if postagem is not None:
            try:
                postagem.fechar_dominio()
            except Exception as fe:
                registrar_log(f"Erro ao fechar o sistema: {fe}")


def processa_tarefa(task_id):
    """
    Função para buscar a tarefa pelo ID, atualizar seu status e processá-la.
    """
    tarefa = TaskStatus.query.get(task_id)
    if not tarefa:
        registrar_log(f"Tarefa com ID {task_id} não encontrada.")
        return

    try:
        tarefa.status = 'processando'
        db.session.commit()

        resultado = processa_fila(tarefa.json_file_path)
        registrar_log(f"Resultado do processamento: {resultado}")

        tarefa.status = 'finalizado'
        db.session.commit()
        registrar_log(f"Tarefa {task_id} finalizada com sucesso.")
    except Exception as e:
        tarefa.status = 'erro'
        tarefa.error = str(e)
        db.session.commit()
        registrar_log(f"Erro ao processar tarefa {task_id}: {e}")
