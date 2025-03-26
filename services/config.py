# Configuração dos usuários e seus caminhos
USERS_CONFIG = {
    "Fiscal": {
        "caminho_executavel": "C:\\Contabil\\contabil.exe",
        "pastas_opcoes": {
            "Impostos": [["FISCAL", "Fiscal"], ["IMPOSTOS", "Impostos"], ["ano"], ["mes_ano"]],
            "Parcelamentos": [["FISCAL", "Fiscal"], ["PARCELAMENTOS", "Parcelamentos"], ["ano"], ["mes_ano"]],
            "Retenções": [["FISCAL", "Fiscal"], ["RETENÇÕES", "Retenções"], ["ano"], ["mes_ano"]]

        }
    },
    "RH": {
        "caminho_executavel": "C:\\Contabil\\contabil.exe",
        "pastas_base": [
            ["PESSOAL", "Pessoal"], ["ano"], ["FOLHA DE PAGAMENTO", "Folha de Pagamento"], ["mes_ano"]
        ]
    },
    "CND": {
        "caminho_executavel": "C:\\Contabil\\contabil.exe",
        "pastas_base": [
            ["CERTIDÃO NEGATIVA DE DÉBITO", "Certidão Negativa de Débito"], ["ano"], ["mes_ano"]
        ]
    },
    "Eduardo": {
        "caminho_executavel": "C:\\Contabil\\contabil.exe",
        "pastas_base": [
            ["FINANCEIRO", "Financeiro"], ["ano"]
        ]
    }
}
