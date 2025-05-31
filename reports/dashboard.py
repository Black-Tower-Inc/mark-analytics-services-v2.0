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
import phonenumbers
from phonenumbers import geocoder, timezone, carrier
from phonenumbers import geocoder, timezone, region_code_for_number
import pycountry
import altair as alt
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

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


def limpiar_prefijo(numero):
    """Elimina un '1' adicional si está después del código de país."""
    try:
        numero_parseado = phonenumbers.parse(numero)
        codigo_pais = numero_parseado.country_code
        prefijo_pais = f"+{codigo_pais}"
        
        # Extraer la parte nacional del número
        numero_nacional = numero[len(prefijo_pais):]  

        if numero_nacional.startswith("1"):
            return prefijo_pais + numero_nacional[1:]  # Elimina el '1' extra
                    
        return numero
    
    except Exception:

        return numero  # Devuelve el número sin modificar en caso de error


# Función auxiliar: obtener zona horaria estimada por número
def obtener_informacion_numero(numero):
    """Obtiene información del número: país, estado, zona horaria y hora actual."""
    try:
        if not numero.startswith("+"):

            numero = "+" + numero

            numero_limpio = limpiar_prefijo(numero)

            numero_parseado = phonenumbers.parse(numero_limpio)

            zonas_horarias = timezone.time_zones_for_number(numero_parseado)

            return zonas_horarias[0] if zonas_horarias else "UTC"
        
    except Exception as e:


        return "America/Mexico_City"


# Función para obtener los datos de MongoDB y procesar los resultados
def obtener_datos_series_un_mes():
    hoy = datetime.now()
    primer_dia = datetime(hoy.year, hoy.month, 1)
    

    pipeline = [
        {"$match": {
            "type": { "$in": ["Notify", "Shopping", "Task", "Lists", "Note", "Date", "Other"] },
            "cdate": { "$gte": primer_dia, "$lte": hoy },
            "userid": { "$nin": [
                "whatsapp:+5212741410473", 
                "whatsapp:+5212292271390", 
                "whatsapp:+5212292071173"
            ]}

            ,"userprompt": { "$nin":["¿Alguna notificación nueva para mi?"]}

        }},
        {"$group": {
            "_id": {
                "year": { "$year": "$cdate" },
                "month": { "$month": "$cdate" },
                "day": { "$dayOfMonth": "$cdate" },
                "type": "$type"
            },
            "count": { "$sum": 1 }
        }},
        {"$group": {
            "_id": {
                "year": "$_id.year",
                "month": "$_id.month",
                "day": "$_id.day"
            },
            "types": { "$push": { "type": "$_id.type", "count": "$count" } },
            "total_count": { "$sum": "$count" }
        }},
        { "$sort": { "_id.year": 1, "_id.month": 1, "_id.day": 1 }}
    ]
    
    data = list(collection_usereminds_1.aggregate(pipeline))

    #data2 = list(collection_usereminds_2.aggregate(pipeline))
    
    if not data:
        return pd.DataFrame(columns=["Fecha", "Notify", "Shopping", "Task", "Lists", "Note", "Date", "Other"])

    # Procesar los datos en formato adecuado
    rows = []
    for record in data:
        fecha = f'{record["_id"]["year"]}-{record["_id"]["month"]}-{record["_id"]["day"]}'
        tipo_count = { "Fecha": fecha }
        for tipo in ["Notify", "Shopping", "Task", "Lists", "Note", "Date", "Other"]:
            tipo_count[tipo] = next((x["count"] for x in record["types"] if x["type"] == tipo), 0)
        rows.append(tipo_count)

    df = pd.DataFrame(rows)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


def obtener_datos_series():
    hoy = datetime.now()
    primer_dia = datetime(2025, 2, 1)  # desde febrero 2025

    pipeline = [
        {"$match": {
            "type": { "$in": ["Notify", "Shopping", "Task", "Lists", "Note", "Date", "Other"] },
            "cdate": { "$gte": primer_dia, "$lte": hoy },
            "userid": { "$nin": [
                "whatsapp:+5212741410473", 
                "whatsapp:+5212292271390", 
                "whatsapp:+5212292071173"
            ]},
            "userprompt": { "$nin": ["¿Alguna notificación nueva para mi?"] }
        }},
        {"$group": {
            "_id": {
                "year": { "$year": "$cdate" },
                "month": { "$month": "$cdate" },
                "day": { "$dayOfMonth": "$cdate" },
                "type": "$type"
            },
            "count": { "$sum": 1 }
        }},
        {"$group": {
            "_id": {
                "year": "$_id.year",
                "month": "$_id.month",
                "day": "$_id.day"
            },
            "types": { "$push": { "type": "$_id.type", "count": "$count" } },
            "total_count": { "$sum": "$count" }
        }},
        { "$sort": { "_id.year": 1, "_id.month": 1, "_id.day": 1 }}
    ]

    # Ejecutar el pipeline en todas las colecciones
    all_data = []
    for col in collections:
        result = list(col.aggregate(pipeline))
        all_data.extend(result)

    if not all_data:
        return pd.DataFrame(columns=["Fecha", "Notify", "Shopping", "Task", "Lists", "Note", "Date", "Other"])

    # Convertir a DataFrame
    rows = []
    for entry in all_data:
        fecha = datetime(entry['_id']['year'], entry['_id']['month'], entry['_id']['day'])
        row = {
            "Fecha": fecha,
            "Notify": 0, "Shopping": 0, "Task": 0,
            "Lists": 0, "Note": 0, "Date": 0, "Other": 0
        }
        for t in entry['types']:
            row[t['type']] = t['count']
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sort_values(by="Fecha").reset_index(drop=True)
    return df

def obtener_audiencia_diaria_de_un_mes():
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
        {"$group": {
            "_id": {
                "year": {"$year": "$cdate"},
                "month": {"$month": "$cdate"},
                "day": {"$dayOfMonth": "$cdate"},
                "userid": "$userid"
            }
        }},
        {"$group": {
            "_id": {
                "year": "$_id.year",
                "month": "$_id.month",
                "day": "$_id.day"
            },
            "votos": {"$sum": 1}
        }},
        {"$sort": {
            "_id.year": 1, 
            "_id.month": 1, 
            "_id.day": 1
        }}
    ]
    
    data = list(collection_usereminds_1.aggregate(pipeline))
    
    if not data:
        return pd.DataFrame(columns=["Fecha", "Votos"])
    
    df = pd.DataFrame(data)
    df["Fecha"] = pd.to_datetime(df["_id"].apply(lambda x: f'{x["year"]}-{x["month"]}-{x["day"]}'))
    df["Votos"] = df["votos"]
    return df[["Fecha", "Votos"]]



def obtener_audiencia_diaria():
    meses_objetivo = ["202503", "202504", "202505"]  # Abril–Julio 2025
    colecciones = [f"userlists{mes}" for mes in meses_objetivo]

    pipeline_base = [
        {
            "$match": {
                "userid": {
                    "$nin": [
                        "whatsapp:+5212741410473", 
                        "whatsapp:+5212292271390", 
                        "whatsapp:+5212292071173"
                    ]
                },
                "userprompt": {
                    "$nin": ["¿Alguna notificación nueva para mi?"]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$cdate"},
                    "month": {"$month": "$cdate"},
                    "day": {"$dayOfMonth": "$cdate"},
                    "userid": "$userid"
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "year": "$_id.year",
                    "month": "$_id.month",
                    "day": "$_id.day"
                },
                "votos": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "_id.year": 1,
                "_id.month": 1,
                "_id.day": 1
            }
        }
    ]

    resultados = []

    for col in colecciones:
        collection = db[col]
        resultados.extend(list(collection.aggregate(pipeline_base)))

    if not resultados:
        return pd.DataFrame(columns=["Fecha", "Votos"])

    df = pd.DataFrame(resultados)
    df["Fecha"] = pd.to_datetime(df["_id"].apply(lambda x: f'{x["year"]}-{x["month"]}-{x["day"]}'))
    df["Votos"] = df["votos"]
    return df[["Fecha", "Votos"]]



# Función para obtener los datos de MongoDB
def obtener_datos():
    pipeline = [
        {
            "$match": {
                "userid": { 
                    "$nin": [
                        "whatsapp:+5216641975849", "bautismen", "16315551181", "139", "whatsapp:+5212282452733", 
                        "whatsapp:+5212281819194", "whatsapp:+5212299575809", "whatsapp:+5212291470698", 
                        "whatsapp:+5212291699231", "16239800755", "whatsapp:+5212291016445", "whatsapp:+5214777873094",
                        "whatsapp:+5212291400309", "whatsapp:+5219131021907", "whatsapp:+5212292071173", 
                        "whatsapp:+5212741410473", "whatsapp:+5212291827438", "whatsapp:+5215568632305", 
                        "whatsapp:+5212741423164", "whatsapp:+5215538373175", "whatsapp:+5212741015659", 
                        "whatsapp:+5212297498880"
                    ]
                }

                ,"userprompt": { "$nin":["¿Alguna notificación nueva para mi?"]}

            }
        },
        {
            "$group": {
                "_id": "$userid",
                "count": { "$sum": 1 }
            }
        },
        {
            "$lookup": {
                "from": "suscriptions",
                "let": { "userid": "$_id" },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$eq": ["$phone", "$$userid"]
                            }
                        }
                    }
                ],
                "as": "subscription_info"
            }
        },
        {
            "$project": {
                "_id": 0,
                "userid": "$_id",
                "document_count": "$count",
                "subscription_info": 1
            }
        },
        {
            "$unwind": "$subscription_info"
        },
        {
            "$project": {
                "_id": 0,
                "userid": "$_id",
                "document_count": 1,
                "user_name": { 
                    "$ifNull": ["$subscription_info.name", "Desconocido"]
                },
                "phone": "$subscription_info.phone"
            }
        }
    ]
    
    data = list(collection_usereminds_real.aggregate(pipeline))
    
    if not data:
        return pd.DataFrame(columns=["userid", "document_count", "user_name", "phone"])

    df = pd.DataFrame(data)
    return df

def obtener_sentimientos_por_un_mes():
    start_date = datetime(2025, 3, 1)  # Primer día del mes de marzo 2025
    end_date = datetime(2026, 1, 1)   # Primer día de abril 2025 (para el rango de marzo)

    pipeline = [
        {
            "$match": {
                "cdate": { 
                    "$gte": start_date,  # Fecha de inicio
                    "$lt": end_date      # Fecha de fin
                },
                "userid": { 
                    "$nin": [
                        "whatsapp:+5212741410473", 
                        "whatsapp:+5212292271390", 
                        "whatsapp:+5212292071173"
                    ]
                }

                ,"userprompt": { "$nin":["¿Alguna notificación nueva para mi?"]}
            }
        },
        {
            "$group": {
                "_id": "$usermood",  # Agrupar por el tipo de sentimiento
                "count": { "$sum": 1 }
            }
        },
        {
            "$project": {
                "_id": 0,
                "Sentimiento": "$_id",  # Cambié "_id" por "Sentimiento"
                "Conteo": "$count"  # Cambié "count" por "Conteo"
            }
        },
        {
            "$sort": { "Sentimiento": 1 }
        }
    ]
    
    data = list(collection_usereminds_1.aggregate(pipeline))
    
    if not data:
        return pd.DataFrame(columns=["Sentimiento", "Conteo"])
    
    df = pd.DataFrame(data)
    return df

# Lista de meses a revisar
meses = ["202404", "202405", "202406", "202407"]
zona = "America_Mexico_City"  # Ajusta según tu zona

# client = MongoClient(MONGO_URI)

# db = client[os.getenv("DATABASE")]

# # Conexión MongoDB
# client = MongoClient("TU_URI")
# database = client["TU_BASE_DE_DATOS"]

def obtener_sentimientos():
    sentimiento_acumulado = {}

    for mes in meses:

        coleccion = db[f"usereminds{mes}_{zona}"]
        
        pipeline = [
            {
                "$match": {
                    "userid": { 
                        "$nin": [
                            "whatsapp:+5212741410473", 
                            "whatsapp:+5212292271390", 
                            "whatsapp:+5212292071173"
                        ]
                    },
                    "userprompt": { "$nin": ["¿Alguna notificación nueva para mi?"] }
                }
            },
            {
                "$group": {
                    "_id": "$usermood",
                    "count": { "$sum": 1 }
                }
            }
        ]

        for doc in coleccion.aggregate(pipeline):
            mood = doc["_id"] or "Sin clasificar"
            sentimiento_acumulado[mood] = sentimiento_acumulado.get(mood, 0) + doc["count"]

    if not sentimiento_acumulado:
        return pd.DataFrame(columns=["Sentimiento", "Conteo"])

    df = pd.DataFrame([
        {"Sentimiento": key, "Conteo": value}
        for key, value in sorted(sentimiento_acumulado.items())
    ])
    return df


def obtener_datos_series_freecredits_users():

    # Fechas
    fecha_inicio = datetime(2025, 2, 1)

    fecha_hoy = datetime.now()

    # Pipeline para MongoDB
    pipeline = [
        {
            "$match": {
                "freecredits": {"$gt" : 0},
                "phone": {
                    "$nin": [
                        "whatsapp:+5216641975849", "bautismen", "16315551181", "139", "whatsapp:+5212282452733", 
                        "whatsapp:+5212281819194", "whatsapp:+5212299575809", "whatsapp:+5212291470698", 
                        "whatsapp:+5212291699231", "16239800755", "whatsapp:+5212291016445", "whatsapp:+5214777873094",
                        "whatsapp:+5212291400309", "whatsapp:+5219131021907", "whatsapp:+5212292071173", 
                        "whatsapp:+5212741410473", "whatsapp:+5212291827438", "whatsapp:+5215568632305", 
                        "whatsapp:+5212741423164", "whatsapp:+5215538373175", "whatsapp:+5212741015659", 
                        "whatsapp:+5212297498880", "5212292071173","5212741410473","5212292271390","5212292468193"
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "phone": 1,
                "start_date": 1,
                "status": 1,
                "subscription_id": 1,
                "freecredits": 1
            }
        }
    ]

    # Consultar Mongo
    data = list(collection_suscriptions.aggregate(pipeline))

    if not data:
        return pd.DataFrame(columns=["phone", "start_date", "status", "subscription_id", "freecredits"])

    # Convertir a DataFrame
    df = pd.DataFrame(data)


    # # Convertir timestamp a datetime y zona horaria
    df["fecha_alta_utc"] = pd.to_datetime(df["start_date"], unit="s", utc=True)


    df = df[["phone", "fecha_alta_utc", "subscription_id", "status", "freecredits"]]

    return df



# Construcción de la interfaz en Streamlit
st.title("📊 Dashboard de documentos generados Mark AI. 2025-2026")

# Botón para actualizar datos
if st.button("Actualizar Datos", key="actualizar_datos_documentos"):
    df = obtener_datos()
    st.success("Datos actualizados correctamente.")
else:
    df = obtener_datos()

# Mostrar tabla con los datos
st.write("### Datos extraídos de MongoDB")
st.dataframe(df)



# Generar y mostrar la gráfica si hay datos
if not df.empty:
    # Definir el gráfico con un tema predefinido, por ejemplo "seaborn"
    fig = px.bar(df, x='user_name', y='document_count', color='user_name', title='Documentos generados por usuario',
                template="seaborn")  # Aplica el tema seaborn
    
    fig.update_layout(
        bargap=0.2, 
        xaxis_tickangle=-45,  # Ángulo de los ticks del eje X
        xaxis_title='Nombre de usuarios',  # Título del eje X
        yaxis_title='Cantidad de documentos',  # Título del eje Y
        title='Documentos generados por usuario'  # Título general del gráfico
    )
    st.plotly_chart(fig)
else:
    st.warning("No hay datos disponibles para mostrar.")


    # Construcción de la interfaz en Streamlit
st.title("📊 Dashboard de tendencias Mark AI. 2025 (MES ACTUAL)")

# Botón para actualizar datos
if st.button("Actualizar Datos", key="actualizar_datos_audiencia_por_el_mes"):
    df_audiencia = obtener_audiencia_diaria_de_un_mes()
    st.success("Datos actualizados correctamente.")
else:
    df_audiencia = obtener_audiencia_diaria_de_un_mes()

# Mostrar gráfica de tendencia de audiencia
if not df_audiencia.empty:
    fig_audiencia = px.line(df_audiencia, x='Fecha', y='Votos', markers=True,
                            title='Tendencia de audiencia por día', template="seaborn")
    fig_audiencia.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Cantidad de usuarios únicos',
        title='Tendencia de audiencia por día',
    )
    st.plotly_chart(fig_audiencia)
else:
    st.warning("No hay datos disponibles para mostrar.")


# Construcción de la interfaz en Streamlit
st.title("📊 Dashboard de tendencias Mark AI. 2025 (MESES)")

# Botón para actualizar datos
if st.button("Actualizar Datos", key="actualizar_datos_audiencia_meses"):
    df_audiencia = obtener_audiencia_diaria()
    st.success("Datos actualizados correctamente.")
else:
    df_audiencia = obtener_audiencia_diaria()

# Agrupar por fecha y contar usuarios únicos (1 voto por usuario por día)
if not df_audiencia.empty:
    df_audiencia = df_audiencia.groupby("Fecha").agg({"Votos": "sum"}).reset_index()

    fig_audiencia = px.line(
        df_audiencia,
        x='Fecha',
        y='Votos',
        markers=True,
        title='Tendencia de audiencia por día (Usuarios únicos)',
        template="seaborn"
    )
    fig_audiencia.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Cantidad de usuarios únicos',
    )
    st.plotly_chart(fig_audiencia)
else:
    st.warning("No hay datos disponibles para mostrar.")







# Construcción de la interfaz en Streamlit
st.title("📊 Tipo de uso. Tendencias Mark AI. (MES ACTUAL)")

# Botón para actualizar datos
if st.button("Actualizar Datos", key="actualizar_datos_series_x"):
    df_series = obtener_datos_series_un_mes()
    st.success("Datos actualizados correctamente.")
else:
    df_series = obtener_datos_series_un_mes()

# Mostrar la gráfica si hay datos
if not df_series.empty:
    # Crear gráfica de líneas para mostrar la tendencia de los tipos de documento por día
    fig_series = px.line(df_series, x='Fecha', y=["Notify", "Shopping", "Task", "Lists", "Note", "Date", "Other"],
                        title='Tendencia de consumo por tipo de documento',
                        labels={"Fecha": "Fecha", "value": "Cantidad de documentos"},
                        markers=True, template="seaborn")
    
    fig_series.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Cantidad de documentos',
        title='Tendencia de consumo por tipo de documento',
    )
    
    st.plotly_chart(fig_series)
else:
    st.warning("No hay datos disponibles para mostrar.")





# Construcción de la interfaz en Streamlit
st.title("📊 Tipo de uso. Tendencias Mark AI.(MESES)")

# Botón para actualizar datos
if st.button("Actualizar Datos", key="actualizar_datos_series_meses"):
    df_series = obtener_datos_series()
    st.success("Datos actualizados correctamente.")
else:
    df_series = obtener_datos_series()

# Mostrar la gráfica si hay datos
if not df_series.empty:
    # Crear gráfica de líneas para mostrar la tendencia de los tipos de documento por día
    fig_series = px.line(df_series, x='Fecha', y=["Notify", "Shopping", "Task", "Lists", "Note", "Date", "Other"],
                        title='Tendencia de consumo por tipo de documento',
                        labels={"Fecha": "Fecha", "value": "Cantidad de documentos"},
                        markers=True, template="seaborn")
    
    fig_series.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Cantidad de documentos',
        title='Tendencia de consumo por tipo de documento',
    )
    
    st.plotly_chart(fig_series)
else:
    st.warning("No hay datos disponibles para mostrar.")



# Construcción de la interfaz en Streamlit
st.title("📊 Gráfico de Sentimientos de la Audiencia - (MES ACTUAL)")

# Botón para actualizar los datos
if st.button("Actualizar Datos de Sentimientos", key="actualizar_datos_sentimientos"):
    df_sentimientos = obtener_sentimientos_por_un_mes()
    st.success("Datos actualizados correctamente.")
else:
    df_sentimientos = obtener_sentimientos_por_un_mes()


# Mostrar gráfico de burbujas de sentimientos
if not df_sentimientos.empty:

    sentimientos = {
        "S": "Satisfacción ✅ – El usuario está feliz con la respuesta.",
        "F": "Frustración ❌ – Respuesta incorrecta o confusa.",
        "T": "Confianza 🔵 – Confianza en la IA, se siente respaldado.",
        "U": "Incertidumbre/Duda 🤔 – No está seguro sobre la respuesta.",
        "I": "Interés ✨ – Encuentra útil o interesante la IA.",
        "B": "Aburrimiento 😴 – Respuesta aburrida o sin interés."
    }

    df_sentimientos["Descripción"] = df_sentimientos["Sentimiento"].map(sentimientos)

    # Crear la gráfica de burbujas
    fig = px.scatter(df_sentimientos, 
                    x="Sentimiento", 
                    y="Conteo", 
                    size="Conteo", 
                    size_max=30,  # Reducir el tamaño máximo de las burbujas
                    color="Sentimiento", 
                    hover_name="Descripción",  # Mostrar la descripción al pasar el ratón
                    title="Distribución de Sentimientos de la Audiencia",
                    labels={"Sentimiento": "Sentimiento", "Conteo": "Cantidad de Respuestas"},
                    template="seaborn")

    # Ajustar el layout para darle más espacio a los ejes y más tamaño a la gráfica
    fig.update_layout(
        width=800,  # Ampliar el tamaño de la gráfica
        height=600,  # Ajustar la altura de la gráfica
        showlegend=False,  # Opcional, quitar la leyenda para una vista más limpia
        xaxis_title="Sentimiento",
        yaxis_title="Cantidad de Respuestas",
        title="Distribución de Sentimientos de la Audiencia"
    )

    #st.plotly_chart(fig)
    st.plotly_chart(fig, key="grafico_un_mes_sentimientos")







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




# Cosntrucción de la interfaz en Streamlit
st.title("📊 Créditos usuarios")

# Botón para actualizar datos
if st.button("Actualizar Datos", key="actualizar_datos_series_freecredits_users"):
    df_series = obtener_datos_series_freecredits_users()
    st.success("Datos actualizados correctamente.")
else:
    df_series = obtener_datos_series_freecredits_users()

# Mostrar la gráfica si hay datos
if not df_series.empty:
    # Crear gráfica de líneas para mostrar la tendencia de los tipos de documento por día

 
    # Asegúrate de que la columna sea datetime
    if not pd.api.types.is_datetime64_any_dtype(df_series["fecha_alta_utc"]):
        df_series["fecha_alta_utc"] = pd.to_datetime(df_series["fecha_alta_utc"], errors='coerce')

    # Crear columna de solo fecha
    df_series["fecha"] = df_series["fecha_alta_utc"].dt.date

    conteo_diario = df_series.groupby("fecha").size().reset_index(name="nuevos_usuarios")

    st.title("Usuarios con 100 créditos desde febrero 2025")

    chart = alt.Chart(conteo_diario).mark_line(point=True).encode(
        x="fecha:T",
        y="nuevos_usuarios:Q",
        tooltip=["fecha", "nuevos_usuarios"]
    ).properties(width=700, height=400)

    st.altair_chart(chart)

 

 

    # Crear columna de solo fecha
    df_series["fecha"] = df_series["fecha_alta_utc"].dt.date

    # Agregar etiquetas según estado de créditos
    df_series["estado_credito"] = df_series["freecredits"].apply(
        lambda x: "100 créditos intactos" if x == 100 else "Créditos consumidos"
    )

    # Agrupar por fecha y estado de crédito
    conteo_combinado = (
        df_series.groupby(["fecha", "estado_credito"])
        .size()
        .reset_index(name="cantidad")
    )

    # Gráfica combinada
    st.subheader("📊 Evolución de usuarios según uso de créditos")
    chart_combinado = alt.Chart(conteo_combinado).mark_line(point=True).encode(
        x="fecha:T",
        y="cantidad:Q",
        color="estado_credito:N",
        tooltip=["fecha", "estado_credito", "cantidad"]
    ).properties(width=750, height=400)

    st.altair_chart(chart_combinado)



    # 📊 Gráfica de puntos individuales con teléfonos
    st.subheader("📈 Usuarios con crédito (por teléfono)")

    chart_por_usuario = alt.Chart(df_series).mark_circle(size=100).encode(
        x="fecha:T",
        y=alt.Y("estado_credito:N", title="Estado de créditos"),
        color="estado_credito:N",
        tooltip=["phone", "fecha_alta_utc", "freecredits"]
    ).properties(width=750, height=400)

    st.altair_chart(chart_por_usuario)



    # Filtrar usuarios con créditos > 0 (excluye 0)
    df_filtrado = df_series[df_series["freecredits"] > 0].copy()

    # Crear columna para estado créditos
    df_filtrado["estado_credito"] = df_filtrado["freecredits"].apply(
        lambda x: "100 créditos intactos" if x == 100 else "Créditos consumidos"
    )

    # Crear columna solo fecha para agrupar
    df_filtrado["fecha"] = df_filtrado["fecha_alta_utc"].dt.date

    # Conteo diario por estado de crédito
    conteo_diario = df_filtrado.groupby(["fecha", "estado_credito"]).size().reset_index(name="usuarios")

    # Selección para interactividad
    selection = alt.selection_point(fields=["fecha", "estado_credito"], empty="all")

    # Gráfica de barras apiladas
    bar_chart = alt.Chart(conteo_diario).mark_bar().encode(
        x=alt.X("fecha:T", title="Fecha"),
        y=alt.Y("usuarios:Q", title="Número de usuarios"),
        color=alt.Color("estado_credito:N", title="Estado de crédito"),
        tooltip=["fecha", "estado_credito", "usuarios"],
        opacity=alt.condition(selection, alt.value(1), alt.value(0.6))
    ).add_params(selection).properties(
        width=700,
        height=400,
        title="Usuarios con créditos (excluyendo 0) por fecha y estado"
    )

    st.altair_chart(bar_chart)

    # Mostrar teléfonos filtrados según selección
    if selection:
        # Para que funcione en Streamlit, capturamos la selección con bind o workaround (más simple es filtrar con checkbox)
        st.subheader("📱 Números de teléfono según selección")

        # Como Altair + Streamlit no captura selección directamente, aquí mostramos todo agrupado o con filtro externo
        # Para ejemplo, mostramos la tabla completa agrupada

        # Mostrar tabla de teléfonos con créditos >0
        st.dataframe(
            df_filtrado[["phone", "freecredits", "fecha_alta_utc", "estado_credito"]]
            .sort_values(by=["fecha_alta_utc", "estado_credito"])
            .reset_index(drop=True)
        )

        # Filtros interactivos
        st.subheader("🔍 Filtros")

        # Rango de fechas
        fecha_min = df_series["fecha_alta_utc"].min().date()
        fecha_max = df_series["fecha_alta_utc"].max().date()
        fecha_rango = st.date_input(
            "Selecciona el rango de fechas",
            value=(fecha_min, fecha_max),
            min_value=fecha_min,
            max_value=fecha_max
        )

        # Estado de crédito
        mostrar_consumidos = st.checkbox("Mostrar créditos consumidos (< 100)", value=True)
        mostrar_intactos = st.checkbox("Mostrar créditos intactos (= 100)", value=True)

        # Aplicar filtros
        df_filtrado = df_series.copy()
        df_filtrado["fecha_alta_utc"] = pd.to_datetime(df_filtrado["fecha_alta_utc"])
        df_filtrado["fecha_alta_date"] = df_filtrado["fecha_alta_utc"].dt.date

        df_filtrado = df_filtrado[
            (df_filtrado["fecha_alta_date"] >= fecha_rango[0]) &
            (df_filtrado["fecha_alta_date"] <= fecha_rango[1])
        ]

        if not mostrar_consumidos:
            df_filtrado = df_filtrado[df_filtrado["freecredits"] == 100]
        if not mostrar_intactos:
            df_filtrado = df_filtrado[df_filtrado["freecredits"] < 100]

        # Excluir los que tienen 0 créditos
        df_filtrado = df_filtrado[df_filtrado["freecredits"] > 0]

        # Clasificar estado de créditos
        df_filtrado["estado_credito"] = df_filtrado["freecredits"].apply(
            lambda x: "100 créditos intactos" if x == 100 else "Créditos consumidos"
        )

        # Ordenar por fecha para mejor visualización
        df_filtrado = df_filtrado.sort_values(by="fecha_alta_utc")

        # Gráfico de líneas
        st.subheader("📈 Créditos por teléfono (líneas)")

        grafica = alt.Chart(df_filtrado).mark_line(point=True).encode(
            x=alt.X("phone:N", title="Teléfono", sort=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("freecredits:Q", title="Créditos disponibles"),
            color=alt.Color("estado_credito:N", title="Estado"),
            tooltip=["phone", "freecredits", "fecha_alta_utc"]
        ).properties(
            width=900,
            height=500
        )

        st.altair_chart(grafica)

        st.subheader("📈 Créditos por teléfono agrupados por fecha de alta")

        # Asegurarse de que fecha_alta_utc es datetime y obtener solo la fecha
        df_filtrado["fecha_alta"] = pd.to_datetime(df_filtrado["fecha_alta_utc"]).dt.date

        # Excluir los que tienen 0 créditos
        df_plot = df_filtrado[df_filtrado["freecredits"] > 0]

        # Gráfico de líneas con puntos y etiquetas por teléfono
        line_chart = alt.Chart(df_plot).mark_line(point=True).encode(
            x=alt.X("fecha_alta:T", title="Fecha de alta"),
            y=alt.Y("freecredits:Q", title="Créditos disponibles"),
            color=alt.Color("phone:N", title="Teléfono"),
            tooltip=["phone", "freecredits", "fecha_alta"]
        ).properties(width=700, height=400)

        # Agregar etiquetas de teléfono en los puntos
        text_labels = alt.Chart(df_plot).mark_text(
            align='left',
            dx=5,
            dy=-5,
            fontSize=10
        ).encode(
            x="fecha_alta:T",
            y="freecredits:Q",
            text="phone:N",
            color=alt.Color("phone:N", legend=None)
        )

        # Mostrar ambos
        st.altair_chart(line_chart + text_labels, use_container_width=True)


        st.subheader("📊 Dispersión de créditos por teléfono")

        # Asegurar formato correcto
        df_filtrado["fecha_alta"] = pd.to_datetime(df_filtrado["fecha_alta_utc"]).dt.date

        # Filtrar los que tienen más de 0 créditos
        df_dispersión = df_filtrado[df_filtrado["freecredits"] > 0]

        # Gráfico de dispersión
        scatter = alt.Chart(df_dispersión).mark_circle(size=100).encode(
            x=alt.X("fecha_alta:T", title="Fecha de alta"),
            y=alt.Y("freecredits:Q", title="Créditos disponibles"),
            color=alt.Color("phone:N", title="Teléfono"),
            tooltip=["phone", "freecredits", "fecha_alta"]
        ).properties(width=800, height=400)

        # Etiquetas con los teléfonos
        labels = alt.Chart(df_dispersión).mark_text(
            align='center',
            dy=-12,
            fontSize=10
        ).encode(
            x="fecha_alta:T",
            y="freecredits:Q",
            text="phone:N",
            color=alt.Color("phone:N", legend=None)
        )

        # Mostrar gráfico combinado
        st.altair_chart(scatter + labels, use_container_width=True)



        st.subheader("📈 Dispersión y regresión: Créditos vs Fecha de alta")

        # Asegurar tipo de fecha
        df_filtrado["fecha_alta"] = pd.to_datetime(df_filtrado["fecha_alta_utc"]).dt.date

        # Solo con créditos > 0
        df_dispersión = df_filtrado[df_filtrado["freecredits"] > 0]

        # Gráfico de dispersión
        puntos = alt.Chart(df_dispersión).mark_circle(size=80).encode(
            x=alt.X("fecha_alta:T", title="Fecha de alta"),
            y=alt.Y("freecredits:Q", title="Créditos disponibles"),
            color=alt.Color("phone:N", title="Teléfono"),
            tooltip=["phone", "freecredits", "fecha_alta"]
        )

        # Línea de regresión (polinómica de grado 2 para detectar curvatura/tendencia)
        regresion = puntos.transform_regression(
            "fecha_alta",
            "freecredits",
            method="poly",
            order=2,
            as_=["fecha_alta", "freecredits"]
        ).mark_line(color="black")

        # Etiquetas con teléfono
        etiquetas = alt.Chart(df_dispersión).mark_text(
            align='center',
            dy=-10,
            fontSize=9
        ).encode(
            x="fecha_alta:T",
            y="freecredits:Q",
            text="phone:N",
            color=alt.Color("phone:N", legend=None)
        )

        # Mostrar todo
        st.altair_chart((puntos + regresion + etiquetas).properties(width=800, height=400), use_container_width=True)



        st.subheader("📊 Dispersión con línea de regresión")

        # Asegurar formato de fecha
        df_filtrado["fecha_alta"] = pd.to_datetime(df_filtrado["fecha_alta_utc"]).dt.date

        # Solo créditos > 0
        df_dispersión = df_filtrado[df_filtrado["freecredits"] > 0].copy()

        # Convertir fecha a ordinal para regresión lineal (Altair necesita numérico)
        df_dispersión["fecha_ordinal"] = pd.to_datetime(df_dispersión["fecha_alta"]).map(pd.Timestamp.toordinal)

        # Puntos
        puntos = alt.Chart(df_dispersión).mark_point(filled=True, color='steelblue').encode(
            x=alt.X("fecha_ordinal:Q", title="Fecha (ordinal)"),
            y=alt.Y("freecredits:Q", title="Créditos disponibles"),
            tooltip=["phone", "freecredits", "fecha_alta"]
        )

        # Línea de regresión lineal
        regresion = puntos.transform_regression(
            "fecha_ordinal", "freecredits",
            method="linear"
        ).mark_line(color='red')

        # Eje con fechas reales
        ticks = alt.Axis(format='%Y-%m-%d')

        # Combinar gráfico y ajustar eje x con fechas legibles
        final_chart = (puntos + regresion).encode(
            x=alt.X("fecha_ordinal:Q", axis=ticks, title="Fecha")
        ).properties(width=700, height=400)

        st.altair_chart(final_chart, use_container_width=True)




else:
    
    st.warning("No hay datos disponibles para mostrar.")
