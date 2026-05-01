# Dados padrão (Gruul) para carregar inicialmente
defaults = {
    0: {'magicas': 0, 'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0}, # <-- Linha nova
    1: {'magicas': 6, 'W': 0, 'U': 0, 'B': 0, 'R': 2, 'G': 3},
    2: {'magicas': 22, 'W': 0, 'U': 0, 'B': 0, 'R': 21, 'G': 5},
    3: {'magicas': 18, 'W': 0, 'U': 0, 'B': 0, 'R': 7, 'G': 16},
    4: {'magicas': 12, 'W': 0, 'U': 0, 'B': 0, 'R': 11, 'G': 5},
    5: {'magicas': 6, 'W': 0, 'U': 0, 'B': 0, 'R': 5, 'G': 3},
    6: {'magicas': 0, 'W': 0, 'U': 0, 'B': 0, 'R': 4, 'G': 0},
    7: {'magicas': 0, 'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0},
    8: {'magicas': 1, 'W': 0, 'U': 0, 'B': 0, 'R': 2, 'G': 0},
}

deck_data = {}
total_magicas_input = 0

# Criando o formulário (só processa quando o botão final é clicado)
with st.sidebar.form("deck_form"):
    st.header("📝 Inserção do Deck")
    st.write("Ajuste as quantidades usando os botões de **+** e **-**")
    
    # A MUDANÇA ESTÁ AQUI: range de 0 a 9 em vez de 1 a 9
    for cmc in range(0, 9):
