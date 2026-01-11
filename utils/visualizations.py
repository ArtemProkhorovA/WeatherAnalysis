import plotly.graph_objects as go
import plotly.express as px
from config.settings import SEASON_COLORS, SEASONS_ORDERED


def create_histogram(city_data):
    fig = px.histogram(
        city_data,
        x='temperature',
        nbins=50,
        title='',
        labels={'temperature': 'Температура (°C)', 'count': 'Частота'}
    )
    fig.update_layout(showlegend=False, height=400)
    return fig


def create_boxplot(city_data):
    fig = px.box(
        city_data,
        x='season_ru',
        y='temperature',
        color='season_ru',
        labels={'temperature': 'Температура (°C)', 'season_ru': 'Сезон'},
        category_orders={'season_ru': SEASONS_ORDERED}
    )
    fig.update_layout(showlegend=False, height=400)
    return fig


def create_timeseries(city_data, city_anomalies):
    fig = go.Figure()
    
    normal_data = city_data[~city_data.index.isin(city_anomalies.index)]
    
    fig.add_trace(go.Scatter(
        x=normal_data['timestamp'],
        y=normal_data['temperature'],
        mode='lines',
        name='Температура',
        line=dict(color='lightblue', width=1),
        opacity=0.6
    ))
    
    fig.add_trace(go.Scatter(
        x=city_data['timestamp'],
        y=city_data['rolling_mean_30'],
        mode='lines',
        name='Скользящее среднее (30 дней)',
        line=dict(color='blue', width=2)
    ))
    
    if len(city_anomalies) > 0:
        fig.add_trace(go.Scatter(
            x=city_anomalies['timestamp'],
            y=city_anomalies['temperature'],
            mode='markers',
            name='Аномалии',
            marker=dict(
                color='red',
                size=8,
                symbol='x',
                line=dict(width=2)
            )
        ))
    
    fig.update_layout(
        xaxis_title='Дата',
        yaxis_title='Температура (°C)',
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_seasonal_bar_chart(season_stats_ordered):
    colors = [SEASON_COLORS.get(s, 'gray') for s in season_stats_ordered['season_ru']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=season_stats_ordered['season_ru'],
        y=season_stats_ordered['mean'],
        error_y=dict(
            type='data',
            array=season_stats_ordered['std'] * 2,
            visible=True
        ),
        marker_color=colors,
        text=season_stats_ordered['mean'].round(1),
        textposition='outside'
    ))
    
    fig.update_layout(
        xaxis_title='Сезон',
        yaxis_title='Температура (°C)',
        showlegend=False,
        height=400
    )
    
    return fig


def create_seasonal_variability_chart(season_stats_ordered):
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=season_stats_ordered['season_ru'],
        y=season_stats_ordered['std'],
        marker_color='coral',
        text=season_stats_ordered['std'].round(2),
        textposition='outside'
    ))
    
    fig.update_layout(
        xaxis_title='Сезон',
        yaxis_title='Стандартное отклонение (°C)',
        showlegend=False,
        height=400
    )
    
    return fig


def create_seasonal_ranges_chart(season_stats_ordered, available_seasons):
    fig = go.Figure()
    
    for season_ru in available_seasons:
        season_data_row = season_stats_ordered[season_stats_ordered['season_ru'] == season_ru].iloc[0]
        mean = season_data_row['mean']
        std = season_data_row['std']
        
        fig.add_trace(go.Box(
            y=[mean - 2*std, mean - std, mean, mean + std, mean + 2*std],
            name=season_ru,
            boxmean=True
        ))
    
    fig.update_layout(
        yaxis_title='Температура (°C)',
        showlegend=True,
        height=400
    )
    
    return fig


def create_anomalies_bar_chart(anomalies_by_season):
    fig = px.bar(
        anomalies_by_season,
        x='season_ru',
        y='count',
        color='season_ru',
        labels={'count': 'Количество аномалий', 'season_ru': 'Сезон'},
        category_orders={'season_ru': SEASONS_ORDERED}
    )
    fig.update_layout(showlegend=False, height=400)
    return fig


def create_current_temp_visualization(current_temp, current_season_ru, normality):
    fig = go.Figure()
    
    fig.add_hrect(
        y0=normality['lower_bound'],
        y1=normality['upper_bound'],
        fillcolor="lightgreen",
        opacity=0.3,
        line_width=0,
        annotation_text="Диапазон нормы",
        annotation_position="left"
    )
    
    fig.add_hline(
        y=normality['mean_temp'],
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Среднее: {normality['mean_temp']:.1f}°C",
        annotation_position="right"
    )
    
    fig.add_trace(go.Scatter(
        x=[current_season_ru],
        y=[current_temp],
        mode='markers+text',
        marker=dict(
            size=20,
            color='red' if not normality['is_normal'] else 'green',
            symbol='circle',
            line=dict(width=2, color='white')
        ),
        name='Текущая температура',
        text=[f"{current_temp:.1f}°C"],
        textposition="top center"
    ))
    
    fig.update_layout(
        yaxis_title='Температура (°C)',
        xaxis_title='Сезон',
        showlegend=False,
        height=400,
        yaxis=dict(
            range=[
                min(normality['lower_bound'], current_temp) - 5,
                max(normality['upper_bound'], current_temp) + 5
            ]
        )
    )
    
    return fig
