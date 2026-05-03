import streamlit as st
import random
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 0. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="MTG Commander Analytics", layout="wide")
st.title("🧙‍♂️ Analisador Dinâmico de Commander")
st.markdown("Simulador estatístico avançado focado na busca do **Sweet Spot** (Janela ideal sem *Screw* e sem *Flood*).")

if 'processar' not in st.session_state:
    st.session_state['processar'] = False
if 'deck_hash' not in st.session_state:
    st.session_state['deck_hash'] = None

simbolos_mana = {
    'W': '⚪ Branco (W)', 
    'U': '🔵 Azul (U)', 
    'B': '⚫ Preto (B)', 
    'R': '🔴 Vermelho (R)', 
    'G': '🟢 Verde (G)'
}

# ==========================================
# 1. FUNÇÕES TÉCNICAS (Cálculo e Simulação)
# ==========================================
def calcular_cmc_medio(curva_mana):
    total_cartas = sum(curva_mana.values())
    if total_cartas == 0: return 0
    return sum(cmc * qtd for cmc, qtd in curva_mana.items()) / total_cartas

def simular_sweet_spot(qtd_terrenos, qtd_ramp, alvo_efetivo, total_simulacoes):
    sucessos = 0
    # Regra de sobrevivência: Você precisa de no mínimo 2 terrenos para conjurar a maioria dos ramps (ou 1 se o alvo for muito agressivo)
    terrenos_minimos = min(2, alvo_efetivo) 
    
    for _ in range(total_simulacoes):
        # O deck agora tem 3 tipos de cartas: L (Terrenos), R (Ramp) e X (Mágicas normais)
        qtd_x = max(0, 99 - qtd_terrenos - qtd_ramp)
        deck = ['L'] * qtd_terrenos + ['R'] * qtd_ramp + ['X'] * qtd_x
        random.shuffle(deck)
        
        mao = deck[:7 + alvo_efetivo]
        terrenos_na_mao = mao.count('L')
        ramp_na_mao = mao.count('R')
        mana_total = terrenos_na_mao + ramp_na_mao
        
        # O Sweet Spot: Bater o alvo de mana somando Terrenos + Ramp (E ter terrenos suficientes para castar o ramp)
        if terrenos_na_mao >= terrenos_minimos and (alvo_efetivo <= mana_total <= alvo_efetivo + 1):
            sucessos += 1
            
    return (sucessos / total_simulacoes) * 100

# ==========================================
# 2. INTERFACE DINÂMICA (Barra Lateral)
# ==========================================
st.sidebar.header("⚙️ Configurações Principais")
cmc_comandante = st.sidebar.number_input("Custo do Comandante (CMC)", min_value=0, max_value=16, value=0, step=1)
# NOVO CAMPO: Informando ao simulador quantas cartas da sua lista geram mana
qtd_ramp = st.sidebar.number_input("Qtd de Pedras de Mana / Ramp", min_value=0, max_value=30, value=0, step=1, help="Ex: Sol Ring, Arcane Signet, Cultivate, Elfos de Mana. Eles assumem parte do peso dos terrenos.")

total_simulacoes = 15000

st.sidebar.divider()

defaults = {cmc: {'magicas': 0, 'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0} for cmc in range(0, 9)}
deck_data = {}
total_magicas_input = 0

st.sidebar.header("📝 Inserção do Deck")
st.sidebar.write("Atualiza instantaneamente ao tirar o cursor do campo.")

for cmc in range(0, 9):
    qtd_atual = st.session_state.get(f"mag_{cmc}", 0)
    
    with st.sidebar.expander(f"Cartas de Custo (CMC) {cmc} - {qtd_atual} cartas", expanded=(cmc == 1)):
        magicas = st.number_input(f"Qtd Mágicas (CMC {cmc})", min_value=0, max_value=99, value=defaults[cmc]['magicas'], step=1, key=f"mag_{cmc}")
        
        st.caption("Pips (Símbolos Coloridos):")
        c1, c2, c3, c4, c5 = st.columns(5)
        w = c1.number_input("⚪ W", min_value=0, value=defaults[cmc]['W'], step=1, key=f"w_{cmc}")
        u = c2.number_input("🔵 U", min_value=0, value=defaults[cmc]['U'], step=1, key=f"u_{cmc}")
        b = c3.number_input("⚫ B", min_value=0, value=defaults[cmc]['B'], step=1, key=f"b_{cmc}")
        r = c4.number_input("🔴 R", min_value=0, value=defaults[cmc]['R'], step=1, key=f"r_{cmc}")
        g = c5.number_input("🟢 G", min_value=0, value=defaults[cmc]['G'], step=1, key=f"g_{cmc}")
        
        total_magicas_input += magicas
        
        if magicas > 0:
            pips = {'W': w, 'U': u, 'B': b, 'R': r, 'G': g}
            pips_limpos = {cor: qtd for cor, qtd in pips.items() if qtd > 0}
            deck_data[cmc] = {'CMC': magicas, 'pips': pips_limpos}

if st.sidebar.button("🚀 Processar Simulação de Sweet Spot", use_container_width=True, type="primary"):
    st.session_state['processar'] = True
    st.session_state['deck_hash'] = hash(str(deck_data) + str(cmc_comandante) + str(qtd_ramp))

# ==========================================
# 3. LÓGICA DE IDENTIDADE E ALVO EFETIVO
# ==========================================
if total_magicas_input >= 99:
    st.error(f"🚨 **ERRO DE LIMITE:** Você inseriu {total_magicas_input} mágicas. O resultado deve cravar em 99 cartas.")
    st.stop()
elif total_magicas_input == 0:
    st.warning("👈 O seu deck está vazio! Insira as cartas na barra lateral.")
    st.stop()
elif qtd_ramp > total_magicas_input:
    st.error("🚨 Você não pode ter mais Ramps do que o total de mágicas do deck!")
    st.stop()

curva_simples = {custo: info['CMC'] for custo, info in deck_data.items()}
total_magicas = sum(curva_simples.values())
terrenos_reais = 99 - total_magicas
cmc_medio = calcular_cmc_medio(curva_simples)

if cmc_comandante <= 2:
    cmc_ajustado = 3
elif cmc_comandante >= 7:
    cmc_ajustado = cmc_comandante - 2
else:
    cmc_ajustado = cmc_comandante

alvo_efetivo = max(1, round((cmc_ajustado + cmc_medio + 1) / 2))

identidade_cores = set()
for info in deck_data.values():
    identidade_cores.update(info['pips'].keys())

pesos_cores = {cor: 0 for cor in identidade_cores}
for custo, info in deck_data.items():
    custo_base = max(1, custo) 
    urgencia = 1 / (custo_base ** 0.5) 
    for cor, pips in info['pips'].items():
        pesos_cores[cor] += pips * urgencia

current_hash = hash(str(deck_data) + str(cmc_comandante) + str(qtd_ramp))

# ==========================================
# 4. DASHBOARD DE RESULTADOS
# ==========================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Mágicas (Incluindo Ramp)", total_magicas)
col2.metric("Terrenos Restantes", terrenos_reais)
col3.metric("CMC Médio do Deck", f"{cmc_medio:.2f}")
col4.metric("🎯 Alvo Efetivo (Turno)", alvo_efetivo, help="Calculado pela tensão entre o CMC do Comandante e a curva do Deck.")

if st.session_state.get('processar') and st.session_state.get('deck_hash') != current_hash:
    st.warning("⚠️ Você alterou os dados do deck. O gráfico está oculto. Clique em **'Processar Simulação de Sweet Spot'** para recalcular.")

st.divider()

col_esquerda, col_direita = st.columns([1, 2])

with col_esquerda:
    st.subheader("🎨 Proporção Sugerida")
    total_pesos = sum(pesos_cores.values())
    if total_pesos > 0:
        for cor in sorted(pesos_cores.keys()):
            proporcao = pesos_cores[cor] / total_pesos
            fontes = round(proporcao * terrenos_reais)
            nome_cor_visual = simbolos_mana.get(cor, cor)
            st.write(f"**{nome_cor_visual}:** {fontes} fontes (Peso: {pesos_cores[cor]:.2f})")
    else:
        st.write("Deck Incolor ou sem pips cadastrados.")
    
    st.subheader(f"📊 Análise de Consistência")
    st.write(f"Buscando **{alvo_efetivo} ou {alvo_efetivo + 1} Fontes de Mana** (Terrenos + Ramp) no Turno **{alvo_efetivo}**:")
    
    if st.session_state.get('processar') and st.session_state.get('deck_hash') == current_hash:
        st.write("Configurações com maior equilíbrio (Pico do Sino):")
        
        resultados = []
        # O teto do range agora respeita o limite físico tirando as pedras de mana
        for t in range(max(0, terrenos_reais - 15), min(99 - qtd_ramp, terrenos_reais + 16)):
            p = simular_sweet_spot(t, qtd_ramp, alvo_efetivo, total_simulacoes)
            resultados.append((t, p))
            
        bons_resultados = [r for r in resultados if r[1] >= 40]
        for t, p in bons_resultados:
            check = " 🟢 **[ATUAL]**" if t == terrenos_reais else ""
            st.write(f"- **{p:.1f}%** -> {t} Lands / {99-t} Mágicas{check}")
            
        if not bons_resultados:
            st.write("Nenhuma configuração alcançou 40%+ de consistência. Seu deck precisa de mais ramp ou uma curva mais baixa.")
    else:
        st.write("_Aguardando processamento..._")

with col_direita:
    st.subheader("Curva de Sweet Spot (Formato de Sino)")
    st.markdown("*A penalidade de **Flood** e **Screw** faz a curva cair nas extremidades.*")
    
    if st.session_state.get('processar') and st.session_state.get('deck_hash') == current_hash:
        range_terrenos = list(range(max(0, terrenos_reais - 15), min(99 - qtd_ramp, terrenos_reais + 16)))
        
        with st.spinner('Executando 15.000 simulações de Monte Carlo...'):
            dados_grafico = [{'T': t, 'P': simular_sweet_spot(t, qtd_ramp, alvo_efetivo, total_simulacoes)} for t in range_terrenos]
            df = pd.DataFrame(dados_grafico)

        if not df.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(df['T'], df['P'], marker='o', color='#2ecc71', linewidth=2, label='Probabilidade de Sweet Spot')

            for i, row in df.iterrows():
                if i % 2 == 0 or row['T'] == terrenos_reais: 
                    ax.annotate(f"{row['P']:.1f}%", (row['T'], row['P']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

            ax.axvline(x=terrenos_reais, color='#e74c3c', linestyle='--', label=f'Atual ({terrenos_reais}L)')
            
            ax.set_title(f"Pico de Otimização para Turno {alvo_efetivo} (Combinação Comandante + Deck + {qtd_ramp} Ramps)", fontsize=10, pad=10)
            ax.set_xlabel("Quantidade de Terrenos (Deck cravado em 99)")
            ax.set_ylabel("Chance de Sweet Spot (%)")
            ax.grid(alpha=0.2)
            ax.legend(loc='lower right')
            plt.tight_layout()
            
            st.pyplot(fig)
        else:
            st.warning("Não foi possível gerar o gráfico para os valores atuais.")
    else:
        st.info("👈 Ajuste o seu deck na barra lateral e clique no botão azul **'Processar Simulação de Sweet Spot'** para calcular a curva em sino.")

# ==========================================
# 5. EXPLICAÇÃO MATEMÁTICA E DOCUMENTAÇÃO
# ==========================================
st.divider()

with st.expander("📚 Entenda a Matemática e a Lógica do Simulador"):
    st.markdown("""
    ### 1. O Método de Monte Carlo
    Em vez de usar fórmulas estatísticas fixas de combinatória (como a Distribuição Hipergeométrica), este simulador usa o **Método de Monte Carlo**. A cada clique em processar, o código cria um deck virtual na memória do servidor, embaralha as cartas, compra a mão inicial e simula a sua compra de turnos 15.000 vezes.

    ### 2. Pedras de Mana (Ramp) e a "Regra da Mão Morta"
    Decks competitivos de Commander rodam com ~35 terrenos porque compensam o restante com *Ramp* (Sol Ring, Signets, etc). O código entende isso e junta Terrenos + Ramp em um único "Pote de Mana".
    *   **A Mão Morta:** A simulação é inteligente o suficiente para saber que uma mão cheia de pedras de mana sem terrenos não funciona. Para a simulação dar sucesso, você deve atingir o Alvo Efetivo de mana, *porém*, tendo comprado no mínimo 2 terrenos reais para conseguir dar os primeiros passos no jogo.

    ### 3. O Cálculo do "Alvo Efetivo" (A Tensão entre Comandante e Deck)
    Simuladores comuns costumam sugerir terrenos focados em atingir mana em turnos altos, o que invariavelmente gera *Mana Flood*. Este painel calcula um alvo matemático dinâmico, baseado na teoria de *Floor and Ceiling* (Asfalto e Teto):
    *   **O Filtro do Comandante:** Comandantes muito baratos (CMC 0, 1 ou 2) são elevados para 3 na conta, assumindo que você precisa de mana para protegê-los. Comandantes caros (CMC 7 ou 8+) têm seu peso reduzido em 2, assumindo que a responsabilidade da rampa final passa a ser de *Mana Rocks*, não de *Land Drops*.
    *   **A Fórmula:** $$Alvo\_Efetivo=\\frac{CMC\_Comandante\_Ajustado + (CMC\_Medio\_Deck + 1)}{2}$$

    ### 4. A Janela do "Sweet Spot" (Gráfico em Formato de Sino)
    A mão avaliada deve ter:
    *   **No Mínimo:** A quantidade de Fontes do *Alvo Efetivo* (evitando o **Mana Screw**).
    *   **No Máximo:** O *Alvo Efetivo* mais 1 Fonte de segurança (evitando o **Mana Flood**).
    Essa limitação transforma o gráfico em um "Sino de Gauss", onde o pico mostra a zona perfeita para o seu deck rodar com consistência máxima sem comprar terrenos à toa.
    """)
