# Benchmark de Paralelismo com Multiprocessing em Python

**Disciplina:** Programação Concorrente e Distribuída  
**Turma:** ADSN04  
**Professor:** Rafael  
**Aluno 1:** Lucas Vasconcelos Pessoa de Oliveira  
**Aluno 2:** Joao Gabriel Lucas Pinheiro de Lima  

**Data:** 10/06/2026  

---

## 1. Descrição do Problema

O programa foi feito para processar uma grande base sintética de **notas fiscais em CSV**, comparando o tempo de execução sequencial com o tempo usando vários processos em paralelo.

A base possui 16 milhões de itens de notas fiscais. Cada linha contém dados como produto, estado, cidade, CNPJ do emissor, quantidade, preço unitário, desconto, alíquota de ICMS e valor total. O objetivo é simular um cenário de análise fiscal pesada, com validações monetárias, cálculo de impostos, agregações e rankings.

| Pergunta | Resposta |
|----------|----------|
| Objetivo | Analisar uma base grande de notas fiscais e comparar execução sequencial com execução paralela |
| Volume de dados | CSV com **16.000.000 registros**, aproximadamente 1,9 GB |
| Algoritmo | Divisão do arquivo CSV por faixas de bytes + processamento paralelo com `multiprocessing.Pool.map()` |
| Complexidade | O(N/p) para a etapa de análise, onde N é o número de registros e p é o número de processos |

---

## 2. Ambiente Experimental

| Item | Descrição |
|------|-----------|
| Processador | AMD Ryzen 7 5700X 8-Core Processor — 3,40 GHz |
| Número de núcleos | 8 núcleos físicos / 16 threads lógicas |
| Memória RAM | 32,0 GB |
| Armazenamento | 932 GB |
| Placa de vídeo | NVIDIA GeForce RTX 5060 Ti — 8 GB |
| Sistema Operacional | Windows 11 — 64 bits |
| Linguagem utilizada | Python 3.12 |
| Biblioteca de paralelização | `multiprocessing` |
| Implementação | CPython |

---

## 3. Metodologia de Testes

O tempo foi medido usando `time.perf_counter()`, contando o tempo total da análise desde o início do processamento até a consolidação dos resultados parciais.

A versão sequencial percorre o CSV inteiro em um único processo. A versão paralela divide o arquivo em partes por offset de bytes, alinhando os cortes em quebras de linha para evitar registros cortados. Cada processo analisa sua parte de forma independente e retorna resultados parciais, que são reduzidos em um resultado final pelo processo principal.

Em cada registro, o programa executa:

- Conversão monetária com `Decimal` (precisão de centavos)
- Parse real de datas com `datetime.strptime`
- Cálculo estimado de ICMS por alíquota
- Validação de `valor_total = quantidade × preço_unitário − desconto`
- Agregação por produto, estado, cidade, CNPJ, categoria e mês
- Cálculo de ticket médio, desvio padrão e score de risco fiscal
- Geração de rankings com `heapq`

### Configurações testadas

- Sequencial puro (baseline, sem pool)
- 2 processos paralelos
- 4 processos paralelos
- 8 processos paralelos
- 12 processos paralelos

> O teste com 1 processo paralelo foi omitido da tabela principal porque o `multiprocessing.Pool` tem overhead de fork, pickle e IPC mesmo sem paralelismo real, resultando em speedup < 1. Esse comportamento é esperado e previsto pela Lei de Amdahl.

---

## 4. Evidências de Execução

As imagens abaixo foram capturadas do Gerenciador de Tarefas do Windows durante a execução, mostrando o uso real de CPU crescendo conforme o número de processos aumenta:

| Configuração | Utilização de CPU observada |
|:------------:|:---------------------------:|
| Sequencial   | ~12%                        |
| 2 processos  | ~14%                        |
| 4 processos  | ~32%                        |
| 8 processos  | ~54%                        |
| 12 processos | ~77%                        |

Isso confirma que o paralelismo está sendo aproveitado de forma real pelo sistema operacional, distribuindo a carga entre os núcleos físicos e lógicos do Ryzen 7 5700X.

---

## 5. Resultados Experimentais

| Nº Processos | Tempo de Execução (s) |
|:------------:|:---------------------:|
| Sequencial   | 241,8228              |
| 2            | 195,7147              |
| 4            | 104,1233              |
| 8            | 54,2650               |
| 12           | 38,2255               |

---

## 6. Cálculo de Speedup e Eficiência

O **speedup** mede quantas vezes a execução paralela ficou mais rápida em relação ao baseline sequencial puro:

```
Speedup(p) = T_sequencial / T(p)
```

A **eficiência** mede o aproveitamento médio de cada processo:

```
Eficiência(p) = Speedup(p) / p × 100%
```

---

## 7. Tabela de Resultados

| Processos | Tempo (s) | Speedup | Eficiência |
|:---------:|:---------:|:-------:|:----------:|
| Seq.      | 241,8228  | 1,00×   | —          |
| 2         | 195,7147  | 1,24×   | 62,0%      |
| 4         | 104,1233  | 2,32×   | 58,0%      |
| 8         | 54,2650   | 4,46×   | 55,8%      |
| 12        | 38,2255   | 6,33×   | 52,8%      |

> **Melhor resultado: 12 processos — 38,2255s — speedup de 6,33×**

---

## 8. Gráficos

<p align="center">
  <img src="tempo.execucao.svg" alt="Gráfico de tempo de execução" width="32%">
  <img src="speedup.svg" alt="Gráfico de speedup" width="32%">
  <img src="eficiencia.svg" alt="Gráfico de eficiência" width="32%">
</p>

---

## 9. Por que a Eficiência Cai com Mais Processos?

A queda de eficiência de 62,0% (2 processos) para 52,8% (12 processos) é um comportamento esperado e previsto teoricamente pela **Lei de Amdahl**.

A Lei de Amdahl estabelece que toda tarefa paralela possui uma fração serial inevitável — partes do trabalho que não podem ser divididas entre processos. Quanto maior o número de processos, mais essa fração serial pesa no tempo total, limitando o ganho real.

No caso deste projeto, as frações seriais identificadas são:

**Leitura do arquivo em disco.** O SSD possui uma fila de I/O única. Com 12 processos lendo simultaneamente, há contenção — os processos se esperam na fila de acesso ao disco, mesmo em NVMe.

**Redução dos resultados parciais.** Após cada worker terminar, um único processo consolida todos os resultados. Esse custo cresce linearmente com o número de workers.

**Overhead do `mp.Pool`.** Fork de processo, serialização com `pickle` e comunicação IPC existem para cada worker. Com 12 processos, esse overhead acumula e não é paralelizável.

**Disputa por cache L3.** O Ryzen 7 5700X possui 32 MB de cache L3 compartilhado entre os 8 núcleos. Com 12 processos ativos, há pressão sobre esse cache, causando cache misses que custam centenas de ciclos cada.

Por isso, mesmo que o speedup continue crescendo (o tempo total continua caindo), a **eficiência por processo diminui** — cada processo adicional contribui menos do que o anterior.

Vale destacar que eficiência baixa não significa que usar mais processos foi uma má escolha. O objetivo do experimento é minimizar o tempo de execução. Com 12 processos e 52,8% de eficiência, o tempo foi de 38,2s — significativamente melhor que os 54,3s com 8 processos e 55,8% de eficiência.

---

## 10. Análise dos Resultados

Os resultados mostram ganho consistente conforme o número de processos aumenta. Com 4 processos, o tempo caiu de 241,8s para 104,1s — redução de 57%. Com 8 processos chegou a 54,3s, e com 12 processos ao melhor resultado de 38,2s.

O uso de CPU observado no Gerenciador de Tarefas confirma o funcionamento real do paralelismo: com 12 processos, o Ryzen 7 5700X atingiu 77% de utilização, evidenciando que todos os núcleos estavam ativos simultaneamente.

**Principais fatores limitantes:**

- Leitura de um CSV de ~1,9 GB em disco (contenção de I/O)
- Parsing de texto e conversões `Decimal` por linha (CPU-bound pesado)
- Overhead de criação e gerenciamento de processos pelo `mp.Pool`
- Custo de serialização com `pickle` na comunicação entre processos
- Pressão sobre o cache L3 compartilhado com múltiplos processos ativos

---

## 11. Conclusão

O paralelismo com `multiprocessing` trouxe melhora expressiva no processamento das 16 milhões de notas fiscais. O tempo caiu de **241,8228s** no sequencial para **38,2255s** com 12 processos — redução de aproximadamente **84% no tempo total**.

O ganho não foi perfeitamente linear porque o processamento possui frações seriais inevitáveis (I/O, redução dos resultados parciais, overhead do pool). A queda de eficiência observada de 62% para 52% é esperada e explicada pela Lei de Amdahl, e não representa falha de implementação.

O experimento comprova que o uso de múltiplos processos é eficiente para esse tipo de análise fiscal pesada, especialmente porque o trabalho por linha é independente e pode ser dividido entre processos sem necessidade de sincronização durante o período.
