# Benchmark de Paralelismo com Multiprocessing em Python

**Disciplina:** Programação Concorrente e Distribuída  
**Turma:** ADSN04  
**Professor:** Rafael  
**Aluno 1:** Lucas Vasconcelos Pessoa de Oliveira

**Aluno 2:** Joao Gabriel Lucas Pinheiro de Lima

**Aluno 3:** Gabriel Yan Ribeiro da Costa

**Aluno 4:** Waldo Andrade Silva

**Data:** 27/05/2026  

---

## 1. Descrição do Problema

O programa foi feito para processar uma grande base sintética de **notas fiscais em CSV**, comparando o tempo de execução sequencial com o tempo usando vários processos em paralelo.

A base possui milhões de itens de notas fiscais. Cada linha contém dados como produto, estado, cidade, CNPJ do emissor, quantidade, preço unitário, desconto, alíquota de ICMS e valor total. O objetivo é simular um cenário de análise fiscal pesada, com validações monetárias, cálculo de impostos, agregações e rankings.

| Pergunta | Resposta |
|----------|----------|
| Objetivo | Analisar uma base grande de notas fiscais e comparar execução sequencial com execução paralela |
| Volume de dados | CSV com 8.000.000 registros, aproximadamente 932 MB |
| Algoritmo | Divisão do arquivo CSV por faixas de bytes + processamento paralelo com `multiprocessing.Pool.map()` |
| Complexidade | O(N/p) para a etapa de análise, onde N é o número de registros e p é o número de processos |

---

## 2. Ambiente Experimental

| Item | Descrição |
|------|-----------|
| Processador | AMD Ryzen 7 5700X 8-Core Processor - 3.40 GHz |
| Número de núcleos | 8 núcleos físicos / 16 threads lógicas |
| Memória RAM | 32,0 GB |
| Armazenamento | 932 GB |
| Placa de vídeo | NVIDIA GeForce RTX 5060 Ti - 8 GB |
| Sistema Operacional | Windows 11 - 64 bits |
| Linguagem utilizada | Python 3 |
| Biblioteca de paralelização | `multiprocessing` |
| Compilador / Versão | CPython |

---

## 3. Metodologia de Testes

O tempo foi medido usando `time.perf_counter()`, contando o tempo total da análise, desde o início do processamento até a consolidação dos resultados.

A versão sequencial percorre o CSV inteiro em um único processo. A versão paralela divide o arquivo em partes por offset de bytes, alinhando os cortes em quebras de linha para evitar registros cortados. Cada processo analisa sua parte e retorna resultados parciais, que depois são reduzidos em um resultado final.

Em cada registro, o programa executa tarefas como:

- Conversão monetária com `Decimal`
- Parse real de datas com `datetime.strptime`
- Cálculo estimado de ICMS
- Validação de `valor_total = quantidade * preço_unitário - desconto`
- Agregação por produto, estado, cidade, CNPJ, categoria e mês
- Cálculo de ticket médio, desvio padrão e score de risco fiscal
- Geração de rankings

### Configurações testadas

- 1 processo
- 2 processos
- 4 processos
- 8 processos
- 12 processos

---

## 4. Resultados Experimentais

| Nº Processos | Tempo de Execução (s) |
|:------------:|:---------------------:|
| 1            | 133.9281              |
| 2            | 68.6179               |
| 4            | 35.8380               |
| 8            | 20.4565               |
| 12           | 18.0960               |

---

## 5. Cálculo de Speedup e Eficiência

O **speedup** mostra quantas vezes a execução paralela ficou mais rápida em relação ao tempo sequencial:

```text
Speedup(p) = T_sequencial / T(p)
```

A **eficiência** mostra o quanto os processos foram aproveitados:

```text
Eficiência(p) = Speedup(p) / p
```

---

## 6. Tabela de Resultados

| Processos | Tempo (s) | Speedup | Eficiência |
|:---------:|:---------:|:-------:|:----------:|
| 1         | 133.9281  | 0.88x   | 88.0%      |
| 2         | 68.6179   | 1.73x   | 86.5%      |
| 4         | 35.8380   | 3.30x   | 82.5%      |
| 8         | 20.4565   | 5.79x   | 72.4%      |
| 12        | 18.0960   | 6.54x   | 54.5%      |

> **Melhor resultado: 12 processos (18.0960s)**

---

## 7. Gráficos

<p align="center">
  <img src="tempo.execucao.svg" alt="Gráfico de tempo de execução" width="32%">
  <img src="speedup.svg" alt="Gráfico de speedup" width="32%">
  <img src="eficiencia.svg" alt="Gráfico de eficiência" width="32%">
</p>

---

## 8. Análise dos Resultados

Os resultados mostram ganho consistente conforme o número de processos aumenta. Com 2 processos, o tempo caiu de 133.9281s para 68.6179s, quase reduzindo pela metade. Com 4 processos, o speedup chegou a 3.30x, ainda com eficiência alta de 82.5%.

O melhor tempo foi obtido com **12 processos**, chegando a 18.0960s e speedup de 6.54x. Isso mostra que, mesmo o Ryzen 7 5700X tendo 8 núcleos físicos, usar mais processos que núcleos ainda trouxe ganho neste caso, provavelmente porque parte do tempo envolve leitura do arquivo, parsing de CSV, criação de objetos `Decimal` e espera por memória/cache.

A eficiência diminuiu conforme os processos aumentaram. Isso é esperado, pois há overhead de criação e gerenciamento de processos, disputa por memória/cache, acesso simultâneo ao arquivo e custo de redução dos resultados parciais. Mesmo assim, a eficiência com 8 processos ainda foi boa, chegando a 72.4%.

**Principais fatores limitantes:**

- Leitura de um CSV grande em disco
- Parsing de texto e conversões por linha
- Uso de `Decimal`, que é mais correto para valores monetários, mas mais pesado que `float`
- Overhead de criação e comunicação entre processos
- Disputa por memória/cache ao usar muitos processos

---

## 9. Conclusão

O paralelismo com `multiprocessing` trouxe uma melhora expressiva no processamento das notas fiscais. O tempo caiu de 133.9281s com 1 processo para 18.0960s com 12 processos.

O melhor resultado foi obtido com **12 processos**, alcançando speedup de **6.54x**. O ganho não foi perfeitamente linear porque o processamento possui overhead de I/O, parsing, agregação e redução dos resultados parciais.

Mesmo assim, o experimento comprova que o uso de múltiplos processos é eficiente para esse tipo de análise fiscal pesada, principalmente porque o trabalho por linha é independente e pode ser dividido entre vários processos.

**Melhorias futuras:**

- Executar cada configuração mais de uma vez e calcular média/desvio padrão
- Testar 16 processos, já que o Ryzen 7 5700X possui 16 threads lógicas
- Comparar CSV com formatos mais eficientes, como Parquet
- Testar `ProcessPoolExecutor` do `concurrent.futures`
- Medir separadamente tempo de leitura, processamento e redução
