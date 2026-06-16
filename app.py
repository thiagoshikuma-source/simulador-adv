import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ==============================================================================
# MÓDULO PRINCIPAL: Configuração da Página e Organização Geral
# ==============================================================================
st.set_page_config(page_title="Simulador ADV", layout="wide")

st.title("📊 Simulador de Absorvedor Dinâmico de Vibração (ADV)")
st.markdown("""
Este aplicativo simula o comportamento de um sistema principal submetido a uma força harmônica,
comparando sua resposta original com a resposta após a introdução de um absorvedor dinâmico (ADV).
""")

# ==============================================================================
# MÓDULO DE ENTRADA DE DADOS: Barra Lateral (Sidebar)
# ==============================================================================
st.sidebar.header("📥 Parâmetros de Entrada")

st.sidebar.subheader("Sistema Principal (Massa 1)")
m1 = st.sidebar.number_input("Massa Principal $m_1$ (kg)", min_value=0.1, value=100.0, step=10.0)
k1 = st.sidebar.number_input("Rigidez Principal $k_1$ (N/m)", min_value=1.0, value=400000.0, step=10000.0)

st.sidebar.subheader("Absorvedor (Massa 2)")
# Sugestão padrão de 10% da massa principal
m2 = st.sidebar.number_input("Massa do ADV $m_2$ (kg)", min_value=0.01, value=10.0, step=1.0) 
# Sugestão de sintonia perfeita (w2 = wn) -> k2 = m2 * (k1/m1)
k2_sintonizado = m2 * (k1 / m1)
k2 = st.sidebar.number_input("Rigidez do ADV $k_2$ (N/m)", min_value=1.0, value=k2_sintonizado, step=10000.0, 
                             help="Para sintonia perfeita na frequência natural original, use o valor padrão.")

st.sidebar.subheader("Excitação Harmônica")
F0 = st.sidebar.number_input("Amplitude da Força $F_0$ (N)", min_value=0.0, value=100.0, step=10.0)

st.sidebar.subheader("Configurações do Gráfico")
f_max = st.sidebar.slider("Frequência Máxima de Varredura (Hz)", min_value=10, max_value=200, value=20)
pontos = st.sidebar.slider("Resolução (Número de Pontos)", min_value=100, max_value=2000, value=1000)

# ==============================================================================
# MÓDULO DE PROCESSAMENTO: Funções Matemáticas e Equações do Livro-Texto
# ==============================================================================

# 1. Cálculo das propriedades naturais
wn_original = np.sqrt(k1 / m1)  # rad/s
f_original = wn_original / (2 * np.pi)  # Hz

wn_adv = np.sqrt(k2 / m2)  # rad/s
f_adv = wn_adv / (2 * np.pi)  # Hz

# 2. Vetor de frequências de excitação (em Hz e transformado para rad/s)
f_vetor = np.linspace(0.1, f_max, pontos)
w_vetor = 2 * np.pi * f_vetor

# 3. Resposta do Sistema Original (Sem ADV - 1 GDL)
# X1_orig = F0 / |k1 - m1*w^2|
X1_original = np.abs(F0 / (k1 - m1 * w_vetor**2))

# 4. Resposta do Sistema Modificado (Com ADV - 2 GDL)
# Equações 9.144 e 9.145 do livro texto
numerador_X1 = k2 - m2 * w_vetor**2
denominador = (k1 + k2 - m1 * w_vetor**2) * (k2 - m2 * w_vetor**2) - k2**2

# Para evitar divisão por zero nas ressonâncias (adiciona um micro "offset" numérico)
denominador[denominador == 0] = 1e-10

X1_modificado = np.abs((numerador_X1 * F0) / denominador)
X2_modificado = np.abs((k2 * F0) / denominador)

# Convertendo para milímetros (mm) para melhor visualização no gráfico
X1_original_mm = X1_original * 1000
X1_modificado_mm = X1_modificado * 1000
X2_modificado_mm = X2_modificado * 1000

# ==============================================================================
# MÓDULO DE APRESENTAÇÃO (SAÍDA): Exibição de Dados e Gráficos
# ==============================================================================

# Criação de abas para organizar a saída
aba_graficos, aba_dados = st.tabs(["📈 Gráficos de Resposta", "📋 Parâmetros Calculados"])

with aba_dados:
    st.subheader("💡 Propriedades Dinâmicas do Sistema")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Freq. Natural Original ($f_n$)", value=f"{f_original:.2f} Hz")
    with col2:
        st.metric(label="Freq. de Sintonia do ADV ($f_a$)", value=f"{f_adv:.2f} Hz")
        
    st.markdown("""
    > **Nota Teórica:** Se a Frequência de Sintonia do ADV for exatamente igual à Frequência Natural Original, 
    > a amplitude da Massa Principal será **zero** exatamente na frequência de operação crítica!
    """)

with aba_graficos:
    st.subheader("Análise da Amplitude de Vibração vs. Frequência de Excitação")
    
    # Criando o gráfico interativo com Plotly
    fig = go.Figure()
    
    # Linha do sistema original
    fig.add_trace(go.Scatter(
        x=f_vetor, y=X1_original_mm,
        mode='lines',
        name='Massa Principal (Sem ADV)',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Linha da massa principal com ADV
    fig.add_trace(go.Scatter(
        x=f_vetor, y=X1_modificado_mm,
        mode='lines',
        name='Massa Principal (Com ADV)',
        line=dict(color='blue', width=3)
    ))
    
    # Linha da massa secundária (ADV)
    fig.add_trace(go.Scatter(
        x=f_vetor, y=X2_modificado_mm,
        mode='lines',
        name='Massa do ADV ($m_2$)',
        line=dict(color='green', width=2, dash='dot')
    ))
    
    # Customização do Layout do Gráfico
    fig.update_layout(
        xaxis_title="Frequência de Excitação (Hz)",
        yaxis_title="Amplitude de Vibração (mm)",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        margin=dict(l=40, r=40, t=20, b=40),
        height=600
    )
    
    # Definindo um teto no eixo Y para não distorcer o gráfico nas ressonâncias (picos infinitos sem amortecimento)
    max_y_view = np.percentile(X1_original_mm, 95) * 4
    fig.update_yaxes(range=[0, max_y_view])
    
    # Renderizar gráfico na tela
    st.plotly_chart(fig, use_container_width=True)

