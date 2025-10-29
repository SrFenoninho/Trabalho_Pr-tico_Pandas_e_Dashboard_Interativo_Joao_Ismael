import pandas as pd
import plotly.express as px
import streamlit as st

COR_PRIMARIA_TEMA = "#12345f"

st.set_page_config(page_title="Dashboard de Músicas do Spotify",
                   page_icon=":musical_note:",
                   layout="wide")

@st.cache_data
def carregar_e_limpar_dados(caminho_ficheiro):
    df = None
    codificacoes_a_tentar = ['utf-16']

    for codificacao in codificacoes_a_tentar:
        try:
            df = pd.read_csv(caminho_ficheiro, encoding=codificacao)
            break
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            st.error(f"Ficheiro '{caminho_ficheiro}' não encontrado. Verifique o caminho.")
            return None

    if df is None:
        st.error("Não foi possível ler o ficheiro. Pode estar corrompido.")
        return None

    if 'streams' in df.columns and df['streams'].dtype == 'object':
        df = df[pd.to_numeric(df['streams'], errors='coerce').notna()]
        df['streams'] = df['streams'].astype(int)

    for col in ['in_shazam_charts', 'in_deezer_playlists']:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '').fillna(0).astype(int)

    df.fillna(0, inplace=True)

    df['release_date'] = pd.to_datetime(
        df['released_year'].astype(str) + '-' + df['released_month'].astype(str) + '-' + df['released_day'].astype(str),
        errors='coerce')
    df.dropna(subset=['release_date'], inplace=True)

    return df

df = carregar_e_limpar_dados("Popular_Spotify_Songs.csv")

if df is None:
    st.stop()

st.sidebar.header("Filtros Interativos:")

year_range = st.sidebar.slider(
    "Selecione o Intervalo de Anos:",
    min_value=int(df["released_year"].min()),
    max_value=int(df["released_year"].max()),
    value=(df["released_year"].min(), df["released_year"].max())
)

top_artists = df['artist(s)_name'].value_counts().nlargest(50).index.tolist()
selected_artists = st.sidebar.multiselect(
    "Selecione o(s) Artista(s):",
    options=top_artists,
    default=[]
)

selected_key = st.sidebar.multiselect(
    "Selecione a Tonalidade (Key):",
    options=df["key"].unique(),
    default=[]
)

df_selection = df.query(
    "released_year >= @year_range[0] and released_year <= @year_range[1]"
)

if selected_artists:
    df_selection = df_selection[df_selection['artist(s)_name'].isin(selected_artists)]
if selected_key:
    df_selection = df_selection[df_selection['key'].isin(selected_key)]

if df_selection.empty:
    st.warning("Nenhum dado disponível para os filtros selecionados!")
    st.stop()

st.title(":bar_chart: Dashboard de Análise de Músicas do Spotify")
st.markdown("##")

total_streams = int(df_selection["streams"].sum())
average_danceability = int(df_selection["danceability_%"].mean())
song_count = df_selection.shape[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Total de Streams:")
    st.subheader(f"{total_streams:,}")
with col2:
    st.subheader("Total de Músicas:")
    st.subheader(f"{song_count}")
with col3:
    st.subheader("Média de Dançabilidade:")
    st.subheader(f"{average_danceability}%")

st.markdown("""---""")

col1, col2 = st.columns(2)

top_10_songs = df_selection.nlargest(10, 'streams')
fig_top_songs = px.bar(
    top_10_songs, x="streams", y="track_name",
    orientation="h", title="<b>Top 10 Músicas por Streams</b>",
    template="plotly_white", hover_data=['artist(s)_name', 'released_year'],
    color_discrete_sequence=[COR_PRIMARIA_TEMA]
)
fig_top_songs.update_layout(plot_bgcolor="rgba(0,0,0,0)", yaxis={'categoryorder':'total ascending'})
col1.plotly_chart(fig_top_songs, use_container_width=True)

songs_by_key = df_selection['key'].value_counts().reset_index()
songs_by_key.columns = ['key', 'count']
fig_key_dist = px.pie(
    songs_by_key, names='key', values='count',
    title='<b>Distribuição de Músicas por Tonalidade</b>', hole=.3
)
col2.plotly_chart(fig_key_dist, use_container_width=True)

st.markdown("""---""")

st.subheader("Análise Avançada de Padrões Musicais")

col3, col4 = st.columns(2)

with col3:
    fig_scatter = px.scatter(
        df_selection,
        x='energy_%',
        y='danceability_%',
        title='<b>Relação entre Energia e Dançabilidade</b>',
        labels={'energy_%': 'Energia (%)', 'danceability_%': 'Dançabilidade (%)'},
        color_discrete_sequence=[COR_PRIMARIA_TEMA]
    )
    fig_scatter.update_traces(opacity=0.6)
    fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_scatter, use_container_width=True)

with col4:
    streams_over_time = df_selection.groupby(df_selection['release_date'].dt.to_period('M'))['streams'].sum().reset_index()
    streams_over_time['release_date'] = streams_over_time['release_date'].dt.to_timestamp()

    if len(streams_over_time) > 1:
        fig_time_series = px.area(
            streams_over_time,
            x='release_date',
            y='streams',
            title='<b>Evolução de Streams no Tempo</b>',
            labels={'release_date': 'Data', 'streams': 'Total de Streams'},
            color_discrete_sequence=[COR_PRIMARIA_TEMA]
        )
        fig_time_series.update_layout(plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_time_series, use_container_width=True)
    else:
        st.info("Não há dados suficientes para mostrar a evolução temporal com os filtros atuais.")

st.subheader("Tabela de Dados Detalhada")

df_para_mostrar = df_selection[['track_name', 'artist(s)_name', 'released_year', 'streams', 'danceability_%', 'energy_%']].copy()
df_para_mostrar.columns = ["Música", "Artista(s)", "Ano", "Streams", "Dançabilidade (%)", "Energia (%)"]
st.dataframe(df_para_mostrar)

hide_st_style = """<style> #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} </style>"""

st.markdown(hide_st_style, unsafe_allow_html=True)