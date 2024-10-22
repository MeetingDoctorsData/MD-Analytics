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
                Year("ChatSentDate") as "Año"
                , MONTHNAME("ChatSentDate") as "Mes"
                , "ConsultationUserDescription"
                , "specialities"."SpecialityES" as "Speciality"
                , count(distinct "ChatMsgID") as "Chats" 
            FROM "ChatConsultations"
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
chatusagedf = MDGetUsageData(conn)
chatusagedf['ConsultationUserDescription'] = chatusagedf['ConsultationUserDescription'].str.capitalize()

# Generamos los filtros a partir de los datos de uso
years_selected = MDMultiselectFilter("Año",chatusagedf.sort_values(by="Año", ascending=False)['Año'].unique())
# Ordenamos el df para poder mostrarlo correctamente
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
chatusagedf['Mes'] = pd.Categorical(chatusagedf['Mes'], categories=months, ordered=True)
month_selected = MDMultiselectFilter("Mes",chatusagedf.sort_values(by="Mes", ascending=True)['Mes'].unique())
usergroups_selected = MDMultiselectFilter("Grupos de usuario",chatusagedf['ConsultationUserDescription'].unique())
especialidad_selected = MDMultiselectFilter("Especialidad",chatusagedf['Speciality'].unique())

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
    mask_groups = chatusagedf['ConsultationUserDescription'].isin(usergroups_selected)
    chatusagedf = chatusagedf[mask_groups]
if especialidad_selected:
    mask_specialities = chatusagedf['Speciality'].isin(especialidad_selected)
    chatusagedf = chatusagedf[mask_specialities]

# Agrupamos el df por Mes para generar un bar chart mensual comparativo interanual
# cy_chatsdf_date = cy_chatsdf.groupby('Mes')['Chats'].sum().reset_index(name ='Chats')
chatusagedf["Año"] = chatusagedf["Año"].astype(str)
if years_selected and len(years_selected) <= 1:
    xAxisName = "Mes"
else:
    xAxisName = "Año"

cy_chatsdf_date = chatusagedf.groupby(xAxisName)['Chats'].sum().reset_index(name ='Chats')

# Generamos el barchart mensual/anual
st.subheader('Evolución de consultas Chat - ' + xAxisName)
st.bar_chart(cy_chatsdf_date, x=xAxisName, y="Chats", color="#4fa6ff", x_label='', y_label='')


# Charts por especialidad

# Agrupamos el df por Especialidad para generar un bar y pie chart
cy_chatsdf_espe = chatusagedf.groupby('Speciality')['Chats'].sum().reset_index(name ='Chats') # .sort_values(by='Chats',ascending=False)
# cy_chatsdf_espe = cy_chatsdf_espe.sort_values(by='Chats',ascending=False)
# print(cy_chatsdf_espe)


st.subheader('Distribución de consultas Chat por Especialidad')

cols = st.columns([1, 1])

# Generamos el donut chart por especialidad
# region_select = alt.selection_point(fields=[chatusagedf['Speciality'].drop_duplicates()], empty="all")
with cols[0]:
    base = alt.Chart(cy_chatsdf_espe).mark_bar().encode(
        theta=alt.Theta("Chats", stack=True), 
        color=alt.Color("Speciality").legend()
        # y=alt.Y('Chats').stack(True),
        # x=alt.X('Speciality', sort='y'),
        # opacity=alt.condition(region_select, alt.value(1), alt.value(0.25))
    ).properties(width=600)

    pie = base.mark_arc(outerRadius=120, innerRadius=50)
    # text = base.mark_text(radius=150, size=15).encode(text="Speciality")

    pie #+ text

# Generamos el barchart por especialidad
with cols[1]:
    st.subheader('')
    # st.bar_chart(cy_chatsdf_espe, x="Speciality", y="Chats", color="Speciality", x_label='', y_label='')

    base2 = alt.Chart(cy_chatsdf_espe).mark_bar().encode(
        alt.X("Speciality", axis=alt.Axis(title='')),
        alt.Y("Chats", axis=alt.Axis(title='')),
        alt.Color("Speciality").legend(None)
    ).properties(
        width=700,
        title=''
    )
    
    base2
