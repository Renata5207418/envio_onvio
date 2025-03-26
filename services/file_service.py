import re
import PyPDF2


def extract_due_date_from_pdf(file_path):
    """Extrai a data de vencimento do PDF e retorna no formato DDMMYYYY."""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            texto = reader.pages[0].extract_text()

        # Lista de padrões a serem testados
        patterns = [
            r'Vencimento[:\s]+(\d{2}/\d{2}/\d{4})',
            r'Venc[:\s]+(\d{2}/\d{2}/\d{4})',
            r'Data\s+de\s+Vencimento[:\s]+(\d{2}/\d{2}/\d{4})'
        ]
        vencimento = None
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                vencimento = match.group(1).replace('/', '')
                print(f"[DEBUG] Data de vencimento extraída com padrão '{pattern}': {vencimento}")
                break

        if not vencimento:
            print(f"[AVISO] Nenhuma data de vencimento encontrada no PDF {file_path}.")
        return vencimento

    except Exception as e:
        print(f"[ERRO] Falha ao extrair data de vencimento do PDF {file_path}: {e}")
        return None


# pdf_directory = r"C:\Users\usuario\Documents\RENATA\Envio_por_onvio\ROBO\HOLERITE"
# Itera sobre todos os arquivos da pasta IMPORTAR OS NA HORA DE TESTAR
# for filename in os.listdir(pdf_directory):
#    if filename.lower().endswith(".pdf"):
#        filepath = os.path.join(pdf_directory, filename)
#        due_date = extract_due_date_from_pdf(filepath)
#        print(f"Arquivo: {filename} - Data de vencimento: {due_date}")
