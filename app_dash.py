import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
# HELPERS DE UI
# ──────────────────────────────────────────────
# Config de toolbar: apenas botão de download, discreto
GRAPH_CONFIG = {
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
        "autoScale2d", "resetScale2d", "hoverClosestCartesian",
        "hoverCompareCartesian", "zoom3d", "pan3d", "orbitRotation",
        "tableRotation", "resetCameraDefault3d", "resetCameraLastSave3d",
        "hoverClosest3d", "zoomInGeo", "zoomOutGeo", "resetGeo",
        "hoverClosestGeo", "sendDataToCloud", "toggleHover", "resetViews",
        "toggleSpikelines", "resetViewMapbox"
    ],
    "displayModeBar": True,
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "filename": "smart_grid_chart", "scale": 2},
}

def info_icon(tooltip_id, text):
    """Ícone i minimalista com tooltip padronizado."""
    return html.Span([
        html.Span("i", id=tooltip_id, className="info-icon"),
        dbc.Tooltip(
            text,
            target=tooltip_id,
            placement="right",
            delay={"show": 100, "hide": 50},
        )
    ], style={"display": "inline-flex", "alignItems": "center"})


def label_with_info(label_text, tooltip_id, tooltip_text):
    """Label de sidebar com ícone i alinhado."""
    return html.Div([
        html.Span(label_text, className="form-label"),
        info_icon(tooltip_id, tooltip_text)
    ], className="sidebar-label-row")

# ──────────────────────────────────────────────
# LÓGICA FUZZY BASE
# ──────────────────────────────────────────────
def build_fuzzy_system():
    geracao_solar = ctrl.Antecedent(np.arange(0, 101, 1), 'geracao_solar')
    demanda_casa  = ctrl.Antecedent(np.arange(0, 101, 1), 'demanda_casa')
    acao_bateria  = ctrl.Consequent(np.arange(-100, 101, 1), 'acao_bateria')

    geracao_solar['baixa'] = fuzz.trimf(geracao_solar.universe, [0,   0,  50])
    geracao_solar['media'] = fuzz.trimf(geracao_solar.universe, [0,  50, 100])
    geracao_solar['alta']  = fuzz.trimf(geracao_solar.universe, [50, 100, 100])

    demanda_casa['baixa'] = fuzz.trimf(demanda_casa.universe, [0,   0,  50])
    demanda_casa['media'] = fuzz.trimf(demanda_casa.universe, [0,  50, 100])
    demanda_casa['alta']  = fuzz.trimf(demanda_casa.universe, [50, 100, 100])

    acao_bateria['descarregar'] = fuzz.trimf(acao_bateria.universe, [-100, -100,  0])
    acao_bateria['manter']      = fuzz.trimf(acao_bateria.universe, [ -50,    0, 50])
    acao_bateria['carregar']    = fuzz.trimf(acao_bateria.universe, [   0,  100, 100])

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
    return ctrl.ControlSystem(regras)

sistema_fuzzy = build_fuzzy_system()
simulador = ctrl.ControlSystemSimulation(sistema_fuzzy)

# ──────────────────────────────────────────────
# PRÉ-COMPULAR SUPERFÍCIE 3D PARA PERFORMANCE
# ──────────────────────────────────────────────
x_grid = np.linspace(0, 100, 20)
y_grid = np.linspace(0, 100, 20)
Z_surface = np.zeros((20, 20))
for i, x_val in enumerate(x_grid):
    for j, y_val in enumerate(y_grid):
        simulador.input['geracao_solar'] = x_val
        simulador.input['demanda_casa'] = y_val
        try:
            simulador.compute()
            Z_surface[j, i] = simulador.output['acao_bateria']
        except:
            Z_surface[j, i] = 0

# ──────────────────────────────────────────────
# API DE CLIMA (Memória local simples)
# ──────────────────────────────────────────────
def fetch_weather_cache():
    url = "https://api.open-meteo.com/v1/forecast?latitude=-23.5505&longitude=-46.6333&daily=temperature_2m_max,precipitation_sum,sunshine_duration&past_days=15&forecast_days=7&timezone=America%2FSao_Paulo"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    
    # MOCK DATA FALLBACK se a API falhar para a Tabela não ficar vazia!
    hoje = datetime.now()
    datas = [(hoje + timedelta(days=i-14)).strftime("%Y-%m-%d") for i in range(22)]
    return {
        "daily": {
            "time": datas,
            "temperature_2m_max": [25.0]*22,
            "sunshine_duration": [36000.0]*22,
        }
    }


WEATHER_DATA = fetch_weather_cache()

# ──────────────────────────────────────────────
# APP DASH E ESTILOS
# ──────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"])
app.title = "Smart Grid House"

# CORES EXATAS DO PLOTLY
COR_SOL  = '#F59E0B'
COR_CASA = '#0EA5E9'
COR_IA   = '#10B981'
COR_SOC  = '#8B5CF6'

# ──────────────────────────────────────────────
# LAYOUT GLOBAL
# ──────────────────────────────────────────────
app.layout = dbc.Container([
    dcc.Store(id='sidebar-state', data=True),
    
    dbc.Button("≡", id="btn_sidebar", n_clicks=0, style={'position': 'absolute', 'top': '15px', 'left': '30px', 'zIndex': 9999, 'backgroundColor': 'transparent', 'color': '#10B981', 'border': 'none', 'fontSize': '2rem', 'padding': '0', 'lineHeight': '1'}),
    
    dbc.Row([
        # SIDEBAR COMPACTA
        dbc.Col([
            html.P("⚡ Smart Grid", className="sidebar-title"),
            html.P("Painel de Controle IA", className="sidebar-subtitle"),

            label_with_info("Objetivo de Economia (%)", "tip-economia",
                            "Reduz a demanda simulada. Quanto maior, mais a IA prioriza carregar a bateria."),
            dcc.Slider(0, 50, 5, value=20, id='meta_economia',
                       marks={0: {'label': '0%', 'style': {'color': '#6B7280', 'fontSize': '0.7rem'}},
                              50: {'label': '50%', 'style': {'color': '#6B7280', 'fontSize': '0.7rem'}}},
                       className="mb-3 pb-2"),

            label_with_info("Cenário Climático", "tip-cenario",
                            "Altera geração solar e consumo conforme o clima do dia."),
            dbc.Select(
                options=[
                    {'label': '⛅ Dia Normal',          'value': 'Normal'},
                    {'label': '🌧️ Chuva / Sem Sol',     'value': 'Chuvoso'},
                    {'label': '☀️ Verão Extremo',        'value': 'Verao'},
                    {'label': '✈️ Casa Vazia (Viagem)',  'value': 'Vazia'}
                ],
                value='Normal',
                id='cenario_drop',
                className="mb-2",
                style={'backgroundColor': '#1F2937', 'color': 'white',
                       'borderColor': '#374151', 'boxShadow': 'none',
                       'fontSize': '0.82rem', 'padding': '6px 10px'}
            ),

            label_with_info("Controle da Bateria", "tip-bateria",
                            "Automático: a IA decide. Forçar Carga/Uso sobrescreve manualmente."),
            dbc.RadioItems(
                options=[
                    {'label': '🧠 Automático (IA)', 'value': 'Auto'},
                    {'label': '🔋 Forçar Carga (+)', 'value': 'Carregar'},
                    {'label': '🔌 Forçar Uso (−)',   'value': 'Descarregar'}
                ],
                value='Auto',
                id='modo_bateria',
                labelStyle={'display': 'block', 'marginBottom': '8px',
                            'color': '#D1D5DB', 'fontSize': '0.82rem'},
                className="mb-2"
            ),

            # Painel de status da IA
            html.Div(id='ia-status-panel')
        ], id="sidebar", width=12, md=3, lg=3, className="sidebar"),

        # MAIN CONTENT
        dbc.Col([
            
            
            dbc.Row(id='metric-cards', className="mb-2 px-2"),

            html.Div([
                dbc.Tabs([
                    dbc.Tab(tab_id="tab-1", label="⚡ Visão Geral"),
                    dbc.Tab(tab_id="tab-2", label="🔮 Previsão & Decisões"),
                ], id="tabs", active_tab="tab-1"),
                
                html.Div(id='charts-wrapper', className="mt-4")
                
            ], className="px-3")
            
        ], id="page-content", width=12, md=9, lg=9, style={'padding': '60px 30px 15px 30px'})
    ], className="m-0")
], fluid=True, style={'padding': '0px'})

# ──────────────────────────────────────────────
# CALLBACK TOGGLE SIDEBAR
# ──────────────────────────────────────────────
@app.callback(
    [Output("sidebar", "style"),
     Output("page-content", "md"),
     Output("page-content", "lg"),
     Output("sidebar-state", "data")],
    [Input("btn_sidebar", "n_clicks")],
    [State("sidebar-state", "data")]
)
def toggle_sidebar(n, is_open):
    if n:
        is_open = not is_open
    if is_open:
        return {'display': 'block'}, 9, 9, is_open
    else:
        return {'display': 'none'}, 12, 12, is_open

# ──────────────────────────────────────────────
# CALLBACK MASTER
# ──────────────────────────────────────────────
@app.callback(
    [Output('metric-cards', 'children'),
     Output('charts-wrapper', 'children'),
     Output('ia-status-panel', 'children')],
    [Input('meta_economia', 'value'),
     Input('cenario_drop', 'value'),
     Input('modo_bateria', 'value'),
     Input('tabs', 'active_tab')]
)
def update_dashboard(meta_eco, cenario, modo_bat, active_tab):
    # DADOS BASE
    horas = list(range(24))
    sol_base = np.array([0, 0, 0, 0, 0, 5, 25, 50, 75, 90, 100, 95, 85, 70, 50, 30, 10, 2, 0, 0, 0, 0, 0, 0])
    casa_base = np.array([10,10,10,10,15,40, 80, 50, 30, 20,  20, 30, 40, 30, 40, 60, 90,100,85,60,40,20,10,10])

    if cenario == "Chuvoso":
        sol_dia = sol_base * 0.3
        casa_dia = casa_base * 1.1
    elif cenario == "Verao":
        sol_dia = sol_base * 1.1
        casa_dia = casa_base * 1.4
    elif cenario == "Vazia":
        sol_dia = sol_base * 1.0
        casa_dia = casa_base * 0.2
    else:
        sol_dia = sol_base
        casa_dia = casa_base

    sol_dia = np.clip(sol_dia, 0, 100)
    casa_dia = np.clip(casa_dia, 0, 100)

    # SIMULAÇÃO
    SOC_INICIAL = 50.0
    soc_atual = SOC_INICIAL
    TAXA_CONVERSAO = 0.3 if modo_bat == "Auto" else 0.5
    respostas_ia = []
    soc_historico = [SOC_INICIAL]

    for h in range(24):
        if modo_bat == "Carregar":
            acao = 80.0
        elif modo_bat == "Descarregar":
            acao = -80.0
        else:
            simulador.input['geracao_solar'] = float(sol_dia[h])
            demanda_ajustada = np.clip(casa_dia[h] * (1.0 + (meta_eco / 100.0)), 0, 100)
            simulador.input['demanda_casa']  = float(demanda_ajustada)
            try:
                simulador.compute()
                acao = simulador.output['acao_bateria']
            except:
                acao = 0.0
        respostas_ia.append(acao)
        novo_soc = np.clip(soc_atual + acao * TAXA_CONVERSAO, 0, 100)
        soc_historico.append(novo_soc)
        soc_atual = novo_soc

    soc_plot = soc_historico[:24]

    # hora atual para linha "Agora"
    hora_atual = datetime.now().hour

    # CARDS — altura fixa, % inline, cor dinâmica na bateria
    def soc_color(val):
        if val < 20:
            return '#EF4444'
        if val < 50:
            return '#F59E0B'
        return '#10B981'

    def make_card(title, value_str, color_accent, progress_val=None, trend=None):
        top_row = [html.H3(value_str, className="metric-value", style={"margin": 0})]
        if trend is not None:
            t_color = '#10B981' if trend >= 0 else '#EF4444'
            t_arrow = '↑' if trend >= 0 else '↓'
            top_row.append(
                html.Span(f"{t_arrow}{abs(trend):.0f}%", className="metric-trend-inline",
                          style={"color": t_color})
            )
        body_children = [
            html.P(title, className="metric-title"),
            html.Div(top_row, className="metric-top-row"),
        ]
        if progress_val is not None:
            body_children.append(html.Div(
                html.Div(className="metric-progress-bar",
                         style={"width": f"{min(progress_val, 100):.1f}%",
                                "backgroundColor": color_accent}),
                className="metric-progress-track"
            ))
        return dbc.Col(
            dbc.Card(
                dbc.CardBody(body_children, className="metric-card-body"),
                style={'borderTop': f'3px solid {color_accent}'}
            ),
            width=12, md=2, lg=2, className="mb-3 flex-grow-1"
        )

    soc_final   = soc_historico[-1]
    soc_cor     = soc_color(soc_final)
    soc_ini_cor = soc_color(SOC_INICIAL)
    tendencia   = soc_final - SOC_INICIAL

    cards = [
        make_card("Bateria Atual",    f"{SOC_INICIAL:.0f}%",              soc_ini_cor, SOC_INICIAL),
        make_card("Bateria Estimada", f"{soc_final:.1f}%",                soc_cor,     soc_final,  tendencia),
        make_card("Pico Geração",     f"{max(sol_dia):.0f}%",             COR_SOL,     max(sol_dia)),
        make_card("Pico Demanda",     f"{max(casa_dia):.0f}%",            COR_CASA,    max(casa_dia)),
        make_card("Demanda da IA",    f"{sum(np.abs(respostas_ia))/24:.1f}%", COR_IA,  sum(np.abs(respostas_ia))/24),
    ]

    # CONFIGURAÇÃO DE GRÁFICOS
    HOVER_STYLE = dict(
        bgcolor='#1A1F2B',
        bordercolor='#374151',
        font=dict(color='#E2E8F0', family='Inter, sans-serif', size=13),
    )

    minimal_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color='#9CA3AF', family="Inter, sans-serif", size=12),
        margin=dict(t=30, l=10, r=20, b=40),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=HOVER_STYLE,
    )

    # FIG 1: 24h
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=horas, y=sol_dia, name='☀️ Geração', fill='tozeroy', fillcolor='rgba(245, 158, 11, 0.1)', line=dict(color=COR_SOL, width=3), mode='lines'))
    fig1.add_trace(go.Scatter(x=horas, y=casa_dia, name='⚡ Consumo', fill='tozeroy', fillcolor='rgba(14, 165, 233, 0.1)', line=dict(color=COR_CASA, width=3), mode='lines'))
    fig1.add_trace(go.Scatter(x=horas, y=respostas_ia, name='🧠 IA Atuação', mode='lines', line=dict(color=COR_IA, dash='dot', width=3)))
    fig1.add_vline(x=hora_atual, line_width=1, line_dash="dash", line_color="#10B981",
                   annotation_text="Agora", annotation_position="top right",
                   annotation_font_color="#10B981", annotation_font_size=11)
    fig1.update_layout(**minimal_layout, hovermode='x unified', title="Balanço Energético 24h")
    # FIG 2: SOC
    fig2 = go.Figure()
    fig2.add_hrect(y0=20, y1=80, fillcolor='rgba(16,185,129,0.05)', line_width=0, annotation_text="Faixa Ideal", annotation_position="top left", annotation_font_color="#10B981")
    fig2.add_trace(go.Scatter(x=horas, y=soc_plot, name='🔋 Nível da Bateria', mode='lines+markers', marker=dict(size=8), line=dict(color=COR_SOC, width=3), fill='tozeroy', fillcolor='rgba(139, 92, 246, 0.1)'))
    fig2.update_layout(**minimal_layout, hovermode='x unified', title="Evolução do SoC (State of Charge)")
    fig2.update_yaxes(range=[0, 105])

    # FIG 3: 3D
    fig3 = go.Figure(data=[go.Surface(z=Z_surface, x=x_grid, y=y_grid, colorscale='Viridis', opacity=0.7)])
    # Sincronia: Adicionar a jornada de 24h na superfície Fuzzy!
    fig3.add_trace(go.Scatter3d(
        x=sol_dia, y=casa_dia, z=respostas_ia,
        mode='lines+markers', line=dict(color='#EF4444', width=6), marker=dict(size=4, color='#EF4444'),
        name='Ações de Hoje (Curva)'
    ))
    fig3.update_layout(
        scene=dict(
            xaxis_title='Geração Solar', yaxis_title='Demanda Casa', zaxis_title='Atuação Bateria',
            xaxis=dict(gridcolor='rgba(255,255,255,0.08)', backgroundcolor='rgba(0,0,0,0)', title_font=dict(color='#E2E8F0')),
            yaxis=dict(gridcolor='rgba(255,255,255,0.08)', backgroundcolor='rgba(0,0,0,0)', title_font=dict(color='#E2E8F0')),
            zaxis=dict(gridcolor='rgba(255,255,255,0.08)', backgroundcolor='rgba(0,0,0,0)', title_font=dict(color='#E2E8F0'))
        ),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color='#9CA3AF', family="Inter, sans-serif"),
        margin=dict(l=0, r=0, t=30, b=0), title="Mapa de Decisão da IA",
        hoverlabel=HOVER_STYLE,
    )

    # FIG 4: WEATHER
    fig4 = go.Figure()
    if WEATHER_DATA:
        df_clima = pd.DataFrame(WEATHER_DATA['daily'])
        df_clima['time'] = pd.to_datetime(df_clima['time'])
        
        # Sincronia 1: Ajuste da Meta Econômica e Cenário Climático Menu Lateral
        mod_cenario = 1.0
        mod_sol = 1.0
        if cenario == "Verao": mod_cenario = 1.4; mod_sol = 1.1
        elif cenario == "Chuvoso": mod_cenario = 1.1; mod_sol = 0.3
        elif cenario == "Vazia": mod_cenario = 0.2; mod_sol = 1.0
        
        df_clima['Consumo Estimado'] = df_clima['temperature_2m_max'] * 1.5 * mod_cenario * (1.0 + (meta_eco / 100.0))
        df_clima['Geração Estimada'] = (df_clima['sunshine_duration'] / 3600 * 5) * mod_sol
        
        fig4.add_trace(go.Bar(x=df_clima['time'], y=df_clima['Consumo Estimado'], name='Consumo Diário Projetado', marker_color='#3B82F6', marker_line_width=0))
        fig4.add_trace(go.Bar(x=df_clima['time'], y=df_clima['Geração Estimada'], name='Geração Diária Projetada', marker_color='#F59E0B', marker_line_width=0))
        fig4.add_vline(x=datetime.now().timestamp() * 1000, line_width=2, line_dash="dash", line_color="#10B981", annotation_text="Hoje", annotation_position="top right")

    fig4.update_layout(**minimal_layout, barmode='group', hovermode='x unified', title="Previsão de 7 Dias")
    fig4.update_xaxes(showgrid=False)
    fig4.update_yaxes(showgrid=False)

    # FIG 5: PIE
    if cenario == "Verao":
        lbl = ['A/C', 'Geladeira', 'Chuveiro', 'Outros']
        val = [50, 20, 15, 15]
    elif cenario == "Chuvoso":
        lbl = ['Chuveiro', 'Geladeira', 'Lavanderia', 'Outros']
        val = [45, 25, 15, 15]
    elif cenario == "Vazia":
        lbl = ['Geladeira', 'Segurança', 'Standby', 'Outros']
        val = [60, 20, 15, 5]
    else:
        lbl = ['Chuveiro', 'A/C', 'Geladeira', 'Outros']
        val = [30, 25, 20, 25]

    fig5 = go.Figure(data=[go.Pie(
        labels=lbl, values=val, hole=.5,
        textinfo='percent+label',
        insidetextorientation='horizontal',
        marker=dict(line=dict(color='#0B0E14', width=2))
    )])
    fig5.update_layout(**minimal_layout, showlegend=False, title="Divisão do Consumo")

    # Painel de status da IA
    hora_idx   = min(hora_atual, 23)
    sol_agora  = sol_dia[hora_idx]
    casa_agora = casa_dia[hora_idx]
    acao_agora = respostas_ia[hora_idx]

    if modo_bat == "Carregar":
        ia_msg = "🔋 Carga forçada manualmente — modo manual ativo."
    elif modo_bat == "Descarregar":
        ia_msg = "🔌 Descarga forçada manualmente — modo manual ativo."
    elif acao_agora > 20:
        ia_msg = f"🧠 Carregando bateria — geração alta ({sol_agora:.0f}%), demanda baixa ({casa_agora:.0f}%)."
    elif acao_agora < -20:
        ia_msg = f"🧠 Descarregando bateria — geração baixa ({sol_agora:.0f}%), demanda alta ({casa_agora:.0f}%)."
    else:
        ia_msg = f"🧠 Mantendo bateria — geração ({sol_agora:.0f}%) e demanda ({casa_agora:.0f}%) equilibradas."

    ia_panel = html.Div([
        html.P("IA — Decisão Atual", className="ia-status-label"),
        html.P(ia_msg, style={"margin": 0})
    ], className="ia-status-panel")

    # ROTEAMENTO DE TABS AGRUPADO
    if active_tab == "tab-1":
        layout_charts = dbc.Row([
            dbc.Col(html.Div(dcc.Graph(figure=fig1, config=GRAPH_CONFIG, style={'height': '380px'}), className="card border-0 bg-transparent shadow-none"), width=12, lg=12, className="mb-5 pb-3"),
            dbc.Col(html.Div(dcc.Graph(figure=fig5, config=GRAPH_CONFIG, style={'height': '380px'}), className="card border-0 bg-transparent shadow-none"), width=12, lg=12, className="mb-5 pb-3"),
            dbc.Col(html.Div(dcc.Graph(figure=fig2, config=GRAPH_CONFIG, style={'height': '320px'}), className="card border-0 bg-transparent shadow-none"), width=12, lg=12, className="mb-5 pb-3"),
        ])
    else:
        layout_charts = dbc.Row([
            dbc.Col(html.Div(dcc.Graph(figure=fig3, config=GRAPH_CONFIG, style={'height': '450px'}), className="card border-0 bg-transparent shadow-none"), width=12, lg=12, className="mb-5 pb-3"),
            dbc.Col(html.Div(dcc.Graph(figure=fig4, config=GRAPH_CONFIG, style={'height': '450px'}), className="card border-0 bg-transparent shadow-none"), width=12, lg=12, className="mb-5 pb-3"),
        ])

    return cards, layout_charts, ia_panel

if __name__ == '__main__':
    app.run(debug=True, dev_tools_ui=False, port=8050)
