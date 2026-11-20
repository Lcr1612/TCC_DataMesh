r"""Experimento complementar QP3: custo e defasagem de sincronizacao do ODS.

O script executa ciclos periodicos controlados, SEM executar o monitoramento_ods.py.
Pare o monitoramento_ods.py (Ctrl+C) antes de usar este experimento.

Coloque este arquivo em: TCC_DataMesh/scripts/carga_ods/experimento_defasagem.py
Execute a partir da raiz do projeto:
    py scripts\carga_ods\experimento_defasagem.py --teste
    py scripts\carga_ods\experimento_defasagem.py --executar
    py scripts\carga_ods\experimento_defasagem.py --restaurar

--teste: 1 alteracao, um ciclo de 15 s; resultado separado (nao oficial).
--executar: 1, 10, 100 e 500 alteracoes, 5 repeticoes, ciclos de 120 s.
--restaurar: recupera os nomes originais se uma execucao anterior falhar.

Metodologia: seleciona somente produtos presentes em UMA linha do ODS,
altera temporariamente seus nomes na origem, sincroniza no proximo ciclo,
confere os dados no ODS e mede o tempo ate a verificacao de disponibilidade.
Ao final, restaura os nomes originais e sincroniza novamente.

AVISO: a defasagem ate a verificacao e um LIMITE SUPERIOR para a disponibilidade;
o instante exato do COMMIT do ODS nao e medido diretamente neste codigo.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg
except ImportError:
    print("Biblioteca psycopg nao instalada. Use o mesmo Python dos demais scripts.")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[2]
RESULTADOS = ROOT / "resultados"
SCRIPT_CARGA = ROOT / "scripts" / "carga_ods" / "carga_incremental.py"
PASSWORD = os.environ.get("TCC_DB_PASSWORD", "tcc123")

CAMPOS = [
    "tipo", "quantidade_planejada", "repeticao", "fase_alteracao_s",
    "intervalo_configurado_s", "atualizacao_origem_min_utc",
    "atualizacao_origem_max_utc", "commit_origem_utc", "inicio_carga_utc",
    "fim_carga_utc", "verificacao_ods_utc", "registros_sincronizados",
    "duracao_total_processo_ms", "espera_commit_ate_inicio_carga_s",
    "defasagem_commit_ate_verificacao_s", "intervalo_origem_ate_verificacao_s",
    "registro_mais_recente_ods_utc", "status"
]
REGEX_REGISTROS = re.compile(r"Registros sincronizados no ODS:\s*(\d+)")


def agora() -> datetime:
    return datetime.now(timezone.utc)


def fmt(t: datetime | None) -> str:
    return t.isoformat(timespec="milliseconds") if t is not None else ""


def conn_produtos():
    return psycopg.connect(host="localhost", port=5435, dbname="db_produtos",
                           user="tcc", password=PASSWORD)


def conn_ods():
    return psycopg.connect(host="localhost", port=5439, dbname="db_ods",
                           user="tcc", password=PASSWORD)


def guardar_csv(path: Path, valores: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    novo = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8-sig", newline="") as arq:
        writer = csv.DictWriter(arq, fieldnames=CAMPOS, delimiter=";")
        if novo:
            writer.writeheader()
        writer.writerow(valores)


def aguardar_ate(alvo: float) -> None:
    restante = alvo - time.monotonic()
    if restante > 0:
        time.sleep(restante)


def executar_carga() -> tuple[int, float, datetime, datetime]:
    """Cronometra o processo completo, incluindo inicializacao e commit."""
    inicio = agora()
    marco = time.perf_counter()
    p = subprocess.run([sys.executable, str(SCRIPT_CARGA)],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", check=False)
    duracao_ms = (time.perf_counter() - marco) * 1000.0
    fim = agora()
    achado = REGEX_REGISTROS.search(p.stdout)
    if p.returncode != 0 or achado is None:
        raise RuntimeError(
            f"Carga incremental falhou (codigo {p.returncode}).\n"
            f"Saida: {p.stdout[-1200:]}\nErro: {p.stderr[-2000:]}"
        )
    return int(achado.group(1)), duracao_ms, inicio, fim


def selecionar_produtos(n: int) -> list[dict]:
    """Cada produto escolhido deve ocupar exatamente uma linha no ODS."""
    with conn_ods() as ods:
        with ods.cursor() as cur:
            cur.execute("""
                SELECT id_produto FROM public.vendas_integradas
                GROUP BY id_produto HAVING COUNT(*) = 1
                ORDER BY id_produto LIMIT %s
            """, (n,))
            ids = [r[0] for r in cur.fetchall()]
    if len(ids) != n:
        raise RuntimeError(f"So foram encontrados {len(ids)} produtos com 1 item no ODS; "
                           f"sao necessarios {n} para esta configuracao.")
    with conn_produtos() as produtos:
        with produtos.cursor() as cur:
            cur.execute("SELECT id_produto, nome FROM public.produto "
                        "WHERE id_produto = ANY(%s)", (ids,))
            nomes = {a: b for a, b in cur.fetchall()}
    if len(nomes) != n:
        raise RuntimeError("Produtos encontrados no ODS nao coincidem com a origem.")
    return [{"id": p, "nome_original": nomes[p]} for p in ids]


def alterar_nomes(produtos: list[dict], etiqueta: str) -> tuple[datetime, datetime, datetime, dict[int, str]]:
    """Muda nomes de produtos e confirma transacao antes do proximo ciclo."""
    nomes = {}
    for item in produtos:
        sufixo = f" [QP3-{etiqueta}]"
        nomes[item["id"]] = item["nome_original"][:100-len(sufixo)] + sufixo
    with conn_produtos() as origem:
        with origem.cursor() as cur:
            cur.executemany("UPDATE public.produto SET nome = %s WHERE id_produto = %s",
                            [(nomes[item["id"]], item["id"]) for item in produtos])
            ids = [p["id"] for p in produtos]
            cur.execute("SELECT MIN(data_atualizacao), MAX(data_atualizacao) "
                        "FROM public.produto WHERE id_produto = ANY(%s)", (ids,))
            min_origem, max_origem = cur.fetchone()
        origem.commit()
    commit = agora()
    if min_origem is None or max_origem is None:
        raise RuntimeError("Datas de atualizacao da origem nao encontradas.")
    return min_origem, max_origem, commit, nomes


def validar_ods(nomes: dict[int, str]) -> tuple[datetime, datetime]:
    ids = list(nomes)
    with conn_ods() as ods:
        with ods.cursor() as cur:
            cur.execute("SELECT id_produto, nome_produto, data_carga_ods "
                        "FROM public.vendas_integradas "
                        "WHERE id_produto = ANY(%s)", (ids,))
            linhas = cur.fetchall()
        ods.commit()
    verificado = agora()
    if len(linhas) != len(ids):
        raise RuntimeError(f"ODS retornou {len(linhas)} itens; eram esperados {len(ids)}.")
    inconsistentes = [p for p, nome, _ in linhas if nomes.get(p) != nome]
    if inconsistentes:
        raise RuntimeError(f"ODS ainda nao refletiu {len(inconsistentes)} produtos: "
                           f"{inconsistentes[:10]}")
    return verificado, max(row[2] for row in linhas)


def restaurar(estado: Path) -> bool:
    if not estado.exists():
        print("Nao ha arquivo de recuperacao pendente.")
        return True
    doc = json.loads(estado.read_text(encoding="utf-8"))
    lista = doc["produtos"]
    print(f"Restaurando {len(lista)} nome(s) original(is) na origem...")
    with conn_produtos() as origem:
        with origem.cursor() as cur:
            cur.executemany("UPDATE public.produto SET nome = %s "
                            "WHERE id_produto = %s AND nome IS DISTINCT FROM %s",
                            [(p["nome_original"], p["id"], p["nome_original"]) for p in lista])
        origem.commit()
    total, duracao, _, _ = executar_carga()
    esperados = {p["id"]: p["nome_original"] for p in lista}
    validar_ods(esperados)
    print(f"Nomes restaurados e sincronizados no ODS. Linhas: {total}; "
          f"duracao do processo: {duracao:.2f} ms.")
    estado.unlink()
    return True


def preparar_estado(arquivo: Path, lista: list[dict]) -> None:
    if arquivo.exists():
        raise RuntimeError(f"Existe recuperacao pendente: {arquivo}. "
                           "Use --restaurar antes de iniciar outro experimento.")
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with arquivo.open("x", encoding="utf-8") as arq:
        json.dump({"produtos": lista, "criado_utc": fmt(agora())},
                  arq, ensure_ascii=False, indent=2)


def testar_ou_executar(teste: bool) -> None:
    if not SCRIPT_CARGA.is_file():
        raise RuntimeError(f"Nao encontrei {SCRIPT_CARGA}")
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    nome = "qp3_teste" if teste else "qp3_experimento"
    csv_path = RESULTADOS / f"{nome}.csv"
    estado = RESULTADOS / "qp3_recuperacao.json"
    if estado.exists():
        raise RuntimeError("Recuperacao pendente de execucao anterior. "
                           "Use --restaurar antes de continuar.")
    if csv_path.exists():
        raise RuntimeError(f"Ja existe {csv_path.name}. Para preservar as medicoes, "
                           "renomeie esse arquivo antes de repetir o experimento.")

    intervalo = 15.0 if teste else 120.0
    lotes = [1] if teste else [1, 10, 100, 500]
    fases = [3.0] if teste else [5.0, 25.0, 50.0, 75.0, 100.0]
    print(f"Modo: {'TESTE (nao oficial)' if teste else 'EXPERIMENTO QP3'}")
    print(f"Intervalo: {intervalo:.0f}s; tamanhos: {lotes}; repeticoes: {len(fases)}")
    print("IMPORTANTE: o monitoramento_ods.py deve estar PARADO.")

    lista = selecionar_produtos(max(lotes))
    preparar_estado(estado, lista)
    print(f"Recuperacao salva em: {estado}")
    restaurou = False
    try:
        print("Executando sincronizacao de referencia (sem contar nas medicoes)...")
        quantidade, _, _, _ = executar_carga()
        print(f"Referencia: {quantidade} registro(s) sincronizado(s).")
        # A primeira verificacao tambem marca o inicio do calendario periodico.
        ultima_verificacao = time.monotonic()
        contador = 0
        for lote in lotes:
            selecionados = lista[:lote]
            for repeticao, fase in enumerate(fases, 1):
                contador += 1
                proxima_verificacao = ultima_verificacao + intervalo
                instante_alteracao = ultima_verificacao + fase
                if instante_alteracao >= proxima_verificacao:
                    raise RuntimeError("A fase deve ser menor que o intervalo.")
                aguardar_ate(instante_alteracao)
                if time.monotonic() >= proxima_verificacao:
                    raise RuntimeError("O tempo de atualizacao ultrapassou o proximo ciclo; "
                                       "execucao interrompida para evitar medida incorreta.")
                min_origem, max_origem, commit, nomes = alterar_nomes(
                    selecionados, f"{lote}-{repeticao}-{contador}")
                if time.monotonic() >= proxima_verificacao:
                    raise RuntimeError("A alteracao terminou apos o inicio programado "
                                       "da sincronizacao; ciclo nao pode ser medido.")
                print(f"[{contador:02d}] {lote} alteracao(oes), fase {fase:.0f}s "
                      f"-> aguardando ciclo previsto...", flush=True)
                aguardar_ate(proxima_verificacao)
                ultima_verificacao = time.monotonic()
                sincronizados, duracao, ini_carga, fim_carga = executar_carga()
                visivel, ultima_data_carga = validar_ods(nomes)
                if sincronizados != lote:
                    raise RuntimeError(f"Foram sincronizadas {sincronizados} linhas, "
                                       f"mas esperavamos {lote}; confira sobreposicao "
                                       "com outro monitor e mudancas externas.")
                espera = (ini_carga - commit).total_seconds()
                defasagem_commit = (visivel - commit).total_seconds()
                intervalo_origem = (visivel - min_origem).total_seconds()
                linha = {
                    "tipo": "TESTE" if teste else "OFICIAL",
                    "quantidade_planejada": lote,
                    "repeticao": repeticao,
                    "fase_alteracao_s": f"{fase:.0f}",
                    "intervalo_configurado_s": f"{intervalo:.0f}",
                    "atualizacao_origem_min_utc": fmt(min_origem),
                    "atualizacao_origem_max_utc": fmt(max_origem),
                    "commit_origem_utc": fmt(commit),
                    "inicio_carga_utc": fmt(ini_carga),
                    "fim_carga_utc": fmt(fim_carga),
                    "verificacao_ods_utc": fmt(visivel),
                    "registros_sincronizados": sincronizados,
                    "duracao_total_processo_ms": f"{duracao:.2f}",
                    "espera_commit_ate_inicio_carga_s": f"{espera:.3f}",
                    "defasagem_commit_ate_verificacao_s": f"{defasagem_commit:.3f}",
                    "intervalo_origem_ate_verificacao_s": f"{intervalo_origem:.3f}",
                    "registro_mais_recente_ods_utc": fmt(ultima_data_carga),
                    "status": "SUCESSO",
                }
                guardar_csv(csv_path, linha)
                print(f"     SUCESSO: sincronizados={sincronizados}, "
                      f"processo={duracao:.2f} ms, "
                      f"defasagem ate verificacao={defasagem_commit:.2f} s", flush=True)
        restaurar(estado)
        restaurou = True
    finally:
         if not restaurou and estado.exists():
            print("\nExecucao interrompida: tentarei restaurar os nomes originais.")
            try:
                restaurar(estado)
            except Exception as erro:
                print(f"RESTAURACAO PENDENTE: {erro}")
                print(f"Nao apague {estado}. Execute --restaurar depois de corrigir a falha.")
    print(f"\nConcluido. Resultados: {csv_path}")
    print("As medidas oficiais do benchmark C1-C6 nao foram modificadas.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimento complementar QP3 do ODS")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--teste", action="store_true", help="1 ciclo curto de validacao")
    grupo.add_argument("--executar", action="store_true", help="experimento oficial com ciclos de 120s")
    grupo.add_argument("--restaurar", action="store_true", help="recupera produtos de execucao interrompida")
    args = parser.parse_args()
    try:
        if args.restaurar:
            restaurar(RESULTADOS / "qp3_recuperacao.json")
        else:
            testar_ou_executar(teste=args.teste)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario. Confira eventual restauracao pendente.")
        raise SystemExit(130)
    except Exception as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
