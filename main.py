import argparse
import multiprocessing as mp
import os

from gerador_nf import gerar_notas
from analisador_sequencial import analisar_sequencial
from analisador_paralelo import analisar_paralelo
from gerar_relatorio import gerar_relatorio


CSV    = "notas_fiscais.csv"
HTML   = "relatorio_nf.html"
VOLUME = 16_000_000
PROCESSOS_PADRAO = "2,4,8,12"   # sem 1: evita confusao sobre speedup < 1

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


def parse_processos(texto: str) -> list:
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


def imprimir_resumo(resultado_seq: dict, resultados_par: list) -> dict:

    melhor = min(resultados_par, key=lambda r: r["tempo_segundos"])
    t_seq  = resultado_seq["tempo_segundos"]

    print("\n" + "=" * 72)
    print("  RESUMO FINAL")
    print("=" * 72)
    print(f"  Baseline sequencial     : {t_seq:.4f}s  (1 processo, sem pool)")
    print(f"  CPUs logicas            : {mp.cpu_count()}")
    print()
    print(f"  {'Processos':>10} {'Tempo':>12} {'Speedup':>10} {'Eficiencia':>12}  Nota")
    print(f"  {'-'*10} {'-'*12} {'-'*10} {'-'*12}  {'-'*30}")

    for r in resultados_par:
        speedup    = round(t_seq / r["tempo_segundos"], 2)
        eficiencia = round((speedup / r["n_workers"]) * 100, 1)
        marca      = "<-- melhor" if r is melhor else ""

        if r["n_workers"] == 1:
            nota = "(overhead de pool — esperado)"
        else:
            nota = marca

        print(
            f"  {r['n_workers']:>10}"
            f" {r['tempo_segundos']:>10.4f}s"
            f" {speedup:>9.2f}x"
            f" {eficiencia:>11.1f}%"
            f"  {nota}"
        )

    print()
    print("  * Speedup < 1 com 1 processo e normal: o multiprocessing.Pool")
    print("    tem overhead de fork + pickle + IPC mesmo sem paralelismo real.")
    print("    A Lei de Amdahl explica: a parte serial do trabalho nao escala.")
    print("=" * 72)
    return melhor


def main():
    parser = argparse.ArgumentParser(description="Pipeline NF Sinteticas")
    parser.add_argument(
        "--processos",
        type=parse_processos,
        default=parse_processos(PROCESSOS_PADRAO),
        help="Lista de processos para testar, separada por virgula (padrao: 2,4,8,12)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Compatibilidade: testa apenas esta quantidade de processos",
    )
    parser.add_argument(
        "--com-1-processo",
        action="store_true",
        help="Inclui 1 processo no teste paralelo (mostra overhead do pool)",
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
        help=f"Quantidade de registros a gerar (padrao: {VOLUME:,})",
    )
    parser.add_argument(
        "--modo",
        choices=["pesado", "rapido"],
        default="pesado",
        help="Carga de analise: pesado usa Decimal, datas, impostos e score fiscal",
    )
    args = parser.parse_args()

    # Monta lista de processos a testar
    if args.workers is not None:
        processos_teste = [args.workers]
    else:
        processos_teste = args.processos
        if args.com_1_processo and 1 not in processos_teste:
            processos_teste = sorted([1] + processos_teste)

    # 1. Geração
    if args.skip_gen and csv_valido(CSV):
        print(f"[skip] '{CSV}' ja existe com layout correto — pulando geracao.\n")
    else:
        if args.skip_gen and os.path.exists(CSV):
            print(f"[regen] '{CSV}' existe com layout antigo. Regenerando.\n")
        gerar_notas(quantidade=args.volume, arquivo=CSV)

    # 2. Baseline sequencial
    print()
    resultado_seq = analisar_sequencial(arquivo=CSV, modo=args.modo)

    # 3. Análises paralelas
    resultados_par = []
    for n in processos_teste:
        print()
        resultado = analisar_paralelo(arquivo=CSV, n_workers=n, modo=args.modo)
        resultados_par.append(resultado)

    # 4. Resumo
    melhor = imprimir_resumo(resultado_seq, resultados_par)

    # 5. Relatório
    print()
    melhor["resultados_processos"] = resultados_par
    gerar_relatorio(resultado_seq, melhor, arquivo_saida=HTML)


if __name__ == "__main__":
    main()