import streamlit as st
import pandas as pd
import random
import json
from PIL import Image, ImageDraw
import os
from io import BytesIO

# Настройка страницы
st.set_page_config(
    page_title="Гача-симулятор по категориям",
    page_icon="🎲",
    layout="wide"
)

# Заголовок приложения
st.title("🎲 Гача-симулятор: Выпадение по категориям")
st.markdown("---")

# Функция для создания изображения-заглушки
def create_placeholder_image(color, size=(150, 150)):
    """Создает простое цветное изображение-заглушку."""
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    # Рисуем градиент или простой узор для красоты
    draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=(255, 255, 255), width=2)
    return img

# Функция для загрузки JSON данных
def load_json_data(json_text):
    """Загружает данные из JSON формата."""
    try:
        data = json.loads(json_text)
        
        # Проверяем структуру данных
        if not isinstance(data, dict):
            st.error("❌ JSON должен быть словарем (объектом)")
            return None
        
        # Проверяем каждую категорию
        categories_data = {}
        total_items = 0
        
        for category, items in data.items():
            if not isinstance(items, list):
                st.error(f"❌ Категория '{category}' должна содержать список")
                return None
            
            # Проверяем каждый предмет в категории
            valid_items = []
            for i, item in enumerate(items):
                # Проверяем наличие обязательных полей
                if not isinstance(item, dict):
                    st.warning(f"⚠️ Элемент {i+1} в категории '{category}' пропущен (не словарь)")
                    continue
                
                # Проверяем и конвертируем поля
                try:
                    name = str(item.get('name', f'Элемент {i+1}'))
                    image = str(item.get('image', ''))
                    rarity = int(item.get('rarity', 3))
                    
                    # Ограничиваем редкость от 1 до 3
                    rarity = max(1, min(3, rarity))
                    
                    valid_items.append({
                        'name': name,
                        'image': image,
                        'rarity': rarity,
                        'weight': rarity  # Используем редкость как вес
                    })
                except (ValueError, TypeError) as e:
                    st.warning(f"⚠️ Ошибка в элементе {i+1} категории '{category}': {e}")
                    continue
            
            if valid_items:
                categories_data[category] = valid_items
                total_items += len(valid_items)
            else:
                st.warning(f"⚠️ Категория '{category}' пуста или содержит некорректные данные")
        
        if categories_data:
            st.success(f"✅ Загружено {total_items} предметов в {len(categories_data)} категориях")
            return categories_data
        else:
            st.error("❌ Нет корректных данных для загрузки")
            return None
            
    except json.JSONDecodeError as e:
        st.error(f"❌ Ошибка парсинга JSON: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Неожиданная ошибка: {str(e)}")
        return None

# Функция для генерации выпавших ингредиентов по категориям
def generate_category_drops(categories_data, category_counts):
    """Генерирует случайные ингредиенты для каждой категории."""
    if not categories_data:
        return {}
    
    results = {}
    
    try:
        for category, items in categories_data.items():
            # Получаем количество для этой категории
            num_drops = category_counts.get(category, 0)
            
            if num_drops <= 0 or not items:
                results[category] = []
                continue
            
            # Создаем списки для взвешенного выбора
            weights = [item['weight'] for item in items]
            indices = list(range(len(items)))
            
            # Выбираем случайные индексы с учетом весов
            selected_indices = random.choices(
                indices,
                weights=weights,
                k=num_drops
            )
            
            # Собираем результаты
            category_results = []
            for idx in selected_indices:
                item = items[idx].copy()
                # Удаляем служебные поля
                display_item = {
                    'name': item['name'],
                    'image': item['image'],
                    'rarity': item['rarity']  # Оставляем для внутреннего использования
                }
                category_results.append(display_item)
            
            results[category] = category_results
        
        return results
    
    except Exception as e:
        st.error(f"❌ Ошибка при генерации: {str(e)}")
        return {}

# Функция для отображения карточки ингредиента (без визуальной редкости)
def display_ingredient_card(ingredient, images_dir="images"):
    """Создает карточку для отображения ингредиента без индикации редкости."""
    
    # Полный путь к изображению
    image_file = ingredient.get('image', '')
    img_display = None
    
    # Пытаемся загрузить изображение
    if image_file and isinstance(image_file, str):
        # Проверяем абсолютный путь или путь относительно images_dir
        if os.path.isabs(image_file) and os.path.exists(image_file):
            image_path = image_file
        else:
            image_path = os.path.join(images_dir, image_file)
        
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail((150, 150))
                img_display = img
            except Exception as e:
                st.warning(f"Не удалось загрузить {image_file}: {e}")
                img_display = None
    
    # Если изображение не загружено, создаем красивую заглушку
    if img_display is None:
        # Используем нейтральный цвет для всех карточек
        img_display = create_placeholder_image("#4A90E2")  # Приятный синий цвет
    
    # Отображаем карточку
    st.image(img_display, width=150, use_container_width=False)
    st.markdown(f"**{ingredient.get('name', 'Неизвестно')}**")
    
    # НЕ отображаем звездочки редкости - просто пустая строка
    st.markdown("")  # Пустая строка для сохранения высоты

# Основной интерфейс приложения
def main():
    # Инициализация session state
    if 'categories_data' not in st.session_state:
        st.session_state.categories_data = None
    if 'generated_results' not in st.session_state:
        st.session_state.generated_results = None
    if 'category_counts' not in st.session_state:
        st.session_state.category_counts = {}
    
    # Боковая панель
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # Выбор способа ввода
        input_method = st.radio(
            "Способ ввода данных",
            ["📝 Ввести JSON", "📁 Загрузить JSON файл"],
            help="Выберите, как вы хотите ввести данные о категориях"
        )
        
        categories_data = None
        
        if input_method == "📝 Ввести JSON":
            # Текстовое поле для ввода JSON
            json_input = st.text_area(
                "Введите JSON данные",
                height=300,
                help="Формат: {\"категория_1\": [{\"name\": \"...\", \"image\": \"...\", \"rarity\": 1}, ...], ...}",
                placeholder='{\n  "Фрукты": [\n    {"name": "Яблоко", "image": "apple.png", "rarity": 3},\n    {"name": "Дуриан", "image": "durian.png", "rarity": 1}\n  ],\n  "Овощи": [\n    {"name": "Морковь", "image": "carrot.png", "rarity": 3}\n  ]\n}'
            )
            
            if json_input:
                categories_data = load_json_data(json_input)
        
        else:  # Загрузить JSON файл
            uploaded_file = st.file_uploader(
                "📂 Выберите JSON файл",
                type=['json'],
                help="Загрузите JSON файл с категориями и предметами"
            )
            
            if uploaded_file is not None:
                try:
                    json_content = uploaded_file.read().decode('utf-8')
                    categories_data = load_json_data(json_content)
                except Exception as e:
                    st.error(f"❌ Ошибка чтения файла: {str(e)}")
        
        # Обновляем данные в session state если загрузили новые
        if categories_data:
            st.session_state.categories_data = categories_data
            # Сбрасываем предыдущие результаты
            st.session_state.generated_results = None
        
        st.markdown("---")
        
        # Показываем пример JSON
        with st.expander("📋 Пример JSON формата"):
            example_json = {
                "Фрукты": [
                    {"name": "Яблоко", "image": "apple.png", "rarity": 3},
                    {"name": "Банан", "image": "banana.png", "rarity": 3},
                    {"name": "Дуриан", "image": "durian.png", "rarity": 1}
                ],
                "Овощи": [
                    {"name": "Морковь", "image": "carrot.png", "rarity": 2},
                    {"name": "Картофель", "image": "potato.png", "rarity": 3}
                ],
                "Специи": [
                    {"name": "Ваниль", "image": "vanilla.png", "rarity": 1},
                    {"name": "Корица", "image": "cinnamon.png", "rarity": 2}
                ]
            }
            st.json(example_json)
            
            st.markdown("""
            **Поля:**
            - `name` - название предмета
            - `image` - имя файла изображения (или полный путь)
            - `rarity` - редкость (1-3, где 1 - самая редкая)
            
            *Редкость влияет только на вероятность выпадения, визуально не отображается*
            """)
    
    # Основная область
    if st.session_state.categories_data:
        categories_data = st.session_state.categories_data
        
        # Отображаем информацию о загруженных категориях
        st.subheader("📊 Загруженные категории")
        
        # Создаем колонки для отображения статистики по категориям
        category_names = list(categories_data.keys())
        cols = st.columns(min(4, len(category_names)))
        
        for i, category in enumerate(category_names[:4]):  # Показываем первые 4 категории
            with cols[i % 4]:
                items_count = len(categories_data[category])
                st.metric(
                    category, 
                    f"{items_count} предметов",
                    help=f"Редкость 1: {sum(1 for x in categories_data[category] if x['rarity'] == 1)}\nРедкость 2: {sum(1 for x in categories_data[category] if x['rarity'] == 2)}\nРедкость 3: {sum(1 for x in categories_data[category] if x['rarity'] == 3)}"
                )
        
        if len(category_names) > 4:
            st.caption(f"и еще {len(category_names) - 4} категорий...")
        
        st.markdown("---")
        
        # Настройка количества выпадений для каждой категории
        st.subheader("🎲 Настройка выпадений по категориям")
        
        # Создаем поля ввода для каждой категории
        category_counts = {}
        
        # Организуем категории в сетку
        num_cols = 3
        cols = st.columns(num_cols)
        
        for i, category in enumerate(category_names):
            with cols[i % num_cols]:
                category_counts[category] = st.number_input(
                    f"📦 {category}",
                    min_value=0,
                    max_value=20,
                    value=st.session_state.category_counts.get(category, 3),
                    step=1,
                    key=f"count_{category}"
                )
        
        # Сохраняем настройки в session state
        st.session_state.category_counts = category_counts
        
        st.markdown("---")
        
        # Кнопка генерации
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_button = st.button(
                "🎰 Сгенерировать выпадения!",
                type="primary",
                use_container_width=True
            )
        
        # Генерация результатов
        if generate_button:
            # Проверяем, выбрано ли хотя бы одно выпадение
            if sum(category_counts.values()) == 0:
                st.warning("⚠️ Выберите хотя бы одно выпадение в какой-нибудь категории")
            else:
                with st.spinner("Генерируем выпадения..."):
                    st.session_state.generated_results = generate_category_drops(
                        categories_data, 
                        category_counts
                    )
        
        # Отображение результатов
        if st.session_state.generated_results:
            results = st.session_state.generated_results
            
            st.markdown("---")
            st.subheader("🎁 Результаты выпадений")
            
            # Общая статистика
            total_drops = sum(len(items) for items in results.values())
            st.metric("Всего выпало предметов", total_drops)
            
            st.markdown("---")
            
            # Отображаем результаты по категориям
            tabs = st.tabs(list(results.keys()))
            
            for tab, (category, items) in zip(tabs, results.items()):
                with tab:
                    if items:
                        st.caption(f"Выпало предметов: {len(items)}")
                        
                        # Создаем сетку для отображения карточек
                        cols_per_row = min(5, len(items))
                        
                        for i in range(0, len(items), cols_per_row):
                            cols = st.columns(cols_per_row)
                            row_items = items[i:i+cols_per_row]
                            
                            for col_idx, item in enumerate(row_items):
                                with cols[col_idx]:
                                    display_ingredient_card(item)
                    else:
                        st.info(f"В категории '{category}' ничего не выпало")
            
            # Кнопка для новой генерации
            if st.button("🔄 Сгенерировать заново", type="secondary"):
                st.session_state.generated_results = None
                st.rerun()
    
    else:
        # Инструкция если данные не загружены
        st.info("👈 **Начните с ввода JSON данных через боковую панель**")
        
        # Красочное описание
        st.markdown("""
        ### 🎯 Как использовать новый гача-симулятор:
        
        1. **Введите JSON данные** с категориями и предметами
        2. **Укажите количество** выпадений для каждой категории
        3. **Нажмите "Сгенерировать!"**
        4. **Получите результаты** сгруппированные по категориям
        
        ### ✨ Особенности:
        
        - 📦 **Категории** - предметы группируются по категориям
        - 🎲 **Индивидуальные настройки** - для каждой категории свое количество
        - 🔄 **Взвешенная случайность** - редкость влияет на шанс выпадения
        - 🎨 **Чистый визуал** - индикаторы редкости скрыты
        
        ### 📊 Как работает редкость:
        
        Редкость (1-3) влияет только на вероятность выпадения:
        - **Редкость 1** - самые редкие (высокий вес)
        - **Редкость 2** - средние
        - **Редкость 3** - самые частые (низкий вес)
        
        *Визуально все карточки выглядят одинаково - редкость только в механике!*
        """)

if __name__ == "__main__":
    main()
