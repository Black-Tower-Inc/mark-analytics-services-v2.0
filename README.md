# 🔐 Aplicación Full Stack en Python con Streamlit + Auth0

Esta es una **aplicación full stack** desarrollada en **Python** usando el framework **[Streamlit](https://streamlit.io/)**. Utiliza **Auth0** como proveedor de autenticación para gestionar el inicio de sesión de forma segura y escalable.

---

## 🚀 ¿Cómo ejecutar la aplicación?

```
streamlit run app.py
```

---

## ⚙️ Requisitos previos

- Tener **Python 3.11+** instalado.
- Tener acceso a internet para usar Auth0.
- Tener una cuenta en [Auth0](https://auth0.com/).

---

## 🛠️ Pasos para configurar y ejecutar

### 1. 🧪 Crear un entorno virtual

#### En Windows:

```
python -m venv venv
venv\Scripts\activate
```

#### En macOS/Linux:

```
python3 -m venv venv
source venv/bin/activate
```

---

### 2. 📦 Instalar dependencias

Asegúrate de estar en el entorno virtual y luego ejecuta:

```
pip install -r requirements.txt
```

---

### 3. 🔐 Configurar autenticación con Auth0

1. Accede a [Auth0](https://auth0.com/) y crea una cuenta.
2. Crea una **nueva aplicación**.
3. Elige **"Aplicación Web Regular"** y selecciona la tecnología **Python**.
4. Ve al apartado **Settings** y copia los siguientes datos:
   - `Client ID`
   - `Client Secret`
   - `Domain`
5. Crea un archivo `.streamlit/secrets.toml` en la raíz del proyecto y añade lo siguiente:

```
[auth0]
client_id = "TU_CLIENT_ID"
client_secret = "TU_CLIENT_SECRET"
domain = "TU_DOMINIO.auth0.com"
```

6. En Auth0, ve a **User Management** y crea un usuario para poder acceder a la app.
7. *(Opcional)* Para añadir otros proveedores de inicio de sesión (como Google), sigue la documentación de Auth0:  
   👉 https://auth0.com/docs/authenticate/identity-providers

---

## 🔑 Enlace útil de login en Streamlit

Consulta la documentación oficial de Streamlit sobre autenticación:  
👉 https://docs.streamlit.io/develop/api-reference/user/st.login

---

## 📁 Estructura recomendada del proyecto

```
.
├── app.py
├── requirements.txt
├── venv/
└── .streamlit/
    └── secrets.toml
```

---

## ✅ ¡Todo listo! Ejecuta la aplicación

```
streamlit run app.py
```

Abre tu navegador y accede a la app protegida por Auth0 🎉
