r"""Executa a carga incremental do ODS periodicamente, sem alterar o script original.

Uso (na raiz do projeto TCC_DataMesh):
    py scripts\carga_ods\monitoramento_ods.py --uma-vez
    py scripts\carga_ods\monitoramento_ods.py
    py scripts\carga_ods\monitoramento_ods.py --intervalo 120

Cada ciclo inicia a rotina existente em um novo processo Python. O registro CSV
contém a duração total do processo, inclusive inicialização e commit.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARGA_INCREMENTAL = ROOT / "scripts" / "carga_ods" / "carga_incremental.py"
REGISTRO = ROOT / "resultados" / "monitoramento_ods.csv"
COLUNAS = [
    "inicio_execucao",
    "fim_execucao",
    "duracao_processo_ms",
    "registros_sincronizados",
    "status",
    "codigo_retorno",
]
PADRAO_REGISTROS = re.compile(r"Registros sincronizados no ODS:\s*(\d+)")


def horario_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def registrar(linha: dict) -> None:
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    novo = not REGISTRO.exists() or REGISTRO.stat().st_size == 0
    with REGISTRO.open("a", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, delimiter=";")
        if novo:
            escritor.writeheader()
        escritor.writerow(linha)


def executar_ciclo() -> None:
    inicio = horario_local()
    marco = time.perf_counter()
    print(f"\n[{inicio}] Iniciando verificacao do ODS...", flush=True)

    try:
        processo = subprocess.run(
            [sys.executable, str(CARGA_INCREMENTAL)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        codigo = processo.returncode
        saida = processo.stdout.strip()
        erro = processo.stderr.strip()
        if saida:
            print(saida, flush=True)
        if erro:
            print("Detalhes/erro:\n" + erro, file=sys.stderr, flush=True)
        achado = PADRAO_REGISTROS.search(saida)
        numero = int(achado.group(1)) if achado else None
        status = "SUCESSO" if codigo == 0 and numero is not None else "ERRO"
    except OSError as exc:
        codigo = -1
        numero = None
        status = "ERRO"
        print(f"Falha ao iniciar a carga incremental: {exc}", file=sys.stderr, flush=True)
   
    duracao_ms = (time.perf_counter() - marco) * 1000
    fim = horario_local()
    registrar({
        "inicio_execucao": inicio,
        "fim_execucao": fim,
        "duracao_processo_ms": f"{duracao_ms:.2f}",
        "registros_sincronizados": numero if numero is not None else "",
        "status": status,
        "codigo_retorno": codigo,
    })
    print(
        f"[{fim}] {status} | Registros: {numero if numero is not None else 'N/D'}"
        f" | Duracao total: {duracao_ms:.2f} ms",
        flush=True,
    )
    print(f"Registro salvo em: {REGISTRO}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitoramento periodico da carga incremental do ODS")
    parser.add_argument("--intervalo", type=float, default=120.0,
                        help="Segundos entre inicios de verificacao (padrao: 120)")
    parser.add_argument("--uma-vez", action="store_true",
                        help="Executa apenas uma verificacao e encerra")
    args = parser.parse_args()
    if args.intervalo <= 0:
        parser.error("--intervalo deve ser maior que zero")
    if not CARGA_INCREMENTAL.is_file():
        parser.error(f"Script de carga incremental nao encontrado: {CARGA_INCREMENTAL}")

    print("Monitoramento do ODS iniciado.")
    print(f"Intervalo entre inicios: {args.intervalo:g} segundos.")
    print("Pressione Ctrl+C para encerrar o monitoramento.")
    try:
        while True:
            marco_ciclo = time.monotonic()
            executar_ciclo()
            if args.uma_vez:
                break
            espera = max(0.0, args.intervalo - (time.monotonic() - marco_ciclo))
            print(f"Proxima verificacao em {espera:.1f} segundos.", flush=True)
            time.sleep(espera)
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido pelo usuario.", flush=True)
    
if __name__ == "__main__":
    main()