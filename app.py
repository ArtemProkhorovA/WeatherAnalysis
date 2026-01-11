import streamlit as st
import pandas as pd

from config.settings import (
    APP_TITLE, APP_ICON, LAYOUT, CITY_MAPPING,
    SEASON_ORDER, SEASONS_ORDERED
)
from utils import (
    load_and_validate_data,
    analyze_city_data,
    get_current_season,
    get_season_name_ru,
    check_temperature_normality,
    get_current_temperature,
    create_histogram,
    create_boxplot,
    create_timeseries,
    create_seasonal_bar_chart,
    create_seasonal_variability_chart,
    create_seasonal_ranges_chart,
    create_anomalies_bar_chart,
    create_current_temp_visualization
)

# Настройка страницы
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Заголовок приложения
st.title(APP_TITLE)
st.markdown("---")

# ============================================================================
# SIDEBAR - Загрузка данных и настройки
# ============================================================================

with st.sidebar:
    st.header("⚙️ Настройки")
    
    # Загрузка файла
    st.subheader("📁 Загрузка данных")
    uploaded_file = st.file_uploader(
        "Выберите CSV файл с историческими данными",
        type=['csv'],
        help="Файл должен содержать колонки: city, timestamp, temperature, season"
    )
    
    # API ключ
    st.subheader("🔑 API ключ OpenWeatherMap")
    api_key = st.text_input(
        "Введите API ключ",
        type="password",
        help="Получите бесплатный ключ на https://openweathermap.org/api"
    )
    
    if api_key:
        st.success("✓ API ключ введён")
    else:
        st.info("ℹ️ Введите API ключ для получения текущей температуры")
    
    st.markdown("---")
    
    # Информация
    with st.expander("ℹ️ О приложении"):
        st.markdown("""
        **Система мониторинга температуры**
        
        Функционал:
        - 📊 Анализ исторических данных
        - 🌡️ Получение текущей температуры
        - 🔍 Выявление аномалий
        - 📈 Визуализация трендов
        - 🎯 Сезонный анализ
        """)

# ============================================================================
# ОСНОВНАЯ ЧАСТЬ ПРИЛОЖЕНИЯ
# ============================================================================

if uploaded_file is None:
    # Страница приветствия
    st.info("👈 Загрузите CSV файл с историческими данными в боковой панели")
    
    st.markdown("""
    ### Формат данных
    
    CSV файл должен содержать следующие колонки:
    - `city` - Название города
    - `timestamp` - Дата (формат: YYYY-MM-DD)
    - `temperature` - Температура в °C
    - `season` - Сезон (winter, spring, summer, autumn)
    
    ### Пример данных:
    """)
    
    example_data = pd.DataFrame({
        'city': ['Москва', 'Москва', 'Москва'],
        'timestamp': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'temperature': [-5.2, -7.8, -4.1],
        'season': ['winter', 'winter', 'winter']
    })
    
    st.dataframe(example_data, use_container_width=True)
    
    st.stop()

# ============================================================================
# ЗАГРУЗКА И ВАЛИДАЦИЯ ДАННЫХ
# ============================================================================

df, error = load_and_validate_data(uploaded_file)

if error:
    st.error(f"❌ {error}")
    st.stop()

st.success(f"✓ Данные успешно загружены: {len(df)} записей, {df['city'].nunique()} городов")

# ============================================================================
# ВЫБОР ГОРОДА
# ============================================================================

st.header("🏙️ Выбор города")

cities = sorted(df['city'].unique())
selected_city = st.selectbox(
    "Выберите город для анализа:",
    cities,
    help="Выберите город из списка доступных в загруженных данных"
)

st.markdown("---")

# Фильтруем данные для выбранного города
city_df = df[df['city'] == selected_city].copy()

# Анализ данных
city_data, season_stats, city_anomalies = analyze_city_data(city_df)

# ============================================================================
# ВКЛАДКИ
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Общая статистика",
    "📈 Временной ряд",
    "🎯 Сезонный анализ",
    "⚠️ Аномалии",
    "🌡️ Текущая температура"
])

# ============================================================================
# ВКЛАДКА 1: ОБЩАЯ СТАТИСТИКА
# ============================================================================

with tab1:
    st.header(f"📊 Описательная статистика: {selected_city}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📅 Период данных",
            f"{(city_data['timestamp'].max() - city_data['timestamp'].min()).days} дней"
        )
    
    with col2:
        st.metric("📏 Записей", f"{len(city_data)}")
    
    with col3:
        st.metric("🌡️ Средняя температура", f"{city_data['temperature'].mean():.1f}°C")
    
    with col4:
        st.metric("⚠️ Аномалий", f"{len(city_anomalies)}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Описательная статистика")
        stats_df = city_data['temperature'].describe().to_frame()
        stats_df.columns = ['Температура (°C)']
        stats_df = stats_df.round(2)
        st.dataframe(stats_df, use_container_width=True)
    
    with col2:
        st.subheader("📊 Распределение температур")
        fig = create_histogram(city_data)
        st.plotly_chart(fig, use_container_width=True, key='temp_histogram')
    
    st.markdown("---")
    
    st.subheader("📦 Распределение температур по сезонам")
    fig = create_boxplot(city_data)
    st.plotly_chart(fig, use_container_width=True, key='temp_boxplot')

# ============================================================================
# ВКЛАДКА 2: ВРЕМЕННОЙ РЯД
# ============================================================================

with tab2:
    st.header(f"📈 Временной ряд температур: {selected_city}")
    
    fig = create_timeseries(city_data, city_anomalies)
    st.plotly_chart(fig, use_container_width=True, key='timeseries_main')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_date = city_data[city_data['temperature'] == city_data['temperature'].max()]['timestamp'].dt.strftime('%Y-%m-%d').values[0]
        st.metric("🔥 Максимум", f"{city_data['temperature'].max():.1f}°C", max_date)
    
    with col2:
        min_date = city_data[city_data['temperature'] == city_data['temperature'].min()]['timestamp'].dt.strftime('%Y-%m-%d').values[0]
        st.metric("❄️ Минимум", f"{city_data['temperature'].min():.1f}°C", min_date)
    
    with col3:
        st.metric("📊 Размах", f"{city_data['temperature'].max() - city_data['temperature'].min():.1f}°C")

# ============================================================================
# ВКЛАДКА 3: СЕЗОННЫЙ АНАЛИЗ
# ============================================================================

with tab3:
    st.header(f"🎯 Сезонный анализ: {selected_city}")
    
    st.subheader("📊 Статистика по сезонам")
    
    season_display = season_stats[['season_ru', 'mean', 'std', 'min', 'max', 'count']].copy()
    season_display.columns = ['Сезон', 'Среднее (°C)', 'Ст. откл. (°C)', 
                               'Минимум (°C)', 'Максимум (°C)', 'Записей']
    season_display = season_display.round(2)
    
    season_display['sort_order'] = season_display['Сезон'].map(SEASON_ORDER)
    season_display = season_display.sort_values('sort_order').drop('sort_order', axis=1)
    
    st.dataframe(season_display, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Средняя температура по сезонам")
        
        available_seasons = [s for s in SEASONS_ORDERED if s in season_stats['season_ru'].values]
        
        if len(available_seasons) > 0:
            season_stats_ordered = season_stats.set_index('season_ru').loc[available_seasons].reset_index()
            fig = create_seasonal_bar_chart(season_stats_ordered)
            st.plotly_chart(fig, use_container_width=True, key='seasonal_mean_temp')
        else:
            st.warning("Недостаточно данных для построения графика")
    
    with col2:
        st.subheader("📊 Вариабельность по сезонам")
        
        if len(available_seasons) > 0:
            fig = create_seasonal_variability_chart(season_stats_ordered)
            st.plotly_chart(fig, use_container_width=True, key='seasonal_variability')
    
    st.markdown("---")
    
    st.subheader("🎯 Диапазоны нормальных температур (среднее ± 2σ)")
    
    if len(available_seasons) > 0:
        fig = create_seasonal_ranges_chart(season_stats_ordered, available_seasons)
        st.plotly_chart(fig, use_container_width=True, key='seasonal_ranges')
        st.info("ℹ️ Диапазон (среднее ± 2σ) включает ~95% нормальных значений температуры")
    else:
        st.warning("Недостаточно данных для построения графика диапазонов")

# ============================================================================
# ВКЛАДКА 4: АНОМАЛИИ
# ============================================================================

with tab4:
    st.header(f"⚠️ Аномалии температуры: {selected_city}")
    
    if len(city_anomalies) == 0:
        st.success("✓ Аномалий не обнаружено!")
        st.info("Все температуры находятся в пределах нормы (среднее ± 2σ) для соответствующих сезонов.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего аномалий", len(city_anomalies))
        
        with col2:
            percent = (len(city_anomalies) / len(city_data)) * 100
            st.metric("Процент аномалий", f"{percent:.2f}%")
        
        with col3:
            high_anomalies = len(city_anomalies[city_anomalies['temperature'] > city_anomalies['upper_bound']])
            st.metric("Высокие аномалии", high_anomalies)
        
        with col4:
            low_anomalies = len(city_anomalies[city_anomalies['temperature'] < city_anomalies['lower_bound']])
            st.metric("Низкие аномалии", low_anomalies)
        
        st.markdown("---")
        
        st.subheader("📊 Распределение аномалий по сезонам")
        
        anomalies_by_season = city_anomalies.groupby('season_ru').size().reset_index(name='count')
        fig = create_anomalies_bar_chart(anomalies_by_season)
        st.plotly_chart(fig, use_container_width=True, key='anomalies_by_season')
        
        st.markdown("---")
        
        st.subheader("📋 Детальная информация об аномалиях")
        
        anomalies_display = city_anomalies[['timestamp', 'temperature', 'season_ru', 'lower_bound', 'upper_bound', 'deviation']].copy()
        anomalies_display['timestamp'] = anomalies_display['timestamp'].dt.strftime('%Y-%m-%d')
        anomalies_display.columns = ['Дата', 'Температура', 'Сезон', 'Нижняя граница', 'Верхняя граница', 'Отклонение']
        anomalies_display = anomalies_display.round(2)
        anomalies_display['Тип'] = anomalies_display.apply(
            lambda row: '🔥 Высокая' if row['Температура'] > row['Верхняя граница'] else '❄️ Низкая',
            axis=1
        )
        
        st.dataframe(anomalies_display.sort_values('Дата', ascending=False), use_container_width=True, hide_index=True)

# ============================================================================
# ВКЛАДКА 5: ТЕКУЩАЯ ТЕМПЕРАТУРА
# ============================================================================

with tab5:
    st.header(f"🌡️ Текущая температура: {selected_city}")
    
    if not api_key:
        st.warning("⚠️ Введите API ключ OpenWeatherMap в боковой панели для получения текущей температуры")
        st.markdown("""
        ### Как получить API ключ:
        
        1. Зарегистрируйтесь на [OpenWeatherMap](https://openweathermap.org/api)
        2. Перейдите в раздел API keys
        3. Скопируйте ваш ключ
        4. Вставьте его в поле слева
        
        API ключ предоставляется бесплатно с лимитом 1000 запросов в день.
        """)
    else:
        city_eng = CITY_MAPPING.get(selected_city, selected_city)
        
        with st.spinner(f'Получение данных о погоде для {selected_city}...'):
            weather_data = get_current_temperature(city_eng, api_key)
        
        if not weather_data['success']:
            if weather_data['error'] == 'invalid_key':
                st.error(f"""
                ❌ **Ошибка: Некорректный API ключ**
                
                {weather_data['message']}
                
                Пожалуйста, проверьте правильность введённого API ключа.
                Дополнительная информация: https://openweathermap.org/faq#error401
                """)
            else:
                st.error(f"❌ Ошибка при получении данных: {weather_data['message']}")
        else:
            current_temp = weather_data['temperature']
            current_season = get_current_season()
            current_season_ru = get_season_name_ru(current_season)
            
            normality = check_temperature_normality(current_temp, current_season, season_stats)
            
            if normality.get('no_data', False):
                st.warning(f"⚠️ **Недостаточно данных для сезона \"{current_season_ru}\"**")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🌡️ Температура", f"{current_temp:.1f}°C")
                with col2:
                    st.metric("🤚 Ощущается как", f"{weather_data['feels_like']:.1f}°C")
                with col3:
                    st.metric("💧 Влажность", f"{weather_data['humidity']}%")
                with col4:
                    st.metric("💨 Ветер", f"{weather_data['wind_speed']} м/с")
                
                st.info(f"**Сезон:** {current_season_ru}\n**Описание:** {weather_data['description']}")
            else:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🌡️ Температура", f"{current_temp:.1f}°C", 
                             f"{current_temp - normality['mean_temp']:.1f}°C от среднего")
                with col2:
                    st.metric("🤚 Ощущается как", f"{weather_data['feels_like']:.1f}°C")
                with col3:
                    st.metric("💧 Влажность", f"{weather_data['humidity']}%")
                with col4:
                    st.metric("💨 Ветер", f"{weather_data['wind_speed']} м/с")
                
                st.markdown("---")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📊 Анализ текущей температуры")
                    
                    st.write(f"**Сезон:** {current_season_ru}")
                    st.write(f"**Описание:** {weather_data['description']}")
                    st.write(f"**Время получения:** {weather_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    st.markdown("---")
                    
                    st.write(f"**Историческое среднее ({current_season_ru}):** {normality['mean_temp']:.1f}°C")
                    st.write(f"**Стандартное отклонение:** {normality['std_temp']:.1f}°C")
                    st.write(f"**Диапазон нормы:** [{normality['lower_bound']:.1f}°C, {normality['upper_bound']:.1f}°C]")
                    st.write(f"**Отклонение:** {normality['deviation']:+.1f}°C ({normality['deviation_in_std']:+.2f}σ)")
                    
                    st.markdown("---")
                    
                    if normality['is_normal']:
                        st.success(f"✅ **НОРМАЛЬНАЯ ТЕМПЕРАТУРА**\n\nТекущая температура находится в пределах нормы для сезона \"{current_season_ru}\".")
                    else:
                        anomaly_type = "АНОМАЛЬНО ВЫСОКАЯ" if current_temp > normality['upper_bound'] else "АНОМАЛЬНО НИЗКАЯ"
                        emoji = "🔥" if current_temp > normality['upper_bound'] else "❄️"
                        st.error(f"{emoji} **{anomaly_type} ТЕМПЕРАТУРА**\n\nОтклонение составляет {abs(normality['deviation_in_std']):.2f}σ от среднего значения.")
                
                with col2:
                    st.subheader("📈 Визуализация")
                    fig = create_current_temp_visualization(current_temp, current_season_ru, normality)
                    st.plotly_chart(fig, use_container_width=True, key='current_temp_viz')
                    st.info("ℹ️ **Интерпретация:**\n- Зелёная зона: нормальный диапазон (среднее ± 2σ)\n- Синяя линия: историческое среднее\n- Точка: текущая температура")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🌡️ Система мониторинга температуры | Powered by Streamlit & OpenWeatherMap</p>
</div>
""", unsafe_allow_html=True)
