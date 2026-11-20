import psycopg
from datetime import datetime, timezone


inicio_carga = datetime.now(timezone.utc)

# O novo corte é definido no início da execução
novo_data_corte = inicio_carga


# Conexão com o ODS
conexao_ods = psycopg.connect(
    host="localhost",
    port=5439,
    dbname="db_ods",
    user="tcc",
    password="tcc123"
)

# Conexão com o nó federador
conexao_federador = psycopg.connect(
    host="localhost",
    port=5438,
    dbname="db_federador",
    user="tcc",
    password="tcc123"
)


# Busca o último instante sincronizado com sucesso
consulta_ultima_carga = """
SELECT data_corte
FROM controle_carga_ods
WHERE status = 'SUCESSO'
ORDER BY id_carga DESC
LIMIT 1;
"""

with conexao_ods.cursor() as cursor:
    cursor.execute(consulta_ultima_carga)
    resultado = cursor.fetchone()

if resultado is None:
    print("Nenhuma carga anterior encontrada.")
    conexao_ods.close()
    conexao_federador.close()
    raise SystemExit

ultimo_data_corte = resultado[0]

print(f"Último data_corte: {ultimo_data_corte}")
print(f"Novo data_corte: {novo_data_corte}")


# Busca somente alterações ocorridas entre os dois cortes
consulta_alteracoes = """
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

WHERE GREATEST(
    p.data_atualizacao,
    c.data_atualizacao,
    f.data_atualizacao,
    pr.data_atualizacao,
    i.data_atualizacao,
    e.data_atualizacao
) > %s
AND GREATEST(
    p.data_atualizacao,
    c.data_atualizacao,
    f.data_atualizacao,
    pr.data_atualizacao,
    i.data_atualizacao,
    e.data_atualizacao
) <= %s

ORDER BY p.id_pedido, pr.id_produto;
"""

with conexao_federador.cursor() as cursor:
    cursor.execute(
        consulta_alteracoes,
        (ultimo_data_corte, novo_data_corte)
    )
    registros_alterados = cursor.fetchall()


# Insere registros novos ou atualiza os existentes
upsert = """
INSERT INTO vendas_integradas (
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
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s
)
ON CONFLICT (id_pedido, id_produto)
DO UPDATE SET
    codigo_pedido = EXCLUDED.codigo_pedido,
    data_pedido = EXCLUDED.data_pedido,
    status_pedido = EXCLUDED.status_pedido,
    valor_total = EXCLUDED.valor_total,
    id_cliente = EXCLUDED.id_cliente,
    cpf = EXCLUDED.cpf,
    nome_cliente = EXCLUDED.nome_cliente,
    id_filial = EXCLUDED.id_filial,
    cnpj_filial = EXCLUDED.cnpj_filial,
    uf = EXCLUDED.uf,
    cidade = EXCLUDED.cidade,
    codigo_produto = EXCLUDED.codigo_produto,
    nome_produto = EXCLUDED.nome_produto,
    categoria = EXCLUDED.categoria,
    quantidade = EXCLUDED.quantidade,
    valor_unitario = EXCLUDED.valor_unitario,
    id_entrega = EXCLUDED.id_entrega,
    data_envio = EXCLUDED.data_envio,
    data_prevista = EXCLUDED.data_prevista,
    data_entrega = EXCLUDED.data_entrega,
    status_entrega = EXCLUDED.status_entrega,
    data_atualizacao_origem = EXCLUDED.data_atualizacao_origem,
    data_carga_ods = CURRENT_TIMESTAMP;
"""

if registros_alterados:
    with conexao_ods.cursor() as cursor:
        cursor.executemany(upsert, registros_alterados)


fim_carga = datetime.now(timezone.utc)


# Registra a execução incremental
registro_carga = """
INSERT INTO controle_carga_ods (
    tipo_carga,
    inicio_carga,
    fim_carga,
    data_corte,
    registros_processados,
    status
)
VALUES (
    'INCREMENTAL',
    %s,
    %s,
    %s,
    %s,
    'SUCESSO'
);
"""

with conexao_ods.cursor() as cursor:
    cursor.execute(
        registro_carga,
        (
            inicio_carga,
            fim_carga,
            novo_data_corte,
            len(registros_alterados)
        )
    )

conexao_ods.commit()

print(
    f"Registros sincronizados no ODS: "
    f"{len(registros_alterados)}"
)

conexao_federador.close()
conexao_ods.close()