import os
import argparse
from services.file_service import (
    extract_due_date_from_pdf,
    extract_text_from_pdf,
    parse_file_info,
    generate_new_filename
)


def test_all_pdfs(directory):
    if not os.path.isdir(directory):
        print(f"[ERRO] O caminho {directory} não é um diretório válido.")
        return

    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("[AVISO] Nenhum arquivo PDF encontrado no diretório.")
        return

    for pdf_file in pdf_files:
        file_path = os.path.join(directory, pdf_file)
        print(f"\nProcessando: {pdf_file}")

        # Extrai o texto completo do PDF
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            print("[AVISO] Nenhum texto extraído do PDF.")
            continue

        # Testa a extração da data de vencimento (somente a primeira página)
        due_date = extract_due_date_from_pdf(file_path)

        # Testa o parse do texto para extrair info
        info = parse_file_info(text)

        # Testa a geração do novo nome do arquivo
        new_filename = generate_new_filename(file_path)

        print("----- RESULTADOS -----")
        print(f"Data de vencimento extraída (extract_due_date_from_pdf): {due_date}")
        print(f"Informações extraídas (parse_file_info): {info}")
        print(f"Novo nome gerado (generate_new_filename): {new_filename}")
        print("-" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teste as funções do file_service.py em todos os PDFs de um diretório")
    parser.add_argument("directory", help="Caminho do diretório com os arquivos PDF")
    args = parser.parse_args()
    test_all_pdfs(args.directory)
