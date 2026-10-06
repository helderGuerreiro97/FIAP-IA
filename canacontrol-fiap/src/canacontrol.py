"""
CanaControl - Monitor de perdas na colheita de cana-de-açúcar
==============================================================
Atividade: Gestão do Agronegócio em Python (Capítulos 3 ao 6) - FIAP

Problema: as perdas na colheita de cana chegam a até 15% na colheita
mecânica, contra cerca de 5% na manual. O CanaControl registra talhões e
colheitas, calcula a perda (t, % e R$), emite alertas quando a perda passa
do limite aceitável e gera ranking e comparativos para apoiar a decisão.

Conteúdos aplicados:
- Subalgoritmos: funções (com retorno) e procedimentos (sem retorno) com parâmetros
- Estruturas de dados: lista, tupla, dicionário e tabela de memória (lista de dicionários)
- Manipulação de arquivos: texto (.txt) e JSON
- Conexão com banco de dados Oracle (biblioteca oracledb)
"""

import json
import os
from datetime import datetime

try:
    import oracledb
except ImportError:
    oracledb = None

# =============================================================
# CONFIGURAÇÕES (tuplas e constantes)
# =============================================================

TIPOS_COLHEITA = ("manual", "mecanica")
# Limite de perda aceitável (%) para cada tipo, na mesma ordem de TIPOS_COLHEITA
LIMITES_PERDA = (5.0, 15.0)

ARQUIVO_JSON = os.path.join("dados", "canacontrol.json")
PASTA_RELATORIOS = "relatorios"

# Credenciais do Oracle (preencha com os dados do seu usuário)
ORACLE_USUARIO = "RM000000"
ORACLE_SENHA = "sua_senha"
ORACLE_DSN = "oracle.fiap.com.br:1521/ORCL"

# =============================================================
# TABELAS DE MEMÓRIA (listas de dicionários)
# =============================================================

talhoes = []    # [{"id": 1, "nome": "...", "area_ha": 0.0, "prod_esperada": 0.0}]
colheitas = []  # [{"id": 1, "id_talhao": 1, "data": "DD/MM/AAAA", "tipo": "...",
                #   "ton_colhidas": 0.0, "preco_ton": 0.0}]


# =============================================================
# VALIDAÇÕES DE ENTRADA
# =============================================================

def ler_texto(mensagem):
    """Função: lê um texto não vazio."""
    while True:
        texto = input(mensagem).strip()
        if texto:
            return texto
        print("  ⚠ O campo não pode ficar vazio.")


def ler_float(mensagem, minimo=0.0, maximo=None):
    """Função: lê um número decimal dentro do intervalo permitido."""
    while True:
        entrada = input(mensagem).strip().replace(",", ".")
        try:
            valor = float(entrada)
        except ValueError:
            print("  ⚠ Digite um número válido (ex.: 120.5).")
            continue
        if valor <= minimo:
            print(f"  ⚠ O valor deve ser maior que {minimo:g}.")
        elif maximo is not None and valor > maximo:
            print(f"  ⚠ O valor não pode passar de {maximo:,.2f}. Confira a digitação.")
        else:
            return valor


def ler_inteiro(mensagem, opcoes_validas):
    """Função: lê um inteiro que esteja entre as opções válidas."""
    while True:
        entrada = input(mensagem).strip()
        if entrada.isdigit() and int(entrada) in opcoes_validas:
            return int(entrada)
        print("  ⚠ Opção inválida. Tente novamente.")


def ler_opcao(mensagem, opcoes):
    """Função: lê um valor que precisa estar na tupla de opções."""
    lista = " / ".join(opcoes)
    while True:
        entrada = input(f"{mensagem} ({lista}): ").strip().lower()
        entrada = entrada.replace("â", "a")  # aceita "mecânica"
        if entrada in opcoes:
            return entrada
        print(f"  ⚠ Digite apenas uma das opções: {lista}.")


def ler_data(mensagem):
    """Função: lê uma data no formato DD/MM/AAAA, sem aceitar datas futuras."""
    while True:
        entrada = input(mensagem).strip()
        try:
            data = datetime.strptime(entrada, "%d/%m/%Y")
        except ValueError:
            print("  ⚠ Data inválida. Use o formato DD/MM/AAAA.")
            continue
        if data > datetime.now():
            print("  ⚠ A data da colheita não pode estar no futuro.")
        else:
            return data.strftime("%d/%m/%Y")


def confirmar(mensagem):
    """Função: retorna True se o usuário responder 's'."""
    while True:
        resposta = input(f"{mensagem} (s/n): ").strip().lower()
        if resposta in ("s", "n"):
            return resposta == "s"
        print("  ⚠ Responda com 's' ou 'n'.")


# =============================================================
# CÁLCULOS
# =============================================================

def proximo_id(registros):
    """Função: gera o próximo ID de uma tabela de memória."""
    if not registros:
        return 1
    return max(r["id"] for r in registros) + 1


def buscar_talhao(id_talhao):
    """Função: retorna o dicionário do talhão ou None."""
    for talhao in talhoes:
        if talhao["id"] == id_talhao:
            return talhao
    return None


def limite_do_tipo(tipo):
    """Função: retorna o limite de perda (%) do tipo de colheita."""
    return LIMITES_PERDA[TIPOS_COLHEITA.index(tipo)]


def calcular_indicadores(colheita, talhao):
    """Função: calcula esperado, perda (t e %), prejuízo e alerta de uma colheita."""
    esperado = talhao["area_ha"] * talhao["prod_esperada"]
    perda_t = max(esperado - colheita["ton_colhidas"], 0.0)
    perda_pct = perda_t / esperado * 100 if esperado else 0.0
    prejuizo = perda_t * colheita["preco_ton"]
    limite = limite_do_tipo(colheita["tipo"])
    return {
        "esperado": esperado,
        "perda_t": perda_t,
        "perda_pct": perda_pct,
        "prejuizo": prejuizo,
        "limite": limite,
        "alerta": perda_pct > limite,
    }


def montar_ranking():
    """Função: soma o prejuízo por talhão e ordena do maior para o menor."""
    totais = {}
    for colheita in colheitas:
        talhao = buscar_talhao(colheita["id_talhao"])
        if talhao is None:
            continue
        ind = calcular_indicadores(colheita, talhao)
        nome = talhao["nome"]
        if nome not in totais:
            totais[nome] = {"perda_t": 0.0, "prejuizo": 0.0, "qtd": 0}
        totais[nome]["perda_t"] += ind["perda_t"]
        totais[nome]["prejuizo"] += ind["prejuizo"]
        totais[nome]["qtd"] += 1
    # Lista de tuplas (nome, dados), ordenada pelo prejuízo
    return sorted(totais.items(), key=lambda item: item[1]["prejuizo"], reverse=True)


def montar_comparativo():
    """Função: agrupa os indicadores por tipo de colheita."""
    resumo = {tipo: {"qtd": 0, "soma_pct": 0.0, "perda_t": 0.0, "prejuizo": 0.0}
              for tipo in TIPOS_COLHEITA}
    for colheita in colheitas:
        talhao = buscar_talhao(colheita["id_talhao"])
        if talhao is None:
            continue
        ind = calcular_indicadores(colheita, talhao)
        dados = resumo[colheita["tipo"]]
        dados["qtd"] += 1
        dados["soma_pct"] += ind["perda_pct"]
        dados["perda_t"] += ind["perda_t"]
        dados["prejuizo"] += ind["prejuizo"]
    return resumo


# =============================================================
# FORMATAÇÃO E EXIBIÇÃO
# =============================================================

def moeda(valor):
    """Função: formata um valor no padrão R$ 1.234,56."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def numero(valor, casas=2):
    """Função: formata número no padrão brasileiro."""
    texto = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return texto


def montar_tabela(cabecalhos, linhas):
    """Função: monta uma tabela de texto alinhada e a retorna como string."""
    larguras = [len(c) for c in cabecalhos]
    for linha in linhas:
        for i, celula in enumerate(linha):
            larguras[i] = max(larguras[i], len(str(celula)))
    separador = "+" + "+".join("-" * (l + 2) for l in larguras) + "+"
    saida = [separador,
             "| " + " | ".join(c.ljust(larguras[i]) for i, c in enumerate(cabecalhos)) + " |",
             separador]
    for linha in linhas:
        saida.append("| " + " | ".join(str(c).ljust(larguras[i]) for i, c in enumerate(linha)) + " |")
    saida.append(separador)
    return "\n".join(saida)


def exibir_tabela(cabecalhos, linhas):
    """Procedimento: imprime uma tabela formatada."""
    if not linhas:
        print("  (nenhum registro encontrado)")
        return
    print(montar_tabela(cabecalhos, linhas))


def titulo(texto):
    """Procedimento: imprime um título de seção."""
    print("\n" + "=" * 60)
    print(f" {texto}")
    print("=" * 60)


def pausar():
    """Procedimento: aguarda o usuário pressionar Enter."""
    input("\nPressione Enter para continuar...")


# =============================================================
# FUNCIONALIDADES DO MENU
# =============================================================

def cadastrar_talhao():
    """Procedimento: cadastra um novo talhão na tabela de memória."""
    titulo("CADASTRAR TALHÃO")
    nome = ler_texto("Nome do talhão: ")
    if any(t["nome"].lower() == nome.lower() for t in talhoes):
        print("  ⚠ Já existe um talhão com esse nome.")
        return
    area = ler_float("Área (hectares): ", maximo=100000)
    prod = ler_float("Produtividade esperada (t/ha): ", maximo=300)
    talhao = {"id": proximo_id(talhoes), "nome": nome, "area_ha": area, "prod_esperada": prod}
    talhoes.append(talhao)
    print(f"\n✔ Talhão '{nome}' cadastrado (ID {talhao['id']}). "
          f"Produção esperada: {numero(area * prod)} t.")


def registrar_colheita():
    """Procedimento: registra uma colheita vinculada a um talhão."""
    titulo("REGISTRAR COLHEITA")
    if not talhoes:
        print("  ⚠ Cadastre um talhão antes de registrar colheitas.")
        return
    listar_talhoes(mostrar_titulo=False)
    ids = [t["id"] for t in talhoes]
    id_talhao = ler_inteiro("ID do talhão: ", ids)
    talhao = buscar_talhao(id_talhao)
    esperado = talhao["area_ha"] * talhao["prod_esperada"]

    data = ler_data("Data da colheita (DD/MM/AAAA): ")
    tipo = ler_opcao("Tipo de colheita", TIPOS_COLHEITA)
    # Trava contra erro de digitação: no máximo o dobro do esperado
    colhido = ler_float("Toneladas colhidas: ", maximo=esperado * 2)
    preco = ler_float("Preço por tonelada (R$): ", maximo=10000)

    colheita = {"id": proximo_id(colheitas), "id_talhao": id_talhao, "data": data,
                "tipo": tipo, "ton_colhidas": colhido, "preco_ton": preco}
    colheitas.append(colheita)

    ind = calcular_indicadores(colheita, talhao)
    print("\n✔ Colheita registrada.")
    print(f"  Esperado: {numero(ind['esperado'])} t | Colhido: {numero(colhido)} t")
    print(f"  Perda: {numero(ind['perda_t'])} t ({numero(ind['perda_pct'])}%) | "
          f"Prejuízo: {moeda(ind['prejuizo'])}")
    if ind["alerta"]:
        print(f"  🚨 ALERTA: perda acima do limite de {numero(ind['limite'], 0)}% "
              f"para colheita {tipo}!")


def listar_talhoes(mostrar_titulo=True):
    """Procedimento: lista os talhões cadastrados."""
    if mostrar_titulo:
        titulo("TALHÕES CADASTRADOS")
    linhas = [(t["id"], t["nome"], numero(t["area_ha"]), numero(t["prod_esperada"]),
               numero(t["area_ha"] * t["prod_esperada"])) for t in talhoes]
    exibir_tabela(("ID", "Talhão", "Área (ha)", "Prod. (t/ha)", "Esperado (t)"), linhas)


def linhas_colheitas():
    """Função: monta as linhas da tabela de colheitas com os indicadores."""
    linhas = []
    for c in colheitas:
        talhao = buscar_talhao(c["id_talhao"])
        if talhao is None:
            continue
        ind = calcular_indicadores(c, talhao)
        situacao = "ALERTA" if ind["alerta"] else "OK"
        linhas.append((c["id"], c["data"], talhao["nome"], c["tipo"],
                       numero(c["ton_colhidas"]), numero(ind["perda_pct"]) + "%",
                       moeda(ind["prejuizo"]), situacao))
    return linhas


CAB_COLHEITAS = ("ID", "Data", "Talhão", "Tipo", "Colhido (t)", "Perda", "Prejuízo", "Situação")


def listar_colheitas():
    """Procedimento: lista todas as colheitas com indicadores."""
    titulo("COLHEITAS REGISTRADAS")
    exibir_tabela(CAB_COLHEITAS, linhas_colheitas())


def relatorio_alertas():
    """Procedimento: mostra resumo geral e as colheitas acima do limite."""
    titulo("RELATÓRIO DE PERDAS E ALERTAS")
    if not colheitas:
        print("  (nenhuma colheita registrada)")
        return
    total_perda = total_prejuizo = 0.0
    alertas = []
    for c in colheitas:
        talhao = buscar_talhao(c["id_talhao"])
        if talhao is None:
            continue
        ind = calcular_indicadores(c, talhao)
        total_perda += ind["perda_t"]
        total_prejuizo += ind["prejuizo"]
        if ind["alerta"]:
            alertas.append((c["data"], talhao["nome"], c["tipo"],
                            numero(ind["perda_pct"]) + "%",
                            numero(ind["limite"], 0) + "%", moeda(ind["prejuizo"])))
    print(f"  Colheitas analisadas: {len(colheitas)}")
    print(f"  Perda total: {numero(total_perda)} t")
    print(f"  Prejuízo total: {moeda(total_prejuizo)}")
    print(f"  Colheitas em alerta: {len(alertas)}\n")
    if alertas:
        exibir_tabela(("Data", "Talhão", "Tipo", "Perda", "Limite", "Prejuízo"), alertas)
        print("\n  💡 Recomendação: revisar regulagem das colhedoras, velocidade de "
              "operação e o momento da colheita nos talhões acima.")
    else:
        print("  ✔ Nenhuma colheita acima do limite. Bom trabalho!")


def exibir_ranking():
    """Procedimento: exibe o ranking de talhões por prejuízo."""
    titulo("RANKING DE TALHÕES POR PREJUÍZO")
    ranking = montar_ranking()
    linhas = [(f"{pos}º", nome, d["qtd"], numero(d["perda_t"]), moeda(d["prejuizo"]))
              for pos, (nome, d) in enumerate(ranking, start=1)]
    exibir_tabela(("Pos.", "Talhão", "Colheitas", "Perda (t)", "Prejuízo"), linhas)


def exibir_comparativo():
    """Procedimento: compara colheita manual x mecânica."""
    titulo("COMPARATIVO: MANUAL x MECÂNICA")
    resumo = montar_comparativo()
    linhas = []
    for tipo in TIPOS_COLHEITA:
        d = resumo[tipo]
        media = d["soma_pct"] / d["qtd"] if d["qtd"] else 0.0
        linhas.append((tipo, d["qtd"], numero(media) + "%",
                       numero(limite_do_tipo(tipo), 0) + "%",
                       numero(d["perda_t"]), moeda(d["prejuizo"])))
    exibir_tabela(("Tipo", "Colheitas", "Perda média", "Limite", "Perda (t)", "Prejuízo"),
                  linhas)


# =============================================================
# ARQUIVOS: JSON E TEXTO
# =============================================================

def salvar_json(caminho):
    """Procedimento: salva as tabelas de memória em um arquivo JSON."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    dados = {"talhoes": talhoes, "colheitas": colheitas}
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)
    print(f"✔ Dados salvos em '{caminho}'.")


def carregar_json(caminho, silencioso=False):
    """Função: carrega o JSON para as tabelas de memória. Retorna True se deu certo."""
    if not os.path.exists(caminho):
        if not silencioso:
            print(f"  ⚠ Arquivo '{caminho}' não encontrado.")
        return False
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (json.JSONDecodeError, OSError) as erro:
        print(f"  ⚠ Não foi possível ler o arquivo: {erro}")
        return False
    talhoes.clear()
    talhoes.extend(dados.get("talhoes", []))
    colheitas.clear()
    colheitas.extend(dados.get("colheitas", []))
    if not silencioso:
        print(f"✔ {len(talhoes)} talhão(ões) e {len(colheitas)} colheita(s) carregados.")
    return True


def gerar_relatorio_txt():
    """Procedimento: gera um relatório completo em arquivo texto."""
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    agora = datetime.now()
    caminho = os.path.join(PASTA_RELATORIOS, f"relatorio_{agora:%Y-%m-%d_%H%M%S}.txt")

    ranking = montar_ranking()
    resumo = montar_comparativo()
    linhas_comp = []
    for tipo in TIPOS_COLHEITA:
        d = resumo[tipo]
        media = d["soma_pct"] / d["qtd"] if d["qtd"] else 0.0
        linhas_comp.append((tipo, d["qtd"], numero(media) + "%", moeda(d["prejuizo"])))

    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write("CANACONTROL - RELATÓRIO DE PERDAS NA COLHEITA DE CANA\n")
        arq.write(f"Gerado em: {agora:%d/%m/%Y %H:%M}\n\n")
        arq.write("COLHEITAS\n")
        arq.write(montar_tabela(CAB_COLHEITAS, linhas_colheitas()) + "\n\n")
        arq.write("RANKING DE TALHÕES POR PREJUÍZO\n")
        arq.write(montar_tabela(("Pos.", "Talhão", "Perda (t)", "Prejuízo"),
                                [(f"{i}º", n, numero(d["perda_t"]), moeda(d["prejuizo"]))
                                 for i, (n, d) in enumerate(ranking, start=1)]) + "\n\n")
        arq.write("COMPARATIVO MANUAL x MECÂNICA\n")
        arq.write(montar_tabela(("Tipo", "Colheitas", "Perda média", "Prejuízo"),
                                linhas_comp) + "\n")
    print(f"✔ Relatório gerado em '{caminho}'.")


# =============================================================
# BANCO DE DADOS ORACLE
# =============================================================

SQL_CRIAR_TALHAO = """
CREATE TABLE TALHAO (
    ID_TALHAO     NUMBER PRIMARY KEY,
    NOME          VARCHAR2(50) NOT NULL,
    AREA_HA       NUMBER(12,2) NOT NULL,
    PROD_ESPERADA NUMBER(10,2) NOT NULL
)"""

SQL_CRIAR_COLHEITA = """
CREATE TABLE COLHEITA (
    ID_COLHEITA   NUMBER PRIMARY KEY,
    ID_TALHAO     NUMBER NOT NULL REFERENCES TALHAO(ID_TALHAO),
    DATA_COLHEITA DATE NOT NULL,
    TIPO          VARCHAR2(10) NOT NULL CHECK (TIPO IN ('manual', 'mecanica')),
    TON_COLHIDAS  NUMBER(12,2) NOT NULL,
    PRECO_TON     NUMBER(10,2) NOT NULL
)"""


def conectar_oracle():
    """Função: abre a conexão com o Oracle. Retorna a conexão ou None."""
    if oracledb is None:
        print("  ⚠ Biblioteca 'oracledb' não instalada. Rode: pip install oracledb")
        return None
    try:
        return oracledb.connect(user=ORACLE_USUARIO, password=ORACLE_SENHA, dsn=ORACLE_DSN)
    except oracledb.Error as erro:
        print(f"  ⚠ Erro ao conectar no Oracle: {erro}")
        return None


def criar_tabelas_oracle(conexao):
    """Procedimento: cria as tabelas TALHAO e COLHEITA se ainda não existirem."""
    cursor = conexao.cursor()
    cursor.execute("SELECT table_name FROM user_tables "
                   "WHERE table_name IN ('TALHAO', 'COLHEITA')")
    existentes = [linha[0] for linha in cursor.fetchall()]
    if "TALHAO" not in existentes:
        cursor.execute(SQL_CRIAR_TALHAO)
        print("✔ Tabela TALHAO criada.")
    if "COLHEITA" not in existentes:
        cursor.execute(SQL_CRIAR_COLHEITA)
        print("✔ Tabela COLHEITA criada.")
    if len(existentes) == 2:
        print("  As tabelas já existem.")
    cursor.close()


def enviar_para_oracle(conexao):
    """Procedimento: substitui os dados do Oracle pelos dados em memória."""
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM COLHEITA")
    cursor.execute("DELETE FROM TALHAO")
    cursor.executemany(
        "INSERT INTO TALHAO (ID_TALHAO, NOME, AREA_HA, PROD_ESPERADA) "
        "VALUES (:1, :2, :3, :4)",
        [(t["id"], t["nome"], t["area_ha"], t["prod_esperada"]) for t in talhoes])
    cursor.executemany(
        "INSERT INTO COLHEITA (ID_COLHEITA, ID_TALHAO, DATA_COLHEITA, TIPO, "
        "TON_COLHIDAS, PRECO_TON) VALUES (:1, :2, TO_DATE(:3, 'DD/MM/YYYY'), :4, :5, :6)",
        [(c["id"], c["id_talhao"], c["data"], c["tipo"], c["ton_colhidas"], c["preco_ton"])
         for c in colheitas])
    conexao.commit()
    cursor.close()
    print(f"✔ Enviados {len(talhoes)} talhão(ões) e {len(colheitas)} colheita(s) ao Oracle.")


def carregar_do_oracle(conexao):
    """Procedimento: carrega os dados do Oracle para as tabelas de memória."""
    cursor = conexao.cursor()
    cursor.execute("SELECT ID_TALHAO, NOME, AREA_HA, PROD_ESPERADA FROM TALHAO "
                   "ORDER BY ID_TALHAO")
    talhoes.clear()
    for id_t, nome, area, prod in cursor.fetchall():
        talhoes.append({"id": id_t, "nome": nome, "area_ha": float(area),
                        "prod_esperada": float(prod)})
    cursor.execute("SELECT ID_COLHEITA, ID_TALHAO, TO_CHAR(DATA_COLHEITA, 'DD/MM/YYYY'), "
                   "TIPO, TON_COLHIDAS, PRECO_TON FROM COLHEITA ORDER BY ID_COLHEITA")
    colheitas.clear()
    for id_c, id_t, data, tipo, ton, preco in cursor.fetchall():
        colheitas.append({"id": id_c, "id_talhao": id_t, "data": data, "tipo": tipo,
                          "ton_colhidas": float(ton), "preco_ton": float(preco)})
    cursor.close()
    print(f"✔ Carregados {len(talhoes)} talhão(ões) e {len(colheitas)} colheita(s) do Oracle.")


def menu_oracle():
    """Procedimento: submenu de operações com o banco Oracle."""
    titulo("BANCO DE DADOS ORACLE")
    print("1. Criar tabelas")
    print("2. Enviar dados da memória para o Oracle")
    print("3. Carregar dados do Oracle para a memória")
    print("0. Voltar")
    opcao = ler_inteiro("Escolha: ", (0, 1, 2, 3))
    if opcao == 0:
        return
    if opcao == 2 and not confirmar("Os dados atuais do Oracle serão substituídos. Continuar?"):
        return
    if opcao == 3 and not confirmar("Os dados em memória serão substituídos. Continuar?"):
        return
    conexao = conectar_oracle()
    if conexao is None:
        return
    try:
        if opcao == 1:
            criar_tabelas_oracle(conexao)
        elif opcao == 2:
            enviar_para_oracle(conexao)
        elif opcao == 3:
            carregar_do_oracle(conexao)
    except oracledb.Error as erro:
        conexao.rollback()
        print(f"  ⚠ Erro no banco de dados: {erro}")
    finally:
        conexao.close()


# =============================================================
# MENU PRINCIPAL
# =============================================================

def exibir_menu():
    """Procedimento: mostra o menu principal."""
    titulo("CANACONTROL - Monitor de Perdas na Colheita de Cana")
    print(f" Talhões: {len(talhoes)} | Colheitas: {len(colheitas)}")
    print("-" * 60)
    print(" 1. Cadastrar talhão")
    print(" 2. Registrar colheita")
    print(" 3. Listar talhões")
    print(" 4. Listar colheitas")
    print(" 5. Relatório de perdas e alertas")
    print(" 6. Ranking de talhões por prejuízo")
    print(" 7. Comparativo manual x mecânica")
    print(" 8. Salvar dados em JSON")
    print(" 9. Carregar dados do JSON")
    print("10. Gerar relatório TXT")
    print("11. Banco de dados Oracle")
    print(" 0. Sair")


def main():
    """Procedimento principal: carrega os dados salvos e executa o menu."""
    if carregar_json(ARQUIVO_JSON, silencioso=True):
        print(f"Dados anteriores carregados de '{ARQUIVO_JSON}'.")

    # Dicionário que liga cada opção do menu à sua função
    acoes = {
        1: cadastrar_talhao,
        2: registrar_colheita,
        3: listar_talhoes,
        4: listar_colheitas,
        5: relatorio_alertas,
        6: exibir_ranking,
        7: exibir_comparativo,
        8: lambda: salvar_json(ARQUIVO_JSON),
        9: lambda: carregar_json(ARQUIVO_JSON),
        10: gerar_relatorio_txt,
        11: menu_oracle,
    }

    while True:
        exibir_menu()
        opcao = ler_inteiro("\nEscolha uma opção: ", range(0, 12))
        if opcao == 0:
            if confirmar("Deseja salvar os dados em JSON antes de sair?"):
                salvar_json(ARQUIVO_JSON)
            print("\nAté logo! 🌱")
            break
        acoes[opcao]()
        pausar()


if __name__ == "__main__":
    main()
