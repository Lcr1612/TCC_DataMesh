import psycopg
from datetime import datetime, timezone


# ============================================================
# CONFIGURACAO
# ============================================================

TAMANHO_LOTE = 5_000


# ============================================================
# CONEXOES
# ============================================================

conexao_federador = psycopg.connect(
    host="localhost",
    port=5438,
    dbname="db_federador",
    user="tcc",
    password="tcc123"
)

conexao_ods = psycopg.connect(
    host="localhost",
    port=5439,
    dbname="db_ods",
    user="tcc",
    password="tcc123"
)


# ============================================================
# INICIO DA CARGA
# ============================================================

inicio_carga = datetime.now(timezone.utc)

# O corte e obtido antes da leitura das fontes.
# Alteracoes posteriores a este instante poderao
# ser capturadas posteriormente pela carga incremental.
with conexao_federador.cursor() as cursor:
    cursor.execute("SELECT CURRENT_TIMESTAMP;")
    data_corte = cursor.fetchone()[0]


# ============================================================
# CONSULTA FEDERADA (MESMA CONSULTA DO SCRIPT ORIGINAL)
# ============================================================

consulta = """
SELECT
    p.id_pedido,
    p.codigo_pedido,
    p.data_pedido,
    p.status AS status_pedido,
    p.valor_total,

    c.id_cliente,
    c.cpf,
    c.nome AS nome_cliente,

    f.id_filial,
    f.cnpj_filial,
    f.uf,
    f.cidade,

    pr.id_produto,
    pr.codigo_produto,
    pr.nome AS nome_produto,
    pr.categoria,

    i.quantidade,
    i.valor_unitario,

    e.id_entrega,
    e.data_envio,
    e.data_prevista,
    e.data_entrega,
    e.status AS status_entrega,

    GREATEST(
        p.data_atualizacao,
        c.data_atualizacao,
        f.data_atualizacao,
        pr.data_atualizacao,
        i.data_atualizacao,
        e.data_atualizacao
    ) AS data_atualizacao_origem

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

ORDER BY
    p.id_pedido,
    pr.id_produto;
"""


# ============================================================
# INSERCAO NO ODS (MESMO INSERT DO SCRIPT ORIGINAL)
# ============================================================

insercao = """
INSERT INTO public.vendas_integradas (
    id_pedido,
    codigo_pedido,
    data_pedido,
    status_pedido,
    valor_total,

    id_cliente,
    cpf,
    nome_cliente,

    id_filial,
    cnpj_filial,
    uf,
    cidade,

    id_produto,
    codigo_produto,
    nome_produto,
    categoria,

    quantidade,
    valor_unitario,

    id_entrega,
    data_envio,
    data_prevista,
    data_entrega,
    status_entrega,

    data_atualizacao_origem
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s,
    %s, %s, %s, %s, %s,
    %s
);
"""


# ============================================================
# EXTRACAO E INSERCAO EM LOTES
# ============================================================

total_registros = 0

try:
    # Cursor nomeado: resultados sao recuperados em lotes
    # em vez de carregar tudo de uma vez na memoria do Python.
    with conexao_federador.cursor(
        name="cursor_carga_inicial_ods"
    ) as cursor_federador:

        cursor_federador.execute(consulta)

        with conexao_ods.cursor() as cursor_ods:
            while True:
                lote = cursor_federador.fetchmany(TAMANHO_LOTE)

                if not lote:
                    break

                cursor_ods.executemany(insercao, lote)
                total_registros += len(lote)

                print(
                    f"Lote de {len(lote)} registros inserido. "
                    f"Total processado: {total_registros}"
                )

    fim_carga = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # REGISTRA SUCESSO
    # --------------------------------------------------------

    with conexao_ods.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.controle_carga_ods (
                tipo_carga,
                inicio_carga,
                fim_carga,
                data_corte,
                registros_processados,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                "INICIAL",
                inicio_carga,
                fim_carga,
                data_corte,
                total_registros,
                "SUCESSO"
            )
        )

    # Commit unico: em caso de erro, todos os lotes sao desfeitos.
    conexao_ods.commit()

    print(
        f"Carga inicial concluida: "
        f"{total_registros} registros inseridos no ODS."
    )
    print("Controle da carga registrado com sucesso.")

except Exception as erro:
    conexao_ods.rollback()
    fim_carga = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # REGISTRA FALHA
    # --------------------------------------------------------

    try:
        with conexao_ods.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.controle_carga_ods (
                    tipo_carga,
                    inicio_carga,
                    fim_carga,
                    data_corte,
                    registros_processados,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (
                    "INICIAL",
                    inicio_carga,
                    fim_carga,
                    data_corte,
                    0,
                    "ERRO"
                )
            )
        conexao_ods.commit()
    except Exception as erro_controle:
        conexao_ods.rollback()
        print(f"Nao foi possivel registrar o erro da carga: {erro_controle}")

    print(f"Erro durante a carga inicial: {erro}")
    raise

finally:
    conexao_federador.close()
    conexao_ods.close()
