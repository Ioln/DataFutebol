
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from mplsoccer import Pitch

# CONFIGURAÇÃO DO SITE
st.set_page_config(page_title="DataFutebol", page_icon="df.png")
st.title("DataFutebol")
st.subheader("Estatísticas do Campeonato Brasileiro | Siga a gente no X/Twitter - @DataFutebol")

# FUNÇÃO PARA CARREGAR DADOS
@st.cache_data
def carregar_dados():
    df = pd.read_csv('BRA25.csv')

    team_mapping = {
        1239: "Flamengo", 1234: "Palmeiras", 1221: "Bahia", 1219: "Internacional", 1230: "Cruzeiro",
        1227: "Botafogo", 1232: "Fluminense", 1226: "Vasco", 1237: "Corinthians", 1224: "São Paulo",
        1241: "Santos", 5438: "Red Bull Bragantino", 1235: "Atlético Mineiro", 2065: "Fortaleza",
        1231: "Sport", 1238: "Vitória", 1244: "Grêmio", 7334: "Ceará", 1220: "Juventude", 6332: "Mirassol",
    }
    df["teamName"] = df["teamId"].map(team_mapping)
    return df

df = carregar_dados()

# FUNÇÃO PARA CALCULAR PPDA E FIELD TILT
@st.cache_data
def calcular_ppda_field_tilt(df):
    resultados = []
    if df['x'].max() <= 1.0:
        df['x'] *= 100
        df['y'] *= 100

    for match_id in df['matchId'].unique():
        dados_partida = df[df['matchId'] == match_id]
        times = dados_partida['teamName'].dropna().unique()

        if len(times) < 2:
            continue

        team_a, team_b = times

        for time in [team_a, team_b]:
            adversario = team_b if time == team_a else team_a

            acoes_defensivas = dados_partida[
                (dados_partida['teamName'] == time) &
                (dados_partida['x'] > 60) &
                (dados_partida['type'].isin(['Tackle', 'Challenge', 'Interception', 'Foul']))
            ]

            passes_cedidos = dados_partida[
                (dados_partida['teamName'] == adversario) &
                (dados_partida['x'] < 40) &
                (dados_partida['type'] == 'Pass') &
                (dados_partida['outcomeType'] == 'Successful')
            ]

            passes_ataque_time = dados_partida[
                (dados_partida['teamName'] == time) &
                (dados_partida['x'] > 67) &
                (dados_partida['type'] == 'Pass')
            ]

            passes_ataque_adv = dados_partida[
                (dados_partida['teamName'] == adversario) &
                (dados_partida['x'] > 67) &
                (dados_partida['type'] == 'Pass')
            ]

            total_defensive = len(acoes_defensivas)
            total_passes_adv = len(passes_cedidos)
            total_passes_attack = len(passes_ataque_time) + len(passes_ataque_adv)

            ppda = total_passes_adv / total_defensive if total_defensive > 0 else np.inf
            field_tilt = len(passes_ataque_time) / total_passes_attack if total_passes_attack > 0 else 0

            resultados.append({
                'teamName': time,
                'PPDA': round(ppda, 2),
                'FieldTilt': round(field_tilt * 100, 2)
            })

    return pd.DataFrame(resultados)

df_ppda_field_tilt = calcular_ppda_field_tilt(df)

# CRIAR COLORMAP "hot" TRANSPARENTE
from matplotlib import cm
hot = cm.get_cmap('hot', 256)
newcolors = hot(np.linspace(0, 1, 256))
newcolors[0, -1] = 0  # Transparente para valor 0
transparent_hot = ListedColormap(newcolors)

# LISTAS DE ESTATÍSTICAS
estatisticas_basicas = [
    "Passes", "Conduções", "Gols", "Passes no Terço Final",
    "Passes certos", "Passes errados", "Aproveitamento de passes (%)",
    "Faltas", "Passes em impedimento", "Passes progressivos",
    "Duelos aéreos ganhos", "Duelos aéreos perdidos",
    "Cruzamentos precisos", "Cruzamentos imprecisos", "Escanteios"
]

estatisticas_avancadas_times = ["PPDA", "Field Tilt%"]
estatisticas_avancadas_jogadores = ["xThreat", "Grandes Chances Perdidas", "Grandes Chances Convertidas", "Grandes Chances Criadas"]

# SIDEBAR
modo = st.sidebar.selectbox("Modo de visualização", ["Jogadores", "Times"])
categoria = st.sidebar.radio("Categoria", ["Estatísticas", "Estatísticas Avançadas"])

if categoria == "Estatísticas":
    estatisticas = estatisticas_basicas
else:
    estatisticas = estatisticas_avancadas_times if modo == "Times" else estatisticas_avancadas_jogadores

estatistica_escolhida = st.selectbox("Escolha a estatística", estatisticas)

# CRIAÇÃO DAS TABELAS
if modo == "Jogadores":
    agrupador = ["playerName", "teamName"]
else:
    agrupador = ["teamName"]

if estatistica_escolhida == "Passes":
    passes_totais = df[df["type"] == "Pass"].groupby(agrupador).size()
    passes_certos = df[(df["type"] == "Pass") & (df["outcomeType"] == "Successful")].groupby(agrupador).size()
    passes_errados = passes_totais - passes_certos
    aproveitamento = (passes_certos / passes_totais * 100).round(2)
    dados_final = pd.DataFrame({
        "Passes certos": passes_certos,
        "Passes errados": passes_errados,
        "Aproveitamento de passes (%)": aproveitamento
    }).reset_index()

elif estatistica_escolhida == "Aproveitamento de passes (%)":
    passes_totais = df[df["type"] == "Pass"].groupby(agrupador).size()
    passes_certos = df[(df["type"] == "Pass") & (df["outcomeType"] == "Successful")].groupby(agrupador).size()
    aproveitamento = (passes_certos / passes_totais * 100).round(2)
    dados_final = aproveitamento.reset_index(name="Aproveitamento de passes (%)")

elif estatistica_escolhida == "PPDA":
    dados_final = df_ppda_field_tilt.groupby("teamName")["PPDA"].mean().reset_index(name="PPDA")
elif estatistica_escolhida == "Field Tilt%":
    dados_final = df_ppda_field_tilt.groupby("teamName")["FieldTilt"].mean().reset_index(name="Field Tilt%")
elif estatistica_escolhida == "xThreat":
    dados_final = df.groupby(agrupador)["xThreat"].sum().reset_index(name="xThreat")
else:
    # Geral para ações básicas
    if estatistica_escolhida == "Conduções":
        filtro = df[df["type"] == "Carry"]
    elif estatistica_escolhida == "Gols":
        filtro = df[df["isGoal"] == True]
    elif estatistica_escolhida == "Passes no Terço Final":
        filtro = df[(df["type"] == "Pass") & (df["x"] > 67)]
    elif estatistica_escolhida == "Faltas":
        filtro = df[df["type"] == "Foul"]
    elif estatistica_escolhida == "Passes em impedimento":
        filtro = df[df["type"] == "OffsidePass"]
    elif estatistica_escolhida == "Passes progressivos":
        filtro = df[(df["type"] == "Pass") & (df["progressive_action"] == True)]
    elif estatistica_escolhida == "Duelos aéreos ganhos":
        filtro = df[df["duelAerialWon"] == True]
    elif estatistica_escolhida == "Duelos aéreos perdidos":
        filtro = df[df["duelAerialLost"] == True]
    elif estatistica_escolhida == "Cruzamentos precisos":
        filtro = df[df["passCrossAccurate"] == True]
    elif estatistica_escolhida == "Cruzamentos imprecisos":
        filtro = df[df["passCrossInaccurate"] == True]
    elif estatistica_escolhida == "Escanteios":
        filtro = df[df["passCorner"] == True]
    elif estatistica_escolhida == "Grandes Chances Perdidas":
        filtro = df[df["bigChanceMissed"] == True]
    elif estatistica_escolhida == "Grandes Chances Convertidas":
        filtro = df[df["bigChanceScored"] == True]
    elif estatistica_escolhida == "Grandes Chances Criadas":
        filtro = df[df["bigChanceCreated"] == True]
    
    dados_final = filtro.groupby(agrupador).size().reset_index(name=estatistica_escolhida)

# Renomear
dados_final.rename(columns={"playerName": "Jogador", "teamName": "Time"}, inplace=True)
st.dataframe(dados_final.sort_values(by=dados_final.columns[-1], ascending=False).reset_index(drop=True))

# VISUALIZAÇÃO NO CAMPO
st.markdown("---")
st.markdown("### Visualização no Campo")

nome_busca = st.text_input("Digite o nome do jogador:")
jogadores_disponiveis = df["playerName"].dropna().unique()
jogadores_filtrados = [j for j in jogadores_disponiveis if nome_busca.lower() in j.lower()]

if jogadores_filtrados:
    jogador = st.selectbox("Selecione o jogador encontrado:", jogadores_filtrados)
else:
    jogador = st.selectbox("Nenhum jogador encontrado. Veja todos:", jogadores_disponiveis)

tipo_mapa = st.radio("Tipo de Mapa", ["Localização", "Heatmap"])
acoes_mapa = st.selectbox("Escolha o tipo de ação", ["Passes", "Conduções", "Finalizações", "Recuperações de bola", "Desarmes", "Interceptações", "Passes-chave"])

traduzir = {
    "Passes": "Pass",
    "Conduções": "Carry",
    "Finalizações": "isShot",
    "Recuperações de bola": "BallRecovery",
    "Desarmes": "Tackle",
    "Interceptações": "Interception",
    "Passes-chave": "keyPass"
}
stat_mapa = traduzir[acoes_mapa]

if stat_mapa in df["type"].unique():
    dados_mapa = df[(df["playerName"] == jogador) & (df["type"] == stat_mapa)]
else:
    dados_mapa = df[(df["playerName"] == jogador) & (df[stat_mapa] == True)]

pitch = Pitch(pitch_type='opta')
fig, ax = pitch.draw(figsize=(10, 6))

if tipo_mapa == "Localização":
    if stat_mapa == "Carry":
        pitch.lines(dados_mapa["x"], dados_mapa["y"], dados_mapa["endX"], dados_mapa["endY"], transparent=True, comet=True, linestyle = '--', ax=ax, color='blue', lw=2, alpha=0.7)
        pitch.scatter(dados_mapa["endX"], dados_mapa["endY"], ax=ax, color='blue', s=80, edgecolors='black')
    elif stat_mapa == "Pass":
        cores = dados_mapa["outcomeType"].apply(lambda x: 'green' if x == 'Successful' else 'red')
        pitch.arrows(dados_mapa["x"], dados_mapa["y"], dados_mapa["endX"], dados_mapa["endY"], ax=ax, color=cores, width=1, headwidth=4, alpha=0.8)
    else:
        pitch.scatter(dados_mapa["x"], dados_mapa["y"], ax=ax, color='green', s=80, edgecolors='black')
else:
    bin_statistic = pitch.bin_statistic(dados_mapa["x"], dados_mapa["y"], statistic="count", bins=(30, 20))
    pitch.heatmap(bin_statistic, ax=ax, cmap=transparent_hot, alpha=0.5)

qtd = len(dados_mapa)
ax.set_title(f"Mapa de {acoes_mapa} do {jogador} no Brasileirão", fontsize=18)

st.pyplot(fig)

