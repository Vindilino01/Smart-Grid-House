# ⚡ Smart Grid House

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Dash-2.18-008DE4?style=for-the-badge&logo=plotly&logoColor=white"/>
  <img src="https://img.shields.io/badge/Lógica-Fuzzy-10B981?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Status-Em%20Desenvolvimento-F59E0B?style=for-the-badge"/>
</p>

> Painel de controle interativo para gestão inteligente de energia residencial com painel solar e banco de baterias. A IA decide, em tempo real, quanto carregar ou descarregar a bateria com base em **Lógica Fuzzy (Mamdani)**.

**Projeto A3 — Sistemas de Controle e Inteligência Artificial — USJT**

---

## 📋 Índice

- [O que é o Smart Grid House](#-o-que-é-o-smart-grid-house)
- [Como usar o painel](#-como-usar-o-painel)
  - [Sidebar — Controles](#sidebar--controles)
  - [Cards de Métricas](#cards-de-métricas)
  - [Aba Visão Geral](#aba--visão-geral)
  - [Aba Previsão & Decisões](#aba--previsão--decisões)
- [Como executar](#-como-executar)
- [Arquitetura técnica](#-arquitetura-técnica)
- [Lógica Fuzzy — detalhamento](#-lógica-fuzzy--detalhamento)
- [API de Clima](#-api-de-clima)
- [Estrutura do projeto](#-estrutura-do-projeto)
- [Stack tecnológica](#-stack-tecnológica)

---

## 🏠 O que é o Smart Grid House

O Smart Grid House simula o "cérebro" de uma residência com energia solar e banco de baterias. A cada hora do dia, o sistema lê dois valores — **geração solar** e **consumo da casa** — e decide de forma contínua e suave quanto carregar ou descarregar a bateria.

O diferencial em relação a sistemas convencionais é o uso de **Lógica Fuzzy**: em vez de ligar/desligar bruscamente (On/Off), a IA calcula um valor proporcional entre -100% e +100%, eliminando o efeito *chattering* e protegendo a vida útil da bateria.

---

## 🖥️ Como usar o painel

### Sidebar — Controles

A barra lateral esquerda concentra todos os controles do sistema. Cada campo tem um ícone **i** que exibe uma dica ao passar o mouse.

#### Objetivo de Economia (%)
Slider de 0% a 50% que simula uma meta de redução de consumo. Ao aumentar esse valor, o sistema multiplica a demanda simulada da casa, forçando a IA a ser mais conservadora e priorizar o carregamento da bateria. Use 0% para ver o comportamento natural do sistema e 50% para simular uma casa com forte gestão de consumo.

#### Cenário Climático
Menu dropdown com quatro opções que alteram os perfis de geração solar e consumo da casa:

| Cenário | Geração Solar | Consumo da Casa | Quando usar |
|---------|--------------|-----------------|-------------|
| ⛅ Dia Normal | 100% (base) | 100% (base) | Dia típico de São Paulo |
| 🌧️ Chuva / Sem Sol | 30% da base | 110% da base | Dias nublados ou chuvosos |
| ☀️ Verão Extremo | 110% da base | 140% da base | Dias quentes com A/C ligado |
| ✈️ Casa Vazia | 100% da base | 20% da base | Viagem — só consumo de standby |

#### Controle da Bateria
Três opções de modo de operação:

- **🧠 Automático (IA)** — a lógica fuzzy decide a cada hora com base na geração e demanda. É o modo padrão e recomendado.
- **🔋 Forçar Carga (+)** — sobrescreve a IA e força carregamento máximo da bateria independente das condições. Útil para simular uma carga forçada antes de uma viagem.
- **🔌 Forçar Uso (−)** — sobrescreve a IA e força descarga máxima. Útil para simular uso intenso da bateria.

#### Painel "IA — Decisão Atual"
No rodapé da sidebar, um painel verde mostra em linguagem natural o que a IA está decidindo **neste momento** (hora atual do relógio), com os valores de geração e demanda da hora. Atualiza automaticamente ao mudar qualquer controle.

---

### Cards de Métricas

Cinco cards no topo da área principal mostram os indicadores mais importantes da simulação. Todos têm altura fixa e uma barra de progresso colorida na base.

| Card | O que mostra | Cor da barra |
|------|-------------|--------------|
| **Bateria Atual** | SoC inicial fixo em 50% (ponto de partida da simulação) | Verde / Amarelo / Vermelho conforme o nível |
| **Bateria Estimada** | SoC projetado ao final das 24h com seta de tendência ↑↓ | Verde / Amarelo / Vermelho conforme o nível |
| **Pico Geração** | Valor máximo de geração solar no dia simulado | Âmbar |
| **Pico Demanda** | Valor máximo de consumo da casa no dia simulado | Azul |
| **Demanda da IA** | Média da intensidade de atuação da IA ao longo do dia | Verde |

A cor dos cards de bateria muda dinamicamente:
- 🔴 Vermelho — abaixo de 20% (zona crítica)
- 🟡 Amarelo — entre 20% e 50% (zona de atenção)
- 🟢 Verde — acima de 50% (zona saudável)

---

### Aba ⚡ Visão Geral

Contém três gráficos que mostram o estado atual do sistema ao longo das 24 horas do dia.

#### Balanço Energético 24h
Gráfico de linhas com três séries:
- **☀️ Geração** (âmbar) — curva de produção solar hora a hora, com pico ao meio-dia
- **⚡ Consumo** (azul) — curva de demanda da casa, com picos pela manhã e à noite
- **🧠 IA Atuação** (verde pontilhado) — decisão da IA a cada hora: positivo = carregando, negativo = descarregando

Uma linha vertical verde tracejada marca a **hora atual** com a anotação "Agora", permitindo identificar imediatamente em que ponto do dia o sistema está operando.

Ao passar o mouse sobre o gráfico, um tooltip escuro unificado mostra os três valores da hora selecionada simultaneamente.

#### Divisão do Consumo
Gráfico de rosca (donut) mostrando a composição percentual do consumo da casa. Os rótulos mudam conforme o cenário selecionado:
- Dia Normal / Verão: Chuveiro, A/C, Geladeira, Outros
- Chuva: Chuveiro, Geladeira, Lavanderia, Outros
- Casa Vazia: Geladeira, Segurança, Standby, Outros

Todos os rótulos são exibidos na horizontal para facilitar a leitura.

#### Evolução do SoC (State of Charge)
Gráfico de linha com marcadores mostrando o nível da bateria hora a hora como resultado acumulado das decisões da IA. Uma faixa verde translúcida destaca a **zona ideal de operação** (20%–80%), que preserva a vida útil da bateria.

---

### Aba 🔮 Previsão & Decisões

Contém dois gráficos voltados para análise preditiva e visualização da inteligência do sistema.

#### Mapa de Decisão da IA (3D)
Superfície tridimensional interativa que mostra **todas as decisões possíveis** do controlador fuzzy para qualquer combinação de geração solar (eixo X) e demanda da casa (eixo Y). O eixo Z mostra a ação resultante na bateria.

Sobre a superfície, uma curva vermelha traça a **jornada real do dia simulado** — os 24 pontos de decisão da IA ao longo das horas. Isso permite ver exatamente em que região do mapa de decisão o sistema operou.

O gráfico pode ser rotacionado livremente clicando e arrastando.

#### Previsão de 7 Dias
Gráfico de barras agrupadas com dados reais da API Open-Meteo para São Paulo, mostrando os últimos 15 dias e os próximos 7 dias:
- **Barras azuis** — consumo diário projetado (baseado na temperatura máxima do dia)
- **Barras âmbar** — geração solar estimada (baseada na duração do sol)

Uma linha verde tracejada marca o dia de hoje. Os valores são ajustados automaticamente conforme o cenário climático e a meta de economia selecionados na sidebar.

---

### Botão de Download

Cada gráfico tem um ícone de câmera discreto no canto superior direito. Ao clicar, baixa o gráfico como imagem PNG em alta resolução (escala 2×).

---

## 🚀 Como executar

### Pré-requisitos
- Python 3.10 ou superior
- pip

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/Smart-Grid-House.git
cd Smart-Grid-House
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute
```bash
python3 app_dash.py
```

### 4. Acesse no navegador
```
http://127.0.0.1:8050
```

O servidor inicia em modo debug na porta 8050. Para parar, pressione `Ctrl+C` no terminal.

---

## 🏗️ Arquitetura técnica

```
┌─────────────────────────────────────────────────────────┐
│                    ENTRADAS (Sensores)                  │
│   geracao_solar [0–100%]     demanda_casa [0–100%]      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               MOTOR FUZZY — Mamdani                     │
│  1. Fuzzificação (trimf)                                │
│  2. Inferência (9 regras If-Then)                       │
│  3. Defuzzificação (Centroide)                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                SAÍDA — Atuador                          │
│         acao_bateria [-100% a +100%]                    │
│  < 0 = descarregar  |  0 = manter  |  > 0 = carregar   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│           MALHA FECHADA — SoC Acumulado                 │
│   SoC(t+1) = clip(SoC(t) + ação × 0.3,  0, 100)        │
└─────────────────────────────────────────────────────────┘
```

O sistema roda em **malha fechada**: a ação da IA em cada hora afeta o SoC, que é acumulado ao longo das 24 horas. O fator de conversão `0.3` representa a eficiência do ciclo de carga/descarga.

A superfície 3D é **pré-computada na inicialização** (grade 20×20 = 400 pontos) para evitar recalcular a cada interação do usuário, garantindo resposta imediata nos callbacks.

---

## 🧠 Lógica Fuzzy — detalhamento

### Variáveis linguísticas

**Entradas (Antecedentes) — funções triangulares (trimf):**

| Variável | Conjunto | Pontos da trimf |
|----------|----------|-----------------|
| `geracao_solar` | baixa | [0, 0, 50] |
| `geracao_solar` | media | [0, 50, 100] |
| `geracao_solar` | alta | [50, 100, 100] |
| `demanda_casa` | baixa | [0, 0, 50] |
| `demanda_casa` | media | [0, 50, 100] |
| `demanda_casa` | alta | [50, 100, 100] |

**Saída (Consequente):**

| Variável | Conjunto | Pontos da trimf |
|----------|----------|-----------------|
| `acao_bateria` | descarregar | [-100, -100, 0] |
| `acao_bateria` | manter | [-50, 0, 50] |
| `acao_bateria` | carregar | [0, 100, 100] |

### Base de regras (matriz 3×3)

| Solar ↓ / Demanda → | Baixa | Média | Alta |
|---------------------|-------|-------|------|
| **Alta** | Carregar | Carregar | Manter |
| **Média** | Carregar | Manter | Descarregar |
| **Baixa** | Manter | Descarregar | Descarregar |

### Defuzzificação

Método **Centroide (Centro de Gravidade)**: calcula o centro de massa da área geométrica resultante da sobreposição das regras ativadas. Produz um valor contínuo e suave — nunca há saltos bruscos entre decisões consecutivas.

### Parâmetros da simulação

```python
SOC_INICIAL    = 50.0   # bateria começa na metade
TAXA_CONVERSAO = 0.3    # fator ação → variação de SoC por hora (modo Auto)
TAXA_CONVERSAO = 0.5    # fator em modo manual (Forçar Carga/Uso)
SOC_MIN        = 0.0    # limite inferior (clip)
SOC_MAX        = 100.0  # limite superior (clip)
```

---

## 🌤️ API de Clima

O gráfico de Previsão de 7 Dias consome a API pública **Open-Meteo** (sem chave, sem cadastro):

```
https://api.open-meteo.com/v1/forecast
  ?latitude=-23.5505
  &longitude=-46.6333
  &daily=temperature_2m_max,precipitation_sum,sunshine_duration
  &past_days=15
  &forecast_days=7
  &timezone=America/Sao_Paulo
```

Campos utilizados:
- `temperature_2m_max` — temperatura máxima diária (usada para estimar consumo)
- `sunshine_duration` — duração do sol em segundos (usada para estimar geração)

Se a API estiver indisponível, o sistema usa dados mock (25°C e 10h de sol por dia) para que o gráfico nunca fique vazio.

---

## 🗂️ Estrutura do projeto

```
Smart-Grid-House/
│
├── app_dash.py                    # Aplicação principal — lógica fuzzy + dashboard
├── assets/
│   └── custom.css                 # Estilos globais — tema escuro, cards, sidebar, tooltips
├── painel-solar-movel/
│   ├── rastreador-solar.ino       # Firmware Arduino — rastreador solar 2 eixos com LDR
│   └── README.md                  # Documentação do hardware
├── requirements.txt               # Dependências Python
├── PRD.md                         # Documento de produto e fundamentação teórica
└── readme.md                      # Este arquivo
```

### `app_dash.py` — organização interna

| Seção | Linhas | Responsabilidade |
|-------|--------|-----------------|
| Helpers de UI | topo | `GRAPH_CONFIG`, `info_icon()`, `label_with_info()` |
| Lógica Fuzzy | após helpers | `build_fuzzy_system()` — define variáveis, funções de pertinência e regras |
| Pré-cômputo 3D | após fuzzy | Grade 20×20 da superfície de controle — roda uma vez na inicialização |
| API de Clima | após 3D | `fetch_weather_cache()` — busca dados reais com fallback mock |
| Layout | após API | Estrutura HTML do Dash — sidebar + cards + tabs + gráficos |
| Callbacks | final | `toggle_sidebar()` e `update_dashboard()` — toda a lógica reativa |

---

## 📦 Stack tecnológica

| Biblioteca | Versão | Papel |
|------------|--------|-------|
| Dash | 2.18 | Framework web reativo — layout + callbacks |
| Dash Bootstrap Components | 1.6 | Grid, cards, tabs, tooltips, select, radio |
| Plotly | 6.7 | Gráficos interativos (linha, rosca, barra, superfície 3D) |
| NumPy | 2.4 | Arrays, universos de discurso, cálculos matriciais |
| scikit-fuzzy | 0.5 | Motor de inferência fuzzy Mamdani |
| SciPy | 1.17 | Dependência interna do scikit-fuzzy |
| NetworkX | 3.6 | Dependência interna do scikit-fuzzy |
| Pandas | 2.3 | Manipulação dos dados da API de clima |
| Requests | 2.32 | Chamada HTTP para a API Open-Meteo |

### Hardware complementar — `painel-solar-movel/`

O repositório inclui também o firmware Arduino de um **rastreador solar de 2 eixos** com 4 sensores LDR. O sistema lê a diferença de luminosidade entre os sensores e ajusta dois servomotores para manter o painel sempre apontado para o sol. Tolerância configurável (`tol = 90`) evita micro-movimentos desnecessários.

---

*Projeto A3 — Sistemas de Controle e Inteligência Artificial — USJT*
