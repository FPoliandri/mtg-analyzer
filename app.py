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
# 2. INTERFACE DINÂMICA (Formulário com Botões)
# ==========================================
st.sidebar.header("⚙️ Configurações da Simulação")
turno_alvo = st.sidebar.slider("Turno Alvo para Drop de Terreno", min_value=1, max_value=10, value=5)
total_simulacoes = st.sidebar.slider("Resolução (Simulações)", min_value=1000, max_value=20000, step=1000, value=10000)

st.sidebar.divider()

# Dados padrão (Agora inicializando tudo zerado)
defaults = {cmc: {'magicas': 0, 'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0} for cmc in range(0, 9)}

deck_data = {}
total_magicas_input = 0

# Criando o formulário (só processa quando o botão final é clicado)
with st.sidebar.form("deck_form"):
    st.header("📝 Inserção do Deck")
    st.write("Ajuste as quantidades usando os botões de **+** e **-**")
    
    # Loop de 0 a 8 para cobrir todos os CMCs
    for cmc in range(0, 9):
        # Lê a memória do site para pegar o valor atual (se não existir, é 0)
        qtd_atual = st.session_state.get(f"mag_{cmc}", 0)
        
        # O título agora mostra o número de cartas de forma dinâmica
        with st.expander(f"Cartas de Custo (CMC) {cmc} - {qtd_atual} cartas", expanded=(cmc == 1)):
            magicas = st.number_input(f"Qtd Mágicas (CMC {cmc})", min_value=0, max_value=99, value=defaults[cmc]['magicas'], step=1, key=f"mag_{cmc}")
            
            st.caption("Pips (Símbolos Coloridos):")
            c1, c2, c3, c4, c5 = st.columns(5)
            w = c1.number_input("W", min_value=0, value=defaults[cmc]['W'], step=1, key=f"w_{cmc}")
            u = c2.number_input("U", min_value=0, value=defaults[cmc]['U'], step=1, key=f"u_{cmc}")
            b = c3.number_input("B", min_value=0, value=defaults[cmc]['B'], step=1, key=f"b_{cmc}")
            r = c4.number_input("R", min_value=0, value=defaults[cmc]['R'], step=1, key=f"r_{cmc}")
            g = c5.number_input("G", min_value=0, value=defaults[cmc]['G'], step=1, key=f"g_{cmc}")
            
            total_magicas_input += magicas
            
            if magicas > 0:
                pips = {'W': w, 'U': u, 'B': b, 'R': r, 'G': g}
                pips_limpos = {cor: qtd for cor, qtd in pips.items() if qtd > 0}
                deck_data[cmc] = {'CMC': magicas, 'pips': pips_limpos}

    st.info("💡 Dica de Deckbuilding: Se precisar remover mágicas para incluir mais terrenos, retirar cartas de custo alto afeta a curva de mana de forma muito mais eficiente do que remover feitiços aleatórios.")
    
    # O botão que dispara tudo
    submit_button = st.form_submit_button("🚀 Processar Simulação", use_container_width=True)

# ==========================================
# 3. LÓGICA DE IDENTIDADE E URGÊNCIA
# ==========================================
# Trava de Segurança
if total_magicas_input >= 99:
    st.error(f"🚨 **ERRO DE LIMITE:** Você inseriu {total_magicas_input} mágicas. O resultado final deve obrigatoriamente cravar em 99 cartas no total. Reduza a quantidade de mágicas na barra lateral para abrir espaço para os terrenos e clique em Processar novamente.")
    st.stop()
elif total_magicas_input == 0:
    st.warning("👈 O seu deck está vazio! Insira as quantidades de mágicas e pips na barra lateral e clique em 'Processar Simulação'.")
    st.stop()

curva_simples = {custo: info['CMC'] for custo, info in deck_data.items()}
total_magicas = sum(curva_simples.values())
terrenos_reais = 99 - total_magicas
cmc_medio = calcular_cmc_medio(curva_simples)

identidade_cores = set()
for info in deck_data.values():
    identidade_cores.update(info['pips'].keys())

pesos_cores = {cor: 0 for cor in identidade_cores}
for custo, info in deck_data.items():
    # Proteção contra erro de divisão por zero (cartas de custo 0)
    custo_base = max(1, custo) 
    urgencia = 1 / (custo_base ** 0.5) 
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
    
    for t in range(max(20, terrenos_reais - 15), min(60, terrenos_reais + 15)):
        p = simular_land_drops(t, turno_alvo, total_simulacoes)
        if 40 <= p <= 50:
            check = " 🟢 **[ATUAL]**" if t == terrenos_reais else ""
            st.write(f"- **{p:.1f}%** -> {t} Lands / {99-t} Mágicas{check}")

with col_direita:
    # ==========================================
    # 5. VISUALIZAÇÃO GRÁFICA
    # ==========================================
    st.subheader("Curva de Probabilidade")
    range_terrenos = list(range(max(20, terrenos_reais - 8), min(60, terrenos_reais + 8)))
    
    with st.spinner('Executando simulações...'):
        dados_grafico = [{'T': t, 'P': simular_land_drops(t, turno_alvo, total_simulacoes)} for t in range_terrenos]
        df = pd.DataFrame(dados_grafico)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df['T'], df['P'], marker='o', color='#2c3e50', linewidth=2, label='Curva de Probabilidade')

    for i, row in df.iterrows():
        ax.annotate(f"{row['P']:.1f}%", (row['T'], row['P']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

    ax.axhspan(40, 50, color='#f1c40f', alpha=0.3, label='Alvo (40-50%)')
    ax.axvline(x=terrenos_reais, color='#e74c3c', linestyle='--', label=f'Atual ({terrenos_reais}L)')
    
    ax.set_title(f"Probabilidade de garantir {turno_alvo} Terrenos no Turno {turno_alvo}", fontsize=10, pad=10)
    ax.set_xlabel("Quantidade de Terrenos (Total do deck sempre cravado em 99)")
    ax.set_ylabel("Chance de Sucesso (%)")
    ax.grid(alpha=0.2)
    ax.legend(loc='lower right')
    plt.tight_layout()
    
    st.pyplot(fig)
