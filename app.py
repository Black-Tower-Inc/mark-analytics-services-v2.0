import streamlit as st
from PIL import Image

def login():

    c1,c2 = st.columns(2)
    with c1:
        st.image("assets/Mark_white.png")
        st.image("assets/Mark_full_vertical_title.png")
        #st.title("Welcome!")
    with c2:
        st.empty()
    
    #st.header("Inicio de sesión")
    if st.button("Inicio de sesión"):
        st.login("auth0")

# def logout():
#     st.title("Cerrar sesión")
#     if st.button("Log out"):
#         st.logout()





# def login():
#     # Ajustes generales de la página
#     st.set_page_config(page_title="Inicio de sesión", layout="centered")


#     img1 = Image.open("assets/Mark_white.png")
#     img2 = Image.open("assets/Mark_full_vertical_title.png")

#     # # CSS personalizado para centrar y estilizar
#     # st.markdown("""
#     #     <style>
#     #         .main {
#     #             display: flex;
#     #             justify-content: center;
#     #             align-items: center;
#     #             height: 100vh;
#     #             background-color: #0e1117;
#     #         }
#     #         .login-card {
#     #             background-color: #161a23;
#     #             border-radius: 1rem;
#     #             padding: 3rem 2rem;
#     #             box-shadow: 0 0 20px rgba(0,0,0,0.4);
#     #             max-width: 400px;
#     #             width: 100%;
#     #             text-align: center;
#     #             color: #ffffff;
#     #             font-family: 'Segoe UI', sans-serif;
#     #         }
#     #         .login-card img {
#     #             max-width: 120px;
#     #             height: auto;
#     #             margin-bottom: 1rem;
#     #         }
#     #         .login-card h1 {
#     #             font-size: 1.8rem;
#     #             margin: 0.5rem 0 0.2rem;
#     #         }
#     #         .login-card h2 {
#     #             font-size: 1rem;
#     #             color: #00BFFF;
#     #             margin: 0;
#     #             font-weight: normal;
#     #         }
#     #         .login-card p {
#     #             font-size: 0.9rem;
#     #             margin-top: 1.5rem;
#     #             color: #cccccc;
#     #         }
#     #         .stButton > button {
#     #             background-color: #00BFFF;
#     #             color: white;
#     #             border: none;
#     #             border-radius: 5px;
#     #             padding: 0.6rem 1.2rem;
#     #             font-size: 1rem;
#     #             font-weight: bold;
#     #             margin-top: 1rem;
#     #         }
#     #         .stButton > button:hover {
#     #             background-color: #009ACD;
#     #         }
#     #     </style>
#     # """, unsafe_allow_html=True)

#     # # HTML estructurado
#     # st.markdown(f"""
#     #     <div class="main">
#     #         <div class="login-card">
#     #             <img src="assets/Mark_white.png" alt="Logo">
#     #             <img src="assets/Mark_full_vertical_title.png" alt="Título">
#     #             <h1>Bienvenido</h1>
#     #             <h2>AI Assistant</h2>
#     #             <p>Inicia sesión para acceder al sistema.</p>
#     # """, unsafe_allow_html=True)

#     # # Botón de login de Streamlit
#     # if st.button("Iniciar sesión"):
#     #     st.login("auth0")

#     # # Cierre del HTML
#     # st.markdown("</div></div>", unsafe_allow_html=True)


    
#     st.markdown('<div class="login-container"><div class="login-card">', unsafe_allow_html=True)

#     st.image(img1, use_column_width=True)
#     st.image(img2, use_column_width=True)

#     st.markdown('<div class="login-title">Bienvenido</div>', unsafe_allow_html=True)
#     st.markdown('<div class="login-subtitle">AI Assistant</div>', unsafe_allow_html=True)
#     st.markdown("Inicia sesión para comenzar a usar la plataforma.", unsafe_allow_html=True)

#     if st.button("Iniciar sesión"):
#         st.login("auth0")

#     st.markdown("</div></div>", unsafe_allow_html=True)










def logout():
    st.set_page_config(page_title="Cerrar sesión", layout="centered")

    st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
            color: white;
        }
        .logout-card {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            backdrop-filter: blur(6px);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<div class='logout-card'>", unsafe_allow_html=True)
            st.title("¿Deseas cerrar sesión?")
            if st.button("Cerrar sesión"):
                st.logout()
            st.markdown("</div>", unsafe_allow_html=True)





login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

dashboard = st.Page(
    "reports/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True
)

assumptions= st.Page(
    "reports/assumptions.py", title="Assumptions", icon=":material/dashboard:"
)

bugs = st.Page("reports/bugs.py", title="Bug reports", icon=":material/bug_report:")
alerts = st.Page(
    "reports/alerts.py", title="System alerts", icon=":material/notification_important:"
)

search = st.Page("tools/search.py", title="Search", icon=":material/search:")
history = st.Page("tools/history.py", title="History", icon=":material/history:")

settings = st.Page("tools/settings.py", title="Settings", icon=":material/search:")
usage = st.Page("tools/usage.py", title="Usage", icon=":material/history:")

if st.user.is_logged_in:
    pg = st.navigation(
        {
            "Account": [logout_page],
            "Reports": [dashboard,assumptions, bugs, alerts],
            "Tools": [search, history,settings, usage]
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()
