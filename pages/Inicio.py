import streamlit as st
from PIL import Image
# from streamlit_dynamic_filters import DynamicFilters

def MDSetAppCFG():
    st.set_page_config(layout="wide")
    custom_html = """
    <div class="banner">
        <img src="https://meetingdoctors.com/app/themes/custom_theme/build/assets/img/logo_meeting_doctors.png" alt="Banner Image">
    </div>
    <style>
        .banner {
            width: 100%;
            height: 200px;
            overflow: hidden;
            background-color: #001042
        }
        .banner img {
            width: 100%;
            object-fit: cover;
            background-color: #001042
        }
    </style>
    """
    # Display the custom HTML
    # st.components.v1.html(custom_html)

def MDSidebar():
    image = Image.open("images/logos/MDLogo.png")
    st.sidebar.image(image)
    st.sidebar.header("Servicios")
    st.sidebar.page_link("pages/Inicio.py", label="Inicio")
    st.sidebar.page_link("pages/Chats.py", label="Chats")
    st.sidebar.page_link("pages/Videocalls.py", label="Videocalls")
    st.sidebar.page_link("pages/NPS.py", label="NPS")

def MDFilters(usersdf, specialitiesdf):
    st.sidebar.header("Filtros")
    st.sidebar.multiselect(
        "Año",
        ["2024", "2023", "2022"]
    )
    st.sidebar.multiselect(
        "Mes",
        ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    )
    st.sidebar.multiselect(
        "Grupos de usuario",
        usersdf
    )
    st.sidebar.multiselect(
        "Especialidad",
        specialitiesdf
    )

def MDConnection():
    # Initialize connection.
    conn = st.connection("snowflake")

    return conn

def MDGetMasterData(conn, tableName):
    # Perform query.
    df = conn.query("SELECT DISTINCT * from "+ chr(34) + tableName + chr(34) +";", ttl=600)

    return df

def MDGetFilteredData(conn, tableName):
    # Perform query.
    df = conn.query("SELECT DISTINCT * from "+ chr(34) + tableName + chr(34) +" WHERE " + chr(34) + "ApiKey" + chr(34) + " = 'ccdf91e84fda3ccf';", ttl=600)

    return df

MDSetAppCFG()
MDSidebar()

st.title('Meeting Doctors Analytics')
st.markdown(
    """
        ### Bienvenido a MD Analytics
        MD Analytics es un app mediante que permite el seguimiento y análisis básico de los distintos servicios contratados.

        👈 Mediante este selector puede seleccionar el servicio que deseas analizar

        **IMPORTANTE: Este dashboard no dispone de datos real-time.** Los datos a analizar siempre son hasta último día cerrado

        *Si tienes cualquier duda o incidencia con el dashboard, ponte en contacto con nuestro equipo de [data](mailto:data@meetingdoctors.com)*
    """
  )
st.subheader('Indicadores generales')

conn = MDConnection()
specialitiesdf = MDGetMasterData(conn,"specialities")
usersdf = MDGetFilteredData(conn,"users")

MDFilters(usersdf["UserCustomerGroup"].str.capitalize().unique(),specialitiesdf["SpecialityES"].unique())