import psycopg

from gerar_massa import gerar_produtos_teste


QUANTIDADE_TESTE = 50


conexao = psycopg.connect(
    host="localhost",
    port=5435,
    dbname="db_produtos",
    user="tcc",
    password="tcc123"
)


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
    quantidade=QUANTIDADE_TESTE
)

dados = [
    (
        produto["codigo_produto"],
        produto["nome"],
        produto["descricao"],
        produto["qtd_estoque"],
        produto["categoria"]
    )
    for produto in produtos
]


with conexao.cursor() as cursor:
    cursor.executemany(
        sql_insert,
        dados
    )


conexao.commit()
conexao.close()


print(
    f"Teste concluído: "
    f"{len(produtos)} produtos inseridos."
)