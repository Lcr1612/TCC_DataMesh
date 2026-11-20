"""Confere equivalencia de resultados C1-C6 entre Federacao e ODS.

Coloque este arquivo na mesma pasta que benchmark.py e execute:
    py scripts\benchmark\validar_consultas.py

Nao grava resultados e nao modifica os bancos.
"""

from collections import Counter
from contextlib import closing

from benchmark import (
    CONSULTAS_FEDERACAO,
    CONSULTAS_ODS,
    conectar_federador,
    conectar_ods,
)


def obter_resultados(conexao, sql):
    with conexao.cursor() as cursor:
        cursor.execute(sql)
        return Counter(cursor.fetchall())


def main():
    falhas = 0

    with closing(conectar_federador()) as federador, closing(conectar_ods()) as ods:
        for consulta in ("C1", "C2", "C3", "C4", "C5", "C6"):
            try:
                linhas_federacao = obter_resultados(
                    federador, CONSULTAS_FEDERACAO[consulta]
                )
                linhas_ods = obter_resultados(ods, CONSULTAS_ODS[consulta])
            except Exception as erro:
                falhas += 1
                print(f"{consulta}: ERRO - {erro}")
                federador.rollback()
                ods.rollback()
                continue

            total_federacao = sum(linhas_federacao.values())
            total_ods = sum(linhas_ods.values())
            iguais = linhas_federacao == linhas_ods

            print(
                f"{consulta}: {'OK' if iguais else 'DIVERGENTE'} | "
                f"Federacao: {total_federacao} | ODS: {total_ods}"
            )

            if not iguais:
                falhas += 1
                somente_federacao = linhas_federacao - linhas_ods
                somente_ods = linhas_ods - linhas_federacao
                for titulo, diferenca in (
                    ("Exemplo apenas na Federacao", somente_federacao),
                    ("Exemplo apenas no ODS", somente_ods),
                ):
                    exemplo = next(iter(diferenca), None)
                    if exemplo is not None:
                        print(f"  {titulo}: {exemplo!r}")

    if falhas:
        print(f"\nValidacao incompleta: {falhas} consulta(s) com problema.")
        raise SystemExit(1)

    print("\nValidacao concluida: C1 a C6 equivalentes.")


if __name__ == "__main__":
    main()