import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
# from streamlit_dynamic_filters import DynamicFilters

def MDSetAppCFG():
    LogoMini = Image.open("images/logos/MDLogoMini.png")
    st.set_page_config(layout="wide", page_title="MeetingDoctors - Analytics", page_icon=LogoMini)
    st.html(
        """
        <style>
            [data-testid="stSidebarContent"] {
                background-color: rgb(0,16,66);
            }
            [data-testid="stSidebarContent"] [data-testid="stMarkdownContainer"],
            [data-testid="stSidebarContent"] [data-testid="stMarkdownContainer"] h2 {
                color: rgb(255,255,255) !important;
            }
            [data-testid="stSidebarContent"] button[title="View fullscreen"],
            .stAppViewMain [data-testid="StyledFullScreenButton"]:has(+ .stImage),
            .stMain [data-testid="StyledFullScreenButton"]:has(+ .stImage) {
                visibility: hidden;
            }
            [data-testid="StyledFullScreenButton"] {
                border: 1px solid #001042;
                border-radius: 50%;
                background-color: rgb(245,245,245);
            }
            [data-testid="stVerticalBlockBorderWrapper"]:has(.stImage) {
                border-color: rgb(79,166,251);
            }
            .stAppViewMain [data-testid="stImageContainer"] img,
            .stMain [data-testid="stImageContainer"] img {
                width: 10% !important;
                margin-left: auto !important;
            }
            .stMarkdown hr {
                border-color: rgb(79,166,251) !important;
            }
            [data-testid="stIconMaterial"] {
                color: rgba(255,255,255,0.7);
            }
            [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVegaLiteChart"]) {
                border-color: rgb(0,16,66);
            }
            [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVegaLiteChart"]:has(canvas) {
                border: 1px solid #001042;
                border-radius: 2%;
                padding: 5%;
                width: 100% !important;
            }
            [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVegaLiteChart"] canvas {
                width: 100% !important;
            }
        </style>
        """
    )

def MDSidebar():
    image = Image.open("images/logos/MDLogoWhite.png")
    st.sidebar.image(image)
    st.sidebar.header("Servicios")
    st.sidebar.page_link("pages/Inicio.py", label="Inicio", icon=":material/home:")
    st.sidebar.page_link("pages/Chats.py", label="Chats", icon=":material/chat:")
    st.sidebar.page_link("pages/Videocalls.py", label="Videocalls", icon=":material/videocam:")
    st.sidebar.page_link("pages/Prescriptions.py", label="Prescriptions", icon=":material/clinical_notes:")
    st.sidebar.page_link("pages/NPS.py", label="NPS", icon=":material/thumb_up:")
    st.sidebar.page_link("pages/Installations.py", label="Installations", icon=":material/download:")
    st.sidebar.page_link("pages/Registrations.py", label="Registrations", icon=":material/app_registration:")
    st.sidebar.page_link("pages/Raw_data.py", label="Raw data", icon=":material/table:")
    st.sidebar.divider()
    st.sidebar.header("Filtros")

def MDMultiselectFilter (multiselectname, df):
    multiselect_df = st.sidebar.multiselect(
        multiselectname,
        df
    )

    return multiselect_df

def MDConnection():
    # Initialize connection.
    conn = st.connection("snowflake")

    return conn

def MDGetUsageData(conn):
    df = conn.query("""
        SELECT 
            Year(try_cast("InstallDate" as date)) as "Año"
            , MONTHNAME(try_cast("InstallDate" as date)) as "Mes"
            , case 
                when "InstallUserCustomerGroup" is null 
                or "InstallUserCustomerGroup" = '' 
                    then 'N/A' 
                else "InstallUserCustomerGroup" 
            end as "InstallUserCustomerGroup"
            , "InstallOsName" as "SistemaOperativo"
            , count(distinct "InstallID") as "Installs" 
        FROM "installations"
        WHERE "ApiKey" = 'ccdf91e84fda3ccf'
        GROUP BY 1,2,3,4
        ;
    """)

    return df

MDSetAppCFG()
MDSidebar()


# Añadimos el Título y el Logo
cols = st.columns(2)
with cols[1]:
    st.image("images/logos/MDLogoMini.png")

with cols[0]:
    st.title('Meeting Doctors Analytics')


# Nos conectamos a la base de datos
conn = MDConnection()

# Obtenemos los datos de uso directamente del dwh
installusagedf = MDGetUsageData(conn)
installusagedf['InstallUserCustomerGroup'] = installusagedf['InstallUserCustomerGroup'].str.capitalize()

# Generamos los filtros a partir de los datos de uso
years_selected = MDMultiselectFilter("Año",installusagedf.sort_values(by="Año", ascending=False)['Año'].unique())
# Ordenamos el df para poder mostrarlo correctamente
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
installusagedf['Mes'] = pd.Categorical(installusagedf['Mes'], categories=months, ordered=True)
month_selected = MDMultiselectFilter("Mes",installusagedf.sort_values(by="Mes", ascending=True)['Mes'].unique())
usergroups_selected = MDMultiselectFilter("Grupos de usuario",installusagedf['InstallUserCustomerGroup'].unique())
sistemaoperativo_selected = MDMultiselectFilter("Sistema Operativo",installusagedf['SistemaOperativo'].unique())

# Seteamos los campos a su tipo de dato correspondiente
# installusagedf["SpecialityID"] = pd.to_numeric(installusagedf['SpecialityID'])

# Pregutamos si hay algun filtro realizado, en caso de tenerlo, lo aplicamos al dataset para generar los gráficos
if years_selected:
    mask_years = installusagedf['Año'].isin(years_selected)
    installusagedf = installusagedf[mask_years] 
if month_selected:
    mask_months = installusagedf['Mes'].isin(month_selected)
    installusagedf = installusagedf[mask_months]
if usergroups_selected:
    mask_groups = installusagedf['InstallUserCustomerGroup'].isin(usergroups_selected)
    installusagedf = installusagedf[mask_groups]
if sistemaoperativo_selected:
    mask_osnames = installusagedf['SistemaOperativo'].isin(sistemaoperativo_selected)
    installusagedf = installusagedf[mask_osnames]

# Agrupamos el df por Mes para generar un bar chart mensual comparativo interanual
# cy_installsdf_date = cy_installsdf.groupby('Mes')['installs'].sum().reset_index(name ='installs')
if years_selected and len(years_selected) <= 1:
    xAxisName = "Mes"
else:
    xAxisName = "Año"

cy_installsdf_date = installusagedf.groupby(xAxisName)['Installs'].sum().reset_index(name ='Installs')

# Generamos el barchart mensual/anual
st.subheader('Evolución de Instalaciones - ' + xAxisName)
st.container(border=True).bar_chart(cy_installsdf_date, x=xAxisName, y="Installs", color="#4fa6ff", x_label='', y_label='')



# Charts por especialidad

# Agrupamos el df por Especialidad para generar un bar y pie chart
cy_installsdf_os = installusagedf.groupby('SistemaOperativo')['Installs'].sum().reset_index(name ='Installs') # .sort_values(by='Installs',ascending=False)
# cy_chatsdf_espe = cy_chatsdf_espe.sort_values(by='Installs',ascending=False)
# print(cy_chatsdf_espe)

st.subheader('')
st.subheader('Distribución de Instalaciones por Sistema Operativo')

cols = st.columns(2)

# Generamos el donut chart por especialidad
# region_select = alt.selection_point(fields=[chatusagedf['Speciality'].drop_duplicates()], empty="all")
with cols[0]:
    base = alt.Chart(cy_installsdf_os).mark_bar().encode(
        theta=alt.Theta("Installs", stack=True), 
        color=alt.Color("SistemaOperativo", legend=None).legend(title='Sistema Operativo')
        # y=alt.Y('Installs').stack(True),
        # x=alt.X('Speciality', sort='y'),
        # opacity=alt.condition(region_select, alt.value(1), alt.value(0.25))
    ).properties(
        width='container'
    )

    pie = base.mark_arc(outerRadius=120, innerRadius=50)
    # text = base.mark_text(radius=150, size=15).encode(text="Speciality:N")

    pie #+ text

# Generamos el barchart por especialidad
with cols[1]:
    base2 = alt.Chart(cy_installsdf_os).mark_bar().encode(
        alt.X("SistemaOperativo", axis=alt.Axis(title='')),
        alt.Y("Installs", axis=alt.Axis(title='')),
        alt.Color("SistemaOperativo").legend(None)
    ).properties(
        width='container'
    )
    
    base2
    