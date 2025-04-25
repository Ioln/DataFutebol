import streamlit as st
import pandas as pd
import io
import requests
import zipfile
import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.ndimage import gaussian_filter
from mplsoccer import Pitch

# CONFIGURAÇÃO DO SITE
st.set_page_config(page_title="DataFutebol", page_icon="df.png")
st.title("DataFutebol")
st.subheader("Estatísticas do Campeonato Brasileiro | Siga a gente no X/Twitter - @DataFutebol")

# ✅ CARREGAR DADOS DO ZIP
@st.cache_data
def carregar_dados():
    with zipfile.ZipFile("BRA25.zip", "r") as z:
        with z.open("BRA25.csv") as f:
            df = pd.read_csv(f)

    team_mapping = {
        1239: "Flamengo", 1234: "Palmeiras", 1221: "Bahia", 1219: "Internacional", 1230: "Cruzeiro",
        1227: "Botafogo", 1232: "Fluminense", 1226: "Vasco", 1237: "Corinthians", 1224: "São Paulo",
        1241: "Santos", 5438: "Red Bull Bragantino", 1235: "Atlético Mineiro", 2065: "Fortaleza",
        1231: "Sport", 1238: "Vitória", 1244: "Grêmio", 7334: "Ceará", 1220: "Juventude", 6332: "Mirassol",
    }

    df["teamName"] = df["teamId"].map(team_mapping)
    return df

df = carregar_dados()

# CALCULAR PPDA E FIELD TILT
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
                (dados_partida['type'].isin(['Tackle', 'Challenge', 'Interception']))
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
hot = cm.get_cmap('hot', 256)
newcolors = hot(np.linspace(0, 1, 256))
newcolors[0, -1] = 0
transparent_hot = ListedColormap(newcolors)

# --- NOVO: ESCOLHER PARTIDA OU CAMPEONATO ---
escopo = st.sidebar.radio("Escolher dados de:", ["Todo Campeonato", "Partida Específica"])

if escopo == "Partida Específica":
    df_partidas = df.drop_duplicates(subset=["matchId", "home", "away"])
    df_partidas["partida_nome"] = df_partidas["home"] + " (home) vs " + df_partidas["away"] + " (away)"
    partidas_disponiveis = df_partidas[["matchId", "partida_nome"]].dropna()
    partida_escolhida = st.sidebar.selectbox("Escolha a partida:", partidas_disponiveis["partida_nome"].values)
    match_id_escolhido = partidas_disponiveis[partidas_disponiveis["partida_nome"] == partida_escolhida]["matchId"].values[0]
    df_filtrado = df[df["matchId"] == match_id_escolhido]
else:
    df_filtrado = df

# LISTAS DE ESTATÍSTICAS
estatisticas_basicas = [
    "Passes", "Conduções", "Gols", "Passes no Terço Final",
    "Passes para impedimento", "Passes progressivos",
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
    passes_totais = df_filtrado[df_filtrado["type"] == "Pass"].groupby(agrupador).size()
    passes_certos = df_filtrado[(df_filtrado["type"] == "Pass") & (df_filtrado["outcomeType"] == "Successful")].groupby(agrupador).size()
    passes_errados = passes_totais - passes_certos
    aproveitamento = (passes_certos / passes_totais * 100).round(2)
    dados_final = pd.DataFrame({
        "Passes certos": passes_certos,
        "Passes errados": passes_errados,
        "Aproveitamento de passes (%)": aproveitamento
    }).reset_index()

elif estatistica_escolhida == "PPDA":
    dados_final = df_ppda_field_tilt.groupby("teamName")["PPDA"].mean().reset_index(name="PPDA")
elif estatistica_escolhida == "Field Tilt%":
    dados_final = df_ppda_field_tilt.groupby("teamName")["FieldTilt"].mean().reset_index(name="Field Tilt%")
elif estatistica_escolhida == "xThreat":
    dados_final = df_filtrado.groupby(agrupador)["xThreat"].sum().reset_index(name="xThreat")
else:
    # Ações básicas
    if estatistica_escolhida == "Conduções":
        filtro = df_filtrado[df_filtrado["type"] == "Carry"]
    elif estatistica_escolhida == "Gols":
        filtro = df_filtrado[df_filtrado["isGoal"] == True]
    elif estatistica_escolhida == "Passes no Terço Final":
        filtro = df_filtrado[(df_filtrado["type"] == "Pass") & (df_filtrado["x"] > 67)]
    elif estatistica_escolhida == "Passes para impedimento":
        filtro = df_filtrado[df_filtrado["type"] == "OffsidePass"]
    elif estatistica_escolhida == "Passes progressivos":
        filtro = df_filtrado[(df_filtrado["type"] == "Pass") & (df_filtrado["progressive_action"] == True)]
    elif estatistica_escolhida == "Duelos aéreos ganhos":
        filtro = df_filtrado[df_filtrado["duelAerialWon"] == True]
    elif estatistica_escolhida == "Duelos aéreos perdidos":
        filtro = df_filtrado[df_filtrado["duelAerialLost"] == True]
    elif estatistica_escolhida == "Cruzamentos precisos":
        filtro = df_filtrado[df_filtrado["passCrossAccurate"] == True]
    elif estatistica_escolhida == "Cruzamentos imprecisos":
        filtro = df_filtrado[df_filtrado["passCrossInaccurate"] == True]
    elif estatistica_escolhida == "Escanteios":
        filtro = df_filtrado[df_filtrado["passCorner"] == True]
    elif estatistica_escolhida == "Grandes Chances Perdidas":
        filtro = df_filtrado[df_filtrado["bigChanceMissed"] == True]
    elif estatistica_escolhida == "Grandes Chances Convertidas":
        filtro = df_filtrado[df_filtrado["bigChanceScored"] == True]
    elif estatistica_escolhida == "Grandes Chances Criadas":
        filtro = df_filtrado[df_filtrado["bigChanceCreated"] == True]
    
    dados_final = filtro.groupby(agrupador).size().reset_index(name=estatistica_escolhida)

# Renomear
dados_final.rename(columns={"playerName": "Jogador", "teamName": "Time"}, inplace=True)
st.dataframe(dados_final.sort_values(by=dados_final.columns[-1], ascending=False).reset_index(drop=True))

# VISUALIZAÇÃO NO CAMPO
st.markdown("---")
st.markdown("### Visualização no Campo")

if modo == "Jogadores":
    nome_busca = st.text_input("Digite o nome do jogador:")
    jogadores_disponiveis = df_filtrado["playerName"].dropna().unique()
    jogadores_filtrados = [j for j in jogadores_disponiveis if nome_busca.lower() in j.lower()]
    if jogadores_filtrados:
        escolhido = st.selectbox("Selecione o jogador encontrado:", jogadores_filtrados)
    else:
        escolhido = st.selectbox("Nenhum jogador encontrado. Veja todos:", jogadores_disponiveis)
    filtro_mapa = (df_filtrado["playerName"] == escolhido)

else:  # modo == "Times"
    times_disponiveis = df_filtrado["teamName"].dropna().unique()
    escolhido = st.selectbox("Selecione o time:", times_disponiveis)
    filtro_mapa = (df_filtrado["teamName"] == escolhido)

tipo_mapa = st.radio("Tipo de Mapa", ["Localização", "Em construção.."])
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

if stat_mapa in df_filtrado["type"].unique():
    dados_mapa = df_filtrado[filtro_mapa & (df_filtrado["type"] == stat_mapa)]
else:
    dados_mapa = df_filtrado[filtro_mapa & (df_filtrado[stat_mapa] == True)]

pitch = Pitch(pitch_type='opta')
fig, ax = plt.subplots(figsize=(10, 6))  # cria o ax manualmente

from scipy.ndimage import gaussian_filter

if tipo_mapa == "Localização":
    pitch.draw(ax=ax)  # desenha o campo antes
    if stat_mapa == "Carry":
        pitch.lines(dados_mapa["x"], dados_mapa["y"], dados_mapa["endX"], dados_mapa["endY"], transparent=True, comet=True, linestyle='--', ax=ax, color='blue', lw=2, alpha=0.7)
        pitch.scatter(dados_mapa["endX"], dados_mapa["endY"], ax=ax, color='blue', s=80, edgecolors='black')
    elif stat_mapa == "Pass":
        cores = dados_mapa["outcomeType"].apply(lambda x: 'green' if x == 'Successful' else 'red')
        pitch.arrows(dados_mapa["x"], dados_mapa["y"], dados_mapa["endX"], dados_mapa["endY"], ax=ax, color=cores, width=1, headwidth=4, alpha=0.8)
    else:
        pitch.scatter(dados_mapa["x"], dados_mapa["y"], ax=ax, color='green', s=80, edgecolors='black')
    pitch.draw(ax=ax)    

qtd = len(dados_mapa)
ax.set_title(f"Mapa de {acoes_mapa} do {'Jogador' if modo == 'Jogadores' else 'Time'} {escolhido} no Brasileirão", fontsize=18)

st.pyplot(fig)
