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
# Tema oscuro visual
st.set_page_config(page_title="Trazabilidad por Usuario", layout="wide")

import plotly.express as px
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
from streamlit_plotly_events import plotly_events


#import streamlit as st
#import pandas as pd
import seaborn as sns
#import matplotlib.pyplot as plt
#from pymongo import MongoClient
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA




import calendar

st.markdown("""
    <style>
    body, .stApp { background-color: #0e1117; color: white; }
    .css-1v0mbdj, .css-ffhzg2, .css-1cypcdb, .css-1v3fvcr { color: white; }
    </style>
""", unsafe_allow_html=True)


# import streamlit as st
# import pymongo
# import pandas as pd
# import plotly.express as px


load_dotenv()

# mongo_uri = st.secrets["DB"]["URIMONGODB"]
# db_name = st.secrets["DB"]["DATABASE"]

# Conexión a MongoDB
MONGO_URI = st.secrets["DB"]["URIMONGODB"] #os.getenv("URIMONGODB") 

client = MongoClient(MONGO_URI)

db = client[st.secrets["DB"]["DATABASE"]]

# # Conexión MongoDB
# client = MongoClient("TU_URI")
# database = client["TU_BASE_DE_DATOS"]


# Configurar conexión a MongoDB
client = MongoClient(MONGO_URI)

collection_usereminds_1 = db["userlists202506"]




collection_usereminds_2 = db["userlists202504"]

collection_usereminds_real = db["usereminds"]

collection_suscriptions = db["suscriptions"]

# Asignación de colecciones por mes
collections = [
    db["userlists202502"],  # febrero
    db["userlists202503"],  # marzo
    db["userlists202504"],  # abril
    db["userlists202505"],  # mayo
    db["userlists202506"]  # mayo
]


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
                "whatsapp:+5212292071173", 
                "5212292468193"
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


    # hoy = datetime.utcnow()
    # primer_dia = datetime(hoy.year, hoy.month, 1)
    

    # pipeline = [
    #     {"$match": {
    #         "type": { "$in": ["Notify", "Shopping", "Task", "Lists", "Note", "Date", "Other"] },
    #         "cdate": { "$gte": primer_dia, "$lte": hoy },
    #         "userid": { "$nin": [
    #             "whatsapp:+5212741410473", 
    #             "whatsapp:+5212292271390", 
    #             "whatsapp:+5212292071173", 
    #             "5212292468193"
    #         ]}


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
                "whatsapp:+5212292071173", 
                "5212292468193"
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
            "whatsapp:+5212292071173", 
            "5212292468193"
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
    meses_objetivo = ["202503", "202504", "202505","202506"]  # Abril–Julio 2025
    colecciones = [f"userlists{mes}" for mes in meses_objetivo]

    pipeline_base = [
        {
            "$match": {
                "userid": {
                    "$nin": [
                        "whatsapp:+5212741410473", 
                        "whatsapp:+5212292271390", 
                        "whatsapp:+5212292071173", 
                        "5212292468193"
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
                        "whatsapp:+5212292071173", 
                        "5212292468193"
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
meses = ["202503","202504", "202505", "202506"]
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
                            "whatsapp:+5212292071173", 
                            "5212292468193"
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
            "whatsapp:+5212292071173", 
            "5212292468193"
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










# import streamlit as st
# import pymongo
# import pandas as pd
# import plotly.express as px
# import datetime

# # Conexión a MongoDB
# client = pymongo.MongoClient("mongodb://localhost:27017/")  # Ajusta si usas credenciales/remoto
db = client["arcobits"]
collection = db["suscriptions"]

# Fechas de febrero a junio 2025
start_ts = int(datetime(2025, 2, 1).timestamp())
end_ts = int(datetime(2025, 6, 30, 23, 59, 59).timestamp())

# # Consulta con filtro por status 'active'
# query = {
#     "start_date": {
#         "$gte": start_ts,
#         "$lte": end_ts
#     },
#     "status": "active"
# }
# data = list(collection.find(query))

# Lista de usuarios a excluir
excluded_users = [
    "5212292071173",
    "5212741410473",
    "5212292271390",
    "5212292468193"
]

# Consulta con filtro por status 'active' y exclusión de usuarios
query = {
    "start_date": {"$gte": start_ts, "$lte": end_ts},
    "status": "active",
    "phone": {"$nin": excluded_users}
}
data = list(collection.find(query))

# Procesar resultados
records = []
for doc in data:
    phone = doc.get("phone", "Sin número")
    start_date = datetime.fromtimestamp(doc["start_date"])
    freecredits = doc.get("freecredits", 100)
    
    # Normalizar: evitar valores negativos
    used = max(0, 100 - freecredits)

    records.append({
        "Usuario": phone,
        "Fecha": start_date,
        "Créditos Usados": used,
        "Créditos Restantes": freecredits
    })

# Convertir a DataFrame
df = pd.DataFrame(records)

# Evitar lista vacía
if df.empty:
    st.warning("No hay usuarios activos con suscripción entre febrero y junio 2025.")
else:
    # Gráfico de burbujas
    fig = px.scatter(
        df,
        x="Fecha",
        y="Créditos Usados",
        size="Créditos Usados",
        color="Usuario",
        hover_data=["Créditos Restantes"],
        title="📊 Consumo de Créditos por Usuario Activo (febrero - junio 2025)",
        height=600
    )

    fig.update_yaxes(range=[0, 100], title="Consumo de créditos (100 = nada usado, 0 = todo usado)")
    fig.update_layout(xaxis_title="Fecha de inicio de suscripción")

    st.title("📊 Gráfico de Burbujas: Consumo de Créditos (Usuarios Activos)")
    st.plotly_chart(fig)
















# Conexión
#client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["arcobits"]

# Rango de meses
months = [2, 3, 4, 5, 6]
year = 2025

# Excluir usuarios de mantenimiento o sistema
excluded_userids = [
    "5212292071173",
    "5212741410473",
    "5212292271390",
    "5212292468193",
    "whatsapp:+5212741410473", 
    "whatsapp:+5212292271390", 
    "whatsapp:+5212292071173"
]

# Recolección de datos
records = []
for month in months:
    coll_name = f"userlists{year}{month:02d}"
    if coll_name not in db.list_collection_names():
        continue

    coll = db[coll_name]

    hoy = datetime.utcnow()
    primer_dia = datetime(2025, 2, 1)

    query = {
        "userid": {"$nin": excluded_userids},
        "userprompt": {"$not": {"$regex": "¿Alguna notificación nueva para mi\\?"}}
    }

    for doc in coll.find(query):
        userid = doc.get("userid")
        cdate_raw = doc.get("cdate")

        if not cdate_raw:
            continue

        if isinstance(cdate_raw, datetime):
            fecha_uso = cdate_raw
        else:
            try:
                fecha_uso = datetime.strptime(cdate_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    fecha_uso = datetime.strptime(cdate_raw, "%Y-%m-%d")
                except ValueError:
                    continue

        records.append({
            "Usuario": userid,
            "Fecha": fecha_uso.date(),
            "Timestamp": fecha_uso,
            "Uso": 1
        })

# Convertimos a DataFrame
df = pd.DataFrame(records)

if df.empty:
    st.warning("No hay datos de uso disponibles de febrero a junio 2025.")
else:
    # Agrupar por usuario y día
    daily_usage = df.groupby(["Usuario", "Fecha"]).agg({
        "Uso": "sum",
        "Timestamp": "first"
    }).reset_index()

    # Crear consumo acumulado por usuario
    daily_usage["Acumulado"] = daily_usage.groupby("Usuario")["Uso"].cumsum()

    # Gráfico
    fig = px.scatter(
        daily_usage,
        x="Fecha",
        y="Acumulado",
        size="Uso",
        color="Uso",
        color_continuous_scale="YlOrRd",
        hover_name="Usuario",
        title="📈 Continuidad e Intensidad de Uso por Usuario (feb-jun 2025)",
        height=600
    )

    fig.update_yaxes(title="Consumo Acumulado")
    fig.update_layout(xaxis_title="Fecha de Uso")

    st.title("📈 Burbujas de Continuidad de Uso")
    st.plotly_chart(fig)








    db = client["arcobits"]

# Rango de meses
months = [2, 3, 4, 5, 6]
year = 2025

# Excluir usuarios de mantenimiento o sistema
excluded_userids = [
    "5212292071173",
    "5212741410473",
    "5212292271390",
    "5212292468193",
    "whatsapp:+5212741410473", 
    "whatsapp:+5212292271390", 
    "whatsapp:+5212292071173"
]

# Recolección de datos
records = []
for month in months:
    coll_name = f"userlists{year}{month:02d}"
    if coll_name not in db.list_collection_names():
        continue

    coll = db[coll_name]

    query = {
        "userid": {"$nin": excluded_userids},
        "userprompt": {"$not": {"$regex": "¿Alguna notificación nueva para mi\\?"}}
    }

    for doc in coll.find(query):
        userid = doc.get("userid")
        cdate_raw = doc.get("cdate")

        if not cdate_raw:
            continue

        if isinstance(cdate_raw, datetime):
            fecha_uso = cdate_raw
        else:
            try:
                fecha_uso = datetime.strptime(cdate_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    fecha_uso = datetime.strptime(cdate_raw, "%Y-%m-%d")
                except ValueError:
                    continue

        records.append({
            "Usuario": userid,
            "Fecha": fecha_uso.date(),
            "Timestamp": fecha_uso,
            "Uso": 1
        })

# Convertimos a DataFrame
df = pd.DataFrame(records)

if df.empty:
    st.warning("No hay datos de uso disponibles de febrero a junio 2025.")
else:
    # Agrupar por usuario y día
    daily_usage = df.groupby(["Usuario", "Fecha"]).agg({
        "Uso": "sum",
        "Timestamp": "first"
    }).reset_index()

    # Crear consumo acumulado por usuario
    daily_usage["Acumulado"] = daily_usage.groupby("Usuario")["Uso"].cumsum()

    # Gráfico con color por usuario
    fig = px.scatter(
        daily_usage,
        x="Fecha",
        y="Acumulado",
        size="Uso",
        color="Usuario",  # <- cambio importante aquí
        hover_name="Usuario",
        title="📊 Continuidad de Uso por Usuario (colores por usuario)",
        height=600
    )

    fig.update_yaxes(title="Consumo Acumulado")
    fig.update_layout(xaxis_title="Fecha de Uso")

    st.title("📊 Burbujas por Usuario en el Tiempo")
    st.plotly_chart(fig)














db = client["arcobits"]

# Configuración
months_map = {
    "Todos": None,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6
}
type_options = ["Todos", "Notify", "Task", "Date", "Shopping","Note", "Other"]
year = 2025
excluded_userids = [
    "5212292071173",
    "5212741410473",
    "5212292271390",
    "5212292468193",
    "whatsapp:+5212741410473", 
    "whatsapp:+5212292271390", 
    "whatsapp:+5212292071173"
]

# Filtros
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    mes_seleccionado = st.radio("Mes:", list(months_map.keys()), horizontal=True)
with col2:
    tipo_seleccionado = st.radio("Tipo:", type_options, horizontal=True)
with col3:
    filtro_usuario = st.text_input("Buscar usuario (opcional):", "")

# Determinar meses
meses = [months_map[mes_seleccionado]] if months_map[mes_seleccionado] else [2, 3, 4, 5, 6]

# Recolección de datos
records = []
for month in meses:
    coll_name = f"userlists{year}{month:02d}"
    if coll_name not in db.list_collection_names():
        continue

    coll = db[coll_name]

    query = {
        "userid": {"$nin": excluded_userids},
        "userprompt": {"$not": {"$regex": "¿Alguna notificación nueva para mi\\?"}}
    }

    # Filtro por tipo
    if tipo_seleccionado != "Todos":
        query["type"] = tipo_seleccionado

    for doc in coll.find(query):
        userid = doc.get("userid", "")
        if filtro_usuario and filtro_usuario not in userid:
            continue

        cdate = doc.get("cdate")
        if not cdate or not isinstance(cdate, datetime):
            continue

        records.append({
            "Usuario": userid,
            "Fecha": cdate.date(),
            "Timestamp": cdate,
            "Uso": 1
        })

# Visualización
df = pd.DataFrame(records)

if df.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    # Agrupar y acumular
    daily_usage = df.groupby(["Usuario", "Fecha"]).agg({
        "Uso": "sum",
        "Timestamp": "first"
    }).reset_index()
    daily_usage["Acumulado"] = daily_usage.groupby("Usuario")["Uso"].cumsum()

    # Gráfico
    fig = px.scatter(
        daily_usage,
        x="Fecha",
        y="Acumulado",
        size="Uso",
        color="Usuario",
        hover_name="Usuario",
        title="📊 Trazabilidad de uso por usuario",
        height=600
    )
    fig.update_yaxes(title="Consumo Acumulado")
    fig.update_layout(xaxis_title="Fecha de Uso")

    st.title("📊 Consumo por Usuario")
    st.plotly_chart(fig)










#DataScience Clusters
# Titulo
st.title("Segmentación de Clientes con DBSCAN")

# Conexión MongoDB
#client = MongoClient("mongodb://localhost:27017")
db = client["arcobits"]

# Cargar datos de febrero a junio
docs = []
for month in range(2, 7):
    coll_name = f"userlists2025{month:02d}"
    collection = db[coll_name]
    docs += list(collection.find({
        "userprompt": {"$nin": ["¿Alguna notificación nueva para mi?"]},
        "userid": {"$nin": [
            "5212292071173",
            "5212741410473",
            "5212292271390",
            "5212292468193",
            "whatsapp:+5212741410473", 
            "whatsapp:+5212292271390", 
            "whatsapp:+5212292071173"
        ]}
    }))



# excluded_userids = [
#     "5212292071173",
#     "5212741410473",
#     "5212292271390",
#     "5212292468193",
#     "whatsapp:+5212741410473", 
#     "whatsapp:+5212292271390", 
#     "whatsapp:+5212292071173"
# ]


# DataFrame principal
df = pd.DataFrame(docs)

if df.empty:
    st.warning("No hay datos disponibles para mostrar.")
    st.stop()

# Parsear fecha y campos
st.subheader("Preprocesando datos...")
df["cdate"] = pd.to_datetime(df["cdate"])
df["month"] = df["cdate"].dt.month
df["day"] = df["cdate"].dt.day
df["year"] = df["cdate"].dt.year
df["userid"] = df["userid"].astype(str)
df["country"] = df["userid"].str[:2]
df["region"] = df["userid"].str[2:6]

# Freecredits desde suscriptions
subs_df = pd.DataFrame(list(db["suscriptions"].find({}, {"phone": 1, "freecredits": 1, "_id": 0})))
df = df.merge(subs_df, how="left", left_on="userid", right_on="phone")

# Limpiar y seleccionar
df = df[["type", "usermood", "importance", "month", "day", "year", "freecredits", "country", "region"]]
df = df.dropna()

# Preprocesamiento
categorical = ["type", "usermood", "country", "region"]
numerical = ["importance", "month", "day", "year", "freecredits"]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ("num", StandardScaler(), numerical)
])

#eps=1.5
pipeline = Pipeline([
    ("pre", preprocessor),
    ("dbscan", DBSCAN(eps=1.5, min_samples=2))
])

# Clustering
st.subheader("Ejecutando DBSCAN...")
df["cluster"] = pipeline.fit_predict(df)

# Reducir dimensiones para visualización
X_transformed = preprocessor.fit_transform(df)
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_transformed)
df["PCA1"] = X_pca[:, 0]
df["PCA2"] = X_pca[:, 1]

# Mostrar resultados
st.subheader("Resultados de Clustering")
st.write("Cantidad de usuarios por cluster:")
st.write(df["cluster"].value_counts().sort_index())

# Gráfico con tema oscuro
plt.style.use('dark_background')
sns.set(style="darkgrid", rc={"axes.facecolor": "#222222", "figure.facecolor": "#222222"})

fig, ax = plt.subplots(figsize=(12, 8))
scatter = sns.scatterplot(
    data=df,
    x="PCA1",
    y="PCA2",
    hue="cluster",
    palette="Set2",
    s=100,
    alpha=0.8,
    edgecolor="black",
    ax=ax
)

ax.grid(False)  # <- Aquí se quita la cuadrícula


plt.title("Visualización de Clusters en 2D (PCA)", fontsize=16, color="white")
plt.xlabel("Componente Principal 1", color="white")
plt.ylabel("Componente Principal 2", color="white")
# plt.xlabel("Componente Principal 1")
# plt.ylabel("Componente Principal 2")
plt.legend(title="Cluster", loc="upper right")
plt.tight_layout()

st.pyplot(fig)


# Mostrar tabla de resumen
st.subheader("Vista previa de datos segmentados")
st.dataframe(df.head(20))











#Buscando el codo para eps

import streamlit as st
from sklearn.neighbors import NearestNeighbors
import numpy as np
import matplotlib.pyplot as plt

# Supongamos que 'df' ya está preprocesado y tienes el preprocessor
X = preprocessor.fit_transform(df)  # Tus datos preprocesados

neighbors = NearestNeighbors(n_neighbors=5)
neighbors_fit = neighbors.fit(X)
distances, indices = neighbors_fit.kneighbors(X)

distances = np.sort(distances[:, 4])  # Distancia al 5to vecino más cercano

fig, ax = plt.subplots()
ax.plot(distances, color='white')
ax.set_ylabel("Distancia al 5to vecino", color='white')
ax.set_xlabel("Puntos ordenados", color='white')
ax.set_title("Curva para elegir eps en DBSCAN", color='white')
ax.grid(False)  # Quita la cuadrícula
fig.patch.set_facecolor('black')  # Fondo negro de la figura
ax.set_facecolor('black')  # Fondo negro del área del gráfico

st.pyplot(fig)



#probando valores para epsilon

# for eps_val in [0.5, 1, 1.5, 2]:
#     dbscan = DBSCAN(eps=eps_val, min_samples=5)
#     clusters = dbscan.fit_predict(X)
#     n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
#     n_noise = list(clusters).count(-1)
#     print(f"eps={eps_val} -> Clusters: {n_clusters}, Ruido: {n_noise}")




















# ##OKKK

# db = client["arcobits"]

# # Configuración
# months_map = {
#     "Todos": None,
#     "Febrero": 2,
#     "Marzo": 3,
#     "Abril": 4,
#     "Mayo": 5,
#     "Junio": 6
# }
# type_options = ["Todos", "Notify", "Task", "Date", "Other"]
# year = 2025
# excluded_userids = [
#     "5212292071173",
#     "5212741410473",
#     "5212292271390",
#     "5212292468193",
#     "whatsapp:+521274141
# 0473", 
#     "whatsapp:+5212292271390", 
#     "whatsapp:+5212292071173"
# ]


# # Filtros
# col1, col2, col3 = st.columns([1, 1, 2])
# with col1:
#     mes_seleccionado = st.radio("Mes:", list(months_map.keys()), horizontal=True)
# with col2:
#     tipo_seleccionado = st.radio("Tipo:", type_options, horizontal=True)
# with col3:
#     filtro_usuario = st.text_input("Buscar Usuario (opcional):", "")

# # Determinar meses
# meses = [months_map[mes_seleccionado]] if months_map[mes_seleccionado] else [2, 3, 4, 5, 6]

# # Recolección de datos
# records = []
# for month in meses:
#     coll_name = f"userlists{year}{month:02d}"
#     if coll_name not in db.list_collection_names():
#         continue

#     coll = db[coll_name]

#     query = {
#         "userid": {"$nin": excluded_userids},
#         "userprompt": {"$not": {"$regex": "¿Alguna notificación nueva para mi\\?"}}
#     }

#     # Filtro por tipo
#     if tipo_seleccionado != "Todos":
#         query["type"] = tipo_seleccionado

#     for doc in coll.find(query):
#         userid = doc.get("userid", "")
#         if filtro_usuario and filtro_usuario not in userid:
#             continue

#         cdate = doc.get("cdate")
#         if not cdate or not isinstance(cdate, datetime):
#             continue

#         records.append({
#             "Usuario": userid,
#             "Fecha": cdate.date(),
#             "Timestamp": cdate,
#             "Uso": 1
#         })

# # Visualización
# df = pd.DataFrame(records)

# if df.empty:
#     st.warning("No hay datos disponibles con los filtros seleccionados.")
# else:
#     # Agrupar y acumular
#     daily_usage = df.groupby(["Usuario", "Fecha"]).agg({
#         "Uso": "sum",
#         "Timestamp": "first"
#     }).reset_index()
#     daily_usage["Acumulado"] = daily_usage.groupby("Usuario")["Uso"].cumsum()

#     # Gráfico
#     fig = px.scatter(
#         daily_usage,
#         x="Fecha",
#         y="Acumulado",
#         size="Uso",
#         color="Usuario",
#         hover_name="Usuario",
#         title="📊 Trazabilidad de Uso por Usuario",
#         height=600
#     )
#     fig.update_yaxes(title="Consumo Acumulado")
#     fig.update_layout(xaxis_title="Fecha de Uso")

#     st.title("📊 Burbujas por Usuario")
#     st.plotly_chart(fig)



##OKK
# # Rango de meses
# months = [2, 3, 4, 5, 6]
# year = 2025

# # Excluir usuarios de mantenimiento o sistema
# excluded_userids = [
#     "5212292071173",
#     "5212741410473",
#     "5212292271390",
#     "5212292468193",
#     "whatsapp:+5212741410473", 
#     "whatsapp:+5212292271390", 
#     "whatsapp:+5212292071173"
# ]

# # Selector de tipo de entrada
# tipo_seleccionado = st.radio(
#     "Filtrar por tipo de uso:",
#     ("Todo", "Notify", "Task", "Other", "Date", "Shopping", "Note")
# )

# # Definimos el filtro 'type' según selección
# type_filter = {}
# if tipo_seleccionado != "Todo":
#     type_filter = {"type": tipo_seleccionado}

# # Recolección de datos
# records = []
# for month in months:
#     coll_name = f"userlists{year}{month:02d}"
#     if coll_name not in db.list_collection_names():
#         continue

#     coll = db[coll_name]

#     query = {
#         "userid": {"$nin": excluded_userids},
#         "userprompt": {"$not": {"$regex": "¿Alguna notificación nueva para mi\\?"}},
#         **type_filter
#     }

#     for doc in coll.find(query):
#         userid = doc.get("userid")
#         cdate_raw = doc.get("cdate")

#         if not cdate_raw:
#             continue

#         if isinstance(cdate_raw, datetime):
#             fecha_uso = cdate_raw
#         else:
#             try:
#                 fecha_uso = datetime.strptime(cdate_raw, "%Y-%m-%d %H:%M:%S")
#             except ValueError:
#                 try:
#                     fecha_uso = datetime.strptime(cdate_raw, "%Y-%m-%d")
#                 except ValueError:
#                     continue

#         records.append({
#             "Usuario": userid,
#             "Fecha": fecha_uso.date(),
#             "Timestamp": fecha_uso,
#             "Uso": 1
#         })

# # Convertimos a DataFrame
# df = pd.DataFrame(records)

# if df.empty:
#     st.warning("No hay datos disponibles para la selección actual.")
# else:
#     # Agrupar por usuario y día
#     daily_usage = df.groupby(["Usuario", "Fecha"]).agg({
#         "Uso": "sum",
#         "Timestamp": "first"
#     }).reset_index()

#     # Crear consumo acumulado por usuario
#     daily_usage["Acumulado"] = daily_usage.groupby("Usuario")["Uso"].cumsum()

#     # Gráfico con color por usuario
#     fig = px.scatter(
#         daily_usage,
#         x="Fecha",
#         y="Acumulado",
#         size="Uso",
#         color="Usuario",
#         hover_name="Usuario",
#         title=f"📊 Uso por Usuario - Filtro: {tipo_seleccionado}",
#         height=600
#     )

#     fig.update_yaxes(title="Consumo Acumulado")
#     fig.update_layout(xaxis_title="Fecha de Uso")

#     st.title("📊 Burbujas por Usuario en el Tiempo")
#     st.plotly_chart(fig)