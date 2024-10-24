import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
from collections import Counter
# from streamlit_dynamic_filters import DynamicFilters

def MDSetAppCFG():
    st.set_page_config(layout="wide", page_title="MeetingDoctors - Analytics", page_icon="https://meetingdoctors.com/app/themes/custom_theme/build/assets/img/icons/icon_meeting.svg")
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
    st.sidebar.page_link("pages/Resumen.py", label="Resumen")
    st.sidebar.page_link("pages/Chats.py", label="Chats")
    st.sidebar.page_link("pages/Videocalls.py", label="Videocalls")
    st.sidebar.page_link("pages/Prescriptions.py", label="Prescriptions")
    st.sidebar.page_link("pages/NPS.py", label="NPS")
    st.sidebar.page_link("pages/Installations.py", label="Installations")
    st.sidebar.page_link("pages/Registrations.py", label="Registrations")
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
    st.scatter_chart(cy_surveysdf_date, x=xAxisName, y="Nps", color="#4fa6ff", x_label='', y_label='')
else:
    st.line_chart(cy_surveysdf_date, x=xAxisName, y="Nps", color="#4fa6ff", x_label='', y_label='') 

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

st.subheader('Distribución de NPS por Especialidad')

cols = st.columns([1, 1])

# Generamos el donut chart por especialidad
# region_select = alt.selection_point(fields=[surveyusagedf['Speciality'].drop_duplicates()], empty="all")
with cols[0]:
    base = alt.Chart(cy_surveysdf_espe).mark_bar().encode(
        theta=alt.Theta("Nps", stack=True), 
        color=alt.Color("Speciality", legend=None).legend()
        # y=alt.Y('surveys').stack(True),
        # x=alt.X('Speciality', sort='y'),
        # opacity=alt.condition(region_select, alt.value(1), alt.value(0.25))
    ).properties(width=600)

    pie = base.mark_arc(outerRadius=120, innerRadius=50)
    # text = base.mark_text(radius=150, size=15).encode(text="Speciality:N")

    pie #+ text

# Generamos el barchart por especialidad
with cols[1]:
    st.subheader(' ')
    # st.bar_chart(cy_surveysdf_espe, x="Speciality", y="Nps", color="Speciality")
    
    base2 = alt.Chart(cy_surveysdf_espe).mark_bar().encode(
        alt.X("Speciality", axis=alt.Axis(title='')),
        alt.Y("Nps", axis=alt.Axis(title='')),
        alt.Color("Speciality").legend(None)
    ).properties(
        width=700
    )
    
    base2