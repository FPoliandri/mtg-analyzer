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
# 1. FUNÇÕES TÉCNICAS (Cálculo e Simulação)
# ==========================================
def calcular_cmc_medio(curva_mana):
    total_cartas = sum(curva_mana.values())
    if total_cartas == 0: return 0
    return sum(cmc * qtd for cmc, qtd in curva_mana.items()) / total_cartas

def simular_land_drops(qtd_terrenos, turnos_alvo, total_simulacoes):
    sucessos = 0
    for _ in range(total_simulacoes):
        # O deck é um sistema fechado de 99 cartas
        deck = ['L'] * qtd_terrenos + ['X'] * (99 - qtd_terrenos)
        random.shuffle(deck)
        # Mão inicial (7) + compras por turno
        mao = deck[:7 + turnos_alvo]
        if mao.count('L') >= turnos_alvo:
            sucessos += 1
    return (sucessos / total_simulacoes) * 100

# ==========================================
# 2. INTERFACE DINÂMICA (Sidebar e Tabela)
# ==========================================
st.sidebar.header("⚙️ Configurações da Simulação")
turno_alvo = st.sidebar.slider("Turno Alvo para Drop de Terreno", min_value=1, max_value=10, value=5)
total_simulacoes = st.sidebar.slider("Resolução (Simulações)", min_value=1000, max_value=20000, step=1000, value=10000)

st.sidebar.divider()
st.sidebar.header("📝 Inserção do Deck")
st.sidebar.write("Preencha a quantidade de mágicas e os pips (símbolos coloridos) por custo (CMC):")

# Tabela inicial (Exemplo)
dados_iniciais = pd.DataFrame({
    "CMC": [1, 2, 3, 4, 5, 6, 7, 8],
    "Mágicas": [6, 22, 18, 12, 6, 0, 0, 1],
    "W (Branco)": [0, 0, 0, 0, 0, 0, 0, 0],
    "U (Azul)": [0, 0, 0, 0, 0, 0, 0, 0],
    "B (Preto)": [0, 0, 0, 0, 0, 0, 0, 0],
    "R (Verm)": [2, 21, 7, 11, 5, 4, 0, 2],
    "G (Verde)": [3, 5, 16, 5, 3, 0, 0, 0]
})

# Transformando o DataFrame em uma planilha editável na tela
deck_df = st.sidebar.data_editor(dados_iniciais, hide_index=True, use_container_width=True)

# Lógica de Proteção: O deck não pode exceder as 99 cartas (sem contar o comandante)
total_magicas_input = deck_df["Mágicas"].sum()
if total_magicas_input >= 99:
    st.sidebar.error(f"🚨 **ERRO:** {total_magicas_input} mágicas inseridas. Reduza para abrir espaço para terrenos.")
    st.error("O cálculo exige que o deck principal tenha no máximo 98 cartas (para sobrar pelo menos 1 espaço de terreno, totalizando 99). Ajuste os valores na tabela lateral para continuar.")
    st.stop() # Trava o aplicativo aqui e não renderiza os gráficos com erro

# ==========================================
# 3. LÓGICA DE IDENTIDADE E URGÊNCIA
# ==========================================
# Convertendo a tabela de volta para o formato de dicionário
deck_data = {}
for index, row in deck_df.iterrows():
    cmc = int(row["CMC"])
    cartas = int(row["Mágicas"])
    if cartas > 0: # Ignora linhas zeradas
        pips = {
            'W': int(row["W (Branco)"]), 
            'U': int(row["U (Azul)"]),
            'B': int(row["B (Preto)"]), 
            'R': int(row["R (Verm)"]), 
            'G': int(row["G (Verde)"])
        }
        # Limpa as cores zeradas
        pips_limpos = {cor: qtd for cor, qtd in pips.items() if qtd > 0}
        deck_data[cmc] = {'CMC': cartas, 'pips': pips_limpos}

curva_simples = {custo: info['CMC'] for custo, info in deck_data.items()}
total_magicas = sum(curva_simples.values())
terrenos_reais = 99 - total_magicas
cmc_medio = calcular_cmc_medio(curva_simples)

identidade_cores = set()
for info in deck_data.values():
    identidade_cores.update(info['pips'].keys())

# Cálculo de Pesos (Correlação Cor vs CMC)
pesos_cores = {cor: 0 for cor in identidade_cores}
for custo, info in deck_data.items():
    urgencia = 1 / (custo ** 0.5) # CMC baixo = Peso maior
    for cor, pips in info['pips'].items():
        pesos_cores[cor] += pips * urgencia

# ==========================================
# 4. DASHBOARD DE RESULTADOS
# ==========================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Mágicas", total_magicas)
col2.metric("Espaços para Terrenos", terrenos_reais)
col3.metric("CMC Médio", f"{cmc_medio:.2f}")
col4.metric("Identidade", ", ".join(sorted(identidade_cores)) if identidade_cores else "Incolor")

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
    else:
        st.write("Deck Incolor ou sem pips cadastrados.")
    
    st.subheader(f"🎯 Análise (Turno {turno_alvo})")
    st.write("Configurações que atingem 40-50% de sucesso:")
    
    # Busca dinamicamente os valores de probabilidade aceitáveis
    for t in range(max(20, terrenos_reais - 15), min(60, terrenos_reais + 15)):
        p = simular_land_drops(t, turno_alvo, total_simulacoes)
        if 40 <= p <= 50:
            check = " 🟢 **[ATUAL]**" if t == terrenos_reais else ""
            st.write(f"- **{p:.1f}%** -> {t} Lands / {99-t} Mágicas{check}")

with col_direita:
    # ==========================================
    # 5. VISUALIZAÇÃO DE DADOS (Gráfico)
    # ==========================================
    st.subheader("Curva de Probabilidade")
    range_terrenos = list(range(max(20, terrenos_reais - 8), min(60, terrenos_reais + 8)))
    
    with st.spinner('Executando simulações de Monte Carlo...'):
        dados_grafico = [{'T': t, 'P': simular_land_drops(t, turno_alvo, total_simulacoes)} for t in range_terrenos]
        df = pd.DataFrame(dados_grafico)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df['T'], df['P'], marker='o', color='#2c3e50', linewidth=2, label='Curva de Probabilidade')

    # Adicionando rótulos nos pontos do gráfico
    for i, row in df.iterrows():
        ax.annotate(f"{row['P']:.1f}%", (row['T'], row['P']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

    ax.axhspan(40, 50, color='#f1c40f', alpha=0.3, label='Alvo (40-50%)')
    ax.axvline(x=terrenos_reais, color='#e74c3c', linestyle='--', label=f'Atual ({terrenos_reais}L)')
    
    ax.set_title(f"Probabilidade de garantir {turno_alvo} Terrenos no Turno {turno_alvo}", fontsize=10, pad=10)
    ax.set_xlabel("Quantidade de Terrenos (Total do deck cravado em 99)")
    ax.set_ylabel("Chance de Sucesso (%)")
    ax.grid(alpha=0.2)
    ax.legend(loc='lower right')
    plt.tight_layout()
    
    st.pyplot(fig)
