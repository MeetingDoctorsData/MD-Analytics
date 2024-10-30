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


# Añadimos el Título y el Logo
cols = st.columns(2)
with cols[1]:
    st.image("images/logos/MDLogoMini.png")

with cols[0]:
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


