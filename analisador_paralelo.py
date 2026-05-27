"""
analisador_paralelo.py
Analisa registros de NF usando multiprocessing.

Divide o CSV por faixas de bytes, cada worker processa um trecho e o
processo principal reduz os resultados parciais.
"""

import csv
import heapq
import os
import time
import multiprocessing as mp
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from analisador_sequencial import finalizar_resultado, moeda, novo_produto


CAMPOS = [
    "item_id", "nf_id", "data", "estado", "cidade", "cnpj_emitente",
    "categoria", "produto", "quantidade", "preco_unitario", "desconto",
    "aliquota_icms", "valor_total"
]


def processar_chunk(args: tuple) -> dict:
    arquivo, offset_inicio, offset_fim, modo = args

    soma_total = Decimal("0")
    soma_icms = Decimal("0")
    total_linhas = 0
    inconsistencias = 0
    notas_suspeitas = 0
    maior_item = {"valor": Decimal("-Infinity"), "item_id": None, "produto": None}
    menor_item = {"valor": Decimal("Infinity"), "item_id": None, "produto": None}

    stats_produto = defaultdict(novo_produto)
    stats_estado = defaultdict(Decimal)
    stats_mes = defaultdict(Decimal)
    stats_categoria = defaultdict(Decimal)
    stats_cidade = defaultdict(Decimal)
    stats_cnpj = defaultdict(Decimal)
    top_itens = []

    with open(arquivo, "rb") as f:
        f.seek(offset_inicio)

        while True:
            pos_atual = f.tell()
            if pos_atual >= offset_fim:
                break

            linha_bytes = f.readline()
            if not linha_bytes:
                break

            linha = linha_bytes.decode("utf-8").strip()
            if not linha:
                continue

            partes = next(csv.reader([linha]))
            if len(partes) != len(CAMPOS) or partes[0] == "item_id":
                continue

            row = dict(zip(CAMPOS, partes))
            total_linhas += 1

            item_id = row["item_id"]
            produto = row["produto"]
            estado = row["estado"]
            cidade = row["cidade"]
            cnpj = row["cnpj_emitente"]
            categoria = row["categoria"]
            data_txt = row["data"]

            if modo == "pesado":
                data = datetime.strptime(data_txt, "%Y-%m-%d")
                mes = f"{data.year:04d}-{data.month:02d}"
                preco = Decimal(row["preco_unitario"])
                desconto = Decimal(row["desconto"])
                aliquota = Decimal(row["aliquota_icms"])
                total = Decimal(row["valor_total"])
                qtd = int(row["quantidade"])
                total_calculado = moeda((preco * qtd) - desconto)
                icms = moeda(total * aliquota)
            else:
                mes = data_txt[:7]
                preco = Decimal(str(float(row["preco_unitario"])))
                desconto = Decimal(str(float(row["desconto"])))
                aliquota = Decimal(str(float(row["aliquota_icms"])))
                total = Decimal(str(float(row["valor_total"])))
                qtd = int(row["quantidade"])
                total_calculado = total
                icms = total * aliquota

            soma_total += total
            soma_icms += icms

            risco = 0
            if total_calculado != total:
                inconsistencias += 1
                risco += 40
            if desconto > moeda(preco * qtd * Decimal("0.04")):
                risco += 20
            if total > Decimal("1500"):
                risco += 15
            if qtd >= 10:
                risco += 5
            if aliquota >= Decimal("0.20"):
                risco += 5
            if risco >= 30:
                notas_suspeitas += 1

            if total > maior_item["valor"]:
                maior_item = {"valor": total, "item_id": item_id, "produto": produto}
            if total < menor_item["valor"]:
                menor_item = {"valor": total, "item_id": item_id, "produto": produto}

            p = stats_produto[produto]
            media_anterior = p["soma_valor"] / p["total_itens"] if p["total_itens"] else total
            if p["total_itens"] > 30 and total > media_anterior * Decimal("2.75"):
                p["outliers_preco"] += 1

            p["soma_valor"] += total
            p["soma_quadrados"] += total * total
            p["quantidade_vendida"] += qtd
            p["total_itens"] += 1
            p["risco_total"] += risco
            if preco < p["preco_min"]:
                p["preco_min"] = preco
            if preco > p["preco_max"]:
                p["preco_max"] = preco

            stats_estado[estado] += total
            stats_mes[mes] += total
            stats_categoria[categoria] += total
            stats_cidade[f"{estado}/{cidade}"] += total
            stats_cnpj[cnpj] += total

            entrada_top = (float(total), item_id, produto)
            if len(top_itens) < 100:
                heapq.heappush(top_itens, entrada_top)
            elif entrada_top[0] > top_itens[0][0]:
                heapq.heapreplace(top_itens, entrada_top)

    return {
        "total_linhas": total_linhas,
        "soma_total": soma_total,
        "soma_icms": soma_icms,
        "maior_item": maior_item,
        "menor_item": menor_item,
        "stats_produto": dict(stats_produto),
        "stats_estado": dict(stats_estado),
        "stats_mes": dict(stats_mes),
        "stats_categoria": dict(stats_categoria),
        "stats_cidade": dict(stats_cidade),
        "stats_cnpj": dict(stats_cnpj),
        "top_itens": top_itens,
        "inconsistencias": inconsistencias,
        "notas_suspeitas": notas_suspeitas,
    }


def reduzir(parciais: list, tempo: float, modo: str) -> dict:
    soma_total = Decimal("0")
    soma_icms = Decimal("0")
    total_linhas = 0
    inconsistencias = 0
    notas_suspeitas = 0
    maior_item = {"valor": Decimal("-Infinity"), "item_id": None, "produto": None}
    menor_item = {"valor": Decimal("Infinity"), "item_id": None, "produto": None}

    stats_produto = defaultdict(novo_produto)
    stats_estado = defaultdict(Decimal)
    stats_mes = defaultdict(Decimal)
    stats_categoria = defaultdict(Decimal)
    stats_cidade = defaultdict(Decimal)
    stats_cnpj = defaultdict(Decimal)
    top_itens = []

    for r in parciais:
        soma_total += r["soma_total"]
        soma_icms += r["soma_icms"]
        total_linhas += r["total_linhas"]
        inconsistencias += r["inconsistencias"]
        notas_suspeitas += r["notas_suspeitas"]

        if r["maior_item"]["valor"] > maior_item["valor"]:
            maior_item = r["maior_item"]
        if r["menor_item"]["valor"] < menor_item["valor"]:
            menor_item = r["menor_item"]

        for prod, s in r["stats_produto"].items():
            p = stats_produto[prod]
            p["soma_valor"] += s["soma_valor"]
            p["soma_quadrados"] += s["soma_quadrados"]
            p["quantidade_vendida"] += s["quantidade_vendida"]
            p["total_itens"] += s["total_itens"]
            p["outliers_preco"] += s["outliers_preco"]
            p["risco_total"] += s["risco_total"]
            if s["preco_min"] < p["preco_min"]:
                p["preco_min"] = s["preco_min"]
            if s["preco_max"] > p["preco_max"]:
                p["preco_max"] = s["preco_max"]

        for estado, v in r["stats_estado"].items():
            stats_estado[estado] += v
        for mes, v in r["stats_mes"].items():
            stats_mes[mes] += v
        for categoria, v in r["stats_categoria"].items():
            stats_categoria[categoria] += v
        for cidade, v in r["stats_cidade"].items():
            stats_cidade[cidade] += v
        for cnpj, v in r["stats_cnpj"].items():
            stats_cnpj[cnpj] += v

        for item in r["top_itens"]:
            if len(top_itens) < 100:
                heapq.heappush(top_itens, item)
            elif item[0] > top_itens[0][0]:
                heapq.heapreplace(top_itens, item)

    return finalizar_resultado(
        total_linhas, soma_total, soma_icms, maior_item, menor_item,
        stats_produto, stats_estado, stats_mes, stats_categoria,
        stats_cidade, stats_cnpj, inconsistencias, notas_suspeitas,
        top_itens, tempo, modo
    )


def dividir_por_bytes(arquivo: str, n_workers: int, modo: str) -> list:
    tamanho = os.path.getsize(arquivo)
    chunk_size = tamanho // n_workers

    limites = [0]
    with open(arquivo, "rb") as f:
        for i in range(1, n_workers):
            f.seek(i * chunk_size)
            f.readline()
            limites.append(f.tell())
    limites.append(tamanho)

    chunks = []
    for inicio, fim in zip(limites, limites[1:]):
        if inicio < fim:
            chunks.append((arquivo, inicio, fim, modo))

    return chunks


def analisar_paralelo(arquivo: str = "notas_fiscais.csv", n_workers: int = None, modo: str = "pesado") -> dict:
    if n_workers is None:
        n_workers = mp.cpu_count()

    print("=" * 60)
    print(f"  ANALISE PARALELA ({modo.upper()})")
    print(f"  Processos : {n_workers}  |  CPUs logicas disponiveis: {mp.cpu_count()}")
    print("=" * 60)

    chunks = dividir_por_bytes(arquivo, n_workers, modo)
    inicio = time.perf_counter()

    with mp.Pool(processes=n_workers) as pool:
        parciais = pool.map(processar_chunk, chunks)

    tempo = time.perf_counter() - inicio
    resultado = reduzir(parciais, tempo, modo)
    resultado["tempo_segundos"] = round(tempo, 4)
    resultado["n_workers"] = n_workers

    _imprimir_resultado(resultado)
    return resultado


def _imprimir_resultado(r: dict) -> None:
    print(f"\n  Registros processados      : {r['total_linhas']:>12,}")
    print(f"  Soma total (R$)            : {r['soma_total']:>15,.2f}")
    print(f"  ICMS estimado (R$)         : {r['soma_icms']:>15,.2f}")
    print(f"  Inconsistencias fiscais    : {r['inconsistencias']:>12,}")
    print(f"  Itens com risco fiscal     : {r['notas_suspeitas']:>12,}")

    print(f"\n  {'Produto':<42} {'Faturamento':>14}  {'Qtd':>10}  {'Ticket':>10}  {'Outliers':>8}")
    print(f"  {'-'*42} {'-'*14}  {'-'*10}  {'-'*10}  {'-'*8}")
    for nome, s in sorted(r["stats_produto"].items(), key=lambda x: -x[1]["soma_valor"])[:20]:
        print(
            f"  {nome[:42]:<42} R${s['soma_valor']:>12,.2f}"
            f"  {s['quantidade_vendida']:>10,}"
            f"  R${s['ticket_medio']:>8,.2f}"
            f"  {s['outliers_preco']:>8,}"
        )

    print(f"\n  Tempo paralelo ({r['n_workers']} processos): {r['tempo_segundos']:.4f}s")
    print("=" * 60)


if __name__ == "__main__":
    analisar_paralelo()
