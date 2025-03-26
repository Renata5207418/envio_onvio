import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
from models import TaskStatus
from tasks import processa_tarefa
from app import app
from services.log_service import registrar_log

UPLOAD_FOLDER = 'uploads/'
DIAS_MAXIMO = 30


def processa_tarefas_pendentes():
    """
    Processa sequencialmente todas as tarefas pendentes com status 'em_fila' armazenadas no banco de dados.

    Essa função realiza as seguintes etapas:
    - Consulta o banco de dados para obter uma lista das tarefas pendentes (status='em_fila').
    - Itera sobre cada tarefa encontrada, processando uma de cada vez por meio da função `processa_tarefa(id)`.
    - Após cada tarefa processada (exceto a última), aguarda uma pausa de 10 minutos antes de continuar com a próxima.
    """
    with app.app_context():
        try:
            tarefas = TaskStatus.query.filter_by(status='em_fila').all()
            total_tasks = len(tarefas)
            registrar_log(f"Iniciando processamento de {total_tasks} tarefas pendentes.")

            for idx, tarefa in enumerate(tarefas):
                registrar_log(f"Iniciando tarefa ID: {tarefa.id}")
                processa_tarefa(tarefa.id)
                registrar_log(f"Tarefa ID: {tarefa.id} processada com sucesso.")

                if idx < total_tasks - 1:
                    registrar_log("Aguardando 10 minutos antes de processar a próxima tarefa.")
                    time.sleep(600)

            registrar_log("Processamento de todas as tarefas pendentes concluído.")
        except Exception as e:
            registrar_log(f"Erro geral ao processar tarefas pendentes: {e}")


def limpa_pdfs_antigos(diretorio, dias_maximo):
    """
    Remove arquivos PDF antigos de forma recursiva dentro do diretório especificado.

    Essa função realiza as seguintes ações:
    - Percorre todas as pastas e subpastas a partir do diretório informado.
    - Verifica a idade dos arquivos PDF encontrados.
    - Remove arquivos PDF cuja última modificação tenha ultrapassado a idade máxima definida.
    """
    agora = time.time()
    idade_maxima = dias_maximo * 86400
    arquivos_removidos = 0

    with app.app_context():
        try:
            registrar_log(f"Iniciando limpeza de PDFs antigos em '{diretorio}'.")
            for pasta_raiz, pastas, arquivos in os.walk(diretorio):
                for arquivo in arquivos:
                    if arquivo.lower().endswith('.pdf'):
                        caminho_arquivo = os.path.join(pasta_raiz, arquivo)
                        tempo_modificacao = os.path.getmtime(caminho_arquivo)
                        if agora - tempo_modificacao > idade_maxima:
                            os.remove(caminho_arquivo)
                            arquivos_removidos += 1
                            registrar_log(f"PDF removido por tempo expirado: {caminho_arquivo}")

            registrar_log(f"Limpeza concluída. Total de PDFs removidos: {arquivos_removidos}.")
        except Exception as e:
            registrar_log(f"Erro geral ao limpar PDFs antigos: {e}")


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=processa_tarefas_pendentes, trigger='cron', hour=19, minute=0)
    scheduler.add_job(limpa_pdfs_antigos, 'cron', hour=23, minute=59, args=[UPLOAD_FOLDER, DIAS_MAXIMO])
    scheduler.start()

    registrar_log("Scheduler iniciado. Aguardando execução agendada.")

    try:
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        registrar_log("Scheduler desligado manualmente.")
