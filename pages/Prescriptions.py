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
                Year("PrescriptionDate") as "Año"
                , MONTHNAME("PrescriptionDate") as "Mes"
                , "PrescriptionUserCustomerGroup"
                , "specialities"."SpecialityES" as "Speciality"
                , count(distinct "PrescriptionsPrimaryKey") as "Prescriptions" 
            FROM "ElectronicPrescriptions"
            LEFT JOIN "specialities" using ("SpecialityID")
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
prescriptionusagedf = MDGetUsageData(conn)
prescriptionusagedf['PrescriptionUserCustomerGroup'] = prescriptionusagedf['PrescriptionUserCustomerGroup'].str.capitalize()

# Generamos los filtros a partir de los datos de uso
years_selected = MDMultiselectFilter("Año",prescriptionusagedf.sort_values(by="Año", ascending=False)['Año'].unique())
# Ordenamos el df para poder mostrarlo correctamente
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
prescriptionusagedf['Mes'] = pd.Categorical(prescriptionusagedf['Mes'], categories=months, ordered=True)
month_selected = MDMultiselectFilter("Mes",prescriptionusagedf.sort_values(by="Mes", ascending=True)['Mes'].unique())
usergroups_selected = MDMultiselectFilter("Grupos de usuario",prescriptionusagedf['PrescriptionUserCustomerGroup'].unique())
especialidad_selected = MDMultiselectFilter("Especialidad",prescriptionusagedf['Speciality'].unique())

# Seteamos los campos a su tipo de dato correspondiente
# prescriptionusagedf["SpecialityID"] = pd.to_numeric(prescriptionusagedf['SpecialityID'])

# Pregutamos si hay algun filtro realizado, en caso de tenerlo, lo aplicamos al dataset para generar los gráficos
if years_selected:
    mask_years = prescriptionusagedf['Año'].isin(years_selected)
    prescriptionusagedf = prescriptionusagedf[mask_years]
if month_selected:
    mask_months = prescriptionusagedf['Mes'].isin(month_selected)
    prescriptionusagedf = prescriptionusagedf[mask_months]
if usergroups_selected:
    mask_groups = prescriptionusagedf['PrescriptionUserCustomerGroup'].isin(usergroups_selected)
    prescriptionusagedf = prescriptionusagedf[mask_groups]
if especialidad_selected:
    mask_specialities = prescriptionusagedf['Speciality'].isin(especialidad_selected)
    prescriptionusagedf = prescriptionusagedf[mask_specialities]

# Agrupamos el df por Mes para generar un bar chart mensual comparativo interanual
# cy_prescriptionsdf_date = cy_prescriptionsdf.groupby('Mes')['prescriptions'].sum().reset_index(name ='prescriptions')
if years_selected and len(years_selected) <= 1:
    xAxisName = "Mes"
else:
    xAxisName = "Año"

cy_prescriptionsdf_date = prescriptionusagedf.groupby(xAxisName)['Prescriptions'].sum().reset_index(name ='Prescriptions')

# Generamos el barchart mensual/anual
st.subheader('Evolución de Recetas Electrónicas - ' + xAxisName)
st.bar_chart(cy_prescriptionsdf_date, x=xAxisName, y="Prescriptions", color="#4fa6ff", x_label='', y_label='')



# Charts por especialidad

# Agrupamos el df por Especialidad para generar un bar y pie chart
cy_prescriptionsdf_espe = prescriptionusagedf.groupby('Speciality')['Prescriptions'].sum().reset_index(name ='Prescriptions') # .sort_values(by='prescriptions',ascending=False)
# cy_prescriptionsdf_espe = cy_prescriptionsdf_espe.sort_values(by='prescriptions',ascending=False)
# print(cy_prescriptionsdf_espe)


st.subheader('Distribución de Recetas Electrónicas por Especialidad')

cols = st.columns([1, 1])

# Generamos el donut chart por especialidad
# region_select = alt.selection_point(fields=[prescriptionusagedf['Speciality'].drop_duplicates()], empty="all")
with cols[0]:
    base = alt.Chart(cy_prescriptionsdf_espe).mark_bar().encode(
        theta=alt.Theta("Prescriptions", stack=True), 
        color=alt.Color("Speciality", legend=None).legend()
        # y=alt.Y('prescriptions').stack(True),
        # x=alt.X('Speciality', sort='y'),
        # opacity=alt.condition(region_select, alt.value(1), alt.value(0.25))
    ).properties(width=600)

    pie = base.mark_arc(outerRadius=120, innerRadius=50)
    # text = base.mark_text(radius=150, size=15).encode(text="Speciality:N")

    pie #+ text

# Generamos el barchart por especialidad
with cols[1]:
    st.subheader(' ')
    # st.bar_chart(cy_prescriptionsdf_espe, x="Speciality", y="Prescriptions", color="Speciality")
    
    base2 = alt.Chart(cy_prescriptionsdf_espe).mark_bar().encode(
        alt.X("Speciality", axis=alt.Axis(title='')),
        alt.Y("Prescriptions", axis=alt.Axis(title='')),
        alt.Color("Speciality").legend(None)
    ).properties(
        width=700
    )
    
    base2