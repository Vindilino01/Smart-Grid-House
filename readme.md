# 🔋 Smart Grid House — Gestão Inteligente de Energia

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Plotly-6.7.0-3F4F75?style=for-the-badge&logo=plotly&logoColor=white"/>
  <img src="https://img.shields.io/badge/Lógica-Fuzzy-10B981?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Status-Concluído-22C55E?style=for-the-badge"/>
</p>

> Controlador inteligente de energia residencial baseado em **Lógica Fuzzy (Mamdani)** com simulação de 24 horas em malha fechada e dashboard interativo gerado em HTML.

**Projeto A3 — Sistemas de Controle e Inteligência Artificial**

---

## 🎯 O que esse projeto faz

Simula o "cérebro" de uma casa com painel solar e banco de baterias. A cada hora do dia, a IA lê a geração solar e o consumo da casa e decide **quanto carregar ou descarregar a bateria** — de forma suave e contínua, sem os trancos do controle On/Off convencional.

| Entrada | Saída |
|---------|-------|
| Geração Solar (0–100%) | Ação na Bateria (-100% a +100%) |
| Demanda da Casa (0–100%) | SoC acumulado ao longo do dia |

---

## 📊 Dashboard Interativo

O script gera um arquivo `smart_grid_dashboard.html` com **3 gráficos interativos**:

- **Simulação das 24h** — curvas de solar, demanda e ação da IA
- **State of Charge (SoC)** — nível real da bateria em malha fechada
- **Superfície de Controle 3D** — mapa completo de decisão do controlador fuzzy

> Abra o `.html` direto no navegador — sem servidor, sem instalação adicional.

---

## 🚀 Como executar

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/smart-grid-fuzzy.git
cd smart-grid-fuzzy
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute
```bash
python ia_plotly.py
```

### 4. Abra o dashboard
```bash
# Windows
start smart_grid_dashboard.html

# macOS
open smart_grid_dashboard.html

# Linux
xdg-open smart_grid_dashboard.html
```

---

## 🧠 Como a IA decide

A lógica fuzzy usa **9 regras If-Then** organizadas numa matriz 3×3:

| Solar ↓ / Demanda → | Baixa | Média | Alta |
|---------------------|-------|-------|------|
| **Alta** | Carregar | Carregar | Manter |
| **Média** | Carregar | Manter | Descarregar |
| **Baixa** | Manter | Descarregar | Descarregar |

Em vez de decidir "liga ou desliga", a IA calcula um valor exato entre -100% e +100% usando o **método do Centroide (defuzzificação)**. Isso elimina o efeito *chattering* e protege a vida útil da bateria.

---

## 🗂️ Estrutura do projeto

```
smart-grid-fuzzy/
│
├── ia_plotly.py                  # Script principal
├── smart_grid_dashboard.html     # Dashboard gerado (abrir no navegador)
├── requirements.txt              # Dependências
├── PRD.md                        # Documento de produto completo
└── README.md                     # Este arquivo
```

---

## 📦 Stack

| Biblioteca | Versão | Uso |
|------------|--------|-----|
| NumPy | 2.4.4 | Cálculos matemáticos e universos de discurso |
| scikit-fuzzy | 0.5.0 | Motor de inferência fuzzy (Mamdani) |
| networkx | 3.6.1 | Dependência interna do scikit-fuzzy |
| Plotly | 6.7.0 | Dashboard interativo em HTML |

---

## 📄 Documentação completa

Consulte o [PRD.md](./PRD.md) para a documentação técnica completa do projeto — arquitetura do sistema, detalhamento da lógica fuzzy, resultados obtidos e referências bibliográficas.

---

*Projeto A3 — Sistemas de Controle e Inteligência Artificial*
