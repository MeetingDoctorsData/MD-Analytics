import streamlit as st
import pandas as pd
import altair as alt
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
    st.sidebar.page_link("pages/Prescriptions.py", label="Prescriptions")
    st.sidebar.page_link("pages/Installations.py", label="Installations")
    st.sidebar.page_link("pages/Registrations.py", label="Registrations")
    st.sidebar.page_link("pages/NPS.py", label="NPS")
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
            with groupings as (
                SELECT 
                    Year(try_cast("NpsDate" as date)) as "Año"
                    , MONTHNAME(try_cast("NpsDate" as date)) as "Mes"
                    , "NpsUserCustomerGroup" as "NpsUserDescription"
                    , "specialities"."SpecialityES" as "Speciality"
                    , count(distinct case when lower("NpsScoreGroup") = 'promoters' then "NpsID" else null end) as "promoters" 
                    , count(distinct case when lower("NpsScoreGroup") = 'detractors' then "NpsID" else null end) as "detractors" 
                    , count(distinct "NpsID") as "surveys" 
                FROM "nps"
                LEFT JOIN "specialities" using ("SpecialityID")
                WHERE "ApiKey" = 'ccdf91e84fda3ccf'
                GROUP BY 1,2,3,4
            )
            select 
                "Año" 
                , "Mes"
                , "NpsUserDescription"
                , "Speciality"
                , round((("promoters" - "detractors") / "surveys")*100, 0) as "Nps"
            from groupings
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
if 'years_selected' not in st.session_state:
    years_selected = MDMultiselectFilter("Año",surveyusagedf.sort_values(by="Año", ascending=False)['Año'].unique())
else:
    years_selected = st.session_state['years_selected']
# Preguntamos si hay filtros de Meses aplicados en otra Page
if 'month_selected' not in st.session_state:
    # Ordenamos el df para poder mostrarlo correctamente
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    surveyusagedf['Mes'] = pd.Categorical(surveyusagedf['Mes'], categories=months, ordered=True)
    month_selected = MDMultiselectFilter("Mes",surveyusagedf.sort_values(by="Mes", ascending=True)['Mes'].unique())
else:
    month_selected = st.session_state['month_selected']
# Preguntamos si hay filtros de UserGroups aplicados en otra Page
if 'usergroups_selected' not in st.session_state:
    usergroups_selected = MDMultiselectFilter("Grupos de usuario",surveyusagedf['NpsUserDescription'].unique())
else:
    usergroups_selected = st.session_state['usergroups_selected']
# Preguntamos si hay filtros de especialidad aplicados en otra Page
if 'especialidad_selected' not in st.session_state:
    especialidad_selected = MDMultiselectFilter("Especialidad",surveyusagedf['Speciality'].unique())
else:
    especialidad_selected = st.session_state['especialidad_selected']


# Seteamos los campos a su tipo de dato correspondiente
# surveyusagedf["SpecialityID"] = pd.to_numeric(surveyusagedf['SpecialityID'])

# Pregutamos si hay algun filtro realizado, en caso de tenerlo, lo aplicamos al dataset para generar los gráficos
if years_selected:
    mask_years = surveyusagedf['Año'].isin(years_selected)
    surveyusagedf = surveyusagedf[mask_years]
    st.session_state['years_selected'] = years_selected
if month_selected:
    mask_months = surveyusagedf['Mes'].isin(month_selected)
    surveyusagedf = surveyusagedf[mask_months]
    st.session_state['month_selected'] = month_selected
if usergroups_selected:
    mask_groups = surveyusagedf['NpsUserDescription'].isin(usergroups_selected)
    surveyusagedf = surveyusagedf[mask_groups]
    st.session_state['usergroups_selected'] = usergroups_selected
if especialidad_selected:
    mask_especialities = surveyusagedf['Speciality'].isin(especialidad_selected)
    surveyusagedf = surveyusagedf[mask_especialities]
    st.session_state['especialidad_selected'] = especialidad_selected

# Boton para hacer reset de los filtros
if st.sidebar.button("Reset filters"):
    del st.session_state['years_selected']
    del st.session_state['month_selected']
    del st.session_state['usergroups_selected']
    del st.session_state['especialidad_selected']

# Agrupamos el df por Mes para generar un bar chart mensual comparativo interanual
# cy_surveysdf_date = cy_surveysdf.groupby('Mes')['surveys'].sum().reset_index(name ='surveys')
if years_selected and len(years_selected) <= 1:
    xAxisName = "Mes"
    cy_surveysdf_date = surveyusagedf.groupby('Mes')['Nps'].mean().round().reset_index(name ='Nps')
else:
    xAxisName = "Año"
    cy_surveysdf_date = surveyusagedf.groupby('Año')['Nps'].mean().round().reset_index(name ='Nps')

# Generamos el barchart mensual/anual
st.subheader('Evolución mensual de NPS') 
st.bar_chart(cy_surveysdf_date, x=xAxisName, y="Nps", color="#4fa6ff")



# Charts por especialidad

# Agrupamos el df por Especialidad para generar un bar y pie chart
cy_surveysdf_espe = surveyusagedf.groupby('Speciality')['Nps'].mean().round().reset_index(name ='Nps') # .sort_values(by='surveys',ascending=False)
# cy_surveysdf_espe = cy_surveysdf_espe.sort_values(by='surveys',ascending=False)
# print(cy_surveysdf_espe)

cols = st.columns([1, 1])

# Generamos el donut chart por especialidad
# region_select = alt.selection_point(fields=[surveyusagedf['Speciality'].drop_duplicates()], empty="all")
with cols[0]:
    st.subheader('Distribución de NPS por Especialidad')
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
    st.bar_chart(cy_surveysdf_espe, x="Speciality", y="Nps", color="Speciality")
    # st.button('kk') 