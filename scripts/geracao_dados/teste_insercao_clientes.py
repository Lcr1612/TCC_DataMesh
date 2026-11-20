import psycopg

from gerar_massa import gerar_clientes_em_lotes


QUANTIDADE_TESTE = 100


conexao = psycopg.connect(
    host="localhost",
    port=5433,
    dbname="db_clientes",
    user="tcc",
    password="tcc123"
)


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

with conexao.cursor() as cursor:

    for lote in gerar_clientes_em_lotes(
        quantidade_total=QUANTIDADE_TESTE
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

        total_inserido += len(lote)


conexao.commit()
conexao.close()
