"""
Data processing and advanced analytics module for the Kepler mission.
"""
import pandas as pd
import numpy as np

def process_and_translate_data(file_path: str) -> pd.DataFrame:
    """
    Loads the processed file and applies string translations along
    with the dynamic calculation of names for tooltips.
    """
    raw_df = pd.read_csv(file_path)
    
    type_translation = {
        "Terrestrial": "Terrestre (tipo Tierra)",
        "Super-Earth": "Súper-Tierra",
        "Neptunian": "Gaseoso menor (Neptuniano)",
        "Gas Giant": "Gigante gaseoso (tipo Júpiter)"
    }
    
    disp_translation = {
        "CONFIRMED": "Confirmado",
        "CANDIDATE": "Candidato",
        "FALSE POSITIVE": "Falso Positivo"
    }
    
    def translate_type(val):
        if pd.isna(val): return val
        for eng, esp in type_translation.items():
            if eng in str(val):
                return esp
        return val

    raw_df['planet_type'] = raw_df['planet_type'].apply(translate_type)
    raw_df['koi_disposition'] = raw_df['koi_disposition'].map(disp_translation).fillna(raw_df['koi_disposition'])
    
    raw_df['tooltip_name'] = np.where(
        raw_df['koi_disposition'] == 'Confirmado', 
        raw_df['kepler_name'], 
        raw_df['kepoi_name']
    )
    
    return raw_df


def calculate_radar_statistics(df_filtered: pd.DataFrame, features: list):
    """
    Robustly calculates group medians, Median Absolute Deviations (MAD), 
    and the maximum/minimum limits for the radar chart.
    """
    if df_filtered.empty:
        return None, None, None, None
        
    df_radar_clean = df_filtered[['planet_type'] + features].dropna().copy()
    if df_radar_clean.empty:
        return None, None, None, None
        
    actual_categories = df_radar_clean['planet_type'].unique().tolist()
    group_medians = df_radar_clean.groupby('planet_type')[features].median()
    
    group_mads = {}
    for cat in actual_categories:
        df_cat = df_radar_clean[df_radar_clean['planet_type'] == cat][features]
        if not df_cat.empty:
            median_series = group_medians.loc[cat]
            group_mads[cat] = (df_cat - median_series).abs().median()
            
    med_min = group_medians.min()
    med_max = group_medians.max()
    
    return group_medians, group_mads, med_min, med_max