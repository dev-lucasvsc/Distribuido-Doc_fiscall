# Benchmark de Paralelismo com Multiprocessing em Python

**Disciplina:** Programação Concorrente e Distribuída  
**Turma:** ADSN04  
**Professor:** Rafael  
**Aluno 1:** Lucas Vasconcelos Pessoa de Oliveira  
**Aluno 2:** Joao Gabriel Lucas Pinheiro de Lima  

**Data:** 23/06/2026  

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
| Sequencial   | 237,7843              |
| 2            | 133,1444              |
| 4            | 68,9927               |
| 8            | 38,5264               |
| 12           | 34,5666               |

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
| Seq.      | 237,7843  | 1,00×   | —          |
| 2         | 133,1444  | 1,79×   | 89,5%      |
| 4         | 68,9927   | 3,45×   | 86,2%      |
| 8         | 38,5264   | 6,17×   | 77,1%      |
| 12        | 34,5666   | 6,88×   | 57,3%      |

> **Melhor resultado: 12 processos — 34,5666s — speedup de 6,88×**

---

## 8. Gráficos

<p align="center">
  <img src="tempo.execucao.svg" alt="Gráfico de tempo de execução" width="32%">
  <img src="speedup.svg" alt="Gráfico de speedup" width="32%">
  <img src="eficiencia.svg" alt="Gráfico de eficiência" width="32%">
</p>

---

## 9. Por que a Eficiência Cai com Mais Processos?

A queda de eficiência de 89,5% (2 processos) para 57,3% (12 processos) é, em essência, o comportamento previsto pela **Lei de Amdahl**: toda tarefa paralela tem uma fração que não escala com o número de processos, e essa fração pesa proporcionalmente mais conforme mais processos são adicionados. A pergunta interessante não é "isso é esperado?" — é, mas sim **qual fração específica do trabalho é essa, no caso deste programa.** Para responder isso com mais precisão, foi feita uma bateria extra de testes com 6, 7, 8, 9, 10, 11 e 12 processos, em vez de testar apenas os quatro pontos da tabela principal.

### Refinando a hipótese: núcleo físico vs. núcleo lógico

A primeira hipótese testada foi a fronteira de hardware: a máquina tem 8 núcleos físicos e 16 threads lógicas via SMT (hyper-threading). A expectativa era ver um "degrau" de queda de desempenho bem marcado entre 8 e 9 processos, quando processos adicionais passam a compartilhar núcleo físico via SMT.

Os dados da bateria 6→12 mostram outra coisa: o ganho marginal de tempo por processo adicional já vem caindo de forma suave desde o 6, sem nenhum salto abrupto justo na passagem de 8 para 9 processos.

| Transição | Tempo ganho |
|:---------:|:-----------:|
| 6 → 7     | -4,99s      |
| 7 → 8     | -2,91s      |
| 8 → 9     | -1,69s      |
| 9 → 10    | -0,12s      |
| 10 → 11   | -1,37s      |
| 11 → 12   | -1,03s      |

Essa queda contínua, sem degrau, descarta a hipótese de saturação física como causa principal e aponta para um segundo tipo de custo: o **overhead de paralelização** — o tempo gasto não no trabalho útil (ler e validar cada linha do CSV), mas na organização desse trabalho entre processos.

### O que é o overhead de paralelização, neste caso

Diferente do tempo computacional "puro" de processar cada uma das 16 milhões de linhas, o overhead é o custo que cada processo adicional traz consigo apenas por existir, antes de processar uma única linha. Esse custo tem três origens concretas e mensuráveis no programa:

- **Custo de criação (`spawn`)**: no Windows, `multiprocessing` usa o método `spawn` em vez de `fork` (disponível apenas em sistemas Unix). Isso significa que cada worker novo reabre o interpretador Python do zero, reimportando módulos e reconstruindo seu estado interno — um custo fixo por processo que não existe em sistemas que usam `fork`.
- **Custo de comunicação (`pickle` + IPC)**: ao final do processamento, cada worker precisa devolver seu dicionário de resultados parciais (somas, rankings, estatísticas por produto/estado/cidade/CNPJ) ao processo principal. Essa transferência exige serialização via `pickle`, que é mais lenta quando os valores envolvidos são `Decimal` em vez de tipos numéricos nativos como `float`.
- **Custo de sincronização (`join`)**: o `pool.map()` só libera o resultado final depois que o último worker termina — o tempo total da etapa paralela é, portanto, limitado pelo processo mais lento da rodada, e não pela média.

Esses três custos por processo são aproximadamente constantes (não dependem de quantas linhas aquele processo processou), enquanto o trabalho útil por processo diminui conforme mais processos dividem o mesmo arquivo. É exatamente essa proporção que se inverte conforme p cresce: com poucos processos, o overhead é irrelevante frente ao trabalho útil; com muitos processos, ele passa a representar uma fração cada vez maior do tempo total — daí a queda suave e contínua de eficiência observada nos dados, em vez de um degrau abrupto ligado a hardware.

## 10. Análise dos Resultados

Os resultados mostram ganho consistente conforme o número de processos aumenta. Com 4 processos, o tempo caiu de 237,8s para 69,0s — redução de aproximadamente 71%. Com 8 processos chegou a 38,5s, e com 12 processos ao melhor resultado de 34,6s.

A eficiência cai de forma suave e contínua, sem degraus abruptos: de 86,2% (4 processos) para 77,1% (8 processos) e 57,3% (12 processos). A bateria adicional de testes com 6 a 12 processos (Seção 9) ajuda a refinar essa leitura: o ajuste estatístico que melhor descreve os dados (R² = 0,986) é um modelo de Amdahl com termo de overhead por processo, ou seja, um modelo do tipo:

```
T(p) = T_serial + T_paralelizavel / p + overhead × p
```

onde o termo `overhead × p` cresce linearmente com o número de processos e absorve, de forma agregada, os três custos descritos na Seção 9 (`spawn`, `pickle`/IPC e sincronização via `join`). O ajuste estatístico estima esse overhead em aproximadamente **1,5 segundo por processo adicional**. Esse modelo é o que melhor explica por que o ganho de tempo entre 8 e 12 processos é tão pequeno (apenas ~4s): cada processo adicional carrega um custo de inicialização e comunicação que nunca é totalmente amortizado pelo trabalho extra que ele executa — a partir de certo ponto, adicionar processos retorna cada vez menos trabalho útil por segundo de overhead pago.

Essa leitura também explica por que a hipótese de saturação de núcleos físicos (Seção 9) foi descartada: se o limitador fosse hardware, esperaríamos um salto concentrado na fronteira de 8→9 processos; o que se observa, em vez disso, é uma penalidade que se acumula de forma proporcional ao número de processos, independentemente de estarem ou não competindo por núcleo físico via SMT.

**Principais fatores limitantes (em ordem de impacto estimado):**

- **Custo de `spawn` de processos no Windows** — reabertura completa do interpretador por worker, sem `fork`; este é o componente mais provável de dominar o termo de overhead, por ser pago integralmente antes de qualquer linha ser processada
- **Custo de serialização com `pickle`** dos dicionários de resultado parcial — agravado pelo uso de `Decimal`, que serializa mais lentamente que tipos numéricos nativos
- **Leitura de um CSV de ~1,9 GB em disco** (contenção de I/O) — fator que não escala com o número de processos e estabelece um piso de tempo que nenhuma quantidade de paralelismo elimina
- **Parsing de texto e conversões `Decimal` por linha** (CPU-bound pesado) — parte do trabalho útil em si, mas que compete pela mesma CPU usada pelos custos de overhead acima

---

## 11. Conclusão

O paralelismo com `multiprocessing` trouxe melhora expressiva no processamento das 16 milhões de notas fiscais. O tempo caiu de **237,7843s** no sequencial para **34,5666s** com 12 processos — redução de aproximadamente **85,5% no tempo total**.

O ganho não foi perfeitamente linear, o que é esperado pela Lei de Amdahl: todo processamento paralelo tem uma fração que não escala com o número de processos. A bateria extra de testes (6 a 12 processos, Seção 9) ajudou a identificar com mais precisão qual fração é essa neste caso — não a saturação abrupta de núcleos físicos, e sim um overhead que cresce de forma aproximadamente linear por processo adicional (~1,5s, ajuste com R² = 0,986), coerente com o custo de `spawn` no Windows e a serialização (`pickle`) do retorno de cada worker. Vale notar que o ganho de tempo entre 8 e 12 processos foi modesto (de 38,5264s para 34,5666s), o que sugere que, para essa carga de trabalho e esse hardware, o overhead por processo já se aproxima de consumir os ganhos adicionais de paralelização.

O experimento comprova que o uso de múltiplos processos é eficiente para esse tipo de análise fiscal pesada, especialmente porque o trabalho por linha é independente e pode ser dividido entre processos sem necessidade de sincronização durante o período. Como próximo passo, a instrumentação direta de `spawn`, `map` e `join` (detalhada na Seção 9) permitiria confirmar com medição direta — em vez de regressão estatística — qual parcela exata do tempo é consumida pela inicialização dos processos.
