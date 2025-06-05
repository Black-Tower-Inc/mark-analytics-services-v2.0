#import streamlit as st

#st.warning("This is the dashboard placeholder.")

# -*- coding: utf-8 -*-
"""
Created on Sat Mar  8 13:09:00 2025

@author: pedrobm
"""

import os
import pytz
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil.relativedelta import relativedelta

load_dotenv()


# mongo_uri = st.secrets["DB"]["URIMONGODB"]
# db_name = st.secrets["DB"]["DATABASE"]

# Conexión a MongoDB
MONGO_URI = st.secrets["DB"]["URIMONGODB"]

client = MongoClient(MONGO_URI)

db = client[st.secrets["DB"]["DATABASE"]]

# # Conexión MongoDB
# client = MongoClient("TU_URI")
# database = client["TU_BASE_DE_DATOS"]

###########################################################################################
#################Grafica de asunción para medir el uso de notificaciones###################
###########################################################################################
# 1. Obtener los últimos 3 periodos (año+mes) en formato 'YYYYMM'
hoy = datetime.utcnow()
fechas_aniomes = [(hoy - relativedelta(months=i)).strftime("%Y%m") for i in range(3)]

# 2. Filtrar las colecciones que correspondan a esos periodos
colecciones_analizar = [db[f"userlists{aniomes}"] for aniomes in fechas_aniomes if f"userlists{aniomes}" in db.list_collection_names()]

# 3. Extraer y agrupar los datos por 'type' para cada colección (periodo)
registros = []
for col in colecciones_analizar:
    aniomes = col.name[-6:]  # Extrae año+mes del nombre de la colección

    pipeline = [
        {"$match": {
            "userprompt": {"$nin": ["¿Alguna notificación nueva para mi?"]},
            "userid": {"$nin": ["5212292071173", "5212741410473", "5212292271390", "5212292468193"]},
            "type": {"$ne": "Other"}
        }},
        {"$group": {"_id": "$type", "total": {"$sum": 1}}},  # Agrupa por 'type' contando documentos
    ]

    resultados = col.aggregate(pipeline)
    for r in resultados:
        registros.append({
            "aniomes": aniomes,
            "type": r["_id"] or "Desconocido",
            "total": r["total"]
        })

# 4. Crear DataFrame
df = pd.DataFrame(registros)

# 5. Calcular porcentaje que representa cada 'type' dentro del total mensual
df_total_aniomes = df.groupby("aniomes")["total"].sum().reset_index(name="total_mes")
df = df.merge(df_total_aniomes, on="aniomes")
df["porcentaje"] = (df["total"] / df["total_mes"]) * 100

# 6. Graficar barras apiladas por 'type' para cada periodo (año+mes)
st.title("📊 Consumo por tipo de interacción (últimos 3 meses).")
st.write("Asunción: El servicio de las notificaciones o recordatorios automáticos, será consumida de un 50% a un 90% por los usuarios, en los primeros 3 meses.")
st.write("Asunción: Las tareas será lo más consultado por los usuarios hasta en un 70% más que otras funciones.")
df["aniomes"] = df["aniomes"].astype(str).str.strip()

orden_aniomes = sorted(fechas_aniomes)

fig = px.bar(
    df,
    x="aniomes",
    y="porcentaje",
    color="type",
    text=df["porcentaje"].apply(lambda x: f"{x:.1f}%"),  # formato texto en %
    title="Distribución de tipos de interacciones por periodo (YYYYMM)",
    labels={"aniomes": "Periodo (YYYYMM)", "porcentaje": "Porcentaje de uso", "type": "Tipo"},
    barmode="stack",
    category_orders={"aniomes": orden_aniomes}
)

fig.update_layout(
    xaxis=dict(
        type='category',
        categoryorder='array',
        categoryarray=orden_aniomes,
        tickmode='array',
        tickvals=orden_aniomes,
        ticktext=orden_aniomes
    )
)

st.plotly_chart(fig)

# 7. Estado actual específica para 'Notify'
df_notify = df[df["type"] == "Notify"]
min_uso = df_notify["porcentaje"].min() if not df_notify.empty else 0
max_uso = df_notify["porcentaje"].max() if not df_notify.empty else 0

st.subheader("📌 Estado actual de la asunción sobre 'Notify'")
if min_uso >= 50 and max_uso <= 90:
    st.success(f"✅ Se cumple. El consumo de 'Notify' se encuentra dentro del rango estimado (50%-90%): de {min_uso:.1f}% a {max_uso:.1f}%.")
elif df_notify.empty:
    st.error("❌ No se encontraron registros del tipo 'Notify' en los últimos 3 meses.")
else:
    st.warning(f"⚠️ No se cumple. El consumo de 'Notify' está fuera del rango: de {min_uso:.1f}% a {max_uso:.1f}%.")


# 7b. Estado actual específica para 'Tarea' (o el tipo que uses)
df_tareas = df[df["type"] == "Task"]  # Ajusta el nombre si usas otro tipo exacto
min_uso_tareas = df_tareas["porcentaje"].min() if not df_tareas.empty else 0
max_uso_tareas = df_tareas["porcentaje"].max() if not df_tareas.empty else 0

st.subheader("📌 Estado actual de la asunción sobre 'Task'")

if max_uso_tareas >= 70:
    st.success(f"✅ Se cumple. Las tareas son lo más consultado por los usuarios, con un consumo máximo de {max_uso_tareas:.1f}%, que es hasta un 70% más que otras funciones.")
elif df_tareas.empty:
    st.error("❌ No se encontraron registros del tipo 'Task' en los últimos 3 meses.")
else:
    st.warning(f"⚠️ No se cumple. Las tareas tienen un consumo menor al 70% ({max_uso_tareas:.1f}%).")

###########################################################################################
#################Grafica de asunción para medir felicidad de usuarios######################
###########################################################################################
# 1. Obtener los últimos 3 periodos (año+mes) en formato 'YYYYMM'

hoy = datetime.utcnow()
fechas_aniomes = [(hoy - relativedelta(months=i)).strftime("%Y%m") for i in range(3)]

estados_buenos = ['S', 'T', 'I']

registros = []
detalle_usuarios = []  # Lista para guardar detalle de cada usuario

for aniomes in fechas_aniomes:
    col_name = f"userlists{aniomes}"
    if col_name not in db.list_collection_names():
        continue
    
    col = db[col_name]
    
    # Usar aggregate con filtro 
    pipeline = [
        {"$match": {
            "userprompt": {"$nin": ["¿Alguna notificación nueva para mi?"]},
            "userid": {"$nin": ["5212292071173", "5212741410473", "5212292271390", "5212292468193"]}
        }},
        {"$project": {
            "userid": 1,
            "usermood": 1
        }}
    ]
    
    cursor = col.aggregate(pipeline)
    df = pd.DataFrame(list(cursor))
    
    if df.empty:
        continue
    
    df['usermood'] = df['usermood'].fillna('N')
    
    # Guardar detalle de cada usuario en esta colección para tabla final
    for userid, grupo in df.groupby("userid")["usermood"]:
        buenos = grupo.isin(estados_buenos).sum()
        sin_sentimiento = (grupo == 'N').sum()
        malos = len(grupo) - buenos - sin_sentimiento
        detalle_usuarios.append({
            "aniomes": aniomes,
            "userid": userid,
            "sentimientos_buenos": buenos,
            "sentimientos_malos": malos,
            "sin_sentimiento": sin_sentimiento
        })
    
    def usuario_feliz(moods):
        total = len(moods)
        buenos = moods.isin(estados_buenos).sum()
        return buenos > total / 2
    
    resumen = df.groupby("userid")["usermood"].apply(usuario_feliz).reset_index(name="es_feliz")
    
    total_usuarios = resumen.shape[0]
    usuarios_felices = resumen["es_feliz"].sum()
    
    registros.append({
        "aniomes": aniomes,
        "total_usuarios": total_usuarios,
        "usuarios_felices": usuarios_felices
    })

df_final = pd.DataFrame(registros)

if df_final.empty or df_final["total_usuarios"].sum() == 0:
    st.warning("No hay datos para el servicio 'Mark' en los últimos 3 meses.")
else:
    df_final["porcentaje_felices"] = (df_final["usuarios_felices"] / df_final["total_usuarios"]) * 100
    
    st.title("📊 Experiencia de usuarios 'Mark' (últimos 3 meses)")
    st.write("Asunción: El servicio 'Mark' mantendrá una calificación buena a excelente en al menos el 90% de los usuarios en los últimos 3 meses.")
    # Asegurar que aniomes sea string
    df_final["aniomes"] = df_final["aniomes"].astype(str)
    
    # Orden explícito para el eje X
    orden_aniomes = sorted(fechas_aniomes)
    
    fig = px.bar(
        df_final,
        x="aniomes",
        y="porcentaje_felices",
        text=df_final["porcentaje_felices"].apply(lambda x: f"{x:.1f}%"),
        labels={"aniomes": "Periodo (YYYYMM)", "porcentaje_felices": "Porcentaje de Usuarios Felices"},
        title="Porcentaje de usuarios con experiencia buena a excelente en 'Mark'",
        range_y=[0, 100],
        category_orders={"aniomes": orden_aniomes}
    )
    
    fig.update_layout(
        xaxis=dict(
            type='category',
            categoryorder='array',
            categoryarray=orden_aniomes,
            tickmode='array',
            tickvals=orden_aniomes,
            ticktext=orden_aniomes
        )
    )
    
    st.plotly_chart(fig)
    
    min_p = df_final["porcentaje_felices"].min()
    max_p = df_final["porcentaje_felices"].max()
    
    st.subheader("📌 Estado actual de la asunción ")
    if min_p >= 90:
        st.success(f"✅ Se cumple. La experiencia de 'Mark' está dentro del rango esperado (>= 90%), con valores de {min_p:.1f}% a {max_p:.1f}%.")
    else:
        st.warning(f"⚠️ No se cumple. La experiencia de 'Mark' bajó del 90% en algunos meses: rango de {min_p:.1f}% a {max_p:.1f}%.")

    # Mostrar tabla con detalles de usuarios y conteos
    df_detalle = pd.DataFrame(detalle_usuarios)
    if not df_detalle.empty:
        st.subheader("📋 Detalle de sentimientos por usuario y periodo")
        st.dataframe(df_detalle.sort_values(["aniomes", "userid"]))


###########################################################################################
#################Entre semana se consume más Mark que en el fin de semana.#################
###########################################################################################
# 1. Obtener datos como antes
registros = []
for col in colecciones_analizar:
    pipeline = [
        {
            "$match": {
                "userprompt": {"$nin": ["¿Alguna notificación nueva para mi?"]},
                "userid": {
                    "$nin": [
                        "5212292071173",
                        "5212741410473",
                        "5212292271390",
                        "5212292468193",
                    ]
                },
            }
        }
    ]

    for doc in col.aggregate(pipeline):
        fecha = doc.get("cdate") or doc.get("timestamp")
        if fecha:
            fecha = fecha if isinstance(fecha, datetime) else fecha["$date"]
            isocal = fecha.isocalendar()
            registros.append({
                "fecha": fecha,
                "año": isocal.year,
                "semana": isocal.week,
                "dia_semana": fecha.weekday(),
                "categoria_dia": "Entre semana" if fecha.weekday() < 5 else "Fin de semana"
            })

# 2. Crear DataFrame
df = pd.DataFrame(registros)

# 3. Agrupar por semana y tipo de día
df["semana_id"] = df["año"].astype(str) + "-W" + df["semana"].astype(str).str.zfill(2)

df_agrupado = df.groupby(["semana_id", "categoria_dia"]).size().reset_index(name="total")

# 4. Calcular porcentaje semanal
df_total_semana = df_agrupado.groupby("semana_id")["total"].sum().reset_index(name="total_semana")
df_agrupado = df_agrupado.merge(df_total_semana, on="semana_id")
df_agrupado["porcentaje"] = (df_agrupado["total"] / df_agrupado["total_semana"]) * 100

# 5. Gráfico de área apilada
st.title("📈 Consumo entre semana vs fin de semana por semana")
st.write("Asunción: Entre semana se consume más Mark que en el fin de semana (por semana, últimos 3 meses).")

fig = px.area(
    df_agrupado,
    x="semana_id",
    y="porcentaje",
    color="categoria_dia",
    line_group="categoria_dia",
    groupnorm="percent",
    title="Distribución porcentual del consumo por semana",
    labels={"semana_id": "Semana", "porcentaje": "Porcentaje", "categoria_dia": "Día"}
)

fig.update_layout(xaxis=dict(type="category"))

st.plotly_chart(fig)

# 6. Evaluar cumplimiento por semana
semanas = df["semana_id"].unique()
df_semana = df_agrupado[df_agrupado["categoria_dia"] == "Entre semana"]
df_finde = df_agrupado[df_agrupado["categoria_dia"] == "Fin de semana"]

cumple = all(
    df_semana[df_semana["semana_id"] == s]["porcentaje"].values[0] >
    df_finde[df_finde["semana_id"] == s]["porcentaje"].values[0]
    for s in semanas
    if s in df_semana["semana_id"].values and s in df_finde["semana_id"].values
)

st.subheader("📌 Estado actual de la asunción")

if cumple:
    st.success("✅ Se cumple. En todas las semanas, el consumo entre semana supera al del fin de semana.")
elif df.empty:
    st.error("❌ No se encontraron registros en las semanas analizadas.")
else:
    st.warning("⚠️ No se cumple. Hay semanas donde el consumo en fin de semana iguala o supera al de entre semana.")


###########################################################################################
###Las personas que más frecuentan a Mark son las que más consumen notificaciones al mes.##
###########################################################################################

# 1. Obtener los últimos 3 periodos (año+mes) en formato 'YYYYMM'
hoy = datetime.utcnow()
fechas_aniomes = [(hoy - relativedelta(months=i)).strftime("%Y%m") for i in range(2, -1, -1)]

# 2. Filtrar las colecciones válidas
colecciones_analizar = {
    aniomes: db[f"userlists{aniomes}"]
    for aniomes in fechas_aniomes
    if f"userlists{aniomes}" in db.list_collection_names()
}

# 3. Obtener los datos por mes
registros = []
for aniomes, col in colecciones_analizar.items():
    pipeline = [
        {
            "$match": {
                "userprompt": {"$nin": ["¿Alguna notificación nueva para mi?"]},
                "userid": {"$nin": ["5212292071173", "5212741410473", "5212292271390", "5212292468193"]},
                "type": {"$ne": "Other"}
            }
        }
    ]
    for doc in col.aggregate(pipeline):
        registros.append({
            "userid": doc.get("userid"),
            "type": doc.get("type"),
            "aniomes": aniomes
        })

# 4. Crear DataFrame
df = pd.DataFrame(registros)

if df.empty:
    st.warning("No hay datos para los periodos seleccionados.")
else:
    # 5. Identificar usuarios top por mes
    df_mes = df.groupby(["aniomes", "userid"]).size().reset_index(name="interacciones")
    top_usuarios_mes = df_mes.groupby("aniomes").apply(
        lambda g: g[g["interacciones"] >= g["interacciones"].max() / 2]
    ).reset_index(drop=True)

    # 6. Filtrar los datos solo para usuarios top por mes
    df_top = df.merge(top_usuarios_mes[["aniomes", "userid"]], on=["aniomes", "userid"])

    # 7. Contar interacciones por mes, usuario y tipo
    df_mes_usuario = df_top.groupby(["aniomes", "userid", "type"]).size().reset_index(name="count")

    # 8. Pivot para análisis
    df_pivot = df_mes_usuario.pivot_table(index=["aniomes", "userid"], columns="type", values="count", fill_value=0).reset_index()

    # 9. Calcular total interacciones por usuario y mes
    df_pivot["total"] = df_pivot.loc[:, df_pivot.columns.difference(["aniomes", "userid"])].sum(axis=1)

    # 10. Determinar si cumple la asunción por usuario y mes: Notify > 50%
    df_pivot["cumple_asuncion"] = df_pivot.get("Notify", 0) > (df_pivot["total"] / 2)

    # 11. Evaluar si al menos la mitad de usuarios cumplen la asunción por mes
    resultado_mes = df_pivot.groupby("aniomes").agg(
        usuarios_total=("userid", "nunique"),
        usuarios_cumplen=("cumple_asuncion", "sum")
    ).reset_index()
    resultado_mes["asuncion_cumple"] = resultado_mes["usuarios_cumplen"] >= (resultado_mes["usuarios_total"] / 2)

    # 12. Preparar datos para gráfica de distribución por tipo
    df_grafica = df_top.groupby(["aniomes", "type"]).size().reset_index(name="total")
    df_total_mes = df_grafica.groupby("aniomes")["total"].sum().reset_index(name="total_mes")
    df_grafica = df_grafica.merge(df_total_mes, on="aniomes")
    df_grafica["porcentaje"] = (df_grafica["total"] / df_grafica["total_mes"]) * 100

    # 13. Graficar barras apiladas
    fig = px.bar(
        df_grafica,
        x="aniomes",
        y="porcentaje",
        color="type",
        text=df_grafica["porcentaje"].apply(lambda x: f"{x:.1f}%"),
        title="Distribución de tipos de interacción por periodo (YYYYMM) - Usuarios Top por Mes",
        labels={"aniomes": "Periodo", "porcentaje": "Porcentaje de uso", "type": "Tipo"},
        barmode="stack",
        category_orders={"aniomes": fechas_aniomes}
    )
    fig.update_layout(
        xaxis=dict(
            type='category',
            categoryorder='array',
            categoryarray=fechas_aniomes,
            tickmode='array',
            tickvals=fechas_aniomes,
            ticktext=fechas_aniomes
        )
    )

    st.title("🔍 Interacciones de usuarios más activos por mes (últimos 3 meses)")
    st.write("Asunción: Las personas que más frecuentan a Mark son las que más consumen notificaciones al mes.")
    st.plotly_chart(fig)

    # 14. Mostrar evaluación de la asunción por mes
    st.subheader("📌 Estado actual de la asunción")
    for _, fila in resultado_mes.iterrows():
        mes = fila["aniomes"]
        cumple = fila["asuncion_cumple"]
        porcentaje = (fila["usuarios_cumplen"] / fila["usuarios_total"]) * 100 if fila["usuarios_total"] > 0 else 0
        if cumple:
            st.success(
                f"✅ En {mes} se cumple la asunción entre los usuarios que más utilizan a Mark. "
                f"{porcentaje:.1f}% de ellos tienen más del 50% de sus interacciones del tipo Notify."
            )
        else:
            st.warning(
                f"⚠️ En {mes} NO se cumple la asunción entre los usuarios que más utilizan a Mark. "
                f"Solo {porcentaje:.1f}% de ellos tienen más del 50% de sus interacciones del tipo Notify."
            )

    # 15. Tabla de detalle por usuario
    df_pivot["periodo"] = pd.to_datetime(df_pivot["aniomes"], format="%Y%m").dt.strftime("%m/%Y")
    tipos = [col for col in df_pivot.columns if col not in ['aniomes', 'userid', 'total', 'periodo', 'cumple_asuncion']]
    cols_orden = ['periodo', 'userid'] + tipos + ['total']
    df_mostrar = df_pivot[cols_orden].rename(columns={'userid': 'usuario'})

    st.subheader("📊 Detalle de interacciones por usuario y periodo (ordenado)")

    # Ordenar
    df_mostrar = df_mostrar.sort_values(by=['periodo', 'total'], ascending=[False, False])

    # Reemplazar ceros con vacío
    df_mostrar = df_mostrar.replace(0, "")

    # Mostrar tabla sin estilos ni colores
    st.dataframe(df_mostrar)
