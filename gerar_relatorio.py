"""
gerar_relatorio.py
Recebe os resultados do analisador (sequencial + paralelo) e
gera um relatório HTML autocontido com visual profissional.
Inclui botão de exportar PDF via window.print() + @media print.
"""

from datetime import datetime


def gerar_relatorio(
    resultado_seq:  dict,
    resultado_par:  dict,
    arquivo_saida:  str = "relatorio_nf.html",
) -> None:
    speedup    = round(resultado_seq["tempo_segundos"] / resultado_par["tempo_segundos"], 2)
    eficiencia = round((speedup / resultado_par["n_workers"]) * 100, 1)
    resultados_processos = resultado_par.get("resultados_processos", [resultado_par])

    produtos = resultado_par["stats_produto"]
    top_produtos = sorted(produtos.items(), key=lambda x: -x[1]["soma_valor"])[:80]

    estados = resultado_par["stats_estado"]
    top_estados = sorted(estados.items(), key=lambda x: -x[1])

    meses = resultado_par["stats_mes"]
    meses_labels = list(meses.keys())
    meses_valores = [round(v, 2) for v in meses.values()]

    max_fat_produto = max(s["soma_valor"] for _, s in top_produtos)
    max_fat_estado  = max(v for _, v in top_estados)
    max_fat_mes     = max(meses_valores) if meses_valores else 1

    def fmt_brl(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    def fmt_int(v): return f"{v:,}".replace(",", ".")

    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")

    linhas_produtos = ""
    for i, (nome, s) in enumerate(top_produtos):
        pct = (s["soma_valor"] / max_fat_produto) * 100
        linhas_produtos += f"""
        <tr class="{'alt' if i % 2 else ''}">
          <td class="nome">{nome}</td>
          <td class="num">{fmt_brl(s['soma_valor'])}</td>
          <td class="num">{fmt_int(s['quantidade_vendida'])}</td>
          <td class="num">{fmt_brl(s['preco_min'])}</td>
          <td class="num">{fmt_brl(s['preco_max'])}</td>
          <td class="bar-cell"><div class="bar" style="width:{pct:.1f}%"></div></td>
        </tr>"""

    linhas_estados = ""
    for estado, total in top_estados:
        pct = (total / max_fat_estado) * 100
        linhas_estados += f"""
        <tr>
          <td class="nome">{estado}</td>
          <td class="num">{fmt_brl(total)}</td>
          <td class="bar-cell"><div class="bar estado" style="width:{pct:.1f}%"></div></td>
        </tr>"""

    barras_mes = ""
    for label, valor in zip(meses_labels, meses_valores):
        pct = (valor / max_fat_mes) * 100 if max_fat_mes else 0
        mes_fmt = label[5:]
        barras_mes += f"""
          <div class="mes-col">
            <div class="mes-bar-wrap">
              <div class="mes-bar" style="height:{pct:.1f}%" title="{fmt_brl(valor)}"></div>
            </div>
            <span class="mes-label">{mes_fmt}</span>
          </div>"""

    linhas_processos = ""
    for r in resultados_processos:
        sp = round(resultado_seq["tempo_segundos"] / r["tempo_segundos"], 2)
        ef = round((sp / r["n_workers"]) * 100, 1)
        destaque = "alt" if r["n_workers"] == resultado_par["n_workers"] else ""
        linhas_processos += f"""
        <tr class="{destaque}">
          <td class="nome">{r['n_workers']}</td>
          <td class="num">{r['tempo_segundos']:.4f}s</td>
          <td class="num">{sp:.2f}x</td>
          <td class="num">{ef:.1f}%</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatório — Análise de Notas Fiscais Sintéticas</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,600;0,900;1,300&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:       #0f0e0c;
    --surface:  #1a1814;
    --border:   #2e2b26;
    --text:     #e8e0d0;
    --muted:    #7a7060;
    --accent:   #c84b31;
    --accent2:  #e8a87c;
    --green:    #6ab187;
    --mono:     'DM Mono', monospace;
    --serif:    'Fraunces', Georgia, serif;
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* ── BOTÃO PDF ── */
  .pdf-btn {{
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    z-index: 999;
    background: var(--accent);
    color: #fff;
    border: none;
    padding: .75rem 1.5rem;
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: .14em;
    text-transform: uppercase;
    cursor: pointer;
    border-radius: 2px;
    box-shadow: 0 4px 24px rgba(200,75,49,.35);
    transition: background .2s, transform .15s, box-shadow .2s;
    display: flex;
    align-items: center;
    gap: .5rem;
  }}
  .pdf-btn:hover {{
    background: #a83a22;
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(200,75,49,.5);
  }}
  .pdf-btn:active {{ transform: translateY(0); }}
  .pdf-btn svg {{ width: 14px; height: 14px; fill: currentColor; }}

  /* ── HEADER ── */
  header {{
    border-bottom: 1px solid var(--border);
    padding: 3rem 4rem 2.5rem;
    position: relative;
    overflow: hidden;
  }}
  header::before {{
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 320px; height: 320px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(200,75,49,.18) 0%, transparent 70%);
    pointer-events: none;
  }}
  .header-label {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: .75rem;
  }}
  header h1 {{
    font-family: var(--serif);
    font-weight: 900;
    font-size: clamp(2rem, 4vw, 3.2rem);
    line-height: 1.1;
    color: var(--text);
  }}
  header h1 em {{
    font-style: italic;
    font-weight: 300;
    color: var(--accent2);
  }}
  .header-meta {{
    margin-top: 1.25rem;
    color: var(--muted);
    font-size: 11px;
    letter-spacing: .06em;
  }}

  /* ── LAYOUT ── */
  main {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 3rem 4rem 5rem;
    display: flex;
    flex-direction: column;
    gap: 3rem;
  }}

  /* ── SECTION TITLE ── */
  .section-title {{
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: .2em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 1.25rem;
    padding-bottom: .5rem;
    border-bottom: 1px solid var(--border);
  }}

  /* ── KPI GRID ── */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
  }}
  .kpi {{
    background: var(--surface);
    padding: 1.5rem 1.75rem;
  }}
  .kpi-label {{
    font-size: 10px;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: .5rem;
  }}
  .kpi-value {{
    font-family: var(--serif);
    font-weight: 600;
    font-size: 1.7rem;
    color: var(--text);
    line-height: 1;
  }}
  .kpi-value.accent {{ color: var(--accent); }}
  .kpi-value.green  {{ color: var(--green); }}
  .kpi-sub {{
    font-size: 10px;
    color: var(--muted);
    margin-top: .35rem;
  }}

  /* ── PERFORMANCE BLOCK ── */
  .perf-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
  }}
  .perf-item {{
    background: var(--surface);
    padding: 1.5rem 1.75rem;
  }}
  .perf-item.highlight {{ background: #1f1a14; }}
  .perf-label {{
    font-size: 10px;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: .4rem;
  }}
  .perf-value {{
    font-family: var(--serif);
    font-weight: 900;
    font-size: 2.4rem;
    line-height: 1;
  }}
  .perf-value.seq {{ color: var(--muted); }}
  .perf-value.par {{ color: var(--accent2); }}
  .perf-value.spd {{ color: var(--accent); }}
  .perf-value.eff {{ color: var(--green); }}
  .speedup-note {{
    margin-top: .5rem;
    font-size: 11px;
    color: var(--muted);
  }}

  /* ── TABLES ── */
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  th {{
    font-size: 10px;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--muted);
    text-align: left;
    padding: .6rem .75rem;
    border-bottom: 1px solid var(--border);
    font-weight: 500;
  }}
  td {{
    padding: .55rem .75rem;
    border-bottom: 1px solid #1e1c18;
    vertical-align: middle;
  }}
  tr.alt td {{ background: #171510; }}
  td.nome {{ color: var(--text); }}
  td.num  {{
    font-family: var(--mono);
    text-align: right;
    color: var(--accent2);
  }}
  td.bar-cell {{ width: 160px; padding-right: 1rem; }}
  .bar {{
    height: 6px;
    background: var(--accent);
    border-radius: 2px;
  }}
  .bar.estado {{ background: var(--green); }}

  /* ── GRÁFICO MENSAL ── */
  .chart-mensal {{
    display: flex;
    align-items: flex-end;
    gap: 6px;
    height: 140px;
    padding: 1rem 0 0;
  }}
  .mes-col {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
  }}
  .mes-bar-wrap {{
    flex: 1;
    width: 100%;
    display: flex;
    align-items: flex-end;
  }}
  .mes-bar {{
    width: 100%;
    background: var(--accent);
    border-radius: 2px 2px 0 0;
    min-height: 3px;
    cursor: default;
  }}
  .mes-bar:hover {{ background: var(--accent2); }}
  .mes-label {{
    font-size: 9px;
    color: var(--muted);
    margin-top: 4px;
    letter-spacing: .05em;
  }}

  /* ── FOOTER ── */
  footer {{
    border-top: 1px solid var(--border);
    padding: 1.5rem 4rem;
    color: var(--muted);
    font-size: 10px;
    letter-spacing: .08em;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }}

  @media (max-width: 700px) {{
    header, main, footer {{ padding-left: 1.5rem; padding-right: 1.5rem; }}
    .perf-grid {{ grid-template-columns: 1fr; }}
  }}

  /* ────────────────────────────────────────────
     ESTILOS DE IMPRESSÃO / EXPORT PDF
     Ativados por window.print() ou Ctrl+P
  ──────────────────────────────────────────── */
  @media print {{
    /* Instrui o navegador a usar fundo escuro no PDF */
    * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}

    /* Esconde o botão flutuante */
    .pdf-btn {{ display: none !important; }}

    /* Remove margens de página do browser */
    @page {{
      size: A4;
      margin: 1.2cm 1.5cm;
    }}

    body {{ font-size: 11px; }}

    header {{ padding: 1.5rem 2rem 1.2rem; }}
    header h1 {{ font-size: 2rem; }}

    main {{ padding: 1.5rem 2rem 2rem; gap: 1.8rem; }}

    /* Evita quebra de página no meio de seções */
    section {{ break-inside: avoid; }}

    /* KPI menor para caber em A4 */
    .kpi-value {{ font-size: 1.3rem; }}
    .perf-value {{ font-size: 1.8rem; }}

    /* Gráfico mensal: altura fixa para impressão */
    .chart-mensal {{ height: 100px; }}

    /* Tabelas: cabeçalho repete em cada página */
    thead {{ display: table-header-group; }}
    tfoot {{ display: table-footer-group; }}

    /* Linha de tabela não quebra no meio */
    tr {{ break-inside: avoid; }}

    footer {{ padding: 1rem 2rem; }}
  }}
</style>
</head>
<body>

<!-- Botão fixo de exportar PDF -->
<button class="pdf-btn" onclick="exportarPDF()">
  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6zm2-5h8v1H8v-1zm0 2.5h5v1H8v-1zm0-5h8v1H8v-1z"/>
  </svg>
  Exportar PDF
</button>

<header>
  <p class="header-label">Análise · Programação Paralela e Distribuída</p>
  <h1>Notas Fiscais<br><em>Sintéticas</em></h1>
  <p class="header-meta">Gerado em {agora} &nbsp;·&nbsp; Base de {fmt_int(resultado_par['total_linhas'])} registros &nbsp;·&nbsp; melhor: {resultado_par['n_workers']} processos &nbsp;·&nbsp; modo {resultado_par.get('modo', 'padrao')}</p>
</header>

<main>

  <section>
    <p class="section-title">01 — Visão Geral da Base</p>
    <div class="kpi-grid">
      <div class="kpi">
        <p class="kpi-label">Total de Registros</p>
        <p class="kpi-value">{fmt_int(resultado_par['total_linhas'])}</p>
        <p class="kpi-sub">itens de notas fiscais</p>
      </div>
      <div class="kpi">
        <p class="kpi-label">Faturamento Total</p>
        <p class="kpi-value accent">{fmt_brl(resultado_par['soma_total'])}</p>
        <p class="kpi-sub">soma de todos os itens</p>
      </div>
      <div class="kpi">
        <p class="kpi-label">ICMS Estimado</p>
        <p class="kpi-value accent">{fmt_brl(resultado_par.get('soma_icms', 0))}</p>
        <p class="kpi-sub">calculo monetario com Decimal</p>
      </div>
      <div class="kpi">
        <p class="kpi-label">Risco Fiscal</p>
        <p class="kpi-value green">{fmt_int(resultado_par.get('notas_suspeitas', 0))}</p>
        <p class="kpi-sub">itens marcados pelo score</p>
      </div>
      <div class="kpi">
        <p class="kpi-label">Inconsistencias</p>
        <p class="kpi-value">{fmt_int(resultado_par.get('inconsistencias', 0))}</p>
        <p class="kpi-sub">validacao total x qtd x preco</p>
      </div>
      <div class="kpi">
        <p class="kpi-label">Maior Item</p>
        <p class="kpi-value">{fmt_brl(resultado_par['maior_item']['valor'])}</p>
        <p class="kpi-sub">{resultado_par['maior_item']['produto']}</p>
      </div>
      <div class="kpi">
        <p class="kpi-label">Menor Item</p>
        <p class="kpi-value">{fmt_brl(resultado_par['menor_item']['valor'])}</p>
        <p class="kpi-sub">{resultado_par['menor_item']['produto']}</p>
      </div>
      <div class="kpi">
        <p class="kpi-label">Produtos Distintos</p>
        <p class="kpi-value green">{len(produtos)}</p>
        <p class="kpi-sub">categorias monitoradas</p>
      </div>
      <div class="kpi">
        <p class="kpi-label">Estados</p>
        <p class="kpi-value green">{len(estados)}</p>
        <p class="kpi-sub">unidades federativas</p>
      </div>
    </div>
  </section>

  <section>
    <p class="section-title">02 — Desempenho: Serial vs Paralelo</p>
    <div class="perf-grid">
      <div class="perf-item">
        <p class="perf-label">Tempo Sequencial</p>
        <p class="perf-value seq">{resultado_seq['tempo_segundos']}s</p>
        <p class="speedup-note">1 processo · baseline</p>
      </div>
      <div class="perf-item">
        <p class="perf-label">Tempo Paralelo</p>
        <p class="perf-value par">{resultado_par['tempo_segundos']}s</p>
        <p class="speedup-note">{resultado_par['n_workers']} processos · multiprocessing</p>
      </div>
      <div class="perf-item highlight">
        <p class="perf-label">Speedup</p>
        <p class="perf-value spd">{speedup}×</p>
        <p class="speedup-note">T_serial / T_paralelo</p>
      </div>
      <div class="perf-item highlight">
        <p class="perf-label">Eficiência</p>
        <p class="perf-value eff">{eficiencia}%</p>
        <p class="speedup-note">speedup / processos × 100</p>
      </div>
    </div>
  </section>

  <section>
    <p class="section-title">03 — Escala por Quantidade de Processos</p>
    <table>
      <thead>
        <tr>
          <th>Processos</th>
          <th style="text-align:right">Tempo</th>
          <th style="text-align:right">Speedup</th>
          <th style="text-align:right">Eficiência</th>
        </tr>
      </thead>
      <tbody>{linhas_processos}</tbody>
    </table>
  </section>

  <section>
    <p class="section-title">04 — Ranking de Produtos por Faturamento</p>
    <table>
      <thead>
        <tr>
          <th>Produto</th>
          <th style="text-align:right">Faturamento</th>
          <th style="text-align:right">Qtd Vendida</th>
          <th style="text-align:right">Preço Mín</th>
          <th style="text-align:right">Preço Máx</th>
          <th></th>
        </tr>
      </thead>
      <tbody>{linhas_produtos}</tbody>
    </table>
  </section>

  <section>
    <p class="section-title">05 — Faturamento por Estado</p>
    <table>
      <thead>
        <tr>
          <th>Estado</th>
          <th style="text-align:right">Faturamento Total</th>
          <th></th>
        </tr>
      </thead>
      <tbody>{linhas_estados}</tbody>
    </table>
  </section>

  <section>
    <p class="section-title">06 — Faturamento Mensal</p>
    <div class="chart-mensal">
      {barras_mes}
    </div>
  </section>

</main>

<footer>
  <span>Análise de Notas Fiscais Sintéticas · Programação Paralela e Distribuída</span>
  <span>{agora}</span>
</footer>

<script>
  function exportarPDF() {{
    // Dica: no diálogo de impressão, selecione "Salvar como PDF"
    // e marque "Gráficos de plano de fundo" para preservar as cores escuras
    window.print();
  }}
</script>

</body>
</html>"""

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[ok] Relatorio gerado: '{arquivo_saida}'")
    print(f"  Abra no navegador e clique em 'Exportar PDF' para salvar.\n")


if __name__ == "__main__":
    print("Execute main.py para gerar o relatório completo.")
