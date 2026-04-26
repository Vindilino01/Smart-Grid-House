import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────
# PASSO 1: UNIVERSOS DE DISCURSO
# ──────────────────────────────────────────────
geracao_solar = ctrl.Antecedent(np.arange(0, 101, 1), 'geracao_solar')
demanda_casa  = ctrl.Antecedent(np.arange(0, 101, 1), 'demanda_casa')
acao_bateria  = ctrl.Consequent(np.arange(-100, 101, 1), 'acao_bateria')

# ──────────────────────────────────────────────
# PASSO 2: FUNÇÕES DE PERTINÊNCIA
# ──────────────────────────────────────────────
geracao_solar['baixa'] = fuzz.trimf(geracao_solar.universe, [0,   0,  50])
geracao_solar['media'] = fuzz.trimf(geracao_solar.universe, [0,  50, 100])
geracao_solar['alta']  = fuzz.trimf(geracao_solar.universe, [50, 100, 100])

demanda_casa['baixa'] = fuzz.trimf(demanda_casa.universe, [0,   0,  50])
demanda_casa['media'] = fuzz.trimf(demanda_casa.universe, [0,  50, 100])
demanda_casa['alta']  = fuzz.trimf(demanda_casa.universe, [50, 100, 100])

acao_bateria['descarregar'] = fuzz.trimf(acao_bateria.universe, [-100, -100,  0])
acao_bateria['manter']      = fuzz.trimf(acao_bateria.universe, [ -50,    0, 50])
acao_bateria['carregar']    = fuzz.trimf(acao_bateria.universe, [   0,  100, 100])

# ──────────────────────────────────────────────
# PASSO 3: BASE DE REGRAS
# ──────────────────────────────────────────────
regras = [
    ctrl.Rule(geracao_solar['alta']  & demanda_casa['baixa'], acao_bateria['carregar']),
    ctrl.Rule(geracao_solar['alta']  & demanda_casa['media'], acao_bateria['carregar']),
    ctrl.Rule(geracao_solar['alta']  & demanda_casa['alta'],  acao_bateria['manter']),
    ctrl.Rule(geracao_solar['media'] & demanda_casa['baixa'], acao_bateria['carregar']),
    ctrl.Rule(geracao_solar['media'] & demanda_casa['media'], acao_bateria['manter']),
    ctrl.Rule(geracao_solar['media'] & demanda_casa['alta'],  acao_bateria['descarregar']),
    ctrl.Rule(geracao_solar['baixa'] & demanda_casa['baixa'], acao_bateria['manter']),
    ctrl.Rule(geracao_solar['baixa'] & demanda_casa['media'], acao_bateria['descarregar']),
    ctrl.Rule(geracao_solar['baixa'] & demanda_casa['alta'],  acao_bateria['descarregar']),
]

sistema_fuzzy = ctrl.ControlSystem(regras)
simulador     = ctrl.ControlSystemSimulation(sistema_fuzzy)

# ──────────────────────────────────────────────
# PASSO 4: SIMULAÇÃO DE MALHA FECHADA (24h)
#   SoC acumula a ação da IA a cada hora
# ──────────────────────────────────────────────
horas    = list(range(24))
sol_dia  = [0, 0, 0, 0, 0, 5, 25, 50, 75, 90, 100, 95, 85, 70, 50, 30, 10, 2, 0, 0, 0, 0, 0, 0]
casa_dia = [10,10,10,10,15,40, 80, 50, 30, 20,  20, 30, 40, 30, 40, 60, 90,100,85,60,40,20,10,10]

SOC_INICIAL    = 50.0   # bateria começa em 50%
SOC_MIN, SOC_MAX = 0.0, 100.0
TAXA_CONVERSAO  = 0.3   # quanto cada unidade de ação muda o SoC por hora

respostas_ia = []
soc_historico = [SOC_INICIAL]
soc_atual = SOC_INICIAL

for h in range(24):
    simulador.input['geracao_solar'] = sol_dia[h]
    simulador.input['demanda_casa']  = casa_dia[h]
    simulador.compute()
    acao = simulador.output['acao_bateria']
    respostas_ia.append(acao)

    # Malha fechada: acumula o SoC
    novo_soc = soc_atual + acao * TAXA_CONVERSAO
    novo_soc  = max(SOC_MIN, min(SOC_MAX, novo_soc))
    soc_atual = novo_soc
    soc_historico.append(soc_atual)

soc_plot = soc_historico[:24]  # um ponto por hora

# ──────────────────────────────────────────────
# PASSO 5: SUPERFÍCIE DE CONTROLE 3D
# ──────────────────────────────────────────────
res = 25
eixo_sol     = np.linspace(0, 100, res)
eixo_demanda = np.linspace(0, 100, res)
Z = np.zeros((res, res))

for i, s in enumerate(eixo_sol):
    for j, d in enumerate(eixo_demanda):
        simulador.input['geracao_solar'] = float(s)
        simulador.input['demanda_casa']  = float(d)
        try:
            simulador.compute()
            Z[i, j] = simulador.output['acao_bateria']
        except Exception:
            Z[i, j] = 0.0

# ──────────────────────────────────────────────
# CORES E ESTILO
# ──────────────────────────────────────────────
COR_SOL      = '#F59E0B'  # âmbar
COR_CASA     = '#3B82F6'  # azul
COR_IA       = '#10B981'  # verde esmeralda
COR_SOC      = '#8B5CF6'  # violeta
COR_SOC_AREA = 'rgba(139,92,246,0.15)'
FUNDO        = '#0F172A'
FUNDO_PLOT   = '#1E293B'
GRADE        = 'rgba(148,163,184,0.12)'
TEXTO        = '#CBD5E1'
TITULO_COR   = '#F1F5F9'

LAYOUT_BASE = dict(
    paper_bgcolor=FUNDO,
    plot_bgcolor=FUNDO_PLOT,
    font=dict(family='Inter, system-ui, sans-serif', color=TEXTO, size=11),
)

# ──────────────────────────────────────────────
# FIGURA 1 — SIMULAÇÃO 24H
# ──────────────────────────────────────────────
fig1 = go.Figure()

# Área solar preenchida
fig1.add_trace(go.Scatter(
    x=horas, y=sol_dia,
    name='Geração Solar (%)',
    mode='lines',
    line=dict(color=COR_SOL, width=2.5),
    fill='tozeroy',
    fillcolor='rgba(245,158,11,0.12)',
    hovertemplate='%{x}h — Solar: <b>%{y}%</b><extra></extra>',
))

# Demanda da casa
fig1.add_trace(go.Scatter(
    x=horas, y=casa_dia,
    name='Demanda Residencial (%)',
    mode='lines',
    line=dict(color=COR_CASA, width=2.5),
    fill='tozeroy',
    fillcolor='rgba(59,130,246,0.10)',
    hovertemplate='%{x}h — Demanda: <b>%{y}%</b><extra></extra>',
))

# Ação da IA (linha tracejada com marcadores)
fig1.add_trace(go.Scatter(
    x=horas, y=respostas_ia,
    name='Ação IA na Bateria (%)',
    mode='lines+markers',
    line=dict(color=COR_IA, width=3, dash='dash'),
    marker=dict(size=7, symbol='diamond', color=COR_IA,
                line=dict(width=1.5, color=FUNDO)),
    hovertemplate='%{x}h — Ação: <b>%{y:.1f}%</b><extra></extra>',
))

# Linha zero de referência
fig1.add_hline(y=0, line=dict(color='rgba(148,163,184,0.3)', width=1, dash='dot'))

fig1.update_layout(
    **LAYOUT_BASE,
    title=dict(
        text='<b>Simulação de 24 Horas</b> — Gestão Fuzzy do Smart Grid',
        font=dict(size=16, color=TITULO_COR), x=0.02
    ),
    xaxis=dict(
        title='Hora do Dia', tickvals=list(range(0, 24, 2)),
        ticktext=[f'{h}h' for h in range(0, 24, 2)],
        gridcolor=GRADE, linecolor=GRADE,
    ),
    yaxis=dict(
        title='Intensidade (%)', range=[-105, 110],
        gridcolor=GRADE, linecolor=GRADE, zeroline=False,
    ),
    legend=dict(
        orientation='h', y=1.12, x=0,
        bgcolor='rgba(0,0,0,0)', font=dict(size=11)
    ),
    hovermode='x unified',
    height=420,
    margin=dict(t=80, l=60, r=30, b=50),
)

# ──────────────────────────────────────────────
# FIGURA 2 — SoC ACUMULADO (MALHA FECHADA)
# ──────────────────────────────────────────────
fig2 = go.Figure()

# Zona de operação ideal (30–80%)
fig2.add_hrect(y0=30, y1=80,
    fillcolor='rgba(16,185,129,0.07)',
    line_width=0,
    annotation_text='Zona ótima de operação (30–80%)',
    annotation_position='top left',
    annotation_font=dict(size=10, color='rgba(16,185,129,0.7)')
)

# Linhas de limite
fig2.add_hline(y=80, line=dict(color='rgba(245,158,11,0.5)', width=1, dash='dot'))
fig2.add_hline(y=30, line=dict(color='rgba(239,68,68,0.5)',  width=1, dash='dot'))
fig2.add_hline(y=100, line=dict(color='rgba(239,68,68,0.3)', width=1, dash='longdash'))
fig2.add_hline(y=0,   line=dict(color='rgba(239,68,68,0.3)', width=1, dash='longdash'))

# Área do SoC preenchida
fig2.add_trace(go.Scatter(
    x=horas, y=soc_plot,
    name='SoC da Bateria (%)',
    mode='lines+markers',
    line=dict(color=COR_SOC, width=3),
    fill='tozeroy',
    fillcolor=COR_SOC_AREA,
    marker=dict(size=8, color=COR_SOC, line=dict(width=2, color=FUNDO)),
    hovertemplate='%{x}h — SoC: <b>%{y:.1f}%</b><extra></extra>',
))

# Annotations nos pontos extremos
soc_max_h = int(np.argmax(soc_plot))
soc_min_h = int(np.argmin(soc_plot))

for h_pt, label, ay in [
    (soc_max_h, f'Máx: {soc_plot[soc_max_h]:.1f}%', -30),
    (soc_min_h, f'Mín: {soc_plot[soc_min_h]:.1f}%',  30),
]:
    fig2.add_annotation(
        x=h_pt, y=soc_plot[h_pt],
        text=label, showarrow=True, arrowhead=2, arrowsize=1,
        arrowcolor=COR_SOC, ay=ay, ax=0,
        font=dict(size=11, color=COR_SOC),
        bgcolor=FUNDO_PLOT, borderpad=4,
    )

fig2.update_layout(
    **LAYOUT_BASE,
    title=dict(
        text='<b>State of Charge (SoC)</b> — Malha Fechada em Tempo Real',
        font=dict(size=16, color=TITULO_COR), x=0.02
    ),
    xaxis=dict(
        title='Hora do Dia', tickvals=list(range(0, 24, 2)),
        ticktext=[f'{h}h' for h in range(0, 24, 2)],
        gridcolor=GRADE, linecolor=GRADE,
    ),
    yaxis=dict(
        title='Nível da Bateria (%)', range=[-5, 110],
        gridcolor=GRADE, linecolor=GRADE, zeroline=False,
    ),
    showlegend=False,
    hovermode='x unified',
    height=420,
    margin=dict(t=80, l=60, r=30, b=50),
)

# ──────────────────────────────────────────────
# FIGURA 3 — SUPERFÍCIE DE CONTROLE 3D
# ──────────────────────────────────────────────
fig3 = go.Figure()

fig3.add_trace(go.Surface(
    x=eixo_demanda,
    y=eixo_sol,
    z=Z,
    colorscale=[
        [0.0,  '#1D4ED8'],   # descarregar forte — azul escuro
        [0.25, '#3B82F6'],   # descarregar leve  — azul
        [0.5,  '#1E293B'],   # manter            — neutro escuro
        [0.75, '#10B981'],   # carregar leve      — verde
        [1.0,  '#F59E0B'],   # carregar forte     — âmbar
    ],
    colorbar=dict(
        title=dict(text='Ação (%)', font=dict(color=TEXTO)),
        tickfont=dict(color=TEXTO),
        thickness=14,
        len=0.7,
    ),
    opacity=0.92,
    hovertemplate=(
        'Demanda: <b>%{x:.0f}%</b><br>'
        'Solar: <b>%{y:.0f}%</b><br>'
        'Ação IA: <b>%{z:.1f}%</b>'
        '<extra></extra>'
    ),
    lighting=dict(ambient=0.7, diffuse=0.6, roughness=0.4, specular=0.3),
    lightposition=dict(x=2, y=2, z=5),
))

fig3.update_layout(
    **LAYOUT_BASE,
    title=dict(
        text='<b>Superfície de Controle Fuzzy 3D</b> — Mapa de Decisão Completo',
        font=dict(size=16, color=TITULO_COR), x=0.02
    ),
    scene=dict(
        xaxis=dict(
            title='Demanda (%)', gridcolor=GRADE,
            backgroundcolor=FUNDO_PLOT, color=TEXTO,
        ),
        yaxis=dict(
            title='Geração Solar (%)', gridcolor=GRADE,
            backgroundcolor=FUNDO_PLOT, color=TEXTO,
        ),
        zaxis=dict(
            title='Ação na Bateria (%)', gridcolor=GRADE,
            backgroundcolor=FUNDO_PLOT, color=TEXTO,
        ),
        camera=dict(eye=dict(x=1.6, y=-1.6, z=1.1)),
        bgcolor=FUNDO_PLOT,
    ),
    height=560,
    margin=dict(t=80, l=10, r=10, b=10),
)

# ──────────────────────────────────────────────
# EXPORTAR COMO HTML ÚNICO
# ──────────────────────────────────────────────
html_24h      = fig1.to_html(full_html=False, include_plotlyjs='cdn')
html_soc      = fig2.to_html(full_html=False, include_plotlyjs=False)
html_surface  = fig3.to_html(full_html=False, include_plotlyjs=False)

html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart Grid — Gestão Fuzzy de Energia</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0F172A;
    font-family: 'Inter', system-ui, sans-serif;
    color: #CBD5E1;
    padding: 32px 24px;
  }}
  header {{
    text-align: center;
    margin-bottom: 40px;
  }}
  header h1 {{
    font-size: 26px;
    font-weight: 700;
    color: #F1F5F9;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
  }}
  header p {{
    font-size: 14px;
    color: #64748B;
  }}
  .badge-row {{
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-top: 14px;
    flex-wrap: wrap;
  }}
  .badge {{
    font-size: 11px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.04em;
  }}
  .b-amber  {{ background: rgba(245,158,11,0.15); color: #F59E0B; }}
  .b-blue   {{ background: rgba(59,130,246,0.15);  color: #60A5FA; }}
  .b-green  {{ background: rgba(16,185,129,0.15);  color: #34D399; }}
  .b-violet {{ background: rgba(139,92,246,0.15);  color: #A78BFA; }}
  .section {{
    max-width: 1100px;
    margin: 0 auto 40px;
  }}
  .section-label {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #475569;
    margin-bottom: 12px;
    padding-left: 4px;
    border-left: 3px solid #334155;
    padding-left: 10px;
  }}
  .card {{
    background: #1E293B;
    border: 1px solid rgba(148,163,184,0.1);
    border-radius: 14px;
    padding: 8px;
    overflow: hidden;
  }}
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    max-width: 1100px;
    margin: 0 auto 40px;
  }}
  .stat {{
    background: #1E293B;
    border: 1px solid rgba(148,163,184,0.1);
    border-radius: 10px;
    padding: 16px 20px;
  }}
  .stat-label {{ font-size: 11px; color: #64748B; margin-bottom: 6px; font-weight: 500; }}
  .stat-value {{ font-size: 24px; font-weight: 700; color: #F1F5F9; }}
  .stat-unit  {{ font-size: 13px; color: #94A3B8; margin-left: 2px; }}
  footer {{
    text-align: center;
    font-size: 12px;
    color: #334155;
    margin-top: 48px;
    padding-top: 24px;
    border-top: 1px solid rgba(148,163,184,0.08);
  }}
</style>
</head>
<body>

<header>
  <h1>Smart Grid House — Gestão Inteligente de Energia</h1>
  <p>Controlador via Lógica Fuzzy · Simulação Software-in-the-Loop (SITL) · 24 horas de operação</p>
  <div class="badge-row">
    <span class="badge b-amber">Geração Solar</span>
    <span class="badge b-blue">Demanda Residencial</span>
    <span class="badge b-green">Ação IA na Bateria</span>
    <span class="badge b-violet">SoC Acumulado</span>
  </div>
</header>

<!-- MÉTRICAS RÁPIDAS -->
<div class="stats-grid">
  <div class="stat">
    <div class="stat-label">SoC Inicial</div>
    <div class="stat-value">50<span class="stat-unit">%</span></div>
  </div>
  <div class="stat">
    <div class="stat-label">SoC Final</div>
    <div class="stat-value">{soc_plot[-1]:.1f}<span class="stat-unit">%</span></div>
  </div>
  <div class="stat">
    <div class="stat-label">Pico Solar</div>
    <div class="stat-value">100<span class="stat-unit">%</span></div>
  </div>
  <div class="stat">
    <div class="stat-label">Pico de Demanda</div>
    <div class="stat-value">100<span class="stat-unit">%</span></div>
  </div>
  <div class="stat">
    <div class="stat-label">Ação Máxima IA</div>
    <div class="stat-value">{max(respostas_ia):.1f}<span class="stat-unit">%</span></div>
  </div>
  <div class="stat">
    <div class="stat-label">Regras Fuzzy</div>
    <div class="stat-value">9</div>
  </div>
</div>

<!-- GRÁFICO 1 -->
<div class="section">
  <div class="section-label">01 — Simulação das 24 Horas</div>
  <div class="card">{html_24h}</div>
</div>

<!-- GRÁFICO 2 -->
<div class="section">
  <div class="section-label">02 — State of Charge (SoC) — Malha Fechada</div>
  <div class="card">{html_soc}</div>
</div>

<!-- GRÁFICO 3 -->
<div class="section">
  <div class="section-label">03 — Superfície de Controle 3D — Mapa de Decisão Fuzzy</div>
  <div class="card">{html_surface}</div>
</div>

<footer>
  Projeto A3 · Sistemas de Controle e Inteligência Artificial · Lógica Fuzzy (Mamdani) · scikit-fuzzy + Plotly
</footer>

</body>
</html>"""

output_path = output_path = 'smart_grid_dashboard.html'

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_completo)

print(f"Dashboard exportado: {output_path}")
print(f"SoC final: {soc_plot[-1]:.1f}%")
print(f"Ação máxima da IA: {max(respostas_ia):.1f}%")
print(f"Ação mínima da IA: {min(respostas_ia):.1f}%")
