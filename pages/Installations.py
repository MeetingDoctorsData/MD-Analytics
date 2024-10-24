import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
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
st.bar_chart(cy_installsdf_date, x=xAxisName, y="Installs", color="#4fa6ff", x_label='', y_label='')



# Charts por especialidad

# Agrupamos el df por Especialidad para generar un bar y pie chart
cy_installsdf_os = installusagedf.groupby('SistemaOperativo')['Installs'].sum().reset_index(name ='Installs') # .sort_values(by='Installs',ascending=False)
# cy_chatsdf_espe = cy_chatsdf_espe.sort_values(by='Installs',ascending=False)
# print(cy_chatsdf_espe)

st.subheader('Distribución de Instalaciones por Sistema Operativo')

cols = st.columns([1, 1])

# Generamos el donut chart por especialidad
# region_select = alt.selection_point(fields=[chatusagedf['Speciality'].drop_duplicates()], empty="all")
with cols[0]:
    base = alt.Chart(cy_installsdf_os).mark_bar().encode(
        theta=alt.Theta("Installs", stack=True), 
        color=alt.Color("SistemaOperativo", legend=None).legend(title='Sistema Operativo')
        # y=alt.Y('Installs').stack(True),
        # x=alt.X('Speciality', sort='y'),
        # opacity=alt.condition(region_select, alt.value(1), alt.value(0.25))
    ).properties(width=600)

    pie = base.mark_arc(outerRadius=120, innerRadius=50)
    # text = base.mark_text(radius=150, size=15).encode(text="Speciality:N")

    pie #+ text

# Generamos el barchart por especialidad
with cols[1]:
    st.subheader(' ')
    # st.bar_chart(cy_installsdf_os, x="SistemaOperativo", y="Installs", color="SistemaOperativo")

    base2 = alt.Chart(cy_installsdf_os).mark_bar().encode(
        alt.X("SistemaOperativo", axis=alt.Axis(title='')),
        alt.Y("Installs", axis=alt.Axis(title='')),
        alt.Color("SistemaOperativo").legend(None)
    ).properties(
        width=700
    )
    
    base2
    