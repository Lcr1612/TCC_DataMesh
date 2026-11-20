import sys
import time
import math
import statistics
from datetime import datetime
from pathlib import Path

import psycopg
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment


# ============================================================
# CONFIGURAÇÕES
# ============================================================

REPETICOES = 10
AQUECIMENTOS = 3

MASSAS_VALIDAS = {
    "M1",
    "M2",
    "M3",
    "M4",
    "M5"
}

CAMINHO_RESULTADOS = (
    Path(__file__).resolve().parents[2]
    / "resultados"
    / "resultados_benchmark.xlsx"
)


# ============================================================
# BANCOS PARA MEDIÇÃO DE ARMAZENAMENTO
# ============================================================

BANCOS_ARMAZENAMENTO = {
    "db_clientes": 5433,
    "db_filiais": 5434,
    "db_produtos": 5435,
    "db_vendas": 5436,
    "db_logistica": 5437,
    "db_federador": 5438,
    "db_ods": 5439
}


# ============================================================
# CABEÇALHOS
# ============================================================

CABECALHO_EXECUCOES = [
    "Massa",
    "Abordagem",
    "Consulta",
    "Repeticao",
    "Tempo_ms",
    "Linhas_retornadas",
    "Data_hora",
    "Status"
]

CABECALHO_RESUMO = [
    "Massa",
    "Consulta",
    "Abordagem",
    "Execucoes",
    "Media_ms",
    "Mediana_ms",
    "Desvio_padrao_ms",
    "Minimo_ms",
    "Maximo_ms",
    "P95_ms"
]

CABECALHO_ARMAZENAMENTO = [
    "Massa",
    "Componente",
    "Tamanho_bytes",
    "Tamanho_MB",
    "Data_hora"
]


# ============================================================
# CONEXÕES
# ============================================================

def conectar_federador():
    return psycopg.connect(
        host="localhost",
        port=5438,
        dbname="db_federador",
        user="tcc",
        password="tcc123"
    )


def conectar_ods():
    return psycopg.connect(
        host="localhost",
        port=5439,
        dbname="db_ods",
        user="tcc",
        password="tcc123"
    )


# ============================================================
# CONSULTAS OFICIAIS - FEDERAÇÃO
# ============================================================

CONSULTAS_FEDERACAO = {

    "C1": """
        SELECT
            p.id_pedido,
            p.codigo_pedido,
            p.data_pedido,
            p.valor_total,
            c.id_cliente,
            c.cpf,
            c.nome
        FROM fdw_vendas.vw_pedidos p
        JOIN fdw_clientes.vw_clientes c
            ON c.id_cliente = p.id_cliente
        WHERE p.status = 'CONCLUIDO'
          AND p.data_pedido >= DATE '2025-06-01'
          AND p.data_pedido < DATE '2025-07-01';
    """,

    "C2": """
        SELECT
            pr.categoria,
            SUM(
                i.quantidade
                * i.valor_unitario
            ) AS faturamento
        FROM fdw_vendas.vw_pedidos p
        JOIN fdw_vendas.vw_itens_pedido i
            ON i.id_pedido = p.id_pedido
        JOIN fdw_produtos.vw_produtos pr
            ON pr.id_produto = i.id_produto
        WHERE p.status = 'CONCLUIDO'
        GROUP BY pr.categoria
        ORDER BY pr.categoria;
    """,

    "C3": """
        SELECT
            p.id_pedido,
            p.codigo_pedido,
            p.data_pedido,
            p.valor_total,
            c.id_cliente,
            c.nome,
            f.id_filial,
            f.cidade,
            f.uf
        FROM fdw_vendas.vw_pedidos p
        JOIN fdw_clientes.vw_clientes c
            ON c.id_cliente = p.id_cliente
        JOIN fdw_filiais.vw_filiais f
            ON f.id_filial = p.id_filial
        WHERE f.uf = 'SP'
          AND p.status = 'CONCLUIDO'
          AND p.data_pedido >= DATE '2025-04-01'
          AND p.data_pedido < DATE '2025-07-01'
        ORDER BY p.id_pedido;
    """,

    "C4": """
        SELECT
            f.uf,
            pr.categoria,
            SUM(
                i.quantidade
                * i.valor_unitario
            ) AS faturamento
        FROM fdw_vendas.vw_pedidos p
        JOIN fdw_filiais.vw_filiais f
            ON f.id_filial = p.id_filial
        JOIN fdw_vendas.vw_itens_pedido i
            ON i.id_pedido = p.id_pedido
        JOIN fdw_produtos.vw_produtos pr
            ON pr.id_produto = i.id_produto
        WHERE p.status = 'CONCLUIDO'
        GROUP BY
            f.uf,
            pr.categoria
        ORDER BY
            f.uf,
            pr.categoria;
    """,

    "C5": """
        SELECT
            p.id_pedido,
            p.codigo_pedido,
            p.data_pedido,
            c.nome AS nome_cliente,
            f.cidade,
            f.uf,
            pr.nome AS nome_produto,
            pr.categoria,
            i.quantidade,
            i.valor_unitario,
            e.data_prevista,
            e.data_entrega,
            e.status AS status_entrega
        FROM fdw_vendas.vw_pedidos p
        JOIN fdw_clientes.vw_clientes c
            ON c.id_cliente = p.id_cliente
        JOIN fdw_filiais.vw_filiais f
            ON f.id_filial = p.id_filial
        JOIN fdw_vendas.vw_itens_pedido i
            ON i.id_pedido = p.id_pedido
        JOIN fdw_produtos.vw_produtos pr
            ON pr.id_produto = i.id_produto
        JOIN fdw_logistica.vw_entregas e
            ON e.id_pedido = p.id_pedido
        WHERE pr.categoria = 'Informática'
          AND f.uf = 'SP'
          AND e.status = 'ENTREGUE'
          AND p.data_pedido >= DATE '2025-07-01'
          AND p.data_pedido < DATE '2025-10-01'
        ORDER BY
            p.id_pedido,
            pr.id_produto;
    """,

    "C6": """
        SELECT
            f.uf,
            pr.categoria,
            COUNT(
                DISTINCT c.id_cliente
            ) AS clientes,
            COUNT(
                DISTINCT p.id_pedido
            ) AS pedidos,
            SUM(
                i.quantidade
                * i.valor_unitario
            ) AS faturamento,
            AVG(
                e.data_entrega
                - p.data_pedido
            ) AS prazo_medio_entrega
        FROM fdw_vendas.vw_pedidos p
        JOIN fdw_clientes.vw_clientes c
            ON c.id_cliente = p.id_cliente
        JOIN fdw_filiais.vw_filiais f
            ON f.id_filial = p.id_filial
        JOIN fdw_vendas.vw_itens_pedido i
            ON i.id_pedido = p.id_pedido
        JOIN fdw_produtos.vw_produtos pr
            ON pr.id_produto = i.id_produto
        JOIN fdw_logistica.vw_entregas e
            ON e.id_pedido = p.id_pedido
        WHERE p.status = 'CONCLUIDO'
          AND e.status = 'ENTREGUE'
        GROUP BY
            f.uf,
            pr.categoria
        ORDER BY
            f.uf,
            pr.categoria;
    """
}


# ============================================================
# CONSULTAS OFICIAIS - ODS
# ============================================================

CONSULTAS_ODS = {

    "C1": """
        SELECT DISTINCT
            id_pedido,
            codigo_pedido,
            data_pedido,
            valor_total,
            id_cliente,
            cpf,
            nome_cliente
        FROM public.vendas_integradas
        WHERE status_pedido = 'CONCLUIDO'
          AND data_pedido >= DATE '2025-06-01'
          AND data_pedido < DATE '2025-07-01';
    """,

    "C2": """
        SELECT
            categoria,
            SUM(
                quantidade
                * valor_unitario
            ) AS faturamento
        FROM public.vendas_integradas
        WHERE status_pedido = 'CONCLUIDO'
        GROUP BY categoria
        ORDER BY categoria;
    """,

    "C3": """
        SELECT DISTINCT
            id_pedido,
            codigo_pedido,
            data_pedido,
            valor_total,
            id_cliente,
            nome_cliente,
            id_filial,
            cidade,
            uf
        FROM public.vendas_integradas
        WHERE uf = 'SP'
          AND status_pedido = 'CONCLUIDO'
          AND data_pedido >= DATE '2025-04-01'
          AND data_pedido < DATE '2025-07-01'
        ORDER BY id_pedido;
    """,

    "C4": """
        SELECT
            uf,
            categoria,
            SUM(
                quantidade
                * valor_unitario
            ) AS faturamento
        FROM public.vendas_integradas
        WHERE status_pedido = 'CONCLUIDO'
        GROUP BY
            uf,
            categoria
        ORDER BY
            uf,
            categoria;
    """,

    "C5": """
        SELECT
            id_pedido,
            codigo_pedido,
            data_pedido,
            nome_cliente,
            cidade,
            uf,
            nome_produto,
            categoria,
            quantidade,
            valor_unitario,
            data_prevista,
            data_entrega,
            status_entrega
        FROM public.vendas_integradas
        WHERE categoria = 'Informática'
          AND uf = 'SP'
          AND status_entrega = 'ENTREGUE'
          AND data_pedido >= DATE '2025-07-01'
          AND data_pedido < DATE '2025-10-01'
        ORDER BY
            id_pedido,
            id_produto;
    """,

    "C6": """
        SELECT
            uf,
            categoria,
            COUNT(
                DISTINCT id_cliente
            ) AS clientes,
            COUNT(
                DISTINCT id_pedido
            ) AS pedidos,
            SUM(
                quantidade
                * valor_unitario
            ) AS faturamento,
            AVG(
                data_entrega
                - data_pedido
            ) AS prazo_medio_entrega
        FROM public.vendas_integradas
        WHERE status_pedido = 'CONCLUIDO'
          AND status_entrega = 'ENTREGUE'
        GROUP BY
            uf,
            categoria
        ORDER BY
            uf,
            categoria;
    """
}


# ============================================================
# FORMATAÇÃO DAS PLANILHAS
# ============================================================

def formatar_planilha(planilha):

    for celula in planilha[1]:

        celula.font = Font(
            bold=True
        )

        celula.alignment = Alignment(
            horizontal="center"
        )

    planilha.freeze_panes = "A2"

    planilha.auto_filter.ref = (
        planilha.dimensions
    )

    larguras = {
        "A": 12,
        "B": 16,
        "C": 12,
        "D": 12,
        "E": 18,
        "F": 20,
        "G": 22,
        "H": 14,
        "I": 18,
        "J": 18
    }

    for coluna, largura in larguras.items():

        planilha.column_dimensions[
            coluna
        ].width = largura

    # Formatação numérica por aba
    if planilha.title == "Resumo":
        for linha in planilha.iter_rows(
            min_row=2,
            min_col=5,
            max_col=10
        ):
            for celula in linha:
                celula.number_format = '#,##0.00'

    elif planilha.title == "Armazenamento":
        for linha in range(2, planilha.max_row + 1):
            planilha[f"C{linha}"].number_format = '#,##0'
            planilha[f"D{linha}"].number_format = '#,##0.00'

    elif planilha.title in MASSAS_VALIDAS:
        for linha in range(2, planilha.max_row + 1):
            planilha[f"E{linha}"].number_format = '#,##0.000'
            planilha[f"F{linha}"].number_format = '#,##0'


# ============================================================
# CRIAÇÃO DO EXCEL
# ============================================================

def criar_excel_se_necessario():

    CAMINHO_RESULTADOS.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if CAMINHO_RESULTADOS.exists():
        return

    workbook = Workbook()

    planilha_inicial = workbook.active

    planilha_inicial.title = "M1"

    planilha_inicial.append(
        CABECALHO_EXECUCOES
    )

    # Cria as demais massas
    for massa in [
        "M2",
        "M3",
        "M4",
        "M5"
    ]:

        planilha = workbook.create_sheet(
            massa
        )

        planilha.append(
            CABECALHO_EXECUCOES
        )

    # Resumo
    resumo = workbook.create_sheet(
        "Resumo"
    )

    resumo.append(
        CABECALHO_RESUMO
    )

    # Armazenamento
    armazenamento = workbook.create_sheet(
        "Armazenamento"
    )

    armazenamento.append(
        CABECALHO_ARMAZENAMENTO
    )

    for planilha in workbook.worksheets:

        formatar_planilha(
            planilha
        )

    workbook.save(
        CAMINHO_RESULTADOS
    )

    workbook.close()


# ============================================================
# MIGRAÇÃO DO EXCEL ANTIGO
# ============================================================

def migrar_excel_antigo():

    if not CAMINHO_RESULTADOS.exists():
        return

    workbook = load_workbook(
        CAMINHO_RESULTADOS
    )

    alterado = False

    # --------------------------------------------------------
    # GARANTE AS ABAS M1-M5
    # --------------------------------------------------------

    for massa in sorted(
        MASSAS_VALIDAS
    ):

        if massa not in workbook.sheetnames:

            planilha = workbook.create_sheet(
                massa
            )

            planilha.append(
                CABECALHO_EXECUCOES
            )

            formatar_planilha(
                planilha
            )

            alterado = True

    # --------------------------------------------------------
    # MIGRA A ANTIGA ABA "Execucoes"
    # --------------------------------------------------------

    if "Execucoes" in workbook.sheetnames:

        antiga = workbook[
            "Execucoes"
        ]

        total_migrado = 0

        for linha in antiga.iter_rows(
            min_row=2,
            values_only=True
        ):

            massa = linha[0]

            if massa in MASSAS_VALIDAS:

                destino = workbook[
                    massa
                ]

                # Evita duplicar se a migração
                # for executada parcialmente.
                chave_nova = (
                    linha[0],
                    linha[1],
                    linha[2],
                    linha[3]
                )

                chaves_existentes = {
                    (
                        existente[0],
                        existente[1],
                        existente[2],
                        existente[3]
                    )
                    for existente
                    in destino.iter_rows(
                        min_row=2,
                        values_only=True
                    )
                    if existente[0]
                }

                if chave_nova not in chaves_existentes:

                    destino.append(
                        list(linha)
                    )

                    total_migrado += 1

        workbook.remove(
            antiga
        )

        alterado = True

        print(
            f"{total_migrado} execuções "
            f"migradas da aba antiga "
            f"'Execucoes'."
        )

    # --------------------------------------------------------
    # GARANTE RESUMO
    # --------------------------------------------------------

    if "Resumo" not in workbook.sheetnames:

        resumo = workbook.create_sheet(
            "Resumo"
        )

        resumo.append(
            CABECALHO_RESUMO
        )

        formatar_planilha(
            resumo
        )

        alterado = True

    # --------------------------------------------------------
    # GARANTE ARMAZENAMENTO
    # --------------------------------------------------------

    if "Armazenamento" not in workbook.sheetnames:

        armazenamento = (
            workbook.create_sheet(
                "Armazenamento"
            )
        )

        armazenamento.append(
            CABECALHO_ARMAZENAMENTO
        )

        formatar_planilha(
            armazenamento
        )

        alterado = True

    # --------------------------------------------------------
    # FORMATA AS ABAS
    # --------------------------------------------------------

    for nome in [
        "M1",
        "M2",
        "M3",
        "M4",
        "M5",
        "Resumo",
        "Armazenamento"
    ]:

        formatar_planilha(
            workbook[nome]
        )

    if alterado:

        workbook.save(
            CAMINHO_RESULTADOS
        )

    workbook.close()


# ============================================================
# EXECUÇÕES JÁ EXISTENTES
# ============================================================

def carregar_execucoes_existentes(
    massa
):

    workbook = load_workbook(
        CAMINHO_RESULTADOS
    )

    planilha = workbook[
        massa
    ]

    existentes = set()

    for linha in planilha.iter_rows(
        min_row=2,
        values_only=True
    ):

        abordagem = linha[1]
        consulta = linha[2]
        repeticao = linha[3]

        if (
            abordagem
            and consulta
            and repeticao
        ):

            existentes.add(
                (
                    massa,
                    abordagem,
                    consulta,
                    repeticao
                )
            )

    workbook.close()

    return existentes


# ============================================================
# REGISTRO DAS EXECUÇÕES
# ============================================================

def registrar_execucoes(
    massa,
    resultados
):

    workbook = load_workbook(
        CAMINHO_RESULTADOS
    )

    planilha = workbook[
        massa
    ]

    for resultado in resultados:

        planilha.append(
            resultado
        )

    formatar_planilha(
        planilha
    )

    workbook.save(
        CAMINHO_RESULTADOS
    )

    workbook.close()


# ============================================================
# ESTATÍSTICAS
# ============================================================

def percentil_95(valores):

    valores = sorted(valores)

    if len(valores) == 1:
        return valores[0]

    percentil = 0.95

    indice = (
        (len(valores) - 1)
        * percentil
    )

    indice_inferior = math.floor(indice)
    indice_superior = math.ceil(indice)

    if indice_inferior == indice_superior:
        return valores[indice_inferior]

    fracao = indice - indice_inferior

    return (
        valores[indice_inferior]
        + fracao
        * (
            valores[indice_superior]
            - valores[indice_inferior]
        )
    )


def atualizar_resumo():

    workbook = load_workbook(
        CAMINHO_RESULTADOS
    )

    resumo = workbook[
        "Resumo"
    ]

    dados = {}

    # --------------------------------------------------------
    # LÊ M1 ATÉ M5
    # --------------------------------------------------------

    for massa in sorted(
        MASSAS_VALIDAS
    ):

        planilha = workbook[
            massa
        ]

        for linha in planilha.iter_rows(
            min_row=2,
            values_only=True
        ):

            (
                massa_linha,
                abordagem,
                consulta,
                repeticao,
                tempo_ms,
                linhas_retornadas,
                data_hora,
                status
            ) = linha

            if repeticao is None or repeticao > REPETICOES:
                continue

            if status != "SUCESSO":
                continue

            if tempo_ms is None:
                continue

            chave = (
                massa,
                consulta,
                abordagem
            )

            dados.setdefault(
                chave,
                []
            ).append(
                float(
                    tempo_ms
                )
            )

    # --------------------------------------------------------
    # LIMPA RESUMO ANTERIOR
    # --------------------------------------------------------

    if resumo.max_row > 1:

        resumo.delete_rows(
            2,
            resumo.max_row - 1
        )

    # --------------------------------------------------------
    # GERA NOVO RESUMO
    # --------------------------------------------------------

    for chave in sorted(
        dados
    ):

        massa, consulta, abordagem = (
            chave
        )

        valores = dados[
            chave
        ]

        media = statistics.mean(
            valores
        )

        mediana = statistics.median(
            valores
        )

        if len(valores) > 1:

            desvio = statistics.stdev(
                valores
            )

        else:

            desvio = 0.0

        minimo = min(
            valores
        )

        maximo = max(
            valores
        )

        p95 = percentil_95(
            valores
        )

        resumo.append([
            massa,
            consulta,
            abordagem,
            len(valores),
            media,
            mediana,
            desvio,
            minimo,
            maximo,
            p95
        ])

    formatar_planilha(
        resumo
    )

    workbook.save(
        CAMINHO_RESULTADOS
    )

    workbook.close()


# ============================================================
# MEDIÇÃO DO ARMAZENAMENTO
# ============================================================

def registrar_armazenamento(
    massa
):

    workbook = load_workbook(
        CAMINHO_RESULTADOS
    )

    planilha = workbook[
        "Armazenamento"
    ]

    componentes_existentes = {
        linha[1]
        for linha in planilha.iter_rows(
            min_row=2,
            values_only=True
        )
        if linha[0] == massa
    }

    tamanhos = {}

    print(
        "\nMedindo armazenamento..."
    )

    for (
        banco,
        porta
    ) in BANCOS_ARMAZENAMENTO.items():

        # ----------------------------------------------------
        # JÁ REGISTRADO
        # ----------------------------------------------------

        if banco in componentes_existentes:

            for linha in planilha.iter_rows(
                min_row=2,
                values_only=True
            ):

                if (
                    linha[0] == massa
                    and linha[1] == banco
                ):

                    tamanhos[
                        banco
                    ] = linha[2]

                    break

            print(
                f"  {banco}: "
                f"já registrado."
            )

            continue

        # ----------------------------------------------------
        # NOVA MEDIÇÃO
        # ----------------------------------------------------

        conexao = psycopg.connect(
            host="localhost",
            port=porta,
            dbname=banco,
            user="tcc",
            password="tcc123"
        )

        try:

            with conexao.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        pg_database_size(
                            current_database()
                        );
                    """
                )

                tamanho_bytes = (
                    cursor.fetchone()[0]
                )

        finally:

            conexao.close()

        tamanhos[
            banco
        ] = tamanho_bytes

        tamanho_mb = (
            tamanho_bytes
            / 1024
            / 1024
        )

        planilha.append([
            massa,
            banco,
            tamanho_bytes,
            tamanho_mb,
            datetime.now()
        ])

        print(
            f"  {banco}: "
            f"{tamanho_mb:.2f} MB"
        )

    # --------------------------------------------------------
    # TOTAL DOS CINCO DOMÍNIOS
    # --------------------------------------------------------

    bancos_dominios = [
        "db_clientes",
        "db_filiais",
        "db_produtos",
        "db_vendas",
        "db_logistica"
    ]

    if (
        "Dominios_total"
        not in componentes_existentes
    ):

        total_dominios = sum(
            tamanhos[
                banco
            ]
            for banco in bancos_dominios
        )

        planilha.append([
            massa,
            "Dominios_total",
            total_dominios,
            total_dominios
            / 1024
            / 1024,
            datetime.now()
        ])

        print(
            f"  Dominios_total: "
            f"{total_dominios / 1024 / 1024:.2f} MB"
        )

    formatar_planilha(
        planilha
    )

    workbook.save(
        CAMINHO_RESULTADOS
    )

    workbook.close()

    print(
        f"Armazenamento de {massa} "
        f"registrado com sucesso."
    )


# ============================================================
# EXECUÇÃO DE UMA CONSULTA
# ============================================================

def executar_consulta(
    conexao,
    consulta
):

    with conexao.cursor() as cursor:

        inicio = (
            time.perf_counter()
        )

        cursor.execute(
            consulta
        )

        registros = (
            cursor.fetchall()
        )

        fim = (
            time.perf_counter()
        )

    tempo_ms = (
        fim - inicio
    ) * 1000

    return (
        tempo_ms,
        len(registros)
    )


# ============================================================
# AQUECIMENTO
# ============================================================

def executar_aquecimento(
    conexao,
    consulta,
    abordagem,
    nome_consulta
):

    print(
        f"  Aquecimento "
        f"{abordagem} - "
        f"{nome_consulta}"
    )

    for numero in range(
        1,
        AQUECIMENTOS + 1
    ):

        (
            tempo_ms,
            linhas
        ) = executar_consulta(
            conexao,
            consulta
        )

        print(
            f"    "
            f"{numero}/{AQUECIMENTOS}: "
            f"{tempo_ms:.3f} ms "
            f"({linhas} linhas)"
        )


# ============================================================
# BENCHMARK
# ============================================================

def executar_benchmark(
    massa
):

    criar_excel_se_necessario()

    # Converte automaticamente o Excel
    # antigo para o novo formato.
    migrar_excel_antigo()

    existentes = (
        carregar_execucoes_existentes(
            massa
        )
    )

    conexao_federador = (
        conectar_federador()
    )

    conexao_ods = (
        conectar_ods()
    )

    abordagens = [
        (
            "Federacao",
            conexao_federador,
            CONSULTAS_FEDERACAO
        ),
        (
            "ODS",
            conexao_ods,
            CONSULTAS_ODS
        )
    ]

    try:

        for nome_consulta in [
            "C1",
            "C2",
            "C3",
            "C4",
            "C5",
            "C6"
        ]:

            print(
                "\n"
                "================================"
            )

            print(
                f"{massa} - "
                f"{nome_consulta}"
            )

            print(
                "================================"
            )

            for (
                abordagem,
                conexao,
                consultas
            ) in abordagens:

                consulta = consultas[
                    nome_consulta
                ]

                # --------------------------------------------
                # REPETIÇÕES AINDA NÃO REGISTRADAS
                # --------------------------------------------

                pendentes = [
                    repeticao
                    for repeticao
                    in range(
                        1,
                        REPETICOES + 1
                    )
                    if (
                        massa,
                        abordagem,
                        nome_consulta,
                        repeticao
                    ) not in existentes
                ]

                # --------------------------------------------
                # JÁ CONCLUÍDA
                # --------------------------------------------

                if not pendentes:

                    print(
                        f"{abordagem}: "
                        f"{REPETICOES} execuções "
                        f"já registradas."
                    )

                    continue

                # --------------------------------------------
                # AQUECIMENTO
                # --------------------------------------------

                executar_aquecimento(
                    conexao,
                    consulta,
                    abordagem,
                    nome_consulta
                )

                novos_resultados = []

                print(
                    f"  Medições oficiais "
                    f"- {abordagem}"
                )

                # --------------------------------------------
                # MEDIÇÕES OFICIAIS
                # --------------------------------------------

                for repeticao in pendentes:

                    try:

                        (
                            tempo_ms,
                            linhas
                        ) = executar_consulta(
                            conexao,
                            consulta
                        )

                        status = (
                            "SUCESSO"
                        )

                        print(
                            f"    "
                            f"{repeticao:02d}/"
                            f"{REPETICOES}: "
                            f"{tempo_ms:.3f} ms "
                            f"({linhas} linhas)"
                        )

                    except Exception as erro:

                        tempo_ms = None
                        linhas = None
                        status = "ERRO"

                        print(
                            f"    ERRO na "
                            f"repetição "
                            f"{repeticao}: "
                            f"{erro}"
                        )

                        conexao.rollback()

                    novos_resultados.append([
                        massa,
                        abordagem,
                        nome_consulta,
                        repeticao,
                        tempo_ms,
                        linhas,
                        datetime.now(),
                        status
                    ])

                    existentes.add(
                        (
                            massa,
                            abordagem,
                            nome_consulta,
                            repeticao
                        )
                    )

                # --------------------------------------------
                # GRAVA NA ABA DA MASSA
                # --------------------------------------------

                registrar_execucoes(
                    massa,
                    novos_resultados
                )

                atualizar_resumo()

    finally:

        conexao_federador.close()
        conexao_ods.close()

    # ========================================================
    # RESUMO
    # ========================================================

    atualizar_resumo()

    # ========================================================
    # ARMAZENAMENTO
    # ========================================================

    registrar_armazenamento(
        massa
    )


    # Atualiza a formatação de todas as abas
    workbook = load_workbook(CAMINHO_RESULTADOS)

    for planilha in workbook.worksheets:
        formatar_planilha(planilha)

    workbook.save(CAMINHO_RESULTADOS)
    workbook.close()

    print(
        "\nBenchmark concluído."
    )

    print(
        f"Arquivo atualizado em:\n"
        f"{CAMINHO_RESULTADOS}"
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Uso: py "
            "scripts\\benchmark\\"
            "benchmark.py M1"
        )

        raise SystemExit

    massa = (
        sys.argv[1].upper()
    )

    if massa not in MASSAS_VALIDAS:

        print(
            f"Massa inválida: "
            f"{massa}"
        )

        print(
            "Escolha entre: "
            "M1, M2, M3, M4 ou M5."
        )

        raise SystemExit

    executar_benchmark(
        massa
    )