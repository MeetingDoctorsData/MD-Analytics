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
            SELECT 
                Year(try_cast("RegisterUserDate" as date)) as "Año"
                , MONTHNAME(try_cast("RegisterUserDate" as date)) as "Mes"
                , "RegisterUserCustomerGroup"
                , count(distinct "RegisterUserID") as "Registers" 
            FROM "Registrations"
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2,3
            ;
    """) 

    return df

MDSetAppCFG()
MDSidebar()

st.title('Meeting Doctors Analytics')

# Nos conectamos a la base de datos
conn = MDConnection()

# Obtenemos los datos de uso directamente del dwh
chatusagedf = MDGetUsageData(conn)
chatusagedf['RegisterUserCustomerGroup'] = chatusagedf['RegisterUserCustomerGroup'].str.capitalize()

# Generamos los filtros a partir de los datos de uso
years_selected = MDMultiselectFilter("Año",chatusagedf.sort_values(by="Año", ascending=False)['Año'].unique())
# Ordenamos el df para poder mostrarlo correctamente
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
chatusagedf['Mes'] = pd.Categorical(chatusagedf['Mes'], categories=months, ordered=True)
month_selected = MDMultiselectFilter("Mes",chatusagedf.sort_values(by="Mes", ascending=True)['Mes'].unique())
usergroups_selected = MDMultiselectFilter("Grupos de usuario",chatusagedf['RegisterUserCustomerGroup'].unique())

# Seteamos los campos a su tipo de dato correspondiente
# chatusagedf["SpecialityID"] = pd.to_numeric(chatusagedf['SpecialityID'])

# Pregutamos si hay algun filtro realizado, en caso de tenerlo, lo aplicamos al dataset para generar los gráficos
if years_selected:
    mask_years = chatusagedf['Año'].isin(years_selected)
    chatusagedf = chatusagedf[mask_years]
if month_selected:
    mask_months = chatusagedf['Mes'].isin(month_selected)
    chatusagedf = chatusagedf[mask_months]
if usergroups_selected:
    mask_groups = chatusagedf['RegisterUserCustomerGroup'].isin(usergroups_selected)
    chatusagedf = chatusagedf[mask_groups]

# Agrupamos el df por Mes para generar un bar chart mensual comparativo interanual
# cy_chatsdf_date = cy_chatsdf.groupby('Mes')['Chats'].sum().reset_index(name ='Chats')
if years_selected and len(years_selected) <= 1:
    xAxisName = "Mes"
    cy_chatsdf_date = chatusagedf.groupby('Mes')['Registers'].sum().reset_index(name ='Registers')
else:
    xAxisName = "Año"
    cy_chatsdf_date = chatusagedf.groupby('Año')['Registers'].sum().reset_index(name ='Registers')

# Generamos el barchart mensual/anual
st.subheader('Evolución mensual de Registros')
st.bar_chart(cy_chatsdf_date, x=xAxisName, y="Registers", color="#4fa6ff")



# Charts por especialidad

# Agrupamos el df por Especialidad para generar un bar y pie chart
cy_chatsdf_grupo = chatusagedf.groupby('RegisterUserCustomerGroup')['Registers'].sum().reset_index(name ='Registers') # .sort_values(by='Registers',ascending=False)
# cy_chatsdf_espe = cy_chatsdf_espe.sort_values(by='Registers',ascending=False)
# print(cy_chatsdf_espe)

cols = st.columns([1, 1])

# Generamos el donut chart por especialidad
# region_select = alt.selection_point(fields=[chatusagedf['Speciality'].drop_duplicates()], empty="all")
with cols[0]:
    st.subheader('Distribución de Registros por Grupos de Usuario')
    base = alt.Chart(cy_chatsdf_grupo).mark_bar().encode(
        theta=alt.Theta("Registers", stack=True), 
        color=alt.Color("RegisterUserCustomerGroup", legend=None).legend()
        # y=alt.Y('Registers').stack(True),
        # x=alt.X('Speciality', sort='y'),
        # opacity=alt.condition(region_select, alt.value(1), alt.value(0.25))
    ).properties(width=500)

    pie = base.mark_arc(outerRadius=120, innerRadius=50)
    # text = base.mark_text(radius=150, size=15).encode(text="Speciality:N")

    pie #+ text

# Generamos el barchart por especialidad
with cols[1]:
    st.subheader(' ')
    st.bar_chart(cy_chatsdf_grupo, x="RegisterUserCustomerGroup", y="Registers", color="RegisterUserCustomerGroup")
    