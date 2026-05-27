"""
analisador_sequencial.py
Analisa registros de NF de forma sequencial.

No modo pesado, o baseline faz trabalho fiscal e estatistico real:
- Decimal para valores monetarios
- parse de datas com datetime.strptime
- calculo e validacao de ICMS/desconto/total
- score simples de risco fiscal
- rankings, outliers e desvio padrao por produto
"""

import csv
import heapq
import math
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


CENTAVOS = Decimal("0.01")


def moeda(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def novo_produto() -> dict:
    return {
        "soma_valor": Decimal("0"),
        "soma_quadrados": Decimal("0"),
        "quantidade_vendida": 0,
        "total_itens": 0,
        "preco_min": Decimal("Infinity"),
        "preco_max": Decimal("-Infinity"),
        "outliers_preco": 0,
        "risco_total": 0,
    }


def analisar_sequencial(arquivo: str = "notas_fiscais.csv", modo: str = "pesado") -> dict:
    print("=" * 60)
    print(f"  ANALISE SEQUENCIAL - BASELINE ({modo.upper()})")
    print("=" * 60)

    inicio = time.perf_counter()

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

    with open(arquivo, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_linhas += 1

            item_id = row["item_id"]
            produto = row["produto"]
            estado = row["estado"]
            cidade = row.get("cidade", "")
            cnpj = row.get("cnpj_emitente", "")
            categoria = row.get("categoria", "Sem categoria")
            data_txt = row["data"]

            if modo == "pesado":
                data = datetime.strptime(data_txt, "%Y-%m-%d")
                mes = f"{data.year:04d}-{data.month:02d}"
                preco = Decimal(row["preco_unitario"])
                desconto = Decimal(row.get("desconto", "0"))
                aliquota = Decimal(row.get("aliquota_icms", "0"))
                total = Decimal(row["valor_total"])
                qtd = int(row["quantidade"])
                total_calculado = moeda((preco * qtd) - desconto)
                icms = moeda(total * aliquota)
            else:
                mes = data_txt[:7]
                preco = Decimal(str(float(row["preco_unitario"])))
                desconto = Decimal(str(float(row.get("desconto", "0"))))
                aliquota = Decimal(str(float(row.get("aliquota_icms", "0"))))
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

    tempo = time.perf_counter() - inicio
    resultado = finalizar_resultado(
        total_linhas, soma_total, soma_icms, maior_item, menor_item,
        stats_produto, stats_estado, stats_mes, stats_categoria,
        stats_cidade, stats_cnpj, inconsistencias, notas_suspeitas,
        top_itens, tempo, modo
    )

    _imprimir_resultado(resultado)
    return resultado


def finalizar_resultado(
    total_linhas, soma_total, soma_icms, maior_item, menor_item,
    stats_produto, stats_estado, stats_mes, stats_categoria,
    stats_cidade, stats_cnpj, inconsistencias, notas_suspeitas,
    top_itens, tempo, modo
) -> dict:
    produtos = {}
    for nome, s in stats_produto.items():
        media = s["soma_valor"] / s["total_itens"] if s["total_itens"] else Decimal("0")
        variancia = (s["soma_quadrados"] / s["total_itens"]) - (media * media) if s["total_itens"] else Decimal("0")
        desvio = math.sqrt(max(float(variancia), 0.0))
        produtos[nome] = {
            "soma_valor": float(moeda(s["soma_valor"])),
            "quantidade_vendida": s["quantidade_vendida"],
            "total_itens": s["total_itens"],
            "preco_min": float(moeda(s["preco_min"])),
            "preco_max": float(moeda(s["preco_max"])),
            "ticket_medio": float(moeda(media)),
            "desvio_padrao": round(desvio, 4),
            "outliers_preco": int(s["preco_max"] > s["preco_min"] * Decimal("2.5")),
            "risco_total": s["risco_total"],
        }

    return {
        "modo": modo,
        "total_linhas": total_linhas,
        "soma_total": float(moeda(soma_total)),
        "soma_icms": float(moeda(soma_icms)),
        "maior_item": {
            "valor": float(moeda(maior_item["valor"])),
            "item_id": maior_item["item_id"],
            "produto": maior_item["produto"],
        },
        "menor_item": {
            "valor": float(moeda(menor_item["valor"])),
            "item_id": menor_item["item_id"],
            "produto": menor_item["produto"],
        },
        "stats_produto": produtos,
        "stats_estado": {k: float(moeda(v)) for k, v in stats_estado.items()},
        "stats_mes": {k: float(moeda(v)) for k, v in sorted(stats_mes.items())},
        "stats_categoria": {k: float(moeda(v)) for k, v in stats_categoria.items()},
        "top_cidades": sorted(
            ((k, float(moeda(v))) for k, v in stats_cidade.items()),
            key=lambda x: -x[1]
        )[:20],
        "top_cnpjs": sorted(
            ((k, float(moeda(v))) for k, v in stats_cnpj.items()),
            key=lambda x: -x[1]
        )[:20],
        "top_itens": sorted(top_itens, reverse=True),
        "inconsistencias": inconsistencias,
        "notas_suspeitas": notas_suspeitas,
        "tempo_segundos": round(tempo, 4),
    }


def _imprimir_resultado(r: dict) -> None:
    print(f"\n  Registros processados      : {r['total_linhas']:>12,}")
    print(f"  Soma total (R$)            : {r['soma_total']:>15,.2f}")
    print(f"  ICMS estimado (R$)         : {r['soma_icms']:>15,.2f}")
    print(f"  Inconsistencias fiscais    : {r['inconsistencias']:>12,}")
    print(f"  Itens com risco fiscal     : {r['notas_suspeitas']:>12,}")

    mi = r["maior_item"]
    me = r["menor_item"]
    print(f"\n  Maior item  (id {mi['item_id']:>8}): R$ {mi['valor']:>10,.2f}  [{mi['produto']}]")
    print(f"  Menor item  (id {me['item_id']:>8}): R$ {me['valor']:>10,.2f}  [{me['produto']}]")

    print(f"\n  {'Produto':<42} {'Faturamento':>14}  {'Qtd':>10}  {'Ticket':>10}  {'Outliers':>8}")
    print(f"  {'-'*42} {'-'*14}  {'-'*10}  {'-'*10}  {'-'*8}")
    for nome, s in sorted(r["stats_produto"].items(), key=lambda x: -x[1]["soma_valor"])[:20]:
        print(
            f"  {nome[:42]:<42} R${s['soma_valor']:>12,.2f}"
            f"  {s['quantidade_vendida']:>10,}"
            f"  R${s['ticket_medio']:>8,.2f}"
            f"  {s['outliers_preco']:>8,}"
        )

    print(f"\n  Tempo sequencial           : {r['tempo_segundos']:.4f}s")
    print("=" * 60)


if __name__ == "__main__":
    analisar_sequencial()
