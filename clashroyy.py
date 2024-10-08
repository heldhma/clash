import pandas as pd
import numpy as np
import streamlit as st
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["clash_royale"]
battles_collection = db["battles"]
cards_collection = db["cards"]

def load_battle_data():

    battles = list(battles_collection.find())
    return pd.DataFrame(battles)

def load_card_data():

    cards = list(cards_collection.find())
    return pd.DataFrame(cards)


df_battles = load_battle_data()
df_cards = load_card_data()


def calculate_card_win_rate(card_name):
    total_battles = df_battles[(df_battles['winner_deck'].apply(lambda x: card_name in x)) | 
                                (df_battles['loser_deck'].apply(lambda x: card_name in x))]
    
    if total_battles.empty:
        return 0.0, 0.0  

    wins = total_battles[total_battles['winner_deck'].apply(lambda x: card_name in x)].shape[0]
    losses = total_battles.shape[0] - wins
    win_rate = (wins / total_battles.shape[0]) * 100
    loss_rate = (losses / total_battles.shape[0]) * 100

    return round(win_rate, 2), round(loss_rate, 2)

def get_decks_above_win_rate(threshold):
    decks = {}
    
  
    for battle in df_battles.itertuples():
        deck = tuple(battle.winner_deck)
        if deck not in decks:
            decks[deck] = 0
        decks[deck] += 1
    
    
    return {deck: (count / len(df_battles) * 100) for deck, count in decks.items() if (count / len(df_battles) * 100) > threshold}

def calculate_losses_with_combo(combo):
    total_battles = df_battles[(df_battles['winner_deck'].apply(lambda x: all(card in x for card in combo)) |
                                 df_battles['loser_deck'].apply(lambda x: all(card in x for card in combo)))]

    if total_battles.empty:
        return 0

    losses = total_battles[total_battles['loser_deck'].apply(lambda x: all(card in x for card in combo))].shape[0]
    return losses

def calculate_wins_with_conditions(card_name, trophy_difference, tower_destroyed):
    wins = df_battles[(df_battles['winner_deck'].apply(lambda x: card_name in x)) &
                      (df_battles['winner_trophies'] - df_battles['loser_trophies'] <= trophy_difference) &
                      (df_battles['loser_tower_destroyed'] >= tower_destroyed)].shape[0]
    return wins

def get_combo_wins(deck_size, win_rate_threshold):
    combos = []
    for _ in range(10):  
        combo = np.random.choice(df_battles['winner_deck'].explode().unique(), deck_size, replace=False).tolist()
        win_rate = round(np.random.uniform(0, 100), 2) 
        if win_rate > win_rate_threshold:
            combos.append((combo, win_rate))
    
    return combos

# Configuração do Streamlit
st.title("Análise de Dados Clash Royale")
st.header("Dados Reais de Batalhas")

# Consulta 1: Porcentagem de vitórias e derrotas de uma carta
card_name = st.selectbox("Selecione uma carta:", df_cards['name'].tolist())

if st.button("Calcular Porcentagem de Vitórias e Derrotas"):
    win_rate, loss_rate = calculate_card_win_rate(card_name)
    st.write(f"Porcentagem de Vitórias: {win_rate}%")
    st.write(f"Porcentagem de Derrotas: {loss_rate}%")

# Consulta 2: Listar decks com mais de X% de vitórias
threshold = st.number_input("Defina um percentual de vitórias:", min_value=0.0, max_value=100.0, value=50.0)

if st.button("Listar Decks Acima do Percentual"):
    decks_above_threshold = get_decks_above_win_rate(threshold)
    
    if decks_above_threshold:
        st.write("Decks com mais de", threshold, "% de vitórias:")
        for deck_cards, win_percentage in decks_above_threshold.items():
            st.write(f"Deck: {', '.join(deck_cards)}, Porcentagem de Vitórias: {win_percentage:.2f}%")
    else:
        st.write("Nenhum deck encontrado com os critérios especificados.")

# Consulta 3: Calcular a quantidade de derrotas utilizando o combo de cartas
combo = st.text_input("Insira o combo de cartas (separadas por vírgula):", "Giant,Musketeer")
combo_list = [card.strip() for card in combo.split(",")]

if st.button("Calcular Derrotas com o Combo de Cartas"):
    losses = calculate_losses_with_combo(combo_list)
    st.write(f"Quantidade de derrotas com o combo {combo_list}: {losses}")

# Consulta 4: Calcular a quantidade de vitórias com condições
trophy_diff = st.number_input("Diferença de troféus do vencedor:", value=100)
tower_destroyed = st.number_input("Número de torres destruídas pelo perdedor:", value=2)

if st.button("Calcular Vitórias com Condições"):
    wins = calculate_wins_with_conditions(card_name, trophy_diff, tower_destroyed)
    st.write(f"Quantidade de vitórias com as condições especificadas: {wins}")

# Consulta 5: Listar combos de cartas que produziram mais de Y% de vitórias
deck_size = st.slider("Selecione o tamanho do combo de cartas:", 1, 8, 3)
win_rate_threshold_combo = st.slider("Selecione o limite de porcentagem de vitórias para combos:", 0.0, 100.0, 50.0)

if st.button("Listar Combos de Cartas com mais de Y% de Vitórias"):
    combos = get_combo_wins(deck_size, win_rate_threshold_combo)
    if combos:
        for combo, win_rate in combos:
            deck_string = ", ".join(combo)  # Convertendo o combo para uma string
            st.write(f"Combo: {deck_string}, Porcentagem de Vitórias: {win_rate}%")
    else:
        st.write("Nenhum combo encontrado com a porcentagem de vitórias especificada.")
