# -*- coding: utf-8 -*-
# Меню сплава: полностью на русском + выгрузка Excel и PDF

import io
import os
import pandas as pd
import streamlit as st

# ==== PDF: пробуем reportlab (с кириллицей через TTF) ====
REPORTLAB_AVAILABLE = False
try:
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except Exception:
    pass  # если не установлено — ниже аккуратно сообщим

# ---------- ДАННЫЕ ПО УМОЛЧАНИЮ (всё на русском) ----------
БЛЮДА_ПО_УМОЛЧАНИЮ = [
    # Блюдо, Ингредиент, Ед.изм, Норма на человека
    ("Овсянка с сухофруктами","Овсяные хлопья","г",70),
    ("Овсянка с сухофруктами","Сухофрукты (микс)","г",30),
    ("Овсянка с сухофруктами","Сахар","г",10),
    ("Овсянка с сухофруктами","Соль","г",1),

    ("Сырники","Творог","г",180),
    ("Сырники","Яйцо куриное","шт",0.5),
    ("Сырники","Мука пшеничная","г",25),
    ("Сырники","Сахар","г",15),
    ("Сырники","Соль","г",1),
    ("Сырники","Масло растительное","мл",10),

    ("Гречка с тушёнкой","Гречка","г",80),
    ("Гречка с тушёнкой","Тушёнка говяжья","г",120),
    ("Гречка с тушёнкой","Лук репчатый","г",20),
    ("Гречка с тушёнкой","Соль","г",5),
    ("Гречка с тушёнкой","Специи","г",1),

    ("Паста с томатным соусом","Паста","г",100),
    ("Паста с томатным соусом","Томатная паста/соус","г",80),
    ("Паста с томатным соусом","Чеснок","г",5),
    ("Паста с томатным соусом","Оливковое масло","мл",10),
    ("Паста с томатным соусом","Соль","г",5),

    ("Рис с овощами и курицей","Рис","г",90),
    ("Рис с овощами и курицей","Курица (филе)","г",120),
    ("Рис с овощами и курицей","Морковь","г",30),
    ("Рис с овощами и курицей","Лук репчатый","г",20),
    ("Рис с овощами и курицей","Масло растительное","мл",10),
    ("Рис с овощами и курицей","Соль","г",5),

    ("Плов по-походному","Рис","г",100),
    ("Плов по-походному","Свинина/говядина","г",130),
    ("Плов по-походному","Морковь","г",40),
    ("Плов по-походному","Лук репчатый","г",25),
    ("Плов по-походному","Масло растительное","мл",12),
    ("Плов по-походному","Соль","г",5),
    ("Плов по-походному","Зира/специи","г",1),

    ("Шурпа упрощённая","Говядина","г",150),
    ("Шурпа упрощённая","Картофель","г",150),
    ("Шурпа упрощённая","Морковь","г",40),
    ("Шурпа упрощённая","Лук репчатый","г",25),
    ("Шурпа упрощённая","Соль","г",6),

    ("Борщ (концентрат) с мясом","Концентрат борща","г",40),
    ("Борщ (концентрат) с мясом","Говядина/свинина","г",120),
    ("Борщ (концентрат) с мясом","Картофель","г",120),
    ("Борщ (концентрат) с мясом","Соль","г",5),

    ("Овощи с фасолью (тушёные)","Фасоль консервированная","г",120),
    ("Овощи с фасолью (тушёные)","Томаты резаные","г",120),
    ("Овощи с фасолью (тушёные)","Лук репчатый","г",20),
    ("Овощи с фасолью (тушёные)","Масло растительное","мл",10),
    ("Овощи с фасолью (тушёные)","Соль","г",5),

    ("Бутерброды с сыром и колбасой","Хлеб","г",90),
    ("Бутерброды с сыром и колбасой","Сыр","г",50),
    ("Бутерброды с сыром и колбасой","Колбаса","г",60),
    ("Бутерброды с сыром и колбасой","Масло сливочное","г",10),
]

ПРИЕМЫ_ПИЩИ = ["Завтрак", "Обед", "Ужин"]

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
@st.cache_data
def загрузить_дефолтные_блюда():
    return pd.DataFrame(
        БЛЮДА_ПО_УМОЛЧАНИЮ,
        columns=["Блюдо","Ингредиент","Ед.изм","Норма на человека"]
    )

def excel_полный(параметры, план_df, блюда_df, закупка_df):
    """Генерит полный Excel с листами: Инструкция / Параметры / План / Блюда / Закупка."""
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    # Инструкция
    ws = wb.active; ws.title = "Инструкция"
    строки = [
        "Меню сплава: как пользоваться",
        "1) Параметры: задай Дни и Участников.",
        "2) План: выбери блюда по дням и приёмам пищи.",
        "3) Блюда: редактируй рецепты и нормы на человека.",
        "4) Закупка: итоговый список ингредиентов.",
    ]
    for i, t in enumerate(строки, 1):
        ws.cell(i,1,t)
    ws.column_dimensions["A"].width = 110

    # Параметры
    ws_in = wb.create_sheet("Параметры")
    ws_in.append(["Параметр","Значение"])
    ws_in.append(["Дни", параметры["days"]])
    ws_in.append(["Участники", параметры["participants"]])
    ws_in.column_dimensions["A"].width = 18
    ws_in.column_dimensions["B"].width = 14

    # План
    ws_p = wb.create_sheet("План")
    заголовки_план = ["День","Приём пищи","Блюдо"]
    ws_p.append(заголовки_план)
    for r in план_df[заголовки_план].itertuples(index=False):
        ws_p.append(list(r))
    for i,w in enumerate([8,16,36],1):
        ws_p.column_dimensions[get_column_letter(i)].width = w

    # Блюда
    ws_d = wb.create_sheet("Блюда")
    заголовки_блюда = ["Блюдо","Ингредиент","Ед.изм","Норма на человека"]
    ws_d.append(заголовки_блюда)
    for r in блюда_df[заголовки_блюда].itertuples(index=False):
        ws_d.append(list(r))
    for i,w in enumerate([28,30,10,18],1):
        ws_d.column_dimensions[get_column_letter(i)].width = w

    # Закупка
    ws_s = wb.create_sheet("Закупка")
    заголовки_закупка = ["Ингредиент","Ед.изм","Итого"]
    ws_s.append(заголовки_закупка)
    for r in закупка_df[заголовки_закупка].itertuples(index=False):
        ws_s.append(list(r))
    for i,w in enumerate([30,10,14],1):
        ws_s.column_dimensions[get_column_letter(i)].width = w

    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio

def pdf_закупка(закупка_df, font_path="DejaVuSans.ttf"):
    """PDF только с таблицей закупки (кириллица через TTF)."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("Не установлен пакет reportlab. Установи: pip install reportlab")

    # Регистрируем шрифт с кириллицей (если файл есть рядом)
    font_name = "Cyrillic"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    else:
        # Если TTF не нашли — используем Helvetica (кириллица может сломаться)
        font_name = "Helvetica"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles["Title"].fontName = font_name

    story = [Paragraph("Итоговая закупка для сплава", styles["Title"])]

    # Данные в таблицу
    данные = [list(закупка_df.columns)] + закупка_df.astype(str).values.tolist()
    table = Table(данные, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('FONTNAME', (0,0), (-1,0), font_name),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------- UI ----------
st.set_page_config(page_title="Меню сплава", layout="wide")
st.title("🛶 Калькулятор меню сплава")

col1, col2 = st.columns(2)
with col1:
    дни = st.number_input("Дни сплава", min_value=1, max_value=30, value=3, step=1)
with col2:
    участники = st.number_input("Участников", min_value=1, max_value=100, value=6, step=1)

# Редактирование базы блюд
if "блюда" not in st.session_state:
    st.session_state["блюда"] = загрузить_дефолтные_блюда()

st.subheader("📋 Блюда и нормы (на 1 человека)")
with st.expander("Редактирование рецептов", expanded=True):
    st.session_state["блюда"] = st.data_editor(
        st.session_state["блюда"],
        num_rows="dynamic",
        use_container_width=True,
        height=420,
        key="редактор_блюд",
    )
    # План по дням
st.subheader("🗓️ План по дням и приёмам пищи")
названия_блюд = ["— не выбрано —"] + sorted(st.session_state["блюда"]["Блюдо"].dropna().unique().tolist())

план_строки = []
колонки = st.columns(3)
for d in range(1, дни+1):
    with колонки[(d-1) % 3]:
        st.markdown(f"День {d}")
        for приём in ПРИЕМЫ_ПИЩИ:
            key = f"план_{d}_{приём}"
            выбор = st.selectbox(приём, названия_блюд, index=0, key=key)
            план_строки.append({"День": d, "Приём пищи": приём, "Блюдо": None if выбор == "— не выбрано —" else выбор})

план_df = pd.DataFrame(план_строки)

# Расчёт закупки
блюда_df = st.session_state["блюда"].dropna(subset=["Блюдо","Ингредиент","Ед.изм","Норма на человека"]).copy()
счётчики = план_df.dropna(subset=["Блюдо"]).groupby("Блюдо").size().rename("Сколько раз").reset_index()
расчёт = блюда_df.merge(счётчики, on="Блюдо", how="left").fillna({"Сколько раз":0})
расчёт["Итого по блюду"] = расчёт["Норма на человека"] * участники * расчёт["Сколько раз"]

закупка = (
    расчёт.groupby(["Ингредиент","Ед.изм"], as_index=False)["Итого по блюду"]
         .sum()
         .rename(columns={"Итого по блюду":"Итого"})
         .sort_values("Ингредиент")
)

# Итоговая закупка + кнопки
st.subheader("🛒 Итоговая закупка")
итог = закупка[закупка["Итого"] > 0].copy()
st.dataframe(итог, use_container_width=True)

# Excel (полный файл с листами)
excel_bytes = excel_полный(
    параметры={"days": int(дни), "participants": int(участники)},
    план_df=план_df,
    блюда_df=блюда_df,
    закупка_df=итог
)
st.download_button(
    "📥 Скачать Excel (полный файл)",
    data=excel_bytes,
    file_name="меню_сплава.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# PDF (только закупка, без нулей)
try:
    pdf_bytes = pdf_закупка(итог, font_path="DejaVuSans.ttf")
    st.download_button(
        "📥 Скачать PDF (только закупка)",
        data=pdf_bytes,
        file_name="закупка.pdf",
        mime="application/pdf",
    )
except Exception as e:
    st.warning(f"PDF сейчас недоступен: {e}\nПроверь, что установлен пакет reportlab и рядом лежит файл шрифта DejaVuSans.ttf.")
