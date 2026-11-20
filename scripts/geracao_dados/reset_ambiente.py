import sys
import psycopg


# ============================================================
# CONEXÕES
# ============================================================

CONFIGURACOES = {
    "clientes": {
        "port": 5433,
        "dbname": "db_clientes"
    },
    "filiais": {
        "port": 5434,
        "dbname": "db_filiais"
    },
    "produtos": {
        "port": 5435,
        "dbname": "db_produtos"
    },
    "vendas": {
        "port": 5436,
        "dbname": "db_vendas"
    },
    "logistica": {
        "port": 5437,
        "dbname": "db_logistica"
    },
    "ods": {
        "port": 5439,
        "dbname": "db_ods"
    }
}


def conectar(configuracao):
    return psycopg.connect(
        host="localhost",
        port=configuracao["port"],
        dbname=configuracao["dbname"],
        user="tcc",
        password="tcc123"
    )


# ============================================================
# RESET
# ============================================================

def resetar_clientes():
    conexao = conectar(
        CONFIGURACOES["clientes"]
    )

    with conexao.cursor() as cursor:
        cursor.execute("""
            TRUNCATE TABLE public.cliente
            RESTART IDENTITY
            CASCADE;
        """)

    conexao.commit()
    conexao.close()

    print("db_clientes zerado.")


def resetar_filiais():
    conexao = conectar(
        CONFIGURACOES["filiais"]
    )

    with conexao.cursor() as cursor:
        cursor.execute("""
            TRUNCATE TABLE public.filial
            RESTART IDENTITY
            CASCADE;
        """)

    conexao.commit()
    conexao.close()

    print("db_filiais zerado.")


def resetar_produtos():
    conexao = conectar(
        CONFIGURACOES["produtos"]
    )

    with conexao.cursor() as cursor:
        cursor.execute("""
            TRUNCATE TABLE public.produto
            RESTART IDENTITY
            CASCADE;
        """)

    conexao.commit()
    conexao.close()

    print("db_produtos zerado.")


def resetar_vendas():
    conexao = conectar(
        CONFIGURACOES["vendas"]
    )

    with conexao.cursor() as cursor:
        cursor.execute("""
            TRUNCATE TABLE
                public.item_pedido,
                public.pedido
            RESTART IDENTITY
            CASCADE;
        """)

    conexao.commit()
    conexao.close()

    print("db_vendas zerado.")


def resetar_logistica():
    conexao = conectar(
        CONFIGURACOES["logistica"]
    )

    with conexao.cursor() as cursor:
        cursor.execute("""
            TRUNCATE TABLE public.entrega
            RESTART IDENTITY
            CASCADE;
        """)

    conexao.commit()
    conexao.close()

    print("db_logistica zerado.")


def resetar_ods():
    conexao = conectar(
        CONFIGURACOES["ods"]
    )

    with conexao.cursor() as cursor:
        cursor.execute("""
            TRUNCATE TABLE
                public.vendas_integradas,
                public.controle_carga_ods
            RESTART IDENTITY
            CASCADE;
        """)

    conexao.commit()
    conexao.close()

    print("db_ods zerado.")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    if (
        len(sys.argv) != 2
        or sys.argv[1].upper() != "CONFIRMAR"
    ):
        print(
            "ATENÇÃO: este script apaga todos os dados "
            "das massas experimentais."
        )

        print(
            "Para executar:"
        )

        print(
            "py scripts\\geracao_dados\\"
            "reset_ambiente.py CONFIRMAR"
        )

        raise SystemExit

    print("Iniciando reset do ambiente...")

    resetar_logistica()
    resetar_vendas()
    resetar_clientes()
    resetar_filiais()
    resetar_produtos()
    resetar_ods()

    print("\nReset concluído com sucesso.")