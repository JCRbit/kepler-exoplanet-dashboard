import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 0. DYNAMIC CALCULATION OF ABSOLUTE PATHS
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "exoplanets_processed.csv")
ICON_PATH = os.path.join(BASE_DIR, "assets", "kepler-22b.png")
KEPLER_PATH = os.path.join(BASE_DIR, "assets", "kepler-telescope.png")
DIVIDER_PATH = os.path.join(BASE_DIR, "assets", "kepler-exoplanets.png")

from src.utils import get_base64_image
from src.styles import inject_custom_css, SCATTER_COLORS, EXECUTIVE_COLORS
from src.metrics import process_and_translate_data, calculate_radar_statistics

# ==============================================================================
# 1. PAGE CONFIGURATION AND STYLE INJECTION
# ==============================================================================
st.set_page_config(
    page_title="Exoplanetas. Misión Kepler",
    page_icon=ICON_PATH,  
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_css()

# ==============================================================================
# 2. EFFICIENT DATA LOADING (WITH CACHING)
# ==============================================================================
@st.cache_data
def load_data_wrapper():
    return process_and_translate_data(DATA_PATH)  

try:
    df = load_data_wrapper()
except FileNotFoundError:
    st.error(f"Data Error: No se detectó el archivo en '{DATA_PATH}'.")
    st.stop()

# ==============================================================================
# 3. SIDEBAR / FILTERS
# ==============================================================================
st.sidebar.markdown("<h3 style='font-size:16px; color:#ffffff;'>FILTROS</h3>", unsafe_allow_html=True)

# Categorical Filters
selected_disp = st.sidebar.multiselect("Estado de Validación:", options=df['koi_disposition'].unique().tolist(), default=df['koi_disposition'].unique().tolist())
selected_type = st.sidebar.multiselect("Clasificación del Planeta:", options=df['planet_type'].unique().tolist(), default=df['planet_type'].unique().tolist())

st.sidebar.markdown("---")

# Slider Filters
# Planetary Radius Filter (koi_prad) - Log Scale
min_prad = max(0.01, float(df['koi_prad'].min())) # Avoid 0 for geometric space calculation
max_prad = float(df['koi_prad'].max())

# Generate logarithmically spaced points for the slider options
prad_options = np.geomspace(min_prad, max_prad, num=400)
prad_options = sorted(list(set([round(x, 2) if x < 10 else round(x, 1) for x in prad_options])))

selected_prad = st.sidebar.select_slider(
    "Planet Radius ($R_\\oplus$):",
    options=prad_options,
    value=(prad_options[0], prad_options[-1])
)

# 2. Equilibrium Temperature Filter (koi_teq) - Log Scale
min_teq = max(1.0, float(df['koi_teq'].min()))
max_teq = float(df['koi_teq'].max())

# Generate logarithmically spaced points for temperature options
teq_options = np.geomspace(min_teq, max_teq, num=300)
teq_options = sorted(list(set([int(round(x)) for x in teq_options])))

selected_teq = st.sidebar.select_slider(
    "Planet Temperature ($K$):",
    options=teq_options,
    value=(teq_options[0], teq_options[-1])
)

# 3. Orbital Period Filter (koi_period) - Log Scale
min_period = max(0.1, float(df['koi_period'].min()))
max_period = float(df['koi_period'].max())

# Generate logarithmically spaced points for the orbital period options
period_options = np.geomspace(min_period, max_period, num=500)
period_options = sorted(list(set([round(x, 2) if x < 10 else round(x, 1) for x in period_options])))

selected_period = st.sidebar.select_slider(
    "Orbital Period (Days):",
    options=period_options,
    value=(period_options[0], period_options[-1])
)

# Combined application of all filters to the DataFrame
df_filtered = df[
    (df['koi_disposition'].isin(selected_disp)) & 
    (df['planet_type'].isin(selected_type)) &
    (df['koi_prad'].between(selected_prad[0], selected_prad[1])) &
    (df['koi_teq'].between(selected_teq[0], selected_teq[1])) &
    (df['koi_period'].between(selected_period[0], selected_period[1]))
]

# ==============================================================================
# 4. HEADER AND KPIs
# ==============================================================================
try:
    img_base64 = get_base64_image(ICON_PATH)  
    src_data = f"data:image/jpeg;base64,{img_base64}"
except FileNotFoundError:
    src_data = ""

st.markdown(
    f"""
    <h1 style='font-size: 30px; margin-bottom: 15px; display: flex; align-items: center; gap: 15px;'>
        {"<img src='" + src_data + "' style='height: 45px; width: auto; border-radius: 8px;' alt='🪐'>" if src_data else "🪐"}
        Exoplanetas. Misión Kepler
    </h1>
    """, 
    unsafe_allow_html=True
)

# Control if the filter leaves the dataframe empty
if df_filtered.empty:
    st.warning("No hay exoplanetas que cumplan con los criterios seleccionados. Intenta ampliar los rangos de los filtros.")
    st.stop()

kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
with kpi_col1:
    st.markdown(f'<div class="executive-card"><div class="kpi-label">Objetos Analizados</div><div class="kpi-val">{df_filtered.shape[0]}</div></div>', unsafe_allow_html=True)
with kpi_col2:
    confirmed_count = df_filtered[df_filtered['koi_disposition'] == 'Confirmado'].shape[0]
    st.markdown(f'<div class="executive-card"><div class="kpi-label">Exoplanetas Confirmados</div><div class="kpi-val">{confirmed_count}</div></div>', unsafe_allow_html=True)
with kpi_col3:
    hab_count = df_filtered[(df_filtered['koi_teq'].between(235, 330)) & (df_filtered['koi_prad'] <= 2.0)].shape[0] if "Confirmado" in selected_disp else 0
    st.markdown(f'<div class="executive-card"><div class="kpi-label">Potencialmente Habitables</div><div class="kpi-val">{hab_count}</div></div>', unsafe_allow_html=True)

# ==============================================================================
# 5. GRAPHICS MATRIX (VISUAL COMPONENT PRESENTATION)
# ==============================================================================

# --- ROW 1: Habitability Scatter Plot ---
with st.container(border=True):
    st.markdown("<h3 style='font-size:15px; margin-top:0px;'>Análisis de Habitabilidad: Temperatura vs Radio Planetario</h3>", unsafe_allow_html=True)
    
    fig1 = px.scatter(
        df_filtered, 
        x="koi_teq", 
        y="koi_prad", 
        color="koi_disposition", 
        log_y=True, 
        range_x=[0, 1600],  
        range_y=[0.01, 100], 
        color_discrete_map=SCATTER_COLORS,
        custom_data=["koi_disposition", "tooltip_name"]
    )
    fig1.add_vrect(x0=200, x1=320, fillcolor="rgba(76, 195, 185, 0.25)", layer="below", line_width=0)
    fig1.add_annotation(x=200, y=0.01, yref="paper", text="200 K", showarrow=False, textangle=-90, xanchor="right", font=dict(color="rgba(76, 195, 185, 0.6)", size=11))
    fig1.add_annotation(x=320, y=0.01, yref="paper", text="320 K", showarrow=False, textangle=-90, xanchor="left", font=dict(color="rgba(76, 195, 185, 0.6)", size=11))
    
    fig1.update_traces(hovertemplate=("Estado de Validación: %{customdata[0]}<br>Nombre: %{customdata[1]}<br>Temperatura (Kelvin): %{x}<br>Radio (Radios Terrestres): %{y}<extra></extra>"))
    fig1.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13, 22, 36, 0.3)", height=320, margin=dict(t=25, b=10, l=10, r=10), 
        xaxis=dict(title="Temperatura (K)"),
        yaxis=dict(title="Radio (Radios Terrestres)", type="log", range=[-1, 3.2], tickmode="array", tickvals=[0.1, 1, 10, 100, 1000], ticktext=["0.1", "1", "10", "100", "1000"]),
        legend=dict(title=None, orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
    )
    st.plotly_chart(fig1, use_container_width=True)

# --- ROW 2: Concentric Rings vs Radar Topological Profile ---
fila2_col1, fila2_col2 = st.columns(2)

with fila2_col1:
    with st.container(border=True):
        st.markdown("<h3 style='font-size:15px; margin-top:0px;'>Tipo de Planetas</h3>", unsafe_allow_html=True)
        t_counts = df_filtered['planet_type'].value_counts().reset_index()
        t_counts.columns = ['planet_type', 'count']
        total_planetas = t_counts['count'].sum()
        
        fig2 = go.Figure()
        grosor_anillo, separacion = 0.10, 0.04
        
        punto_partida_y = 0.9  
        paso_vertical = 0.06   

        for i, row in t_counts.iterrows():
            radio_exterior = 1.0 - (i * (grosor_anillo + separacion))
            radio_interior = radio_exterior - grosor_anillo
            hole_proporcional = max(0.1, radio_interior / radio_exterior) if radio_exterior > 0 else 0.1
            margin_val = (1.0 - radio_exterior) / 2
            
            fig2.add_trace(go.Pie(
                labels=[row['planet_type'], ""], 
                values=[row['count'], total_planetas - row['count']],
                hole=hole_proporcional, 
                direction="clockwise", 
                sort=False,
                domain=dict(x=[margin_val, 1.0 - margin_val], y=[margin_val, 1.0 - margin_val]),
                marker=dict(colors=[EXECUTIVE_COLORS[i % len(EXECUTIVE_COLORS)], "rgba(255,255,255,0.02)"], 
                line=dict(color='#1a263b', width=1.5)),
                textinfo="none", 
                hoverinfo="label+value+percent" if row['count'] > 0 else "none", 
                showlegend=False
            ))
            
            posicion_y = punto_partida_y - (i * paso_vertical)
            
            fig2.add_annotation(
                x=0.5, 
                y=posicion_y, 
                text=f"<span style='color:{EXECUTIVE_COLORS[i % len(EXECUTIVE_COLORS)]}; font-size:11px;'><b>{row['planet_type']}</b>:</span> <span style='color:#8b949e; font-size:11px;'>{row['count']}</span>",
                showarrow=False, 
                xref="paper", 
                yref="paper", 
                xanchor="right", 
                yanchor="middle", 
                bgcolor="rgba(26, 38, 59, 0.85)", 
                bordercolor="rgba(255, 255, 255, 0.05)", 
                borderwidth=1, 
                borderpad=2
            )
        
        fig2.add_annotation(text=f"<span style='font-size:22px; font-weight:700; color:#ffffff;'>{total_planetas}</span><br><span style='font-size:9px; color:#8b949e; letter-spacing:1px;'>Kepler Object of Interest</span>", showarrow=False, x=0.5, y=0.5)
        fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=10, b=10), height=450, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

with fila2_col2:
    with st.container(border=True):
        st.markdown("<h3 style='font-size:15px; margin-top:0px;'>Perfil Topológico</h3>", unsafe_allow_html=True)
        
        features_radar = ['koi_prad', 'koi_teq', 'koi_insol', 'koi_srad', 'koi_steff']
        group_medians, group_mads, med_min, med_max = calculate_radar_statistics(df_filtered, features_radar)
        
        if group_medians is not None:
            med_denom = (med_max - med_min).replace(0, 1)
            
            feature_labels = [
                f"Radio Planeta<br><span style='color:#4cc3b9; font-size:9px;'>[{med_min['koi_prad']:.1f} a {med_max['koi_prad']:.1f} R⊕]</span>",
                f"Temperatura Planeta<br><span style='color:#4cc3b9; font-size:9px;'>[{med_min['koi_teq']:.0f} a {med_max['koi_teq']:.0f} K]</span>",
                f"Insolación<br><span style='color:#4cc3b9; font-size:9px;'>[{med_min['koi_insol']:.1f} a {med_max['koi_insol']:.1f} E]</span>",
                f"Radio Estrella<br><span style='color:#4cc3b9; font-size:9px;'>[{med_min['koi_srad']:.1f} a {med_max['koi_srad']:.1f} R☉]</span>",
                f"Temperatura Estrella<br><span style='color:#4cc3b9; font-size:9px;'>[{med_min['koi_steff']:.0f} a {med_max['koi_steff']:.0f} K]</span>"
            ]
            
            fig_radar = go.Figure()
            theta_labels = feature_labels + [feature_labels[0]]
            
            for idx, cat in enumerate(group_medians.index):
                med_real = group_medians.loc[cat].tolist()
                mad_real = group_mads[cat].tolist() if cat in group_mads else [0.0]*5
                
                r_values = [0.15 + ((group_medians.loc[cat, f] - med_min[f]) / med_denom[f] * 0.80) for f in features_radar]
                r_values.append(r_values[0])
                
                units = ["R⊕ (Radios Terrestres)", "K (Kelvin)", "Veces la Tierra", "R☉ (Radios Solares)", "K (Kelvin)"]
                clean_names = ['Radio Planeta', 'Temperatura Planeta', 'Insolación', 'Radio Estrella', 'Temperatura Estrella']
                
                text_hover = [f"<b>{name}</b><br>Mediana: {m:.2f} {u}<br>Dispersión (MAD): {mad:.2f}" for name, m, mad, u in zip(clean_names, med_real, mad_real, units)]
                text_hover.append(text_hover[0])
                
                color_asignado = EXECUTIVE_COLORS[idx % len(EXECUTIVE_COLORS)]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_values, 
                    theta=theta_labels, 
                    name=cat, 
                    # mode='lines',
                    line=dict(color=color_asignado, width=2.5),
                    marker=dict(
                            size=12,
                            color='rgba(0,0,0,0)',
                            line=dict(color='rgba(0,0,0,0)', width=0)
                        ),
                    fill='toself',
                    fillcolor=f"rgba{tuple(int(color_asignado.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.05,)}",
                    text=text_hover, 
                    hoverinfo="name+text"
                ))
            
            fig_radar.update_layout(
                polar=dict(
                    domain=dict(x=[0.05, 0.95], y=[0.12, 0.98]),
                    radialaxis=dict(visible=True, range=[0, 1], showticklabels=False, gridcolor="rgba(255, 255, 255, 0.05)", linecolor="rgba(255, 255, 255, 0.1)"),
                    angularaxis=dict(visible=True, gridcolor="rgba(255, 255, 255, 0.08)", linecolor="rgba(255, 255, 255, 0.15)", tickfont=dict(size=9.5, color="#ffffff")),
                    bgcolor="rgba(13, 22, 36, 0.4)"
                ),
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=450, margin=dict(t=35, b=75, l=45, r=45),
                showlegend=True, legend=dict(orientation="h", yanchor="top", y=0.1, xanchor="center", x=0.5, font=dict(size=10, color="#8b949e"))
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.warning("Seleccione elementos en los filtros para generar la topología de radar.")

# --- ROW 3: Ridgeline Plot vs Insolation Flow ---
fila3_col1, fila3_col2 = st.columns(2)

with fila3_col1:
    with st.container(border=True):
        st.markdown("<h3 style='font-size:15px; margin-top:0px;'>Periodo Orbital: Distribución</h3>", unsafe_allow_html=True)
        
        fig3 = go.Figure()
        if not df_filtered.empty:
            categories_real = df_filtered['planet_type'].unique().tolist()
            for idx, cat in enumerate(categories_real):
                df_cat = df_filtered[df_filtered['planet_type'] == cat]
                if not df_cat.empty:
                    fig3.add_trace(go.Violin(
                        x=np.log10(df_cat['koi_period']), y=[idx] * len(df_cat), name=cat,
                        orientation='h', side='positive', width=1.8, points=False,      
                        line_color=EXECUTIVE_COLORS[idx % len(EXECUTIVE_COLORS)], fillcolor=EXECUTIVE_COLORS[idx % len(EXECUTIVE_COLORS)], opacity=0.7
                    ))
            
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13, 22, 36, 0.3)", showlegend=False, height=380, margin=dict(t=20, b=20, l=10, r=10),
                xaxis=dict(title="Periodo Orbital (Días)", tickmode='array', tickvals=[-1, 0, 1, 2, 3], ticktext=["0.1", "1", "10", "100", "1000"], gridcolor="rgba(255, 255, 255, 0.05)", tickfont=dict(color="#8b949e")),
                yaxis=dict(tickmode='array', tickvals=list(range(len(categories_real))), ticktext=categories_real, gridcolor="rgba(255, 255, 255, 0.05)", tickfont=dict(color="#8b949e"), automargin=True)
            )
        st.plotly_chart(fig3, use_container_width=True)

with fila3_col2:
    with st.container(border=True):
        st.markdown("<h3 style='font-size:15px; margin-top:0px;'>Flujo de Insolación vs Temperatura</h3>", unsafe_allow_html=True)
        
        fig4 = px.scatter(
            df_filtered, x="koi_insol", y="koi_teq", log_x=True, color="planet_type", 
            color_discrete_sequence=EXECUTIVE_COLORS, custom_data=["planet_type", "koi_insol", "koi_teq"]
        )
        fig4.update_traces(hovertemplate=("Tipo de Planeta: %{customdata[0]}<br>Flujo de Insolación: %{customdata[1]} F⊕ (Flujo Terrestre)<br>Temperatura: %{customdata[2]} K (Kelvin)<extra></extra>"))
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13, 22, 36, 0.3)", height=380,
            xaxis=dict(title="Flujo de Insolación (F⊕)"), yaxis=dict(title="Temperatura (K)"),
            legend=dict(title=None, orientation="v", yanchor="top", y=-0.35, xanchor="center", x=0.4)
        )
        st.plotly_chart(fig4, use_container_width=True)


# ==============================================================================
# 6. DATA GOVERNANCE AND DETECTED BIASES WARNING
# ==============================================================================

try:
    divider_base64 = get_base64_image(DIVIDER_PATH)  
    src_divider = f"data:image/jpeg;base64,{divider_base64}"
except FileNotFoundError:
    src_divider = ""

if src_divider:
    st.markdown(
        f"""
        <div style="text-align: center; margin: 35px 0 25px 0;">
            <img src="{src_divider}" style="width: 300px; max-height: 200px; object-fit: cover; opacity: 0.6; border-radius: 4px;" alt="---">
        </div>
        """, 
        unsafe_allow_html=True
    )
else:
    st.markdown("<br><hr style='border-top: 1px solid rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)

try:
    kepler_img_base64 = get_base64_image(KEPLER_PATH)  
    src_data_gobernanza = f"data:image/jpeg;base64,{kepler_img_base64}"
except FileNotFoundError:
    src_data_gobernanza = ""

st.markdown(
    f"""
    <h2 style='font-size: 20px; font-weight: 600; color: #ffffff; margin-bottom: 25px; display: flex; align-items: center; gap: 12px;'>
    {"<img src='" + src_data_gobernanza + "' style='height: 40px; width: auto; border-radius: 6px; margin-right: 15px;' alt='🪐'>" if src_data_gobernanza else "🪐"}
    Gobernanza de Datos y Sesgos Detectados
    </h2>
    """, 
    unsafe_allow_html=True
)

# --- 6.1: GOVERNANCE ---
gob_fila1_col1, gob_fila1_col2 = st.columns([1, 3], gap="large")

with gob_fila1_col1:
    # Main title in first column
    st.markdown("<div style='font-size: 16px; font-weight: 600; margin-top: 10px; margin-bottom: 30px;'><font color='#4cc3b9'>Gobernanza y Origen de los Datos</font></div>", unsafe_allow_html=True)    

with gob_fila1_col2:
    with st.container(border=True):
        st.markdown(
            """
            Los datos utilizados provienen originalmente del [**Archivo de Exoplanetas de la NASA**](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=cumulative), 
            específicamente de la tabla de Objetos de Interés de Kepler (KOI).
            
            * **Propiedad y Custodia:** El pipeline de procesamiento, limpieza y feature engineering aplicado es para fines de este desarrollo analítico.
            * **Uso y Licencia:** Los datos originales son de dominio público.
            * **Privacidad:** El dataset no contiene datos de carácter personal (PII) ni información confidencial, limitándose a mediciones astrofísicas y telemetría espacial.
            """
        )

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# --- 6.2. BIAS ANALYSIS ---

gob_fila2_col1, gob_fila2_col2 = st.columns([1, 3], gap="large")

with gob_fila2_col1:
    # Section main title in first column
    st.markdown("<div style='font-size: 16px; font-weight: 600; margin-top: 10px; margin-bottom: 30px;'><font color='#4cc3b9'>Análisis de Sesgos en los Datos</font></div>", unsafe_allow_html=True)    
    
    # Subtitle bias A in first column
    st.markdown("<div style='margin-top: 0px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size:14px; font-weight:600; color:#4cc3b9;'>Sesgo de Selección por Método de Tránsito</h4>", unsafe_allow_html=True)
    
    # Subtitle bias B in first column
    st.markdown("<div style='margin-top: 550px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size:14px; font-weight:600; color:#4cc3b9;'>Sesgo de Supervivencia y Falsos Positivos</h4>", unsafe_allow_html=True)
    
    # Subtitle bias C in first column
    st.markdown("<div style='margin-top: 110px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size:14px; font-weight:600; color:#4cc3b9;'>Sesgo de Clasificación en el Perfil Topológico</h4>", unsafe_allow_html=True)

with gob_fila2_col2:
    with st.container(border=True):

        st.markdown(
            """
            Las conclusiones estadísticas extraídas de este dashboard deben considerar los siguientes sesgos intrínsecos del método de observación empleado por la Misión Kepler:
            """
        )
        
        # --- Bias A Content ---
        st.markdown(
            """
            La misión Kepler detecta exoplanetas utilizando el método de tránsito (la caída en la luz de una estrella cuando un planeta pasa frente a ella). Esto genera un sesgo masivo hacia:
            * *Planetas de periodos orbitales cortos:* Es mucho más probable detectar planetas que orbitan muy cerca de su estrella que planetas con órbitas similares a la de la Tierra (365 días) o Júpiter (11 años), ya que se requieren observar múltiples tránsitos para confirmar el objeto.
            * *Planetas de gran tamaño:* Los gigantes gaseosos (*Gigante gaseoso* o *Gaseoso menor*) provocan una caída de luz significativamente mayor y más fácil de medir que los planetas de tamaño *Terrestre*.
            """
        )
        
        # ABSOLUTE BAR CHART
        if not df_filtered.empty:
            df_bias_chart = df_filtered.groupby(['planet_type', 'koi_disposition']).size().reset_index(name='frecuencia')
            orden_columnas_x = ["Gigante gaseoso (tipo Júpiter)", "Gaseoso menor (Neptuniano)", "Súper-Tierra", "Terrestre (tipo Tierra)"]
            orden_apilado_y = ["Confirmado", "Candidato", "Falso Positivo"]
            
            fig_bias = px.bar(
                df_bias_chart,
                x="planet_type",
                y="frecuencia",
                color="koi_disposition",
                title="Estado de Validación por Tipo de Planeta",
                labels={"planet_type": "Clasificación del Planeta", "frecuencia": "Número de Observaciones", "koi_disposition": "Estado de Validación"},
                color_discrete_map=SCATTER_COLORS,
                category_orders={"planet_type": orden_columnas_x, "koi_disposition": orden_apilado_y},
                text_auto=True
            )
            
            fig_bias.update_layout(
                barmode="stack", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13, 22, 36, 0.3)", height=300,
                margin=dict(t=40, b=20, l=10, r=10), xaxis=dict(title=None, tickfont=dict(color="#ffffff")),
                yaxis=dict(visible=False), showlegend=True,
                legend=dict(title=None, orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, traceorder="normal")
            )
            fig_bias.update_traces(textfont=dict(size=10, color="#ffffff"))
            st.plotly_chart(fig_bias, use_container_width=True)

        # --- Bias B Content ---
        st.markdown(
            """
            El dataset contiene un volumen elevado de registros clasificados originalmente como *False Positive* o *Candidate*. La gráfica de habitabilidad y la distribución de periodos orbitales están fuertemente condicionadas por objetos que aún no han sido confirmados por observaciones de seguimiento (como velocidad radial o imagen directa). Eliminar o filtrar estos estados distorsiona la distribución real de las observaciones de la misión.
            """
        )

        # --- Bias C Content ---
        st.markdown(
            """
            En el gráfico de radar, variables como el flujo de insolación (`koi_insol`) o la temperatura del planeta (`koi_teq`) se calculan a partir de modelos teóricos de equilibrio térmico de albedo cero. No representan mediciones atmosféricas reales. Por lo tanto, el volumen de planetas etiquetados como *\"Potencialmente Habitables\"* es un sesgo de criba preliminar y no implica habitabilidad biológica confirmada.
            """
        )
        st.caption("**Nota:** Este dataset representa una muestra de lo que la tecnología de 2009-2018 era capaz de medir con mayor facilidad, no representa la demografía ni la distribución real de planetas en la Vía Láctea.")

st.markdown("<p style='text-align: center; color: #57606a; font-size: 11px; margin-top: 35px;'>Kepler Exoplanet Mission 2009-2018</p>", unsafe_allow_html=True)