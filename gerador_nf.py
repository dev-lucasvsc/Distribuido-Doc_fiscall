"""
gerador_nf.py
Gera uma base grande de Notas Fiscais sinteticas e salva em CSV.
Cada linha = 1 item de NF, com campos suficientes para benchmark pesado.
"""

import csv
import random
from datetime import datetime, timedelta

BASE_PRODUTOS = [
    ("Alimentos", "Arroz 5kg", 25.0, 8.0),
    ("Alimentos", "Feijao 1kg", 10.0, 4.0),
    ("Alimentos", "Oleo de Soja 900ml", 8.0, 3.0),
    ("Alimentos", "Acucar 1kg", 5.0, 2.0),
    ("Alimentos", "Farinha de Trigo 1kg", 6.0, 2.5),
    ("Alimentos", "Macarrao 500g", 4.5, 1.5),
    ("Laticinios", "Leite Integral 1L", 5.5, 2.0),
    ("Laticinios", "Manteiga 200g", 10.0, 3.0),
    ("Mercearia", "Cafe 500g", 18.0, 6.0),
    ("Mercearia", "Sal 1kg", 2.5, 0.5),
    ("Carnes", "Carne Bovina 1kg", 45.0, 15.0),
    ("Carnes", "Frango 1kg", 18.0, 6.0),
    ("Frios", "Ovos 12un", 14.0, 4.0),
    ("Padaria", "Pao de Forma", 8.0, 2.5),
    ("Laticinios", "Iogurte 170g", 3.5, 1.0),
    ("Frios", "Queijo Mussarela 1kg", 42.0, 12.0),
    ("Limpeza", "Detergente 500ml", 3.0, 1.0),
    ("Limpeza", "Sabao em Po 1kg", 12.0, 4.0),
    ("Higiene", "Shampoo 400ml", 15.0, 5.0),
    ("Higiene", "Papel Higienico 4un", 8.0, 2.5),
]

MARCAS = ["Norte", "Sul", "Real", "Prime", "Bom", "Max", "Solar", "Verde", "Nobre", "Delta"]
PRODUTOS = [
    (categoria, f"{nome} {marca} Lote {lote:03d}", preco * (1 + lote / 1600), variacao)
    for lote in range(1, 21)
    for marca in MARCAS
    for categoria, nome, preco, variacao in BASE_PRODUTOS
]

ESTADOS = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "GO", "PE", "CE"]
CIDADES = {
    "SP": ["Sao Paulo", "Campinas", "Santos", "Ribeirao Preto", "Sorocaba"],
    "RJ": ["Rio de Janeiro", "Niteroi", "Petropolis", "Macae", "Campos"],
    "MG": ["Belo Horizonte", "Uberlandia", "Juiz de Fora", "Contagem", "Betim"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria"],
    "PR": ["Curitiba", "Londrina", "Maringa", "Cascavel", "Ponta Grossa"],
    "BA": ["Salvador", "Feira de Santana", "Vitoria da Conquista", "Ilheus", "Camacari"],
    "SC": ["Florianopolis", "Joinville", "Blumenau", "Chapeco", "Itajai"],
    "GO": ["Goiania", "Aparecida de Goiania", "Anapolis", "Rio Verde", "Luziania"],
    "PE": ["Recife", "Olinda", "Caruaru", "Petrolina", "Jaboatao"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Sobral", "Maracanau"],
}
ALIQUOTAS_ICMS = {
    "SP": 0.18, "RJ": 0.20, "MG": 0.18, "RS": 0.17, "PR": 0.19,
    "BA": 0.20, "SC": 0.17, "GO": 0.17, "PE": 0.18, "CE": 0.18,
}
CNPJS = [f"{i:02d}.{(i * 379) % 1000:03d}.{(i * 7919) % 1000:03d}/0001-{(i * 13) % 100:02d}" for i in range(1, 5001)]

DATA_INICIO = datetime(2022, 1, 1)
DATA_FIM    = datetime(2024, 12, 31)
DELTA_DIAS  = (DATA_FIM - DATA_INICIO).days

# Pré-computa datas para evitar cálculo repetido no loop
DATAS = [
    (DATA_INICIO + timedelta(days=d)).strftime("%Y-%m-%d")
    for d in range(DELTA_DIAS + 1)
]


def gerar_notas(quantidade: int = 16_000_000, arquivo: str = "notas_fiscais.csv") -> None:
    """
    Gera `quantidade` linhas flat de itens de NF.
    Cada linha representa 1 item com seu nf_id, data, estado, produto, qtd, preço e total.
    """
    print(f"Gerando {quantidade:,} registros de itens de NF...")

    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "item_id", "nf_id", "data", "estado", "cidade", "cnpj_emitente",
            "categoria", "produto", "quantidade", "preco_unitario", "desconto",
            "aliquota_icms", "valor_total"
        ])

        # Agrupa em NFs de 1–6 itens até atingir `quantidade` linhas
        item_id = 1
        nf_id   = 1

        while item_id <= quantidade:
            n_itens = random.randint(1, 6)
            data    = random.choice(DATAS)
            estado  = random.choice(ESTADOS)
            cidade  = random.choice(CIDADES[estado])
            cnpj    = random.choice(CNPJS)
            aliquota = ALIQUOTAS_ICMS[estado]

            for _ in range(n_itens):
                if item_id > quantidade:
                    break

                categoria, nome, preco_base, variacao = random.choice(PRODUTOS)
                preco = round(preco_base + random.uniform(-variacao, variacao * 2), 2)
                preco = max(preco, 0.50)
                qtd   = random.randint(1, 10)
                desconto = round(random.choice([0, 0, 0, 0.01, 0.02, 0.03, 0.05]) * preco * qtd, 2)
                total = round((preco * qtd) - desconto, 2)

                writer.writerow([
                    item_id, nf_id, data, estado, cidade, cnpj, categoria, nome,
                    qtd, preco, desconto, aliquota, total
                ])
                item_id += 1

            nf_id += 1

            if item_id % 500_000 == 1:
                print(f"  {item_id - 1:,} registros gerados...")

    print(f"\n[ok] Arquivo '{arquivo}' criado com sucesso!")
    print(f"  Total de registros : {quantidade:,}")
    print(f"  Total de NFs       : {nf_id - 1:,}\n")


if __name__ == "__main__":
    gerar_notas()
