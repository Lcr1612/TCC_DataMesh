import psycopg

from gerar_massa import gerar_filiais_teste


QUANTIDADE_TESTE = 20


conexao = psycopg.connect(
    host="localhost",
    port=5434,
    dbname="db_filiais",
    user="tcc",
    password="tcc123"
)


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
    quantidade=QUANTIDADE_TESTE
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
conexao.close()


print(
    f"Teste concluído: "
    f"{len(filiais)} filiais inseridas."
)