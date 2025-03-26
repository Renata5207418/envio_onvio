from db_service import get_empresa_codigo

if __name__ == '__main__':
    # Substitua pelo número do CNPJ desejado para teste
    cnpj_teste = "12287467000143"

    codigo = get_empresa_codigo(cnpj_teste)

    if codigo:
        print(f"Código da empresa para o CNPJ {cnpj_teste}: {codigo}")
    else:
        print(f"Empresa com o CNPJ {cnpj_teste} não encontrada.")
