import pandas as pd
import numpy as np
from datetime import datetime
from config.settings import SEASON_MAPPING, ANOMALY_THRESHOLD, ROLLING_WINDOW


def translate_season(season):
    return SEASON_MAPPING.get(season.lower(), season)


def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'


def get_season_name_ru(season_eng):
    return translate_season(season_eng)


def load_and_validate_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        required_columns = ['city', 'timestamp', 'temperature', 'season']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return None, f"Отсутствуют необходимые колонки: {', '.join(missing_columns)}"
        
        df['season'] = df['season'].str.lower().str.strip()
        df['season_ru'] = df['season'].apply(translate_season)
        df = df.sort_values(['city', 'timestamp']).reset_index(drop=True)
        return df, None 
    except Exception as e:
        return None, f"Ошибка при загрузке файла: {str(e)}"


def analyze_city_data(city_df):
    city_df = city_df.sort_values('timestamp').copy()
    city_df['rolling_mean_' + str(ROLLING_WINDOW)] = city_df['temperature'].rolling(
        window=ROLLING_WINDOW, min_periods=1
    ).mean()
    
    season_stats = city_df.groupby('season')['temperature'].agg([
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max'),
        ('count', 'count')
    ]).reset_index()
    season_stats['season_ru'] = season_stats['season'].apply(translate_season)
    
    anomalies_list = []
    for season in city_df['season'].unique():
        season_data = city_df[city_df['season'] == season]
        mean_temp = season_data['temperature'].mean()
        std_temp = season_data['temperature'].std()
        
        # Считаю аномалии относительно сезона
        lower_bound = mean_temp - ANOMALY_THRESHOLD * std_temp
        upper_bound = mean_temp + ANOMALY_THRESHOLD * std_temp
        
        anomalies = season_data[
            (season_data['temperature'] < lower_bound) | 
            (season_data['temperature'] > upper_bound)
        ].copy()
        
        if len(anomalies) > 0:
            anomalies['lower_bound'] = lower_bound
            anomalies['upper_bound'] = upper_bound
            anomalies['deviation'] = anomalies['temperature'] - mean_temp
            anomalies_list.append(anomalies)
    
    if anomalies_list:
        city_anomalies = pd.concat(anomalies_list, ignore_index=True)
    else:
        city_anomalies = pd.DataFrame()
    return city_df, season_stats, city_anomalies


def check_temperature_normality(current_temp, season, season_stats):
    season_data = season_stats[season_stats['season'] == season]
    
    if len(season_data) == 0:
        return {
            'is_normal': None,
            'mean_temp': None,
            'std_temp': None,
            'lower_bound': None,
            'upper_bound': None,
            'deviation': None,
            'deviation_in_std': None,
            'no_data': True
        }
    
    mean_temp = season_data['mean'].values[0]
    std_temp = season_data['std'].values[0]
    
    lower_bound = mean_temp - ANOMALY_THRESHOLD * std_temp
    upper_bound = mean_temp + ANOMALY_THRESHOLD * std_temp
    
    is_normal = lower_bound <= current_temp <= upper_bound
    deviation = current_temp - mean_temp
    deviation_in_std = deviation / std_temp if std_temp > 0 else 0
    
    return {
        'is_normal': is_normal,
        'mean_temp': mean_temp,
        'std_temp': std_temp,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'deviation': deviation,
        'deviation_in_std': deviation_in_std,
        'no_data': False
    }
