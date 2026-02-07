import streamlit as st
import pandas as pd
import random
from PIL import Image
import os

# Настройка страницы
st.set_page_config(
    page_title="Гача-симулятор ингредиентов",
    page_icon="🍀",
    layout="wide"
)

# Заголовок приложения
st.title("🍀 Гача-симулятор: Выпадение ингредиентов")
st.markdown("---")

# Функция для загрузки данных (упрощенная)
def load_data(file):
    """Загружает Excel-файл и подготавливает веса для вероятностного выбора."""
    try:
        df = pd.read_excel(file, engine='openpyxl')
        
        # Проверяем минимальное количество столбцов
        if len(df.columns) < 4:
            st.error("❌ В файле должно быть как минимум 4 столбца: №, Название, Изображение, Редкость")
            return None
        
        # Используем первые 4 столбца
        df = df.iloc[:, :4].copy()
        df.columns = ['id', 'name', 'image', 'rarity']
        
        # Проверяем типы данных
        df['id'] = pd.to_numeric(df['id'], errors='coerce')
        df['rarity'] = pd.to_numeric(df['rarity'], errors='coerce')
        
        # Удаляем строки с NaN в важных столбцах
        df = df.dropna(subset=['id', 'name', 'rarity'])
        
        # Проверяем диапазон редкости
        if not df['rarity'].between(1, 3).all():
            st.warning("⚠️ Некоторые значения редкости не в диапазоне 1-3. Будут использованы только корректные значения.")
            df = df[df['rarity'].between(1, 3)]
        
        # Создаем веса на основе редкости
        df['weight'] = df['rarity']
        
        return df
    
    except Exception as e:
        st.error(f"❌ Ошибка при чтении файла: {str(e)}")
        return None

# Функция для генерации выпавших ингредиентов
def generate_drops(df, num_drops):
    """Генерирует случайные ингредиенты с учетом редкости."""
    if df is None or len(df) == 0:
        return []
    
    try:
        # Используем вероятностный выбор с учетом весов
        indices = random.choices(
            range(len(df)), 
            weights=df['weight'].values, 
            k=num_drops
        )
        
        results = []
        for idx in indices:
            ingredient = df.iloc[idx]
            results.append({
                'id': int(ingredient['id']) if pd.notna(ingredient['id']) else 0,
                'name': str(ingredient['name']),
                'image': str(ingredient['image']) if pd.notna(ingredient['image']) else '',
                'rarity': int(ingredient['rarity']) if pd.notna(ingredient['rarity']) else 3
            })
        
        return results
    except Exception as e:
        st.error(f"❌ Ошибка при генерации: {str(e)}")
        return []

# Функция для отображения карточки ингредиента
def display_ingredient_card(ingredient, images_dir="images"):
    """Создает карточку для отображения ингредиента."""
    # Цвет рамки в зависимости от редкости
    rarity_colors = {
        1: "#FFD700",  # Золотой для самой редкой
        2: "#C0C0C0",  # Серебряный
        3: "#CD7F32"   # Бронзовый для самой частой
    }
    
    # Полный путь к изображению
    image_file = ingredient.get('image', '')
    img_display = None
    
    if image_file and isinstance(image_file, str):
        image_path = os.path.join(images_dir, image_file)
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail((150, 150))
                img_display = img
            except:
                img_display = None
    
    # Если изображение не загружено, создаем заглушку
    if img_display is None:
        # Создаем простой цветной квадрат
        rarity = ingredient.get('rarity', 3)
        color = rarity_colors.get(rarity, "#CD7F32")
        
        # Создаем изображение с помощью PIL
        img = Image.new('RGB', (150, 150), color=color)
        img_display = img
    
    # Создаем карточку
    name = ingredient.get('name', 'Неизвестно')
    rarity = ingredient.get('rarity', 3)
    color = rarity_colors.get(rarity, "#CD7F32")
    
    # Отображаем карточку
    st.image(img_display, width=150)
    st.markdown(f"**{name}**")
    
    # Звездочки для редкости
    stars_count = 4 - rarity
    stars = "★" * stars_count
    st.markdown(f'<span style="color: {color};">{stars}</span>', unsafe_allow_html=True)

# Основной интерфейс приложения
def main():
    # Боковая панель для настроек
    with st.sidebar:
        st.header("⚙️ Настройки генерации")
        
        # Загрузка файла
        uploaded_file = st.file_uploader(
            "📂 Загрузите Excel-файл", 
            type=['xlsx', 'xls'],
            help="Файл должен содержать 4 столбца: №, Название, Изображение, Редкость"
        )
        
        # Пример файла для скачивания
        if not uploaded_file:
            st.markdown("---")
            st.markdown("### 📋 Пример файла")
            # Создаем пример данных
            example_data = pd.DataFrame({
                '№': [1, 2, 3, 4, 5],
                'Название': ['Яблоко', 'Банан', 'Апельсин', 'Манго', 'Дуриан'],
                'Изображение': ['apple.png', 'banana.png', 'orange.png', 'mango.png', 'durian.png'],
                'Редкость': [3, 3, 3, 2, 1]
            })
            
            # Кнопка для скачивания примера
            @st.cache_data
            def convert_df_to_csv(df):
                return df.to_csv(index=False).encode('utf-8')
            
            csv = convert_df_to_csv(example_data)
            st.download_button(
                label="📥 Скачать пример (CSV)",
                data=csv,
                file_name="ingredients_example.csv",
                mime="text/csv",
            )
        
        # Ввод количества ингредиентов
        num_drops = st.slider(
            "🎲 Количество ингредиентов",
            min_value=1,
            max_value=50,
            value=12,
            step=1
        )
        
        # Кнопка генерации
        generate_button = st.button(
            "🎰 Сгенерировать!",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        st.markdown("### 📊 Система редкости")
        st.markdown("""
        - **🥉 Редкость 3** (3 звезды) - Частое выпадение
        - **🥈 Редкость 2** (2 звезды) - Среднее выпадение  
        - **🥇 Редкость 1** (1 звезда) - Редкое выпадение
        """)
    
    # Основная область
    if uploaded_file is not None:
        try:
            # Загружаем данные
            df = load_data(uploaded_file)
            
            if df is not None and not df.empty:
                # Показываем статистику
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Всего ингредиентов", len(df))
                with col2:
                    rare_count = len(df[df['rarity'] == 1])
                    st.metric("Редких", rare_count)
                with col3:
                    common_count = len(df[df['rarity'] == 3])
                    st.metric("Частых", common_count)
                
                # Генерация при нажатии кнопки
                if generate_button:
                    st.markdown("---")
                    st.subheader(f"🎁 Результаты: {num_drops} выпавших ингредиентов")
                    
                    # Генерируем выпавшие ингредиенты
                    drops = generate_drops(df, num_drops)
                    
                    if drops:
                        # Показываем статистику выпадений
                        rarity_counts = {1: 0, 2: 0, 3: 0}
                        for drop in drops:
                            rarity_counts[drop['rarity']] += 1
                        
                        stat_col1, stat_col2, stat_col3 = st.columns(3)
                        with stat_col1:
                            st.metric("Редких выпало", rarity_counts[1])
                        with stat_col2:
                            st.metric("Средних выпало", rarity_counts[2])
                        with stat_col3:
                            st.metric("Частых выпало", rarity_counts[3])
                        
                        # Отображаем карточки в сетке
                        st.markdown("### 🖼️ Выпавшие ингредиенты")
                        
                        # Создаем сетку
                        cols_per_row = min(6, len(drops))  # Максимум 6 в ряду
                        for i in range(0, len(drops), cols_per_row):
                            cols = st.columns(cols_per_row)
                            row_drops = drops[i:i+cols_per_row]
                            
                            for col_idx, drop in enumerate(row_drops):
                                with cols[col_idx]:
                                    display_ingredient_card(drop)
                        
                        # Кнопка для повторной генерации
                        if st.button("🔄 Сгенерировать еще раз", type="secondary"):
                            st.rerun()
                    else:
                        st.warning("Не удалось сгенерировать ингредиенты.")
            else:
                st.error("❌ Не удалось загрузить данные. Проверьте формат файла.")
                
        except Exception as e:
            st.error(f"❌ Произошла ошибка: {str(e)}")
            st.info("Попробуйте загрузить другой файл или перезапустить приложение.")
    
    else:
        # Инструкция если файл не загружен
        st.info("👈 **Начните с загрузки Excel-файла через боковую панель**")
        
        # Пример интерфейса
        st.markdown("""
        ### 🎯 Как использовать:
        1. **Загрузите Excel-файл** с ингредиентами
        2. **Укажите количество** ингредиентов для генерации
        3. **Нажмите "Сгенерировать!"**
        4. **Наслаждайтесь** результатами!
        
        ### 📋 Формат файла:
        Файл должен содержать 4 столбца в следующем порядке:
        
        | № | Название ингредиента | Файл изображения | Редкость |
        |---|----------------------|------------------|----------|
        | 1 | Яблоко | apple.png | 3 |
        | 2 | Банан | banana.png | 3 |
        | 3 | Дуриан | durian.png | 1 |
        
        **Редкость:** 1-3, где 1 - самая редкая, 3 - самая частая
        """)

if __name__ == "__main__":
    main()
