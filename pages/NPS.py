import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
from collections import Counter
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
            [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVegaLiteChart"]:has(canvas),
            .stColumn [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVegaLiteChart"]:has(canvas) {
                border: 1px solid #001042;
                border-radius: 2%;
                padding: 5%;
                width: 100% !important;
            }
            [data-testid="column"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVegaLiteChart"] canvas,
            .stColumn [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVegaLiteChart"] canvas {
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
            Year("NpsDate") as "Año"
            , MONTHNAME("NpsDate") as "Mes"
            , "NpsUserCustomerGroup" as "NpsUserDescription"
            , "specialities"."SpecialityES" as "Speciality"
            , count(distinct case when lower("NpsScoreGroup") = 'promoters' then "NpsID" else null end) as "promoters" 
            , count(distinct case when lower("NpsScoreGroup") = 'detractors' then "NpsID" else null end) as "detractors" 
            , count(distinct "NpsID") as "surveys" 
        FROM "nps"
        LEFT JOIN "specialities" using ("SpecialityID")
        WHERE "ApiKey" = 'ccdf91e84fda3ccf'
        AND try_to_decimal("nps"."SpecialityID") not in (8, 61, 24)
        GROUP BY 1,2,3,4
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
surveyusagedf = MDGetUsageData(conn)
surveyusagedf['NpsUserDescription'] = surveyusagedf['NpsUserDescription'].str.capitalize()

# Generamos los filtros a partir de los datos de uso
# Preguntamos si hay filtros de Años aplicados en otra Page
years_selected = MDMultiselectFilter("Año",surveyusagedf.sort_values(by="Año", ascending=False)['Año'].unique())
# Preguntamos si hay filtros de Meses aplicados en otra Page
# Ordenamos el df para poder mostrarlo correctamente
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
surveyusagedf['Mes'] = pd.Categorical(surveyusagedf['Mes'], categories=months, ordered=True)
month_selected = MDMultiselectFilter("Mes",surveyusagedf.sort_values(by="Mes", ascending=True)['Mes'].unique())
# Preguntamos si hay filtros de UserGroups aplicados en otra Page
usergroups_selected = MDMultiselectFilter("Grupos de usuario",surveyusagedf['NpsUserDescription'].unique())
# Preguntamos si hay filtros de especialidad aplicados en otra Page
especialidad_selected = MDMultiselectFilter("Especialidad",surveyusagedf['Speciality'].unique())



# Seteamos los campos a su tipo de dato correspondiente
# surveyusagedf["SpecialityID"] = pd.to_numeric(surveyusagedf['SpecialityID'])

# Pregutamos si hay algun filtro realizado, en caso de tenerlo, lo aplicamos al dataset para generar los gráficos
if years_selected:
    mask_years = surveyusagedf['Año'].isin(years_selected)
    surveyusagedf = surveyusagedf[mask_years]
if month_selected:
    mask_months = surveyusagedf['Mes'].isin(month_selected)
    surveyusagedf = surveyusagedf[mask_months]
if usergroups_selected:
    mask_groups = surveyusagedf['NpsUserDescription'].isin(usergroups_selected)
    surveyusagedf = surveyusagedf[mask_groups]
if especialidad_selected:
    mask_specialities = surveyusagedf['Speciality'].isin(especialidad_selected)
    surveyusagedf = surveyusagedf[mask_specialities]

# Agrupamos el df por Mes para generar un bar chart mensual comparativo interanual
# cy_surveysdf_date = cy_surveysdf.groupby('Mes')['surveys'].sum().reset_index(name ='surveys')
surveyusagedf["Año"] = surveyusagedf["Año"].astype(str)
if years_selected and len(years_selected) <= 1:
    xAxisName = "Mes"
else:
    xAxisName = "Año"

cy_surveysdf_date = surveyusagedf.groupby(xAxisName).agg({'promoters':'sum','detractors':'sum','surveys':'sum'})
cy_surveysdf_date['Nps'] = ((cy_surveysdf_date['promoters'] - cy_surveysdf_date['detractors']) / cy_surveysdf_date['surveys'])*100
cy_surveysdf_date = cy_surveysdf_date.groupby(xAxisName)['Nps'].mean().round(1).reset_index(name ='Nps')

st.subheader('Evolución de NPS - ' + xAxisName)

# Generamos el barchart mensual/anual
# st.bar_chart(cy_surveysdf_date, x=xAxisName, y="Nps", color="#4fa6ff")

# Generamos el linechart mensual/anual
if (cy_surveysdf_date[xAxisName].nunique() == 1) or (len(years_selected) == 1 and len(month_selected) == 1):
    st.container(border=True).scatter_chart(cy_surveysdf_date, x=xAxisName, y="Nps", color="#4fa6ff", x_label='', y_label='')
else:
    st.container(border=True).line_chart(cy_surveysdf_date, x=xAxisName, y="Nps", color="#4fa6ff", x_label='', y_label='') 

# Linechart alternativo
# line_with_points = alt.Chart(cy_surveysdf_date, width=1035).mark_line(point=True).encode(
#     x=alt.X(xAxisName),
#     # x=alt.X(xAxisName).axis(format='.0f', title=xAxisName),
#     y=alt.Y("Nps"),
#     color=alt.ColorValue("#4fa6ff")
# )

# line_with_points


# Charts por especialidad

# Agrupamos el df por Especialidad para generar un bar y pie chart
cy_surveysdf_espe = surveyusagedf.groupby('Speciality').agg({'promoters':'sum','detractors':'sum','surveys':'sum'})
cy_surveysdf_espe['Nps'] = ((cy_surveysdf_espe['promoters'] - cy_surveysdf_espe['detractors']) / cy_surveysdf_espe['surveys'])*100
cy_surveysdf_espe = cy_surveysdf_espe.groupby('Speciality')['Nps'].mean().round(1).reset_index(name ='Nps') # .sort_values(by='surveys',ascending=False)
# cy_surveysdf_espe = cy_surveysdf_espe.sort_values(by='surveys',ascending=False)
# print(cy_surveysdf_espe)

st.subheader('')
st.subheader('Distribución de NPS por Especialidad')

cols = st.columns(2)

# Generamos el donut chart por especialidad
# region_select = alt.selection_point(fields=[surveyusagedf['Speciality'].drop_duplicates()], empty="all")
with cols[0]:
    base = alt.Chart(cy_surveysdf_espe).mark_bar().encode(
        theta=alt.Theta("Nps", stack=True), 
        color=alt.Color("Speciality", legend=None).legend()
        # y=alt.Y('surveys').stack(True),
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
    base2 = alt.Chart(cy_surveysdf_espe).mark_bar().encode(
        alt.X("Speciality", axis=alt.Axis(title='')),
        alt.Y("Nps", axis=alt.Axis(title='')),
        alt.Color("Speciality").legend(None)
    ).properties(
        width='container'
    )
    
    base2