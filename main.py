"""
main.py
Orquestra o pipeline:
  1. Gera 8M de registros de NF sinteticas, se necessario
  2. Roda analise sequencial como baseline
  3. Roda analise paralela com 1, 2, 4, 8 e 12 processos
  4. Calcula speedup e eficiencia para cada cenario
  5. Gera relatorio HTML usando o melhor resultado paralelo

Uso:
  python main.py
  python main.py --skip-gen
  python main.py --processos 1,2,4,8,12
  python main.py --workers 8      # compatibilidade: testa apenas 8 processos
"""

import argparse
import multiprocessing as mp
import os

from gerador_nf import gerar_notas
from analisador_sequencial import analisar_sequencial
from analisador_paralelo import analisar_paralelo
from gerar_relatorio import gerar_relatorio


CSV = "notas_fiscais.csv"
HTML = "relatorio_nf.html"
VOLUME = 8_000_000
PROCESSOS_PADRAO = "1,2,4,8,12"
COLUNAS_ESPERADAS = [
    "item_id", "nf_id", "data", "estado", "cidade", "cnpj_emitente",
    "categoria", "produto", "quantidade", "preco_unitario", "desconto",
    "aliquota_icms", "valor_total",
]


def csv_valido(arquivo: str) -> bool:
    if not os.path.exists(arquivo):
        return False
    try:
        with open(arquivo, "r", encoding="utf-8", newline="") as f:
            cabecalho = f.readline().strip().split(",")
        return cabecalho == COLUNAS_ESPERADAS
    except OSError:
        return False


def parse_processos(texto: str) -> list[int]:
    processos = []
    for parte in texto.split(","):
        parte = parte.strip()
        if not parte:
            continue
        valor = int(parte)
        if valor < 1:
            raise argparse.ArgumentTypeError("A quantidade de processos deve ser >= 1")
        processos.append(valor)

    if not processos:
        raise argparse.ArgumentTypeError("Informe ao menos uma quantidade de processos")

    return sorted(set(processos))


def imprimir_resumo(resultado_seq: dict, resultados_par: list[dict]) -> dict:
    melhor = min(resultados_par, key=lambda r: r["tempo_segundos"])

    print("\n" + "=" * 72)
    print("  RESUMO FINAL - PROCESSOS")
    print("=" * 72)
    print(f"  Sequencial              : {resultado_seq['tempo_segundos']:.4f}s")
    print(f"  CPUs logicas detectadas : {mp.cpu_count()}")
    print("  Ryzen 7 5700X           : 8 nucleos fisicos / 16 threads logicas")
    print()
    print(f"  {'Processos':>10} {'Tempo':>12} {'Speedup':>10} {'Eficiencia':>12}")
    print(f"  {'-' * 10} {'-' * 12} {'-' * 10} {'-' * 12}")

    for r in resultados_par:
        speedup = round(resultado_seq["tempo_segundos"] / r["tempo_segundos"], 2)
        eficiencia = round((speedup / r["n_workers"]) * 100, 1)
        marca = "  <-- melhor" if r is melhor else ""
        print(
            f"  {r['n_workers']:>10}"
            f" {r['tempo_segundos']:>10.4f}s"
            f" {speedup:>9.2f}x"
            f" {eficiencia:>11.1f}%"
            f"{marca}"
        )

    print("=" * 72)
    return melhor


def main():
    parser = argparse.ArgumentParser(description="Pipeline NF Sinteticas")
    parser.add_argument(
        "--processos",
        type=parse_processos,
        default=parse_processos(PROCESSOS_PADRAO),
        help="Lista de processos para testar, separada por virgula (padrao: 1,2,4,8,12)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Compatibilidade: testa apenas esta quantidade de processos",
    )
    parser.add_argument(
        "--skip-gen",
        action="store_true",
        help="Pula geracao do CSV se ele ja existir no layout atual",
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=VOLUME,
        help="Quantidade de registros a gerar (padrao: 8.000.000)",
    )
    parser.add_argument(
        "--modo",
        choices=["pesado", "rapido"],
        default="pesado",
        help="Carga de analise: pesado usa Decimal, datas, impostos, rankings e score fiscal",
    )
    args = parser.parse_args()

    processos_teste = [args.workers] if args.workers is not None else args.processos

    if args.skip_gen and csv_valido(CSV):
        print(f"[skip] '{CSV}' ja existe - pulando geracao.\n")
    else:
        if args.skip_gen and os.path.exists(CSV):
            print(f"[regen] '{CSV}' existe, mas o layout e antigo. Regenerando.\n")
        gerar_notas(quantidade=args.volume, arquivo=CSV)

    print()
    resultado_seq = analisar_sequencial(arquivo=CSV, modo=args.modo)

    resultados_par = []
    for n_processos in processos_teste:
        print()
        resultado = analisar_paralelo(arquivo=CSV, n_workers=n_processos, modo=args.modo)
        resultados_par.append(resultado)

    melhor = imprimir_resumo(resultado_seq, resultados_par)

    print()
    melhor["resultados_processos"] = resultados_par
    gerar_relatorio(resultado_seq, melhor, arquivo_saida=HTML)


if __name__ == "__main__":
    main()
