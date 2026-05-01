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

# Memória do aplicativo para saber quando rodar o gráfico
if 'processar' not in st.session_state:
    st.session_state['processar'] = False
if 'deck_hash' not in st.session_state:
    st.session_state['deck_hash'] = None

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
        deck = ['L'] * qtd_terrenos + ['X'] * (99 - qtd_terrenos)
        random.shuffle(deck)
        mao = deck[:7 + turnos_alvo]
        if mao.count('L') >= turnos_alvo:
            sucessos += 1
    return (sucessos / total_simulacoes) * 100

# ==========================================
# 2. INTERFACE DINÂMICA (Sem Formulário)
# ==========================================
st.sidebar.header("⚙️ Configurações da Simulação")
turno_alvo = st.sidebar.slider("Turno Alvo para Drop de Terreno", min_value=1, max_value=10, value=5)
total_simulacoes = st.sidebar.slider("Resolução (Simulações)", min_value=1000, max_value=20000, step=1000, value=10000)

st.sidebar.divider()

defaults = {cmc: {'magicas': 0, 'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0} for cmc in range(0, 9)}
deck_data = {}
total_magicas_input = 0

st.sidebar.header("📝 Inserção do Deck")
st.sidebar.write("Os dados e títulos atualizam instantaneamente ao tirar o cursor do campo.")

# O 'for' agora está livre (fora do st.form), então reage na mesma hora!
for cmc in range(0, 9):
    qtd_atual = st.session_state.get(f"mag_{cmc}", 0)
    
    with st.sidebar.expander(f"Cartas de Custo (CMC) {cmc} - {qtd_atual} cartas", expanded=(cmc == 1)):
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

st.sidebar.info("💡 Dica: Remover cartas de custo alto ajusta a curva de mana de forma eficiente.")

# O Botão serve como um "gatilho" para a matemática pesada
if st.sidebar.button("🚀 Processar Simulação Gráfica", use_container_width=True, type="primary"):
    st.session_state['processar'] = True
    # Criamos um "carimbo" (hash) da configuração exata no momento do clique
    st.session_state['deck_hash'] = hash(str(deck_data) + str(turno_alvo) + str(total_simulacoes))

# ==========================================
# 3. LÓGICA DE IDENTIDADE (Instantânea)
# ==========================================
if total_magicas_input >= 99:
    st.error(f"🚨 **ERRO DE LIMITE:** Você inseriu {total_magicas_input} mágicas. O resultado deve cravar em 99 cartas no total.")
    st.stop()
elif total_magicas_input == 0:
    st.warning("👈 O seu deck está vazio! Insira as cartas na barra lateral.")
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
    custo_base = max(1, custo) 
    urgencia = 1 / (custo_base ** 0.5) 
    for cor, pips in info['pips'].items():
        pesos_cores[cor] += pips * urgencia

# Comparamos o deck atual com o deck do último clique no botão
current_hash = hash(str(deck_data) + str(turno_alvo) + str(total_simulacoes))

# ==========================================
# 4. DASHBOARD DE RESULTADOS
# ==========================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Mágicas", total_magicas)
col2.metric("Espaços para Terrenos", terrenos_reais)
col3.metric("CMC Médio", f"{cmc_medio:.2f}")
col4.metric("Identidade", ", ".join(sorted(identidade_cores)) if identidade_cores else "Incolor")

# Aviso se o usuário mudou um valor após já ter gerado um gráfico
if st.session_state.get('processar') and st.session_state.get('deck_hash') != current_hash:
    st.warning("⚠️ Você alterou os dados do deck. O gráfico está oculto. Clique em **'Processar Simulação Gráfica'** para recalcular.")

st.divider()

col_esquerda, col_direita = st.columns([1, 2])

with col_esquerda:
    # A sugestão de cores é matemática leve, aparece na hora!
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
    
    # A análise de alvo é pesada, só aparece se o botão foi clicado
    if st.session_state.get('processar') and st.session_state.get('deck_hash') == current_hash:
        st.write("Configurações que atingem 40-50% de sucesso:")
        for t in range(max(0, terrenos_reais - 15), min(100, terrenos_reais + 16)):
            p = simular_land_drops(t, turno_alvo, total_simulacoes)
            if 40 <= p <= 50:
                check = " 🟢 **[ATUAL]**" if t == terrenos_reais else ""
                st.write(f"- **{p:.1f}%** -> {t} Lands / {99-t} Mágicas{check}")
    else:
        st.write("_Aguardando processamento..._")

with col_direita:
    st.subheader("Curva de Probabilidade")
    
    # O Gráfico é pesado, só aparece se o botão foi clicado
    if st.session_state.get('processar') and st.session_state.get('deck_hash') == current_hash:
        range_terrenos = list(range(max(0, terrenos_reais - 10), min(100, terrenos_reais + 11)))
        
        with st.spinner('Executando simulações de Monte Carlo...'):
            dados_grafico = [{'T': t, 'P': simular_land_drops(t, turno_alvo, total_simulacoes)} for t in range_terrenos]
            df = pd.DataFrame(dados_grafico)

        if not df.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(df['T'], df['P'], marker='o', color='#2c3e50', linewidth=2, label='Curva de Probabilidade')

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
        else:
            st.warning("Não foi possível gerar o gráfico para os valores atuais.")
    else:
        st.info("👈 Ajuste o seu deck na barra lateral e clique no botão azul **'Processar Simulação Gráfica'** para gerar os cálculos complexos.")
