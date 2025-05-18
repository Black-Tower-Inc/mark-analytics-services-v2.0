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

# Conexión a MongoDB
MONGO_URI = os.getenv("URIMONGODB") 

client = MongoClient(MONGO_URI)

db = client[os.getenv("DATABASE")]

# # Conexión MongoDB
# client = MongoClient("TU_URI")
# database = client["TU_BASE_DE_DATOS"]


# Configurar conexión a MongoDB
client = MongoClient(MONGO_URI)

collection_usereminds_1 = db["userlists202505"]




collection_usereminds_2 = db["userlists202504"]

collection_usereminds_real = db["usereminds"]

collection_suscriptions = db["suscriptions"]

# Asignación de colecciones por mes
collections = [
    db["userlists202502"],  # febrero
    db["userlists202503"],  # marzo
    db["userlists202504"],  # abril
    db["userlists202505"],  # mayo
]





# Obtener datos de la colección
userlists_data = list(collection_usereminds_1.find({}, {"cdate": 1}))

# Extraer las horas de los timestamps
hours = [doc["cdate"].hour for doc in userlists_data if "cdate" in doc]

# Contar ocurrencias por hora
hour_counts = Counter(hours)
hours_sorted = sorted(hour_counts.keys())
counts_sorted = [hour_counts[hour] for hour in hours_sorted]

# Crear la figura
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(hours_sorted, counts_sorted, color='skyblue')
ax.set_xticks(range(24))
ax.set_xlabel("Hora del día")
ax.set_ylabel("Cantidad de interacciones")
ax.set_title("Interacciones por Hora del Día")
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Mostrar en Streamlit
st.pyplot(fig)


# Obtener datos de la colección
userlists_data = list(collection_usereminds_1.find({}, {"cdate": 1}))

# Extraer las horas de los timestamps
hours = [doc["cdate"].hour for doc in userlists_data if "cdate" in doc]

# Contar ocurrencias por hora
hour_counts = Counter(hours)
hours_sorted = sorted(hour_counts.keys())
counts_sorted = [hour_counts[hour] for hour in hours_sorted]

# Crear gráfica interactiva con Plotly
fig = px.bar(
    x=hours_sorted, 
    y=counts_sorted, 
    labels={'x': 'Hora del día', 'y': 'Cantidad de interacciones'}, 
    title="Interacciones por Hora del Día",
    text_auto=True
)

# Mostrar en Streamlit
st.plotly_chart(fig, use_container_width=True)



# Obtener datos de la colección
userlists_data = list(collection_usereminds_1.find({}, {"cdate": 1}))

# Mapeo de días de la semana
dias_semana = ["L", "M", "X", "J", "V", "S", "D"]

# Extraer los días de la semana
dias = [dias_semana[doc["cdate"].weekday()] for doc in userlists_data if "cdate" in doc]

# Contar ocurrencias por día
dias_counts = Counter(dias)
dias_sorted = ["L", "M", "X", "J", "V", "S", "D"]  # Orden correcto
counts_sorted = [dias_counts[dia] for dia in dias_sorted]

# Crear gráfica interactiva con Plotly
fig = px.bar(
    x=dias_sorted, 
    y=counts_sorted, 
    labels={'x': 'Día de la semana', 'y': 'Cantidad de interacciones'}, 
    title="Interacciones por Día de la Semana",
    text_auto=True
)

# Mostrar en Streamlit
st.plotly_chart(fig, use_container_width=True)

# Función para obtener los datos de MongoDB
def obtener_datos_actividad():
    hoy = datetime.utcnow()
    primer_dia = datetime(hoy.year, hoy.month, 1)
    
    pipeline = [
        {"$match": {"userid": {"$nin": [
            "whatsapp:+5212741410473", 
            "whatsapp:+5212292271390", 
            "whatsapp:+5212292071173"
        ]}
        
        ,"userprompt": { "$nin":["¿Alguna notificación nueva para mi?"]}

        }}, 
        {"$project": {
            "hour": {"$hour": "$cdate"},
            "day_of_week": {"$dayOfWeek": "$cdate"}  # 1=Sunday, 2=Monday, ..., 7=Saturday
        }},
        {"$group": {
            "_id": {"day_of_week": "$day_of_week", "hour": "$hour"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.day_of_week": 1, "_id.hour": 1}}
    ]
    
    data = list(collection_usereminds_1.aggregate(pipeline))
    
    if not data:
        return pd.DataFrame(columns=["Dia de la semana", "Hora", "Actividad"])
    
    # Crear el DataFrame
    df = pd.DataFrame(data)
    df['Dia de la semana'] = df['_id'].apply(lambda x: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'][x['day_of_week'] - 1])
    df['Hora'] = df['_id'].apply(lambda x: x['hour'])
    df['Actividad'] = df['count']
    
    return df[['Dia de la semana', 'Hora', 'Actividad']]

# Construcción de la interfaz en Streamlit
st.title("📊 Actividad de los usuarios: Días de la semana y Horas")

# Botón para actualizar datos
if st.button("Actualizar Datos de Actividad", key="actualizar_datos_actividad"):
    df_actividad = obtener_datos_actividad()
    st.success("Datos actualizados correctamente.")
else:
    df_actividad = obtener_datos_actividad()

# Mostrar la gráfica de burbujas si hay datos
if not df_actividad.empty:
    fig_actividad = px.scatter(df_actividad, 
                               x='Dia de la semana', 
                               y='Hora', 
                               size='Actividad', 
                               size_max=30,  # Ajusta el tamaño máximo de las burbujas
                               color='Actividad', 
                               hover_data=['Actividad'], 
                               title='Concentración de actividad de usuarios por día de la semana y hora',
                               labels={'Dia de la semana': 'Día de la semana', 'Hora': 'Hora', 'Actividad': 'Actividad de usuarios'},
                               template="seaborn")

    # Ajustar el layout
    fig_actividad.update_layout(
        width=800, 
        height=600, 
        showlegend=False, 
        xaxis_title="Día de la semana", 
        yaxis_title="Hora del día",
        title="Concentración de actividad de usuarios por día de la semana y hora"
    )
    
    st.plotly_chart(fig_actividad)
else:
    st.warning("No hay datos disponibles para mostrar.")


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
            "userid": {"$nin": ["5212292071173", "5212741410473", "5212292271390"]}
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
print(df)

# 7. Conclusión específica para 'Notify'
df_notify = df[df["type"] == "Notify"]
min_uso = df_notify["porcentaje"].min() if not df_notify.empty else 0
max_uso = df_notify["porcentaje"].max() if not df_notify.empty else 0

st.subheader("📌 Conclusión sobre 'Notify'")
st.write("Asunción: El servicio de las notificaciones o recordatorios automáticos, será consumida de un 50% a un 90% por los usuarios, en los primeros 3 meses.")
if min_uso >= 50 and max_uso <= 90:
    st.success(f"✅ El consumo de 'Notify' se encuentra dentro del rango estimado (50%-90%): de {min_uso:.1f}% a {max_uso:.1f}%.")
elif df_notify.empty:
    st.error("❌ No se encontraron registros del tipo 'Notify' en los últimos 3 meses.")
else:
    st.warning(f"⚠️ El consumo de 'Notify' está fuera del rango: de {min_uso:.1f}% a {max_uso:.1f}%.")


# 7b. Conclusión específica para 'Tarea' (o el tipo que uses)
df_tareas = df[df["type"] == "Task"]  # Ajusta el nombre si usas otro tipo exacto
min_uso_tareas = df_tareas["porcentaje"].min() if not df_tareas.empty else 0
max_uso_tareas = df_tareas["porcentaje"].max() if not df_tareas.empty else 0

st.subheader("📌 Conclusión sobre 'Task'")
st.write("Asunción: Las tareas será lo más consultado por los usuarios hasta en un 70% más que otras funciones.")
if max_uso_tareas >= 70:
    st.success(f"✅ Las tareas son lo más consultado por los usuarios, con un consumo máximo de {max_uso_tareas:.1f}%, que es hasta un 70% más que otras funciones.")
elif df_tareas.empty:
    st.error("❌ No se encontraron registros del tipo 'Task' en los últimos 3 meses.")
else:
    st.warning(f"ℹ️ Las tareas tienen un consumo menor al 70% ({max_uso_tareas:.1f}%).")

