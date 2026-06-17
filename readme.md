# Benchmark de Paralelismo com Multiprocessing em Python

**Disciplina:** Programação Concorrente e Distribuída  
**Turma:** ADSN04  
**Professor:** Rafael  
**Aluno 1:** Lucas Vasconcelos Pessoa de Oliveira  
**Aluno 2:** Joao Gabriel Lucas Pinheiro de Lima  

**Data:** 17/06/2026  

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

A queda de eficiência de 89,5% (2 processos) para 57,3% (12 processos) tem uma causa concreta e mensurável, identificada a partir de uma rodada de testes adicional com 6, 7, 8, 9, 10, 11 e 12 processos.

### Correção em relação a uma hipótese anterior

Uma primeira leitura levantou a hipótese de que o gargalo seria a fronteira entre núcleos físicos e lógicos: como a máquina possui 8 núcleos físicos e 16 threads lógicas (SMT/hyper-threading), seria esperado um "degrau" de queda de desempenho exatamente entre 8 e 9 processos, quando processos adicionais passariam a disputar o mesmo núcleo físico via SMT.

Os dados da bateria 6→12 não confirmam essa hipótese. O ganho marginal de tempo por processo adicional é decrescente de forma suave e contínua, sem nenhum salto abrupto na fronteira de 8 núcleos:

| Transição | Tempo ganho |
|:---------:|:-----------:|
| 6 → 7     | -4,99s      |
| 7 → 8     | -2,91s      |
| 8 → 9     | -1,69s      |
| 9 → 10    | -0,12s      |
| 10 → 11   | -1,37s      |
| 11 → 12   | -1,03s      |

Se o limite fosse a saturação de SMT, esperar-se-ia uma queda brusca exatamente em 8→9, e não é isso que aparece — a curva já está desacelerando desde o 6. A única anomalia é 9→10 (ganho quase nulo), mais provável de ser ruído de medição (execução única, sem repetição, sujeita a variação do agendador do Windows) do que um efeito de arquitetura.

### Também há um erro de medição na explicação anterior

A versão anterior deste relatório apontava a etapa de **redução dos resultados parciais** (`reduzir()`) como uma das causas da perda de eficiência. Isso está tecnicamente incorreto: no código, o cronômetro é parado antes dessa etapa rodar.

```python
inicio = time.perf_counter()
with mp.Pool(processes=n_workers) as pool:
    parciais = pool.map(processar_chunk, chunks)
tempo = time.perf_counter() - inicio          # <- cronômetro para AQUI
resultado = reduzir(parciais, tempo, modo)    # <- reduce roda DEPOIS, fora do timer
```

Como `reduzir()` executa depois que `tempo` já foi capturado, o custo dessa etapa não influencia nenhum dos valores reportados na Seção 7. A causa real precisa estar dentro da janela que o `with mp.Pool(...)` efetivamente mede: a criação dos processos e o `pool.map()`.

### O que os dados sugerem como causa real

Ajustando os 7 pontos da bateria 6–12 contra dois modelos:

- **Amdahl puro** — `T(p) = a + b/p` → R² = 0,961
- **Amdahl + overhead linear por processo** — `T(p) = a + b/p + c·p` → R² = 0,986

O segundo modelo explica os dados visivelmente melhor, sem precisar de nenhum limite físico de núcleo. O termo `c` (custo que cresce linearmente com o número de processos) ficou em torno de **1,5s por processo adicional**, o que é mais compatível com:

- **Spawn de processos no Windows.** Diferente de Linux/Mac (que usam `fork`), o `multiprocessing` no Windows usa `spawn`: cada processo novo reabre um interpretador Python do zero e reimporta os módulos. Esse custo existe por processo e cresce com `n_workers`.
- **IPC de retorno via `pickle`.** Cada worker serializa um dicionário com agregações por produto, estado, cidade, CNPJ, categoria e mês — várias dessas chaves carregando valores `Decimal`, que é mais caro de empacotar/desempacotar do que tipos nativos como `int` ou `float`. Com mais processos, esse custo total de serialização cresce.

Ou seja: a explicação mais defensável não é "acabaram os núcleos físicos", e sim que **cada processo adicional carrega um custo fixo de inicialização e comunicação que nunca é totalmente amortizado pelo trabalho que ele executa** — e esse custo passa a pesar proporcionalmente mais conforme `n_workers` cresce, mesmo com mais CPU disponível.

### Validação ainda pendente

A regressão acima é evidência indireta. Para confirmar com medição direta, a próxima etapa é instrumentar `analisar_paralelo()` separando os três tempos dentro da janela medida:

```python
t0 = time.perf_counter()
pool = mp.Pool(processes=n_workers)
t_spawn = time.perf_counter() - t0
parciais = pool.map(processar_chunk, chunks)
t_map = time.perf_counter() - t0 - t_spawn
pool.close(); pool.join()
t_join = time.perf_counter() - t0 - t_spawn - t_map
```

Rodar isso em `p=6` e `p=12` e comparar `t_spawn` mostra diretamente se o overhead de inicialização cresce na ordem de grandeza esperada (~1,5s/processo). Recomenda-se também repetir cada configuração 3 vezes (mediana, não execução única) e comparar com `--modo rapido` (sem `Decimal`/`datetime.strptime`) na mesma faixa 6–12: se a curva de overhead se mantiver parecida mesmo sem a carga aritmética pesada, isso isola definitivamente a causa como custo de infraestrutura de processo (spawn/IPC), e não da computação em si.

Independente da causa exata do overhead, eficiência baixa não significa que usar mais processos foi uma má escolha: o objetivo do experimento é minimizar o tempo de execução, e com 12 processos e 57,3% de eficiência o tempo foi de 34,6s — o menor entre todas as configurações testadas.

---

## 10. Análise dos Resultados

Os resultados mostram ganho consistente conforme o número de processos aumenta. Com 4 processos, o tempo caiu de 237,8s para 69,0s — redução de aproximadamente 71%. Com 8 processos chegou a 38,5s, e com 12 processos ao melhor resultado de 34,6s.

A eficiência cai de forma suave e contínua, não em degraus: de 86,2% (4 processos) para 77,1% (8 processos) e 57,3% (12 processos). Uma bateria adicional de testes com 6 a 12 processos (ver Seção 9) mostrou que essa queda não tem relação com a fronteira entre núcleos físicos e lógicos da máquina — o ajuste estatístico que melhor descreve os dados (R² = 0,986) é um modelo de Amdahl com overhead linear por processo, compatível com o custo de `spawn` de processos no Windows e com a serialização (`pickle`) dos resultados parciais via IPC. Isso explica por que o ganho de tempo entre 8 e 12 processos é pequeno (apenas ~4s): cada processo adicional carrega um custo fixo de inicialização e comunicação que nunca é totalmente amortizado pelo trabalho extra que ele executa.

**Principais fatores limitantes:**

- Custo de `spawn` de processos no Windows (reabertura completa do interpretador por worker, sem `fork`)
- Custo de serialização com `pickle` dos dicionários de resultado parcial (agravado pelo uso de `Decimal`)
- Leitura de um CSV de ~1,9 GB em disco (contenção de I/O)
- Parsing de texto e conversões `Decimal` por linha (CPU-bound pesado)

---

## 11. Conclusão

O paralelismo com `multiprocessing` trouxe melhora expressiva no processamento das 16 milhões de notas fiscais. O tempo caiu de **237,7843s** no sequencial para **34,5666s** com 12 processos — redução de aproximadamente **85,5% no tempo total**.

O ganho não foi perfeitamente linear, mas a causa não é uma fração serial genérica do tipo previsto pela Lei de Amdahl pura: os dados da bateria 6–12 processos mostram uma queda suave e contínua de eficiência, melhor explicada por um overhead que cresce de forma aproximadamente linear com o número de processos (~1,5s por processo adicional, ajuste com R² = 0,986). Isso é mais coerente com custo de `spawn` no Windows e IPC/`pickle` de retorno do que com saturação de núcleos físicos ou com a etapa de redução dos resultados parciais — esta última, aliás, roda fora da janela cronometrada pelo código, então não pode ser apontada como causa da perda de eficiência observada. Vale notar que o ganho de tempo entre 8 e 12 processos foi modesto (de 38,5264s para 34,5666s), o que sugere que, para essa carga de trabalho e esse hardware, o overhead por processo já se aproxima de consumir os ganhos de paralelização adicionais.

O experimento comprova que o uso de múltiplos processos é eficiente para esse tipo de análise fiscal pesada, especialmente porque o trabalho por linha é independente e pode ser dividido entre processos sem necessidade de sincronização durante o período. Como próximo passo, a instrumentação direta de `spawn`, `map` e `join` (detalhada na Seção 9) permitiria confirmar com medição — em vez de regressão — qual parcela exata do tempo é consumida pela inicialização dos processos.
