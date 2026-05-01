import streamlit as st
import random
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 0. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="MTG Commander Analytics", layout="wide")
st.title("🧙‍♂️ Analisador Dinâmico de Commander")
st.markdown("Simulador estatístico de Land Drops baseado no Método de Monte Carlo para decks de exatas 99 cartas.")

# ==========================================
# 1. FUNÇÕES TÉCNICAS (Mantidas intactas)
# ==========================================
def calcular_cmc_medio(curva_mana):
    total_cartas = sum(curva_mana.values())
    if total_cartas == 0: return 0
    return sum(cmc * qtd for cmc, qtd in curva_mana.items()) / total_cartas

def simular_land_drops(qtd_terrenos, turnos_alvo, total_simulacoes):
    sucessos = 0
    for _ in range(total_simulacoes):
        deck = ['L'] * qtd_terrenos + ['X'] * (99 - qtd_terrenos)
        random.shuffle(deck)
        mao = deck[:7 + turnos_alvo]
        if mao.count('L') >= turnos_alvo:
            sucessos += 1
    return (sucessos / total_simulacoes) * 100

# ==========================================
# 2. INTERFACE DINÂMICA (Sidebar)
# ==========================================
st.sidebar.header("⚙️ Configurações da Simulação")
turno_alvo = st.sidebar.slider("Turno Alvo para Drop de Terreno", min_value=1, max_value=10, value=5)
total_simulacoes = st.sidebar.slider("Resolução (Simulações)", min_value=1000, max_value=20000, step=1000, value=10000)

deck_data = {
    1: {'CMC': 6,  'pips': {'G': 3, 'R': 2}},
    2: {'CMC': 22, 'pips': {'G': 5, 'R': 21}},
    3: {'CMC': 18, 'pips': {'G': 16, 'R': 7}},      
    4: {'CMC': 12, 'pips': {'G': 5, 'R': 11}},      
    5: {'CMC': 6,  'pips': {'G': 3, 'R': 5}},
    6: {'CMC': 0,  'pips': {'B': 0, 'R': 4}},
    7: {'CMC': 0,  'pips': {'B': 0, 'R': 0}},
    8: {'CMC': 1,  'pips': {'B': 0, 'R': 2}},
}

# ==========================================
# 3. CÁLCULOS E DASHBOARD
# ==========================================
curva_simples = {custo: info['CMC'] for custo, info in deck_data.items()}
total_magicas = sum(curva_simples.values())
terrenos_reais = 99 - total_magicas
cmc_medio = calcular_cmc_medio(curva_simples)

identidade_cores = set()
for info in deck_data.values():
    identidade_cores.update(info['pips'].keys())

pesos_cores = {cor: 0 for cor in identidade_cores}
for custo, info in deck_data.items():
    urgencia = 1 / (custo ** 0.5) 
    for cor, pips in info['pips'].items():
        pesos_cores[cor] += pips * urgencia

# Exibindo os dados na tela do site
col1, col2, col3, col4 = st.columns(4)
col1.metric("Mágicas", total_magicas)
col2.metric("Espaços para Terrenos", terrenos_reais)
col3.metric("CMC Médio", f"{cmc_medio:.2f}")
col4.metric("Identidade", ", ".join(sorted(identidade_cores)))

st.divider()

col_esquerda, col_direita = st.columns([1, 2])

with col_esquerda:
    st.subheader("🎨 Proporção Sugerida")
    total_pesos = sum(pesos_cores.values())
    if total_pesos > 0:
        for cor in sorted(pesos_cores.keys()):
            proporcao = pesos_cores[cor] / total_pesos
            fontes = round(proporcao * terrenos_reais)
            st.write(f"**{cor}:** {fontes} fontes (Peso: {pesos_cores[cor]:.2f})")
    
    st.subheader(f"🎯 Análise (Turno {turno_alvo})")
    st.write("Configurações que atingem 40-50% de sucesso:")
    for t in range(25, 46):
        p = simular_land_drops(t, turno_alvo, total_simulacoes)
        if 40 <= p <= 50:
            check = " 🟢 **[ATUAL]**" if t == terrenos_reais else ""
            st.write(f"- **{p:.1f}%** -> {t} Lands / {99-t} Mágicas{check}")

with col_direita:
    # ==========================================
    # 4. VISUALIZAÇÃO GRÁFICA NO SITE
    # ==========================================
    st.subheader("Curva de Probabilidade")
    range_terrenos = list(range(max(20, terrenos_reais - 6), terrenos_reais + 8))
    
    # Adicionando um spinner enquanto roda as simulações
    with st.spinner('Executando simulações de Monte Carlo...'):
        dados_grafico = [{'T': t, 'P': simular_land_drops(t, turno_alvo, total_simulacoes)} for t in range_terrenos]
        df = pd.DataFrame(dados_grafico)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df['T'], df['P'], marker='o', color='#2c3e50', linewidth=2, label='Curva de Probabilidade')

    for i, row in df.iterrows():
        ax.annotate(f"{row['P']:.1f}%", (row['T'], row['P']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

    ax.axhspan(40, 50, color='#f1c40f', alpha=0.3, label='Alvo (40-50%)')
    ax.axvline(x=terrenos_reais, color='#e74c3c', linestyle='--', label=f'Atual ({terrenos_reais}L)')
    ax.set_xlabel("Quantidade de Terrenos (Total do deck cravado em 99)")
    ax.set_ylabel("Chance de Sucesso (%)")
    ax.grid(alpha=0.2)
    ax.legend()
    
    # Renderiza o gráfico no Streamlit
    st.pyplot(fig)