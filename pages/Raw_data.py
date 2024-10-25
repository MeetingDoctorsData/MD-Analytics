import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
# from streamlit_dynamic_filters import DynamicFilters


def MDSetAppCFG():
    LogoMini = Image.open("images/logos/MDLogoMini.png")
    st.set_page_config(layout="wide", page_title="MeetingDoctors - Analytics", page_icon=LogoMini)
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
    st.sidebar.page_link("pages/Raw_data.py", label="Raw data")
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
        select 
            chat."Año"
            , chat."Mes"
            , "Chats"
            , case when "Videocalls" is null then 0 else "Videocalls" end as "Videocalls"
            , case when "Prescriptions" is null then 0 else "Prescriptions" end as "Prescriptions"
            , case when "Nps" is null then '#' else to_varchar("Nps") end as "Nps"
            , case when "Installations" is null then 0 else "Installations" end as "Installations"
            , case when "Registrations" is null then 0 else "Registrations" end as "Registrations"
        from (
            SELECT 
                Year("ChatSentDate") as "Año"
                , MONTHNAME("ChatSentDate") as "Mes"
                , count(distinct "ChatMsgID") as "Chats" 
            FROM "ChatConsultations"
            LEFT JOIN "specialities" using ("SpecialityID")
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2
        ) as chat
        full outer join (
            SELECT 
                Year("VcDate") as "Año"
                , MONTHNAME("VcDate") as "Mes"
                , count(distinct "VcID") as "Videocalls" 
            FROM "Videocalls"
            LEFT JOIN "specialities" using ("SpecialityID")
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            AND lower("VcStatus") = 'finished'
            GROUP BY 1,2
        ) as vc on chat."Año" = vc."Año" and chat."Mes" = vc."Mes"
        full outer join (
            SELECT 
                Year("PrescriptionDate") as "Año"
                , MONTHNAME("PrescriptionDate") as "Mes"
                , count(distinct "PrescriptionsPrimaryKey") as "Prescriptions" 
            FROM "ElectronicPrescriptions"
            -- FROM "ElectronicPrescriptions_2"
            LEFT JOIN "specialities" using ("SpecialityID")
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2
        ) as receta on chat."Año" = receta."Año" and chat."Mes" = receta."Mes"
        full outer join (
            select "Año", "Mes", round((("promoters"-"detractors")/"surveys")*100, 1) as "Nps"
            from (
                SELECT 
                    Year("NpsDate") as "Año"
                    , MONTHNAME("NpsDate") as "Mes"
                    , count(distinct case when lower("NpsScoreGroup") = 'promoters' then "NpsID" else null end) as "promoters" 
                    , count(distinct case when lower("NpsScoreGroup") = 'detractors' then "NpsID" else null end) as "detractors" 
                    , count(distinct "NpsID") as "surveys" 
                FROM "nps"
                LEFT JOIN "specialities" using ("SpecialityID")
                WHERE "ApiKey" = 'ccdf91e84fda3ccf'
                AND try_to_decimal("nps"."SpecialityID") not in (8, 61, 24)
                GROUP BY 1,2
            )
        ) as nps on chat."Año" = nps."Año" and chat."Mes" = nps."Mes"
        full outer join (
            SELECT 
                Year("InstallDate") as "Año"
                , MONTHNAME("InstallDate") as "Mes"
                , count(distinct "InstallID") as "Installations" 
            FROM "installations"
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2
        ) as installs on chat."Año" = installs."Año" and chat."Mes" = installs."Mes"
        full outer join (
            SELECT 
                Year("RegisterUserDate") as "Año"
                , MONTHNAME("RegisterUserDate") as "Mes"
                , count(distinct "RegisterUserID") as "Registrations" 
            FROM "Registrations"
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2
        ) as registers on chat."Año" = registers."Año" and chat."Mes" = registers."Mes"
        ;
    """)

    return df


MDSetAppCFG()
MDSidebar()


st.title('Meeting Doctors Analytics')

# Nos conectamos a la base de datos
conn = MDConnection()

# Obtenemos los datos de uso directamente del dwh
usagesdf = MDGetUsageData(conn)

# Generamos los filtros a partir de los datos de uso
years_selected = MDMultiselectFilter("Año",usagesdf.sort_values(by="Año", ascending=False)['Año'].unique())
# Ordenamos el df para poder mostrarlo correctamente
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
usagesdf['Mes'] = pd.Categorical(usagesdf['Mes'], categories=months, ordered=True)
month_selected = MDMultiselectFilter("Mes",usagesdf.sort_values(by="Mes", ascending=True)['Mes'].unique())

# Seteamos los campos a su tipo de dato correspondiente
# usagesdf["SpecialityID"] = pd.to_numeric(usagesdf['SpecialityID'])

# Pregutamos si hay algun filtro realizado, en caso de tenerlo, lo aplicamos al dataset para generar los gráficos
if years_selected:
    mask_years = usagesdf['Año'].isin(years_selected)
    usagesdf = usagesdf[mask_years]
if month_selected:
    mask_months = usagesdf['Mes'].isin(month_selected)
    usagesdf = usagesdf[mask_months]

# Ordenamos el DataFrame por Año/Mes
usagesdf = usagesdf.sort_values(by=["Año", "Mes"], ascending=[False, False])

# Generamos la tabla
st.subheader('Raw data summary')
st.dataframe(usagesdf, use_container_width=True, hide_index=True)

# st.dataframe(usagesdf.set_index(usagesdf.columns[0]).style.hide(axis="index"))
# st.markdown(usagesdf.style.hide(axis="index").to_html(), unsafe_allow_html=True)


