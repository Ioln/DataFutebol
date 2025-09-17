import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.image as mpimg
from mplsoccer import Pitch, VerticalPitch
from highlight_text import ax_text
import numpy as np
from adjustText import adjust_text
from scipy.stats import percentileofscore, rankdata

# ===========================
# CARREGAR DADOS (lazy load)
# ===========================
@st.cache_data
def carregar_dados():
    arquivo = "BRA25.parquet"
    if os.path.exists(arquivo):
        return pd.read_parquet(arquivo)
    else:
        st.error("Arquivo BRA25.parquet não encontrado no repositório!")
        return pd.DataFrame()  # retorna vazio se não achar


# ===========================
# APP
# ===========================
st.sidebar.title("Menu")
menu_option = st.sidebar.radio("Navegação", ["Visualizações", "Rankings", "Comparação", "Contato"])

st.subheader("👋 Seja bem-vindo ao aplicativo do DataFutebol")
st.markdown("Nos siga nas Redes Sociais → **@DataFutebol** | Apoie o projeto! Chave Pix-> iolncant@gmail.com")

# 🔑 Só carrega os dados quando precisar
if menu_option in ["Visualizações", "Rankings", "Comparação"]:
    df = carregar_dados()

    if df.empty:
        st.stop()  # encerra se não achou os dados

df = carregar_dados()

team_mapping = {
    1239: "Flamengo",
    1234: "Palmeiras",
    1221: "Bahia",
    1219: "Internacional",
    1230: "Cruzeiro",
    1227: "Botafogo",
    1232: "Fluminense",
    1226: "Vasco",
    1237: "Corinthians",
    1224: "São Paulo",
    1241: "Santos",
    5438: "Red Bull Bragantino",
    1235: "Atlético Mineiro",
    2065: "Fortaleza",
    1231: "Sport",
    1238: "Vitória",
    1244: "Grêmio",
    7334: "Ceará",
    1220: "Juventude",
    6332: "Mirassol",
}

# Substituir os IDs pelos nomes
df["teamName"] = df["teamId"].map(team_mapping)

data = df

# ===========================
# FILTRO POR PARTIDA (CONFRONTO)
# ===========================
st.sidebar.subheader("Filtrar por Partida")
# Criar coluna de confronto se ainda não existir
if 'confronto' not in df.columns:
    df['confronto'] = df['home'] + " x " + df['away']

# Lista de confrontos
confrontos = df[['matchId', 'confronto']].drop_duplicates()
confrontos_sorted = confrontos.sort_values('confronto')
confronto_options = ["Todos"] + confrontos_sorted['confronto'].tolist()
selected_confronto = st.sidebar.selectbox("Escolha a partida:", confronto_options)

# Filtrar o dataframe
if selected_confronto != "Todos":
    match_id = confrontos_sorted[confrontos_sorted['confronto'] == selected_confronto]['matchId'].iloc[0]
    df_filtered = df[df['matchId'] == match_id]
else:
    df_filtered = df.copy()

plot_types = [
    "Passes para o Terço Final",
    "Ações Defensivas",
    "Escanteios",
    "Dribles Completos",
    "Passes Progressivos",
    "Passes Certos e Errados",
    "Chances Criadas",
    "Ações Defensivas no Ataque",
    "Finalizações",
    "Mapa de Calor",
    "Passes para a Área"
]

# Fonte
fnt = fm.FontProperties(fname='BigShoulders_18pt-Regular.ttf')
menu_option = st.sidebar.radio("Navegação", ["Visualizações", "Rankings", "Comparação", "Contato"])

#st.title("⚽ Visualizações Avançadas - DataFutebol")

st.subheader("👋 Seja bem-vindo ao aplicativo do DataFutebol")
st.markdown("Nos siga nas Redes Sociais → **@DataFutebol** | Apoie o projeto! Chave Pix → **b034e142-4211-4107-9dd0-baa364d8e381** | Agradeço ao @CruzeiroData pela ajuda!")


def add_logo(fig, team_name):
    try:
        logo = mpimg.imread(f"{team_name}.png")
        ax_img = fig.add_axes([0.12, 0.93, 0.1, 0.1])
        ax_img.imshow(logo)
        ax_img.axis("off")
    except:
        pass

# ======================================================
# FUNÇÕES DE PLOTAGEM
# ======================================================

def plot_passes_final(data, selected):
    pitch = Pitch(pitch_type='opta', line_color='dimgray', pitch_color='#f7f7f7')
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor('#f7f7f7')

    passes = data[(data['type'] == 'Pass') & (data['outcomeType'] == 'Successful')]
    terco_final = passes[passes['last_third_entry'] == True]
    outros_passes = passes[passes['last_third_entry'] == False]

    pitch.lines(terco_final.x, terco_final.y, terco_final.endX, terco_final.endY,
                comet=True, color="seagreen", lw=4, ax=ax, linestyle="--")
    ax.scatter(terco_final.endX, terco_final.endY, s=120, c="seagreen", edgecolors="black")

    pitch.lines(outros_passes.x, outros_passes.y, outros_passes.endX, outros_passes.endY,
                comet=True, color="gray", lw=4, ax=ax, alpha=0.3, linestyle="--")
    ax.scatter(outros_passes.endX, outros_passes.endY, s=100, c="gray", edgecolors="black", alpha=0.3)

    v1, v2 = len(outros_passes), len(terco_final)
    ax.set_title(f"Passes para o Terço Final - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Total: {v1}> | <Terço Final: {v2}> | viz by @DataFutebol',
            highlight_textprops=[{"color": "black"}, {"color": "seagreen"}],
            ax=ax, fontproperties=fnt, ha='center', va='center', fontsize=15, color="dimgray")

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_boxpass(data, selected):
    pitch = Pitch(pitch_type='opta', line_color='dimgray',
                          pitch_color='#f7f7f7')
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor('#f7f7f7')

    passes_box = data[(data['type'] == 'Pass') & (data['outcomeType'] == 'Successful') & (data['passFreekick'])]
    box = passes_box[passes_box['box_entry'] == True]

    pitch.lines(box.x, box.y, box.endX, box.endY,
                comet=True, color="green", lw=4, ax=ax)
    ax.scatter(box.endX, box.endY, s=120, c="green",  edgecolors="black")

    box_count = len(box)
    ax.set_title(f"Passes para a Área - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Total: {box_count}> | viz by @DataFutebol',
            highlight_textprops=[{"color": "green"}],
            ax=ax, fontproperties=fnt, ha='center', va='center', fontsize=15, color="dimgray")

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_defensivas(data, selected):
    pitch = Pitch(pitch_type='opta', line_color='dimgray', pitch_color='#f7f7f7')
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor('#f7f7f7')

    tackle = data[data['type'] == 'Tackle']
    interception = data[data['type'] == 'Interception']
    clearance = data[data['type'] == 'Clearance']
    ball_recovery = data[data['type'] == 'BallRecovery']
    foul = data[data['type'] == 'Foul']

    pitch.scatter(tackle.x, tackle.y, s=200, c="royalblue", edgecolors="black", ax=ax)
    pitch.scatter(interception.x, interception.y, s=200, c="orange", edgecolors="black", marker='s', ax=ax)
    pitch.scatter(clearance.x, clearance.y, s=200, c="purple", edgecolors="black", marker='H', ax=ax)
    pitch.scatter(ball_recovery.x, ball_recovery.y, s=200, c="green", edgecolors="black", marker='D', ax=ax)
    pitch.scatter(foul.x, foul.y, s=200, c="red", edgecolors="black", marker='X', ax=ax)

    tk, it, cl, br, fo = len(tackle), len(interception), len(clearance), len(ball_recovery), len(foul)

    ax.set_title(f"Ações Defensivas - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Desarmes: {tk}> | <Interceptações: {it}> | <Bolas Recuperadas: {br}> | '
                       f'<Rebatidas: {cl}> | <Faltas: {fo}> | viz by @DataFutebol',
            highlight_textprops=[{"color": "royalblue"}, {"color": "orange"},
                                 {"color": "green"}, {"color": "purple"}, {"color": "red"}],
            ax=ax, fontproperties=fnt, ha='center', va='center', color='dimgray', fontsize=15)

    add_logo(fig, data['teamName'].iloc[0])
    return fig


def plot_escanteios(data, selected):
    pitch = Pitch(pitch_type="opta", line_color="dimgray", pitch_color="#f7f7f7")
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor("#f7f7f7")

    complete_pass = data[data['passCornerAccurate'] == True]
    incomplete_pass = data[data['passCornerInaccurate'] == True]

    pitch.lines(incomplete_pass.x, incomplete_pass.y, incomplete_pass.endX, incomplete_pass.endY,
                lw=5, comet=True, color='purple', ax=ax, alpha=0.2)
    pitch.scatter(incomplete_pass.endX, incomplete_pass.endY, color='none',
                  s=300, edgecolors='purple', ax=ax, marker='X')

    pitch.lines(complete_pass.x, complete_pass.y, complete_pass.endX, complete_pass.endY,
                lw=5, comet=True, color='green', ax=ax, alpha=0.2)
    pitch.scatter(complete_pass.endX, complete_pass.endY, color='green',
                  s=300, edgecolors='black', ax=ax)

    v1 = len(complete_pass)
    v2 = 100 * (len(complete_pass) / (len(complete_pass) + len(incomplete_pass))) if len(complete_pass)+len(incomplete_pass) > 0 else 0

    ax.set_title(f"Escanteios - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Escanteios Certos: {v1}> | <Aproveitamento: {v2:.2f}%> | viz by @DataFutebol',
            highlight_textprops=[{"color": "green"}, {"color": "black"}],
            ax=ax, fontproperties=fnt, ha='center', va='center', color='dimgray', fontsize=15)

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_dribles(data, selected):
    pitch = Pitch(pitch_type="opta", line_color="dimgray", pitch_color="#f7f7f7")
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor("#f7f7f7")

    drib = data[data["dribbleWon"] == True]
    dribe = data[data["dribbleLost"] == True]
    pitch.scatter(drib.x, drib.y, s=200, c="darkgreen", marker="^", ax=ax, edgecolors="black")
    pitch.scatter(dribe.x, dribe.y, s=200, c="red", marker="^", ax=ax, edgecolors="black")

    v1 = len(drib)
    v2 = 100*(len(drib)/(len(drib) + len(dribe)))
    ax.set_title(f"Dribles Completos - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Dribles Completos: {v1}> | <Aproveitamento: {v2:.2f}%> | viz by @DataFutebol',
        highlight_textprops=[{"color": "green"}, {"color":"black"}],
        ax=ax, fontproperties=fnt, ha='center', va='center', color='dimgray', fontsize=15)

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_passes_progressivos(data, selected):
    pitch = Pitch(pitch_type="opta", line_color="dimgray", pitch_color="#f7f7f7")
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor("#f7f7f7")

    passes = data[(data["type"] == "Pass") & (data["progressive_action"] == True) & (data['passFreekick'] == False)]
    p = data[(data["type"] == "Pass") & (data["progressive_action"] == False)]
    pitch.lines(passes.x, passes.y, passes.endX, passes.endY,
                comet=True, color="blue", lw=3, ax=ax)
    pitch.scatter(passes.endX, passes.endY, s=200, c="blue", marker="o", ax=ax, edgecolors="black")
    pitch.lines(p.x, p.y, p.endX, p.endY,
                comet=True, color="gray", lw=3, alpha = 0.3, ax=ax)
    pitch.scatter(p.endX, p.endY, s=100, c="gray", marker="o", alpha = 0.3, ax=ax, edgecolors="black")

    ax.set_title(f"Passes Progressivos - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Total: {len(passes)}> | viz by @DataFutebol',
            highlight_textprops=[{"color": "black"}], ax=ax, fontproperties=fnt, ha='center', va='center', color='dimgray', fontsize=15)

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_passes_certos_errados(data, selected):
    pitch = Pitch(pitch_type="opta", line_color="dimgray", pitch_color="#f7f7f7")
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor("#f7f7f7")

    passes = data[(data["type"] == "Pass") & (data['passFreekick'] == False)]
    certos = passes[passes["outcomeType"] == "Successful"]
    errados = passes[passes["outcomeType"] == "Unsuccessful"]

    pitch.lines(certos.x, certos.y, certos.endX, certos.endY,
                comet=True, color="royalblue", lw=3, ax=ax)
    pitch.scatter(certos.endX, certos.endY,
                  color='royalblue', s=300, edgecolors='black', ax=ax)
    pitch.lines(errados.x, errados.y, errados.endX, errados.endY,
                comet=True, color="red", lw=2, ax=ax, alpha=0.7)
    pitch.scatter(errados.endX, errados.endY,
                  color='red', s=300, edgecolors='black', ax=ax, alpha = 0.7)

    ax.set_title(f"Passes Certos e Errados - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Certos: {len(certos)}> | <Errados: {len(errados)}> | viz by @DataFutebol', highlight_textprops=[{"color": "royalblue"}, {"color": "red"}],
        ax=ax, fontproperties=fnt, ha='center', va='center', color='dimgray', fontsize=15)

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_chances(data, selected):
    pitch = Pitch(pitch_type="opta", line_color="dimgray", pitch_color="#f7f7f7")
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor("#f7f7f7")

    chances = data[(data["passKey"] == True) & (data['assist'] == False)]
    pitch.lines(chances.x, chances.y, chances.endX, chances.endY,
                comet=True, color="blue", lw=3, ax=ax)
    pitch.scatter(chances.endX, chances.endY, s=100, c="blue", marker ='s', edgecolors="black", ax=ax)
    assists = data[data['assist'] == True]
    pitch.lines(assists.x, assists.y, assists.endX, assists.endY,
                comet=True, color="gold", lw=3, ax=ax)
    pitch.scatter(assists.endX, assists.endY, s=400, c="gold", marker ='*', edgecolors="black", ax=ax)


    ax.set_title(f"Chances Criadas - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Chances Criadas: {len(chances)}> | <Assistências> | viz by @DataFutebol', highlight_textprops=[{"color": "blue"}, {"color": "gold"}],
        ax=ax, fontproperties=fnt, ha='center', va='center', color='dimgray', fontsize=15)

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_defensivas_ataque(data, selected):
    pitch = VerticalPitch(pitch_type="opta", line_color="dimgray", pitch_color="#f7f7f7", half = True)
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor("#f7f7f7")
    at = data[data['x'] > 50]
    tacklea = at[at['type'] == 'Tackle']
    interceptiona = at[at['type'] == 'Interception']
    ball_recoverya = at[at['type'] == 'BallRecovery']
    foula = at[at['type'] == 'Foul']
    pitch.scatter(tacklea.x, tacklea.y, s=200, c="royalblue", edgecolors="black", ax=ax)
    pitch.scatter(interceptiona.x, interceptiona.y, s=200, c="orange", edgecolors="black", marker = 's', ax=ax)
    pitch.scatter(ball_recoverya.x, ball_recoverya.y, s=200, c="green", edgecolors="black", marker = 'D', ax=ax)
    pitch.scatter(foula.x, foula.y, s=200, c="red", edgecolors="black", marker = 'X', ax=ax)
    tka = len(tacklea)
    ita = len(interceptiona)
    bra = len(ball_recoverya)
    foa = len(foula)

    ax.set_title(f"Ações Defensivas no Campo de Ataque - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Desarmes: {tka}> | <Interceptações: {ita}> | <Bolas Recuperadas: {bra}> | <Faltas: {foa}> | viz by @DataFutebol',
        highlight_textprops=[{"color": "royalblue"}, {"color": "orange"}, {"color":"green"}, {"color":"red"}],
        ax=ax, fontproperties=fnt, ha='center', va='center', color='dimgray', fontsize=15)

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_finalizacoes(data, selected):
    pitch = VerticalPitch(pitch_type="opta", line_color="dimgray", pitch_color="#f7f7f7", half = True)
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor("#f7f7f7")

    goals = data[data['isGoal'] == True]
    off_target = data[data['shotOffTarget'] == True]
    trave = data[data['shotOnPost'] == True]
    on_target = data[(data['shotOnTarget'] == True) & (data['isGoal'] == False)]
    pitch.scatter(off_target.x, off_target.y,
                  c="red", s=300, marker="X", ax=ax)
    pitch.scatter(trave.x, trave.y,
                  c="blue", s=250, marker="^", ax=ax)
    pitch.scatter(on_target.x, on_target.y,
                  c="green", s=350, marker="o", ax=ax)
    pitch.scatter(goals.x, goals.y,
                  c="gold", s=500, marker="*", edgecolors="black", ax=ax)

    go = len(goals)
    of = len(off_target)
    tr = len(trave)
    on = len(on_target)
    ax.set_title(f"Finalizações - {selected}", fontproperties=fnt, fontsize=30)
    ax_text(50, 102, s=f'<Gols: {go}> | <Pra Fora: {of}> | <Trave: {tr}> | <No Alvo: {on}> | viz by @DataFutebol',
        highlight_textprops=[{"color": "gold"}, {"color": "red"}, {"color":"blue"}, {"color":"green"}],
        ax=ax, fontproperties=fnt, ha='center', va='center', color='dimgray', fontsize=15)

    add_logo(fig, data['teamName'].iloc[0])
    return fig

def plot_heatmap(data, selected):
    pitch = Pitch(pitch_type="opta", line_color="dimgray", pitch_color="#f7f7f7")
    fig, ax = pitch.draw(figsize=(16, 11))
    fig.set_facecolor("#f7f7f7")
    act = data[data['isTouch'] == True]
    pitch.kdeplot(act.x, act.y, ax=ax, shade=True, cmap="Reds", bw_adjust=1,
                  levels=100, fill=True, alpha = 0.7)

    ax.set_title(f"Heatmap - {selected}", fontproperties=fnt, fontsize=30)
    add_logo(fig, data['teamName'].iloc[0])
    return fig

def show_visualization(data, selected, plot_choice):
  if plot_choice == "Passes para o Terço Final":
    st.pyplot(plot_passes_final(data_filtered, selected))
  elif plot_choice == "Ações Defensivas":
    st.pyplot(plot_defensivas(data_filtered, selected))
  elif plot_choice == "Escanteios":
    st.pyplot(plot_escanteios(data_filtered, selected))
  elif plot_choice == "Dribles Completos":
    st.pyplot(plot_dribles(data_filtered, selected))
  elif plot_choice == "Passes Progressivos":
    st.pyplot(plot_passes_progressivos(data_filtered, selected))
  elif plot_choice == "Passes Certos e Errados":
    st.pyplot(plot_passes_certos_errados(data_filtered, selected))
  elif plot_choice == "Chances Criadas":
    st.pyplot(plot_chances(data_filtered, selected))
  elif plot_choice == "Ações Defensivas no Ataque":
    st.pyplot(plot_defensivas_ataque(data_filtered, selected))
  elif plot_choice == "Finalizações":
    st.pyplot(plot_finalizacoes(data_filtered, selected))
  elif plot_choice == "Mapa de Calor":
    st.pyplot(plot_heatmap(data_filtered, selected))
  elif plot_choice == "Passes para a Área":
    st.pyplot(plot_boxpass(data_filtered, selected))

def show_rankings(df):
    st.title("📊 Rankings de Jogadores")

    # ----------------------------
    # FILTROS
    # ----------------------------
    teams = sorted(df['teamName'].dropna().unique())
    team_filter = st.selectbox("Selecione o time (ou Todos):", ["Todos"] + teams)

    min_games = st.number_input("Número mínimo de jogos:", min_value=1, value=1)

    mode = st.radio("Modo de visualização:", ["Total", "Por jogo"])

    # ----------------------------
    # CÁLCULO DE MÉTRICAS
    # ----------------------------
    # contar jogos distintos por jogador
    games_played = df.groupby("playerName")["matchId"].nunique().reset_index()
    games_played.columns = ["playerName", "Jogos"]

    # agregar métricas
    agg_funcs = {
        # Passes
        "passAccurate": "sum",
        "passInaccurate": "sum",
        "box_entry": "sum",
        "progressive_action": "sum",
        "last_third_entry": "sum",

        # Ataque
        "isGoal": "sum",
        "assist": "sum",
        "passKey": "sum",
        "passCornerAccurate": "sum",
        "passCornerInaccurate": "sum",
        "shotsTotal": "sum",
        "shotOnTarget": "sum",
        "shotOffTarget": "sum",
        "shotOnPost": "sum",
        "dribbleWon": "sum",
        "dribbleLost": "sum",

        # Defesa
        "tackleWon": "sum",
        "tackleLost": "sum",
        "ballRecovery": "sum",
        "clearanceTotal": "sum",
        "interceptionAll": "sum",
        "foulCommitted": "sum",
    }

    stats = df.groupby(["playerName", "teamName"]).agg(agg_funcs).reset_index()
    stats = stats.merge(games_played, on="playerName", how="left")

    # calcular derivados
    stats["Passes Totais"] = stats["passAccurate"] + stats["passInaccurate"]
    stats["Passes Certos"] = stats["passAccurate"]
    stats["Passes Errados"] = stats["passInaccurate"]
    stats["Aproveitamento nos Passes"] = (stats["passAccurate"] / stats["Passes Totais"] * 100).round(1)

    stats["Passes para a Área"] = stats["box_entry"]
    stats["Passes Progressivos"] = stats["progressive_action"]
    stats["Passes para o Terço Final"] = stats["last_third_entry"]

    stats["Gols"] = stats["isGoal"]
    stats["Assistências"] = stats["assist"]
    stats["Chances Criadas"] = stats["passKey"]

    stats["Escanteios Certos"] = stats["passCornerAccurate"]
    stats["Escanteios Errados"] = stats["passCornerInaccurate"]
    stats["Acerto nos Escanteios"] = (stats["passCornerAccurate"] / (stats["passCornerAccurate"] + stats["passCornerInaccurate"]) * 100).round(1)

    stats["Finalizações"] = stats["shotsTotal"]
    stats["Finalizações no Alvo"] = stats["shotOnTarget"]
    stats["Finalizações pra Fora"] = stats["shotOffTarget"]
    stats["Finalizações na Trave"] = stats["shotOnPost"]
    stats["Taxa de Conversão"] = (stats["isGoal"] / stats["shotsTotal"] * 100).round(1)
    stats["Aproveitamento nas Finalizações"] = (stats["shotOnTarget"] / stats["shotsTotal"] * 100).round(1)

    stats["Dribles Totais"] = stats["dribbleWon"] + stats["dribbleLost"]
    stats["Dribles Corretos"] = stats["dribbleWon"]
    stats["Dribles Errados"] = stats["dribbleLost"]
    stats["Aproveitamento nos Dribles"] = (stats["dribbleWon"] / stats["Dribles Totais"] * 100).round(1)

    stats["Desarmes"] = stats["tackleWon"] + stats["tackleLost"]
    stats["Bolas Recuperadas"] = stats["ballRecovery"]
    stats["Rebatidas"] = stats["clearanceTotal"]
    stats["Interceptações"] = stats["interceptionAll"]
    stats["Faltas"] = stats["foulCommitted"]

    # ----------------------------
    # AJUSTE TOTAL vs POR JOGO
    # ----------------------------
    if mode == "Por jogo":
        for col in [
            "Passes Totais", "Passes Certos", "Passes Errados", "Passes para a Área",
            "Passes Progressivos", "Passes para o Terço Final",
            "Gols", "Assistências", "Chances Criadas",
            "Escanteios Certos", "Escanteios Errados",
            "Finalizações", "Finalizações no Alvo", "Finalizações pra Fora", "Finalizações na Trave",
            "Dribles Totais", "Dribles Corretos", "Dribles Errados",
            "Desarmes", "Bolas Recuperadas", "Rebatidas", "Interceptações", "Faltas"
        ]:
            stats[col] = (stats[col] / stats["Jogos"]).round(2)

    # ----------------------------
    # FILTROS FINAIS
    # ----------------------------
    if team_filter != "Todos":
        stats = stats[stats["teamName"] == team_filter]

    stats = stats[stats["Jogos"] >= min_games]

    # ----------------------------
    # TABELAS
    # ----------------------------
    st.subheader("🎯 Passes")
    st.dataframe(stats[["playerName", "teamName", "Jogos",
                        "Passes Totais", "Passes Certos", "Passes Errados", "Aproveitamento nos Passes",
                        "Passes para a Área", "Passes Progressivos", "Passes para o Terço Final"]])

    st.subheader("⚡ Ataque")
    st.dataframe(stats[["playerName", "teamName", "Jogos",
                        "Gols", "Assistências", "Chances Criadas",
                        "Escanteios Certos", "Escanteios Errados", "Acerto nos Escanteios",
                        "Finalizações", "Finalizações no Alvo", "Finalizações pra Fora", "Finalizações na Trave",
                        "Taxa de Conversão", "Aproveitamento nas Finalizações",
                        "Dribles Totais", "Dribles Corretos", "Dribles Errados", "Aproveitamento nos Dribles"]])

    st.subheader("🛡️ Defesa")
    st.dataframe(stats[["playerName", "teamName", "Jogos",
                        "Desarmes", "Bolas Recuperadas", "Rebatidas", "Interceptações", "Faltas"]])

def show_comparacao(df):
    st.title("📈 Comparação de Jogadores")

    # ----------------------------
    # 1. Pré-processamento e agregação (mantido)
    # ----------------------------
    agg_funcs = {
        "passAccurate": "sum", "passInaccurate": "sum", "box_entry": "sum",
        "progressive_action": "sum", "last_third_entry": "sum", "isGoal": "sum",
        "assist": "sum", "passKey": "sum", "passCornerAccurate": "sum",
        "passCornerInaccurate": "sum", "shotsTotal": "sum", "shotOnTarget": "sum",
        "shotOffTarget": "sum", "shotOnPost": "sum", "dribbleWon": "sum",
        "dribbleLost": "sum", "tackleWon": "sum", "tackleLost": "sum",
        "ballRecovery": "sum", "clearanceTotal": "sum", "interceptionAll": "sum",
        "foulCommitted": "sum",
    }
    
    stats = df.groupby(["playerName", "teamName"]).agg(agg_funcs).reset_index()
    games_played = df.groupby(["playerName", "teamName"])["matchId"].nunique().reset_index()
    games_played.columns = ["playerName", "teamName", "Jogos"]
    stats = stats.merge(games_played, on=["playerName", "teamName"], how="left")
    
    # Calcular médias por jogo
    cols_to_avg = [col for col in agg_funcs.keys()]
    stats_per_game = stats.set_index(["playerName", "teamName"])[cols_to_avg].div(stats["Jogos"].values, axis=0).reset_index()

    # Calcular as estatísticas específicas com base nas médias
    stats_per_game["Passes Totais"] = stats_per_game["passAccurate"] + stats_per_game["passInaccurate"]
    stats_per_game["Aproveitamento nos Passes"] = np.where(stats_per_game["Passes Totais"] > 0, (stats_per_game["passAccurate"] / stats_per_game["Passes Totais"] * 100).round(1), 0)
    stats_per_game["Passes para a Área"] = stats_per_game["box_entry"]
    stats_per_game["Passes Progressivos"] = stats_per_game["progressive_action"]
    stats_per_game["Passes para o Terço Final"] = stats_per_game["last_third_entry"]
    stats_per_game["Gols"] = stats_per_game["isGoal"]
    stats_per_game["Assistências"] = stats_per_game["assist"]
    stats_per_game["Chances Criadas"] = stats_per_game["passKey"]
    stats_per_game["Taxa de Conversão"] = np.where(stats_per_game["shotsTotal"] > 0, (stats_per_game["isGoal"] / stats_per_game["shotsTotal"] * 100).round(1), 0)
    stats_per_game["Aproveitamento nos Dribles"] = np.where((stats_per_game["dribbleWon"] + stats_per_game["dribbleLost"]) > 0, (stats_per_game["dribbleWon"] / (stats_per_game["dribbleWon"] + stats_per_game["dribbleLost"]) * 100).round(1), 0)
    stats_per_game["Desarmes"] = stats_per_game["tackleWon"]
    stats_per_game["Interceptações"] = stats_per_game["interceptionAll"]
    stats_per_game["Rebatidas"] = stats_per_game["clearanceTotal"]
    stats_per_game["Bolas Recuperadas"] = stats_per_game["ballRecovery"]

    # Estatísticas disponíveis para seleção
    available_stats = [
        "Passes Totais", "Aproveitamento nos Passes", "Passes para a Área",
        "Passes Progressivos", "Passes para o Terço Final", "Gols",
        "Assistências", "Chances Criadas", "Taxa de Conversão",
        "Aproveitamento nos Dribles", "Desarmes", "Interceptações",
        "Rebatidas", "Bolas Recuperadas"
    ]
    
    # ----------------------------
    # 2. Widgets para seleção de jogadores e estatísticas
    # ----------------------------
    times_all = sorted(stats["teamName"].dropna().unique())
    
    st.markdown("### Seleção de Jogadores")
    st.markdown("Selecione um time, e em seguida um jogador. Você pode selecionar até 4 jogadores.")
    
    cols = st.columns(4)
    jogadores_selecionados = []
    
    for i, col in enumerate(cols):
        with col:
            time = st.selectbox(f"Time {i+1}", ['Nenhum'] + times_all, key=f"time_{i}")
            jogador = 'Nenhum'
            if time != 'Nenhum':
                jogadores_do_time = sorted(stats[stats["teamName"] == time]["playerName"].dropna().unique())
                jogador = st.selectbox(f"Jogador {i+1}", ['Nenhum'] + jogadores_do_time, key=f"jogador_{i}")
            
            if jogador != 'Nenhum':
                jogadores_selecionados.append(jogador)
    
    selected_stats = st.multiselect("Escolha de 4 a 10 estatísticas:", available_stats)

    if not (4 <= len(selected_stats) <= 10):
        st.info("Escolha **entre 4 e 10 estatísticas** para montar o radar.")
        return
    
    if len(jogadores_selecionados) < 2:
        st.info("Selecione pelo menos **2 jogadores** para comparar.")
        return
    
    # -----------------------------------------------------------------
    # 3. Preparar os dados para o gráfico de radar (com percentil global)
    # -----------------------------------------------------------------
    df_plot = stats_per_game[stats_per_game["playerName"].isin(jogadores_selecionados)].copy()
    
    for stat in selected_stats:
        # Calcula o percentil de cada jogador em relação a TODOS os jogadores na base de dados
        all_stats = stats_per_game[stat].dropna().values
        # Usando rankdata para percentil
        df_plot[stat] = [rankdata(all_stats, method='average')[np.argwhere(all_stats == x)[0][0]] / len(all_stats) for x in df_plot[stat]]

    df_plot_long = df_plot.melt(id_vars="playerName", value_vars=selected_stats, var_name="Estatística", value_name="Percentil")

    # ----------------------------
    # 4. Montar o gráfico com Plotly Express
    # ----------------------------
    fig = go.Figure()
    
    # Padronização de cores
    colors = ["#28a745", "#007bff", "#6f42c4", "#fd7e14"] 
    # verde, azul, roxo, laranja (bootstrap palette)
    
    for i, jogador in enumerate(jogadores_selecionados):
        jogador_data = df_plot_long[df_plot_long["playerName"] == jogador]
        fig.add_trace(go.Scatterpolar(
            r=jogador_data["Percentil"],
            theta=jogador_data["Estatística"],
            fill='toself',
            name=jogador,
            line_color=colors[i % len(colors)] 
            # Garantir que a cor se repita caso mais de 4 jogadores sejam selecionados (embora o limite seja 4)
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0, 0.25, 0.50, 0.75, 1.0],
                ticktext=['0%', '25%', '50%', '75%', '100%']
            )
        ),
        showlegend=True,
        title_text='', 
        legend=dict(
            yanchor="top",
            y=1.1,
            xanchor="left",
            x=1.1
        )
    )
    
    st.plotly_chart(fig)
def show_contato():
    st.title("📬 Contato")

    st.write(
        "Este site foi criado para a **análise de estatísticas do Campeonato Brasileiro 2025**.Se você tiver dúvidas, sugestões ou interesse em parcerias, sinta-se à vontade para entrar em contato.")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Autor")
        st.write("Ioannis Canteiro")
        st.write("Aluno de Ciência de Dados e Inteligência Artificial na PUCRS")
        st.write("Criador do DataFutebol")

    with col2:
        st.subheader("Dados de Contato")
        st.write("📧 **E-mail:** contato.datafutebol@gmail.com")
        st.write("🔗 **LinkedIn:** www.linkedin.com/in/ioannis-canteiro-958280226")
        # Substitua com seu link do LinkedIn para mais profissionalismo

    st.markdown("---")

    st.info("Obrigado por visitar o DataFutebol!")

# ======================================================
# APP
# ======================================================

st.sidebar.title("Menu")
if menu_option == "Visualizações":
    view_option = st.radio("Deseja visualizar por:", ["Jogador", "Time"], key="view_option")

    if view_option == "Jogador":
        # Primeiro escolhe o time
        selected_team = st.selectbox(
            "Escolha o time:",
            sorted(df_filtered['teamName'].dropna().unique()),
            key="team_for_player"
        )

        # Filtra apenas jogadores desse time
        players_in_team = sorted(df_filtered[df_filtered['teamName'] == selected_team]['playerName'].dropna().unique())

        # Agora o usuário escolhe o jogador dentro do time
        selected_player = st.selectbox(
            "Escolha o jogador:",
            players_in_team,
            key="player_viz"
        )

        # Filtrar os dados
        data_filtered = df_filtered[df_filtered['playerName'] == selected_player]

    else:
        # Visualização por time
        selected_team = st.selectbox(
            "Escolha o time:",
            sorted(df_filtered['teamName'].dropna().unique()),
            key="team_viz"
        )
        data_filtered = df_filtered[df_filtered['teamName'] == selected_team]

    # Tipo de plotagem
    plot_choice = st.selectbox("Escolha o tipo de plotagem:", plot_types, key="plot_choice")
    show_visualization(data_filtered, selected_player if view_option=="Jogador" else selected_team, plot_choice)

elif menu_option == "Rankings":
    show_rankings(df_filtered)
elif menu_option == "Comparação":
    show_comparacao(df_filtered)
elif menu_option == "Contato":
    show_contato()
