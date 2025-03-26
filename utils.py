import pyautogui
from datetime import datetime
from pywinauto import Application, findwindows
import subprocess
import time


class PostaDocumentos:
    """
    Classe responsável por automatizar a publicação de documentos no sistema Domínio.
    Utiliza a configuração do usuário (obtida no config.py) para definir os caminhos,
    onde o 'usuário_web' define a configuração (caminho executável, pastas, etc.) e o
    'usuário_dominio' é o login que será utilizado no sistema Domínio.
    """

    def __init__(self, config_usuario, usuario_web, usuario_dominio, senha_dominio, senha_onvio,
                 caminho_documento, nome_documento, ano, mes_ano, empresa, data_vencimento, opcao=None):
        """
        Parâmetros:
          - config_usuario: dicionário com a configuração do usuário (extraído do USERS_CONFIG).
          - usuario_web: usuário que define qual configuração utilizar.
          - usuario_dominio: usuário para login no sistema Domínio.
          - senha_dominio, senha_onvio: senhas para os respectivos logins.
          - caminho_documento, nome_documento, ano, mes_ano, empresa, data_vencimento: demais parâmetros do robô.
          - opcao: para usuários com "pastas_opcoes", indica qual opção utilizar (ex.: "Impostos").
        """
        self.config = config_usuario
        self.usuario_web = usuario_web
        self.usuario_dominio = usuario_dominio
        self.senha_dominio = senha_dominio
        self.senha_onvio = senha_onvio
        self.caminho_documento = caminho_documento
        self.nome_documento = nome_documento
        self.ano = ano
        self.mes_ano = mes_ano
        self.empresa = empresa
        self.data_vencimento = data_vencimento
        self.opcao = opcao

        # Obtém o caminho do executável a partir da configuração
        self.caminho_executavel = self.config.get("caminho_executavel")

    def processar(self):
        """
        Processa a publicação do documento no sistema Domínio.
        """
        try:
            self.abrir_sistema()
            self.fazer_login()
            self.entrar_no_campo_upload()
        finally:
            self.fechar_dominio()

    def processar_multiplos(self, arquivos, codigo_empresa):
        """
        Processa múltiplos arquivos para a mesma empresa, mantendo o Domínio aberto.
        """
        try:
            print(f"Processando múltiplos arquivos para a empresa {codigo_empresa}...")

            # Atualiza os atributos necessários
            self.empresa = codigo_empresa

            # Extrai o ano e o mês do primeiro arquivo para a pasta
            primeiro_arquivo = arquivos[0]["nome_arquivo"]
            partes = primeiro_arquivo.split('-')[-1].split('.')[0]
            self.mes_ano = f"{partes[:2]}.{partes[2:]}"
            self.ano = partes[2:]

            # Acessa o campo de upload e envia todos os arquivos juntos
            self.entrar_no_campo_upload()
            print(f"Arquivos enviados com sucesso para a empresa {codigo_empresa}.")

        except Exception as e:
            print(f"Erro ao processar múltiplos arquivos para a empresa {codigo_empresa}: {e}")
            raise

    def abrir_sistema(self):
        """
         Abre o sistema Domínio para iniciar o processo de postagem.
         """
        try:
            print("Abrindo o Sistema Domínio...")
            subprocess.Popen([self.caminho_executavel, '/escrita'])
            print("Sistema Domínio aberto com sucesso.")
            time.sleep(15)  # Aguardar o carregamento inicial do sistema
        except Exception as e:
            print(f"Erro ao tentar abrir o sistema: {e}")

    def fazer_login(self):
        """
        Realiza o login no sistema Domínio utilizando as credenciais fornecidas.
        """
        try:
            print("Tentando login no sistema Domínio...")
            app = Application(backend="uia").connect(path=self.caminho_executavel)
            login_window = app.window(title_re="Conectando.*")
            login_window.wait('visible', timeout=30)

            # Preencher usuário
            usuario_field = login_window.child_window(auto_id="1005", control_type="Edit")
            usuario_field.click_input(double=True)
            usuario_field.type_keys("{DEL}")
            usuario_field.type_keys(self.usuario_dominio, with_spaces=True)
            print(f"Usuário {self.usuario_dominio} inserido.")

            # Preencher senha
            login_window.child_window(auto_id="1007", control_type="Edit").type_keys(self.senha_dominio,
                                                                                     with_spaces=True)
            print("Senha do Domínio inserida.")

            # Clicar no botão "OK"
            login_window.child_window(auto_id="1003", title="OK").click()
            time.sleep(15)  # Esperar carregar após login
            print("Login realizado com sucesso.")
        except Exception as e:
            print(f"Erro ao realizar o login: {e}")

    def entrar_no_campo_upload(self):
        """Navega para o campo de upload e preenche os campos necessários."""
        try:
            print("Tentando acessar o campo de upload...")

            app = Application(backend="uia").connect(path=self.caminho_executavel)
            janela_principal = app.window(title_re="Domínio Escrita Fiscal.*")

            # Clicar no botão de upload
            botao_upload = janela_principal.child_window(auto_id="picturePublicacaoDocumentosExternos",
                                                         control_type="Pane")
            botao_upload.click_input()
            time.sleep(3)

            if self.verificar_aviso_onvio():
                print("Aviso detectado. Conectando ao Onvio...")
                if not self.realizar_login_onvio():
                    print("Login do Onvio não realizado. Continuando para a janela de upload...")

                print("Clicando novamente no botão de upload...")
                botao_upload.click_input()
                time.sleep(3)

            print("Acessando a janela de upload 'Publicação de Documentos Externos'...")
            janela_upload = app.window(class_name="FNWND3190")

            if not janela_upload.exists(timeout=5):
                raise Exception("Não foi possível acessar a janela de upload 'Publicação de Documentos Externos'.")

            janela_upload.set_focus()
            print("Janela 'Publicação de Documentos Externos' acessada com sucesso.")

            self.preencher_campos_publicacao(janela_upload)

            print("Confirmando a publicação...")
            botao_publicar = janela_upload.child_window(title="Publicar", auto_id="1003", control_type="Button")
            if botao_publicar.exists():
                botao_publicar.click_input()
                print("Publicação concluída com sucesso.")
            else:
                raise Exception("Botão 'Publicar' não encontrado.")

            time.sleep(2)
            pyautogui.press("enter")
            time.sleep(2)
            pyautogui.press("esc")

        except Exception as e:
            print(f"Erro ao entrar no campo de upload: {e}")

    def preencher_campos_publicacao(self, janela_upload):
        """
            Preenche os campos necessários na janela de publicação de documentos.
        """
        try:
            print("Preenchendo os campos de publicação...")

            # Preencher o campo do caminho do(s) documento(s)
            campo_caminho_documentos = janela_upload.child_window(auto_id="1013", control_type="Edit")
            if campo_caminho_documentos.exists(timeout=10):
                # Verifica se o campo já está preenchido
                valor_atual = campo_caminho_documentos.get_value()
                if valor_atual:
                    print(f"[AVISO] O campo de caminho já está preenchido com: {valor_atual}."
                          f" Reiniciando a janela de upload.")
                    pyautogui.press("esc")
                    time.sleep(2)
                    self.entrar_no_campo_upload()
                    return
                # Se o campo estiver vazio, preenche normalmente
                campo_caminho_documentos.click_input()
                campo_caminho_documentos.type_keys(self.caminho_documento, with_spaces=True)
                print("Caminho do documento preenchido.")
            else:
                raise Exception("Campo 'Caminho do(s) documento(s)' não encontrado.")

            # Preencher o campo "Empresa"
            campo_empresa = janela_upload.child_window(auto_id="1001", class_name="PBEDIT190", control_type="Edit")
            if campo_empresa.exists(timeout=10):
                campo_empresa.click_input()
                campo_empresa.type_keys(self.empresa, with_spaces=True)
                print(f"Empresa preenchida: {self.empresa}")
            else:
                raise Exception("Campo 'Empresa' não encontrado.")

            # Abrir a janela de seleção de pasta usando o botão "..."
            self.selecionar_pasta_publicacao(janela_upload)

            # Checkbox "Data de vencimento"
            if self.data_vencimento:  # Verifica se a data foi fornecida
                checkbox_vencimento = janela_upload.child_window(auto_id="1006", control_type="CheckBox")
                if checkbox_vencimento.exists(timeout=10):
                    if checkbox_vencimento.get_toggle_state() == 0:
                        checkbox_vencimento.toggle()
                        print("Checkbox 'Data de vencimento' ativada.")
                else:
                    raise Exception("Checkbox 'Data de vencimento' não encontrada.")

                try:
                    # Tenta interpretar a data como "YYYY-MM-DD"
                    dt = datetime.strptime(self.data_vencimento, "%Y-%m-%d")
                    data_formatada = dt.strftime("%d/%m/%Y")
                except ValueError:
                    # Se não estiver nesse formato, mantém a original
                    data_formatada = self.data_vencimento

                # Preencher o campo "Data de vencimento"
                print(f"Inserindo a data de vencimento: {data_formatada}")
                pyautogui.typewrite(data_formatada)
                print(f"Data de vencimento preenchida: {data_formatada}")
            else:
                print("Data de vencimento não fornecida. Pulando etapa.")

            # Botão "Publicar"
            botao_publicar = janela_upload.child_window(auto_id="1003", control_type="Button")
            if botao_publicar.exists(timeout=10):
                botao_publicar.click_input()
                print("Publicação concluída com sucesso.")
            else:
                raise Exception("Botão 'Publicar' não encontrado.")
        except Exception as e:
            print(f"Erro ao preencher os campos de publicação: {e}")

    def selecionar_pasta_publicacao(self, janela_upload):
        """
        Navega na estrutura de pastas para selecionar ou criar o diretório de destino,
        utilizando a configuração do usuário.
        """
        try:
            print("Abrindo janela de seleção de pasta...")
            combo_pasta = janela_upload.child_window(auto_id="1001", control_type="ComboBox")
            if combo_pasta.exists(timeout=10):
                combo_pasta.click_input()
                time.sleep(1)
                pyautogui.press("tab")
                time.sleep(1)
                pyautogui.press("space")
                print("Botão '...' clicado com sucesso para abrir a seleção de pasta.")
            else:
                raise Exception("Caixa de combinação próxima ao campo de pasta não encontrada.")
            janela_pastas = janela_upload.child_window(title="Portal do Cliente - Estrutura de Pastas",
                                                       control_type="Window")
            if janela_pastas.exists(timeout=10):
                print("Janela 'Portal do Cliente - Estrutura de Pastas' acessada com sucesso.")
                janela_pastas.set_focus()
            else:
                raise Exception("Janela 'Portal do Cliente - Estrutura de Pastas' não encontrada.")

            # Monta a estrutura de pastas com base na configuração do usuário
            if "pastas_base" in self.config:
                estrutura = self.config["pastas_base"]
            elif "pastas_opcoes" in self.config:
                if self.opcao and self.opcao in self.config["pastas_opcoes"]:
                    estrutura = self.config["pastas_opcoes"][self.opcao]
                else:
                    # Se não for informado, pega a primeira opção disponível
                    key = list(self.config["pastas_opcoes"].keys())[0]
                    estrutura = self.config["pastas_opcoes"][key]
            else:
                raise Exception("Nenhuma configuração de pastas encontrada para o usuário.")

            # Processa a estrutura, substituindo placeholders "ano" e "mes_ano"
            caminho_pastas = []
            for item in estrutura:
                if isinstance(item, list):
                    valor = item[1] if len(item) > 1 else item[0]
                elif isinstance(item, str):
                    valor = item
                else:
                    valor = str(item)

                # Substituição dos placeholders com comparação case-insensitive
                valor_normalizado = valor.lower()
                if valor_normalizado == "ano":
                    valor = str(self.ano)
                elif valor_normalizado == "mes_ano":
                    valor = str(self.mes_ano)

                caminho_pastas.append(valor)

            print(f"Estrutura de pastas definida: {caminho_pastas}")

            # Percorre cada pasta da estrutura: tenta acessar ou cria se não existir.
            for pasta in caminho_pastas:
                print(f"Tentando acessar a pasta: {pasta}")
                grid = janela_pastas.child_window(auto_id="dgvPastas", control_type="Table")
                encontrado = False
                for item in grid.descendants(control_type="DataItem"):
                    valor_legacy = item.legacy_properties().get("Value", "").strip().lower()
                    valor_text = item.window_text().strip().lower()
                    print(f"DEBUG: legacy='{valor_legacy}', text='{valor_text}'")
                    if valor_legacy == pasta.lower() or valor_text == pasta.lower():
                        # Se for a última pasta (mes_ano) faça um clique único em vez de duplo
                        if pasta.lower() == caminho_pastas[-1].lower():
                            item.click_input()
                            print(f"Pasta '{pasta}' selecionada com sucesso (clique único).")
                        else:
                            item.double_click_input()
                            print(f"Pasta '{pasta}' acessada com sucesso.")
                        encontrado = True
                        break
                if not encontrado:
                    print(f"Pasta '{pasta}' não encontrada. Criando nova pasta...")
                    self.criar_pasta(janela_pastas, pasta)
                    # Após criar, tenta acessar novamente
                    grid = janela_pastas.child_window(auto_id="dgvPastas", control_type="Table")
                    for item in grid.descendants(control_type="DataItem"):
                        valor_legacy = item.legacy_properties().get("Value", "").strip().lower()
                        valor_text = item.window_text().strip().lower()
                        if valor_legacy == pasta.lower() or valor_text == pasta.lower():
                            if pasta.lower() == caminho_pastas[-1].lower():
                                item.click_input()
                                print(f"Pasta '{pasta}' criada e selecionada com sucesso (clique único).")
                            else:
                                item.double_click_input()
                                print(f"Pasta '{pasta}' criada e acessada com sucesso.")
                            break

            # Confirma a seleção clicando no botão OK
            self.confirmar_selecao_ok(janela_pastas)

        except Exception as e:
            print(f"Erro ao selecionar a pasta de publicação: {e}")
            raise

    @staticmethod
    def criar_pasta(janela_pastas, nome_pasta):
        """
        Cria uma nova pasta especificada no grid.
        """
        try:
            # Clicar no botão "Incluir"
            botao_incluir = janela_pastas.child_window(auto_id="btnIncluir", control_type="Button")
            if not botao_incluir.exists(timeout=5):
                raise Exception("Botão 'Incluir' não encontrado.")
            botao_incluir.click_input()
            time.sleep(1)

            # Preencher o nome da nova pasta
            campo_nome_pasta = janela_pastas.child_window(auto_id="txtNome", control_type="Edit")
            if not campo_nome_pasta.exists(timeout=5):
                raise Exception("Campo para nomear a nova pasta não encontrado.")
            campo_nome_pasta.click_input()
            campo_nome_pasta.type_keys(nome_pasta, with_spaces=True)
            print(f"Nome da nova pasta inserido: {nome_pasta}")
            time.sleep(1)

            # Clicar no botão "Salvar"
            botao_salvar = janela_pastas.child_window(auto_id="btnSalvar", control_type="Button")
            if not botao_salvar.exists(timeout=5):
                raise Exception("Botão 'Salvar' não encontrado.")
            botao_salvar.click_input()
            print(f"Pasta '{nome_pasta}' criada com sucesso.")
            time.sleep(2)

            # Atualiza o grid
            botao_atualizar = janela_pastas.child_window(auto_id="btnAtualizar", control_type="Button")
            if not botao_atualizar.exists(timeout=5):
                raise Exception("Botão 'Atualizar' não encontrado.")
            botao_atualizar.click_input()
            print("Grid atualizado com sucesso.")
            time.sleep(2)

        except Exception as e:
            print(f"Erro ao criar pasta '{nome_pasta}': {e}")
            raise

    @staticmethod
    def buscar_pasta_mes_ano(janela_pastas, nome_pasta):
        """
        Busca a pasta especificada no grid e clica para selecionar.
        """
        try:
            print(f"Procurando pela pasta: '{nome_pasta}'")

            # Grid contendo as pastas
            grid = janela_pastas.child_window(auto_id="dgvPastas", control_type="Table")
            grid.set_focus()
            pyautogui.press("home")
            time.sleep(0.5)

            # Captura todas as pastas visíveis
            itens_visiveis = grid.descendants(control_type="DataItem")
            for index, item in enumerate(itens_visiveis):
                value_legacy = item.legacy_properties().get("Value", "").strip().lower()
                value_value = item.window_text().strip().lower()

                # Diagnóstico detalhado
                print(f"[Linha {index}] Legacy: '{value_legacy}', Value: '{value_value}'")

                # Normaliza o texto visível para comparação
                valor_normalizado = value_legacy.replace("-", ".").lower()

                # Compara com o nome esperado
                if valor_normalizado == nome_pasta:
                    print(f"Pasta '{valor_normalizado}' encontrada na linha {index}.")

                    # Navega até a linha
                    for _ in range(index):
                        pyautogui.press("down")
                        time.sleep(0.3)

                    # Clica na pasta encontrada
                    item.click_input(double=False)
                    print("Pasta selecionada com sucesso.")
                    return True

            print(f"Pasta '{nome_pasta}' não encontrada.")
            return False
        except Exception as e:
            print(f"Erro ao buscar pasta: {e}")
            raise

    @staticmethod
    def criar_pasta_mes_ano(janela_pastas, nome_pasta):
        """
        Cria uma nova pasta especificada no grid.
        """
        try:
            # Clicar no botão "Incluir"
            botao_incluir = janela_pastas.child_window(auto_id="btnIncluir", control_type="Button")
            if not botao_incluir.exists(timeout=5):
                raise Exception("Botão 'Incluir' não encontrado.")
            botao_incluir.click_input()
            time.sleep(1)

            # Preencher o nome da nova pasta
            campo_nome_pasta = janela_pastas.child_window(auto_id="txtNome", control_type="Edit")
            if not campo_nome_pasta.exists(timeout=5):
                raise Exception("Campo para nomear a nova pasta não encontrado.")
            campo_nome_pasta.click_input()
            campo_nome_pasta.type_keys(nome_pasta, with_spaces=True)
            print(f"Nome da nova pasta inserido: {nome_pasta}")
            time.sleep(1)

            # Clicar no botão "Salvar"
            botao_salvar = janela_pastas.child_window(auto_id="btnSalvar", control_type="Button")
            if not botao_salvar.exists(timeout=5):
                raise Exception("Botão 'Salvar' não encontrado.")
            botao_salvar.click_input()
            print(f"Pasta '{nome_pasta}' criada com sucesso.")
            time.sleep(2)

            # Atualiza o grid
            botao_atualizar = janela_pastas.child_window(auto_id="btnAtualizar", control_type="Button")
            if not botao_atualizar.exists(timeout=5):
                raise Exception("Botão 'Atualizar' não encontrado.")
            botao_atualizar.click_input()
            print("Grid atualizado com sucesso.")
            time.sleep(2)

        except Exception as e:
            print(f"Erro ao criar pasta: {e}")
            raise

    @staticmethod
    def confirmar_selecao_ok(janela_pastas):
        """
        Confirma a seleção clicando no botão OK.
        """
        try:
            botao_ok = janela_pastas.child_window(auto_id="btnOk", control_type="Button")
            if botao_ok.exists(timeout=5):
                botao_ok.click_input()
                print("Botão 'OK' clicado para confirmar a seleção.")
            else:
                raise Exception("Botão 'OK' não encontrado.")
        except Exception as e:
            print(f"Erro ao clicar em OK: {e}")
            raise

    @staticmethod
    def verificar_aviso_onvio():
        """Verifica e interage com a janela de aviso sobre o Onvio."""
        try:
            print("Verificando se há uma janela de aviso sobre o Onvio...")

            janela_handles = findwindows.find_windows(title="Atenção", class_name="#32770")
            if janela_handles:
                print(f"Janela de aviso detectada. Handle: {janela_handles[0]}")

                app = Application(backend="uia").connect(handle=janela_handles[0])
                janela_aviso = app.window(handle=janela_handles[0])
                janela_aviso.set_focus()

                pyautogui.press("ENTER")
                print("ENTER pressionado para fechar a janela de aviso.")

                return True

            print("Nenhuma janela de aviso detectada.")
            return False
        except Exception as e:
            print(f"Erro ao verificar ou interagir com a janela de aviso: {e}")
            return False

    def realizar_login_onvio(self):
        """Realiza o login no Onvio após tratar o aviso."""
        try:
            print("Realizando login no Onvio...")

            app = Application(backend="uia").connect(path=self.caminho_executavel)
            janela_principal = app.window(title_re="Domínio Escrita Fiscal.*")

            botao_onvio = janela_principal.child_window(auto_id="btnConexao", control_type="Button")
            botao_onvio.click_input()
            print("Botão de conexão do Onvio clicado.")

            print("Aguardando a janela de login do Onvio...")
            janela_handles = []
            for _ in range(10):
                janela_handles = findwindows.find_windows(title="Usuário Onvio", class_name="FNWNS3190")
                if janela_handles:
                    break
                time.sleep(1)

            if not janela_handles:
                print("Janela de login do Onvio não encontrada. Continuando sem login.")
                return False

            janela_login_handle = janela_handles[0]
            app = Application(backend="uia").connect(handle=janela_login_handle)
            janela_login = app.window(handle=janela_login_handle)
            print(f"Janela de login encontrada. Handle: {janela_login_handle}")

            janela_login.set_focus()

            print("Localizando o campo de senha...")
            campo_senha = janela_login.child_window(auto_id="1003", class_name="Edit", control_type="Edit")

            if campo_senha.exists() and campo_senha.is_enabled():
                print("Campo de senha localizado e habilitado.")
                campo_senha.set_focus()

                campo_senha.set_text(self.senha_onvio)
                print("Senha do Onvio inserida com set_text().")

                print("Usando atalho Alt+G para realizar o login...")
                janela_login.type_keys("%g", with_spaces=True)
                print("Login no Onvio realizado com sucesso.")
                return True
            else:
                raise Exception("Campo de senha não localizado ou não está habilitado.")

        except Exception as e:
            print(f"Erro ao tentar realizar login no Onvio: {e}")
            return False

    @staticmethod
    def verificar_e_fechar_atencao():
        """
        Verifica se a janela 'Atenção' está aberta e clica em 'OK'.
        """
        try:
            print("Verificando a presença da janela 'Atenção'...")
            atencao_handle = findwindows.find_windows(title="Atenção", class_name="#32770")
            if atencao_handle:
                print("Janela 'Atenção' detectada.")
                app = Application(backend="uia").connect(handle=atencao_handle[0])
                janela_atencao = app.window(handle=atencao_handle[0])

                # Localizar e clicar no botão OK
                botao_ok = janela_atencao.child_window(title="OK", control_type="Button")
                if botao_ok.exists(timeout=5):
                    botao_ok.click_input()
                    print("Botão 'OK' clicado na janela 'Atenção'.")
                else:
                    raise Exception("Botão 'OK' não encontrado na janela 'Atenção'.")
            else:
                print("Janela 'Atenção' não encontrada.")
        except Exception as e:
            print(f"Erro ao interagir com a janela 'Atenção': {e}")

    def fechar_dominio(self):
        """Fecha o sistema Domínio de forma segura usando pywinauto."""
        try:
            app = Application(backend="uia").connect(path=self.caminho_executavel)

            janela_principal = app.window(title_re="Domínio Escrita Fiscal.*")

            janela_principal.close()
            time.sleep(3)
            pyautogui.press("ENTER")
            print("Sistema Domínio fechado com sucesso.")
        except Exception as e:
            print(f"Erro ao fechar o sistema Domínio: {e}")
