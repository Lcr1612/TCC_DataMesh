import random
from decimal import Decimal

import psycopg

from gerar_massa import (
    CATALOGO_PRODUTOS,
    QUANTIDADE_ITENS,
    PESOS_ITENS,
    STATUS_PEDIDOS,
    PESOS_STATUS_PEDIDOS,
    gerar_data_pedido,
    gerar_dados_entrega
)


SEMENTE_TESTE = 2025
QUANTIDADE_PEDIDOS = 20

random.seed(SEMENTE_TESTE)


# ============================================================
# CONEXÕES
# ============================================================

conexao_clientes = psycopg.connect(
    host="localhost",
    port=5433,
    dbname="db_clientes",
    user="tcc",
    password="tcc123"
)

conexao_filiais = psycopg.connect(
    host="localhost",
    port=5434,
    dbname="db_filiais",
    user="tcc",
    password="tcc123"
)

conexao_produtos = psycopg.connect(
    host="localhost",
    port=5435,
    dbname="db_produtos",
    user="tcc",
    password="tcc123"
)

conexao_vendas = psycopg.connect(
    host="localhost",
    port=5436,
    dbname="db_vendas",
    user="tcc",
    password="tcc123"
)

conexao_logistica = psycopg.connect(
    host="localhost",
    port=5437,
    dbname="db_logistica",
    user="tcc",
    password="tcc123"
)


# ============================================================
# BUSCA IDs REAIS
# ============================================================

with conexao_clientes.cursor() as cursor:
    cursor.execute("""
        SELECT id_cliente
        FROM public.cliente
        ORDER BY id_cliente;
    """)

    ids_clientes = [
        registro[0]
        for registro in cursor.fetchall()
    ]


with conexao_filiais.cursor() as cursor:
    cursor.execute("""
        SELECT id_filial
        FROM public.filial
        ORDER BY id_filial;
    """)

    ids_filiais = [
        registro[0]
        for registro in cursor.fetchall()
    ]


with conexao_produtos.cursor() as cursor:
    cursor.execute("""
        SELECT
            id_produto,
            nome,
            categoria
        FROM public.produto
         WHERE codigo_produto LIKE 'PRD-%'
        ORDER BY id_produto;
    """)

    produtos = cursor.fetchall()


# ============================================================
# FUNÇÃO AUXILIAR PARA IDENTIFICAR O TIPO DO PRODUTO
# ============================================================

def identificar_tipo_produto(nome, categoria):

    tipos_categoria = CATALOGO_PRODUTOS.get(categoria)

    if tipos_categoria is None:
        return None

    for tipo_produto in tipos_categoria:

        if nome.startswith(tipo_produto + " "):
            return tipo_produto

    return None


# ============================================================
# PREÇO-BASE DOS PRODUTOS USADOS NO TESTE
# ============================================================

precos_base = {}

for id_produto, nome, categoria in produtos:

    tipo_produto = identificar_tipo_produto(
        nome,
        categoria
    )

    if tipo_produto is None:
        continue

    valor_minimo, valor_maximo = (
        CATALOGO_PRODUTOS[categoria][tipo_produto]
    )

    preco_base = Decimal(
        str(
            round(
                random.uniform(
                    valor_minimo,
                    valor_maximo
                ),
                2
            )
        )
    )

    precos_base[id_produto] = preco_base


# Só utiliza produtos gerados pelo nosso catálogo
ids_produtos_validos = list(
    precos_base.keys()
)


# ============================================================
# GERA E INSERE OS 20 PEDIDOS
# ============================================================

pedidos_criados = []


for _ in range(QUANTIDADE_PEDIDOS):

    id_cliente = random.choice(
        ids_clientes
    )

    id_filial = random.choice(
        ids_filiais
    )

    codigo_pedido = (
        f"PED-{random.randint(1000000000, 9999999999)}"
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

    produtos_escolhidos = random.sample(
        ids_produtos_validos,
        quantidade_itens
    )

    itens = []
    valor_total = Decimal("0.00")

    for id_produto in produtos_escolhidos:

        quantidade = random.randint(
            1,
            5
        )

        preco_base = precos_base[
            id_produto
        ]

        variacao = Decimal(
            str(
                round(
                    random.uniform(
                        0.85,
                        1.15
                    ),
                    4
                )
            )
        )

        valor_unitario = (
            preco_base * variacao
        ).quantize(
            Decimal("0.01")
        )

        valor_total += (
            valor_unitario
            * quantidade
        )

        itens.append({
            "id_produto": id_produto,
            "quantidade": quantidade,
            "valor_unitario": valor_unitario
        })

    valor_total = valor_total.quantize(
        Decimal("0.01")
    )


    # --------------------------------------------------------
    # INSERE PEDIDO E RECUPERA O ID REAL
    # --------------------------------------------------------

    with conexao_vendas.cursor() as cursor:

        cursor.execute(
            """
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
            )
            RETURNING id_pedido;
            """,
            (
                codigo_pedido,
                data_pedido,
                status_pedido,
                valor_total,
                id_cliente,
                id_filial
            )
        )

        id_pedido = cursor.fetchone()[0]


    # --------------------------------------------------------
    # INSERE ITENS
    # --------------------------------------------------------

    with conexao_vendas.cursor() as cursor:

        for item in itens:

            cursor.execute(
                """
                INSERT INTO public.item_pedido (
                    id_pedido,
                    id_produto,
                    quantidade,
                    valor_unitario
                )
                VALUES (
                    %s, %s, %s, %s
                );
                """,
                (
                    id_pedido,
                    item["id_produto"],
                    item["quantidade"],
                    item["valor_unitario"]
                )
            )


    pedidos_criados.append({
        "id_pedido": id_pedido,
        "data_pedido": data_pedido,
        "status": status_pedido
    })


conexao_vendas.commit()


# ============================================================
# GERA ENTREGAS EM ORDEM INDEPENDENTE
# ============================================================

random.shuffle(
    pedidos_criados
)


for pedido in pedidos_criados:

    dados_entrega = gerar_dados_entrega(
        pedido["data_pedido"],
        pedido["status"]
    )

    codigo_entrega = (
        f"ENT-{random.randint(1000000000, 9999999999)}"
    )

    with conexao_logistica.cursor() as cursor:

        cursor.execute(
            """
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
            """,
            (
                codigo_entrega,
                pedido["id_pedido"],
                dados_entrega["data_envio"],
                dados_entrega["data_prevista"],
                dados_entrega["data_entrega"],
                dados_entrega["status_entrega"]
            )
        )


conexao_logistica.commit()


# ============================================================
# FECHA CONEXÕES
# ============================================================

conexao_clientes.close()
conexao_filiais.close()
conexao_produtos.close()
conexao_vendas.close()
conexao_logistica.close()


print(
    f"Teste concluído: "
    f"{QUANTIDADE_PEDIDOS} pedidos inseridos "
    f"com seus itens e entregas."
)