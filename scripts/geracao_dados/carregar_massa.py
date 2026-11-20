import random
from decimal import Decimal
import sys

import psycopg

from gerar_massa import (
    MASSAS,
    SEMENTE,
    TAMANHO_LOTE,
    QUANTIDADE_ITENS,
    PESOS_ITENS,
    STATUS_PEDIDOS,
    PESOS_STATUS_PEDIDOS,
    gerar_clientes_em_lotes,
    gerar_filiais_teste,
    gerar_produtos_teste,
    gerar_data_pedido,
    gerar_dados_entrega,
    gerar_valor_unitario,
    dividir_em_lotes
)


# ============================================================
# CONEXÕES
# ============================================================

def conectar_bancos():
    conexoes = {
        "clientes": psycopg.connect(
            host="localhost",
            port=5433,
            dbname="db_clientes",
            user="tcc",
            password="tcc123"
        ),

        "filiais": psycopg.connect(
            host="localhost",
            port=5434,
            dbname="db_filiais",
            user="tcc",
            password="tcc123"
        ),

        "produtos": psycopg.connect(
            host="localhost",
            port=5435,
            dbname="db_produtos",
            user="tcc",
            password="tcc123"
        ),

        "vendas": psycopg.connect(
            host="localhost",
            port=5436,
            dbname="db_vendas",
            user="tcc",
            password="tcc123"
        ),

        "logistica": psycopg.connect(
            host="localhost",
            port=5437,
            dbname="db_logistica",
            user="tcc",
            password="tcc123"
        )
    }

    return conexoes


def fechar_conexoes(conexoes):
    for conexao in conexoes.values():
        conexao.close()


# ============================================================
# CARGA DE CLIENTES
# ============================================================

def carregar_clientes(
    conexao,
    quantidade
):
    sql_insert = """
    INSERT INTO public.cliente (
        cpf,
        nome,
        endereco,
        telefone
    )
    VALUES (
        %s,
        %s,
        %s,
        %s
    );
    """

    total_inserido = 0
    numero_lote = 0

    with conexao.cursor() as cursor:

        for lote in gerar_clientes_em_lotes(
            quantidade_total=quantidade
        ):
            dados = [
                (
                    cliente["cpf"],
                    cliente["nome"],
                    cliente["endereco"],
                    cliente["telefone"]
                )
                for cliente in lote
            ]

            cursor.executemany(
                sql_insert,
                dados
            )

            numero_lote += 1
            total_inserido += len(lote)

            print(
                f"Clientes - lote {numero_lote}: "
                f"{len(lote)} registros inseridos."
            )

    conexao.commit()

    print(
        f"Clientes concluídos: "
        f"{total_inserido} registros."
    )

# ============================================================
# CARGA DE FILIAIS
# ============================================================

def carregar_filiais(
    conexao,
    quantidade
):
    sql_insert = """
    INSERT INTO public.filial (
        cnpj_filial,
        uf,
        cidade,
        endereco,
        telefone
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s
    );
    """

    filiais = gerar_filiais_teste(
        quantidade=quantidade
    )

    dados = [
        (
            filial["cnpj_filial"],
            filial["uf"],
            filial["cidade"],
            filial["endereco"],
            filial["telefone"]
        )
        for filial in filiais
    ]

    with conexao.cursor() as cursor:
        cursor.executemany(
            sql_insert,
            dados
        )

    conexao.commit()

    print(
        f"Filiais concluídas: "
        f"{len(filiais)} registros."
    )

# ============================================================
# CARGA DE PRODUTOS
# ============================================================

def carregar_produtos(
    conexao,
    quantidade
):
    sql_insert = """
    INSERT INTO public.produto (
        codigo_produto,
        nome,
        descricao,
        qtd_estoque,
        categoria
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s
    );
    """

    produtos = gerar_produtos_teste(
        quantidade=quantidade
    )

    total_inserido = 0
    numero_lote = 0

    with conexao.cursor() as cursor:

        for lote in dividir_em_lotes(produtos):

            dados = [
                (
                    produto["codigo_produto"],
                    produto["nome"],
                    produto["descricao"],
                    produto["qtd_estoque"],
                    produto["categoria"]
                )
                for produto in lote
            ]

            cursor.executemany(
                sql_insert,
                dados
            )

            numero_lote += 1
            total_inserido += len(lote)

            print(
                f"Produtos - lote {numero_lote}: "
                f"{len(lote)} registros inseridos."
            )

    conexao.commit()

    print(
        f"Produtos concluídos: "
        f"{total_inserido} registros."
    )

    return produtos


# ============================================================
# ASSOCIA IDs REAIS AOS PRODUTOS
# ============================================================

def associar_ids_produtos(
    conexao,
    produtos
):
    codigos_produtos = [
        produto["codigo_produto"]
        for produto in produtos
    ]

    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id_produto,
                codigo_produto
            FROM public.produto
            WHERE codigo_produto = ANY(%s);
            """,
            (codigos_produtos,)
        )

        registros = cursor.fetchall()

    mapa_ids = {
        codigo_produto: id_produto
        for id_produto, codigo_produto in registros
    }

    for produto in produtos:

        codigo_produto = produto[
            "codigo_produto"
        ]

        if codigo_produto not in mapa_ids:
            raise RuntimeError(
                f"Produto não encontrado no banco: "
                f"{codigo_produto}"
            )

        produto["id_produto"] = (
            mapa_ids[codigo_produto]
        )

    print(
        f"IDs associados a "
        f"{len(produtos)} produtos."
    )

    return produtos    


# ============================================================
# BUSCA IDs REAIS
# ============================================================

def buscar_ids(
    conexao,
    tabela,
    coluna_id
):
    consulta = f"""
    SELECT {coluna_id}
    FROM public.{tabela}
    ORDER BY {coluna_id};
    """

    with conexao.cursor() as cursor:
        cursor.execute(consulta)

        return [
            registro[0]
            for registro in cursor.fetchall()
        ]


# ============================================================
# GRUPOS PARA DISTRIBUIÇÃO NÃO UNIFORME
# ============================================================

def criar_grupos_distribuicao(elementos):
    elementos = list(elementos)

    random.shuffle(elementos)

    quantidade = len(elementos)

    limite_alto = int(
        quantidade * 0.20
    )

    limite_medio = (
        limite_alto
        + int(quantidade * 0.30)
    )

    grupo_alto = elementos[
        :limite_alto
    ]

    grupo_medio = elementos[
        limite_alto:limite_medio
    ]

    grupo_baixo = elementos[
        limite_medio:
    ]

    return (
        grupo_alto,
        grupo_medio,
        grupo_baixo
    )


# ============================================================
# SELEÇÃO PONDERADA EFICIENTE
# ============================================================

def selecionar_por_grupo(
    grupo_alto,
    grupo_medio,
    grupo_baixo
):
    grupo_escolhido = random.choices(
        ["alto", "medio", "baixo"],
        weights=[0.50, 0.30, 0.20],
        k=1
    )[0]

    if grupo_escolhido == "alto" and grupo_alto:
        return random.choice(grupo_alto)

    if grupo_escolhido == "medio" and grupo_medio:
        return random.choice(grupo_medio)

    if grupo_escolhido == "baixo" and grupo_baixo:
        return random.choice(grupo_baixo)

    # Proteção caso algum grupo fique vazio
    elementos_disponiveis = (
        grupo_alto
        + grupo_medio
        + grupo_baixo
    )

    return random.choice(elementos_disponiveis)


# ============================================================
# SELEÇÃO DE PRODUTOS SEM REPETIÇÃO NO PEDIDO
# ============================================================

def selecionar_produtos_distintos(
    quantidade,
    grupo_alto,
    grupo_medio,
    grupo_baixo
):
    produtos_escolhidos = set()

    while len(produtos_escolhidos) < quantidade:

        produto = selecionar_por_grupo(
            grupo_alto,
            grupo_medio,
            grupo_baixo
        )

        produtos_escolhidos.add(produto)

    return list(produtos_escolhidos)

# ============================================================
# CÓDIGOS ÚNICOS E REPRODUZÍVEIS
# ============================================================

def gerar_codigo_unico(
    prefixo,
    numero,
    deslocamento=0
):
    valor = (
        numero * 2_654_435_761
        + SEMENTE
        + deslocamento
    ) % 10_000_000_000

    return f"{prefixo}-{valor:010d}"


#################

# ============================================================
# CARGA DE PEDIDOS, ITENS E ENTREGAS
# ============================================================

def carregar_vendas_em_lotes(
    conexoes,
    quantidade_pedidos,
    produtos,
    tamanho_lote=TAMANHO_LOTE
):
    conexao_clientes = conexoes["clientes"]
    conexao_filiais = conexoes["filiais"]
    conexao_vendas = conexoes["vendas"]
    conexao_logistica = conexoes["logistica"]

    # --------------------------------------------------------
    # IDs reais existentes nos bancos
    # --------------------------------------------------------

    ids_clientes = buscar_ids(
        conexao_clientes,
        "cliente",
        "id_cliente"
    )

    ids_filiais = buscar_ids(
        conexao_filiais,
        "filial",
        "id_filial"
    )

    if not ids_clientes:
        raise RuntimeError(
            "Nenhum cliente encontrado."
        )

    if not ids_filiais:
        raise RuntimeError(
            "Nenhuma filial encontrada."
        )

    if not produtos:
        raise RuntimeError(
            "Nenhum produto disponível."
        )

    # --------------------------------------------------------
    # 90% dos clientes serão ativos
    # --------------------------------------------------------

    quantidade_clientes_ativos = max(
        1,
        round(len(ids_clientes) * 0.90)
    )

    clientes_ativos = random.sample(
        ids_clientes,
        quantidade_clientes_ativos
    )

    random.shuffle(clientes_ativos)

    # --------------------------------------------------------
    # Grupos de distribuição
    # --------------------------------------------------------

    (
        filiais_alta,
        filiais_media,
        filiais_baixa
    ) = criar_grupos_distribuicao(
        ids_filiais
    )

    ids_produtos = [
        produto["id_produto"]
        for produto in produtos
    ]

    produto_por_id = {
        produto["id_produto"]: produto
        for produto in produtos
    }

    (
        produtos_alta,
        produtos_media,
        produtos_baixa
    ) = criar_grupos_distribuicao(
        ids_produtos
    )

    # --------------------------------------------------------
    # SQL
    # --------------------------------------------------------

    sql_pedido = """
    INSERT INTO public.pedido (
        codigo_pedido,
        data_pedido,
        status,
        valor_total,
        id_cliente,
        id_filial
    )
    VALUES (
        %s, %s, %s, %s, %s, %s
    );
    """

    sql_item = """
    INSERT INTO public.item_pedido (
        id_pedido,
        id_produto,
        quantidade,
        valor_unitario
    )
    VALUES (
        %s, %s, %s, %s
    );
    """

    sql_entrega = """
    INSERT INTO public.entrega (
        codigo_entrega,
        id_pedido,
        data_envio,
        data_prevista,
        data_entrega,
        status
    )
    VALUES (
        %s, %s, %s, %s, %s, %s
    );
    """

    total_pedidos = 0
    total_itens = 0
    total_entregas = 0

    numero_pedido_global = 1

    # --------------------------------------------------------
    # Processamento em lotes
    # --------------------------------------------------------

    while total_pedidos < quantidade_pedidos:

        quantidade_lote = min(
            tamanho_lote,
            quantidade_pedidos - total_pedidos
        )

        pedidos_lote = []
        itens_temporarios = []
        dados_entregas = []

        codigos_pedidos_lote = []

        for _ in range(quantidade_lote):

            # Garante pelo menos um pedido para cada
            # cliente ativo antes de começar repetições.
            if numero_pedido_global <= len(
                clientes_ativos
            ):
                id_cliente = clientes_ativos[
                    numero_pedido_global - 1
                ]
            else:
                id_cliente = random.choice(
                    clientes_ativos
                )

            id_filial = selecionar_por_grupo(
                filiais_alta,
                filiais_media,
                filiais_baixa
            )

            codigo_pedido = gerar_codigo_unico(
                "PED",
                numero_pedido_global
            )

            data_pedido = gerar_data_pedido()

            status_pedido = random.choices(
                STATUS_PEDIDOS,
                weights=PESOS_STATUS_PEDIDOS,
                k=1
            )[0]

            quantidade_itens = random.choices(
                QUANTIDADE_ITENS,
                weights=PESOS_ITENS,
                k=1
            )[0]

            quantidade_itens = min(
                quantidade_itens,
                len(produtos)
            )

            produtos_escolhidos = (
                selecionar_produtos_distintos(
                    quantidade_itens,
                    produtos_alta,
                    produtos_media,
                    produtos_baixa
                )
            )

            itens_pedido = []
            valor_total = Decimal("0.00")

            for id_produto in produtos_escolhidos:

                produto = produto_por_id[
                    id_produto
                ]

                quantidade = random.randint(
                    1,
                    5
                )

                valor_unitario = (
                    gerar_valor_unitario(
                        produto
                    )
                )

                valor_total += (
                    valor_unitario
                    * quantidade
                )

                itens_pedido.append(
                    (
                        id_produto,
                        quantidade,
                        valor_unitario
                    )
                )

            valor_total = valor_total.quantize(
                Decimal("0.01")
            )

            pedidos_lote.append(
                (
                    codigo_pedido,
                    data_pedido,
                    status_pedido,
                    valor_total,
                    id_cliente,
                    id_filial
                )
            )

            codigos_pedidos_lote.append(
                codigo_pedido
            )

            itens_temporarios.append(
                itens_pedido
            )

            dados_entrega = gerar_dados_entrega(
                data_pedido,
                status_pedido
            )

            dados_entregas.append(
                dados_entrega
            )

            numero_pedido_global += 1

        # ----------------------------------------------------
        # Insere pedidos
        # ----------------------------------------------------

        with conexao_vendas.cursor() as cursor:

            cursor.executemany(
                sql_pedido,
                pedidos_lote
            )

        # Recupera os IDs reais criados
        with conexao_vendas.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id_pedido,
                    codigo_pedido
                FROM public.pedido
                WHERE codigo_pedido = ANY(%s);
                """,
                (codigos_pedidos_lote,)
            )

            registros = cursor.fetchall()

        mapa_pedidos = {
            codigo: id_pedido
            for id_pedido, codigo in registros
        }

        # ----------------------------------------------------
        # Monta itens usando os IDs reais
        # ----------------------------------------------------

        itens_lote = []

        entregas_lote = []

        inicio_numero_lote = (
            numero_pedido_global
            - quantidade_lote
        )

        for indice in range(quantidade_lote):

            codigo_pedido = (
                codigos_pedidos_lote[indice]
            )

            id_pedido = mapa_pedidos[
                codigo_pedido
            ]

            for (
                id_produto,
                quantidade,
                valor_unitario
            ) in itens_temporarios[indice]:

                itens_lote.append(
                    (
                        id_pedido,
                        id_produto,
                        quantidade,
                        valor_unitario
                    )
                )

            dados_entrega = (
                dados_entregas[indice]
            )

            numero_entrega_logico = (
                inicio_numero_lote
                + indice
            )

            codigo_entrega = gerar_codigo_unico(
                "ENT",
                numero_entrega_logico,
                deslocamento=97_531
            )

            entregas_lote.append(
                (
                    codigo_entrega,
                    id_pedido,
                    dados_entrega[
                        "data_envio"
                    ],
                    dados_entrega[
                        "data_prevista"
                    ],
                    dados_entrega[
                        "data_entrega"
                    ],
                    dados_entrega[
                        "status_entrega"
                    ]
                )
            )

        # A ordem das entregas é embaralhada,
        # tornando id_entrega independente de id_pedido.
        random.shuffle(
            entregas_lote
        )

        # ----------------------------------------------------
        # Insere itens
        # ----------------------------------------------------

        with conexao_vendas.cursor() as cursor:

            cursor.executemany(
                sql_item,
                itens_lote
            )

        # ----------------------------------------------------
        # Insere entregas
        # ----------------------------------------------------

        with conexao_logistica.cursor() as cursor:

            cursor.executemany(
                sql_entrega,
                entregas_lote
            )

        # Confirma o lote nos dois bancos
        conexao_vendas.commit()
        conexao_logistica.commit()

        total_pedidos += quantidade_lote
        total_itens += len(itens_lote)
        total_entregas += len(
            entregas_lote
        )

        numero_lote = (
            total_pedidos
            + tamanho_lote
            - 1
        ) // tamanho_lote

        print(
            f"Vendas - lote {numero_lote}: "
            f"{quantidade_lote} pedidos, "
            f"{len(itens_lote)} itens e "
            f"{len(entregas_lote)} entregas."
        )

    print(
        "\nCarga de vendas concluída:"
    )

    print(
        f"Pedidos: {total_pedidos}"
    )

    print(
        f"Itens: {total_itens}"
    )

    print(
        f"Entregas: {total_entregas}"
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Uso: py carregar_massa.py "
            "M1 | M2 | M3 | M4 | M5"
        )
        raise SystemExit

    massa_escolhida = sys.argv[1].upper()

    if massa_escolhida in MASSAS:
        configuracao = MASSAS[massa_escolhida]

    else:
        print(
            f"Massa inválida: {massa_escolhida}"
        )
        raise SystemExit

    print(
        f"\nCarga selecionada: {massa_escolhida}"
    )

    print(
        f"Clientes: {configuracao['clientes']}"
    )

    print(
        f"Filiais: {configuracao['filiais']}"
    )

    print(
        f"Produtos: {configuracao['produtos']}"
    )

    print(
        f"Pedidos: {configuracao['pedidos']}"
    )

    conexoes = conectar_bancos()

    print(
        "\nConexões realizadas com sucesso."
    )

    try:

        # --------------------------------------------
        # CLIENTES
        # --------------------------------------------

        carregar_clientes(
            conexoes["clientes"],
            configuracao["clientes"]
        )

        # --------------------------------------------
        # FILIAIS
        # --------------------------------------------

        carregar_filiais(
            conexoes["filiais"],
            configuracao["filiais"]
        )

        # --------------------------------------------
        # PRODUTOS
        # --------------------------------------------

        produtos = carregar_produtos(
            conexoes["produtos"],
            configuracao["produtos"]
        )

        produtos = associar_ids_produtos(
            conexoes["produtos"],
            produtos
        )

        # --------------------------------------------
        # PEDIDOS + ITENS + ENTREGAS
        # --------------------------------------------

        carregar_vendas_em_lotes(
            conexoes=conexoes,
            quantidade_pedidos=configuracao[
                "pedidos"
            ],
            produtos=produtos
        )

        print(
            f"\nCarga {massa_escolhida} "
            f"concluída com sucesso."
        )

    finally:

        fechar_conexoes(
            conexoes
        )

        print(
            "Conexões encerradas."
        )