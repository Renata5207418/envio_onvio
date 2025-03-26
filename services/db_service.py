import sqlanydb
import logging

logging.basicConfig(level=logging.INFO)


class DatabaseConnection:
    def __init__(self, host, port, dbname, user, password):
        self.conn_str = {
            "servername": host,
            "dbn": dbname,
            "userid": user,
            "password": password,
            "LINKS": f"tcpip(host={host};port={port})"
        }
        self.conn = None

    def connect(self):
        """Estabelece conexão com o banco de dados."""
        try:
            logging.info(
                f"Tentando conectar ao banco: {self.conn_str['dbn']} em {self.conn_str['servername']}:"
                f"{self.conn_str['LINKS']}")
            self.conn = sqlanydb.connect(**self.conn_str)
        except sqlanydb.Error as e:
            logging.error(f"Erro ao conectar ao banco de dados: {e}")
            self.conn = None

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn is not None:
            self.conn.close()

    def execute_query(self, query, params=None):
        """Executa uma consulta SQL e retorna os resultados."""
        if self.conn is None:
            logging.error("Conexão ao banco não estabelecida.")
            return None
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            resultados = cursor.fetchall()
            return resultados
        except sqlanydb.Error as e:
            logging.error(f"Erro ao executar a consulta: {e}")
            return None
        finally:
            cursor.close()


def get_empresa_codigo(cnpj):
    """Busca o código da empresa (codi_emp) a partir do CNPJ (cgce_emp)."""
    logging.info(f"🔍 Buscando código da empresa para o CNPJ: {cnpj}")

    # Configuração do banco de dados
    db_params = {
        "host": "dominio",
        "port": 2638,
        "dbname": "contabil",
        "user": "AUTOMACAOE",
        "password": "123456"
    }

    db_conn = DatabaseConnection(**db_params)
    db_conn.connect()

    if not db_conn.conn:
        logging.error("❌ Conexão com o banco falhou. Encerrando busca.")
        return None

    # Consulta SQL para buscar apenas o código da empresa
    query = "SELECT codi_emp FROM bethadba.geempre WHERE cgce_emp = ?;"

    resultado = db_conn.execute_query(query, (cnpj,))
    db_conn.close()

    if resultado:
        codigo_empresa = resultado[0][0]
        logging.info(f"✅ Código da empresa encontrado: {codigo_empresa}")
        return codigo_empresa
    else:
        logging.error(f"❌ Empresa com CNPJ '{cnpj}' não encontrada.")
        return None
