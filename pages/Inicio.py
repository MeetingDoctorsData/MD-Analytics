import streamlit as st
import pandas as pd
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
            .stAppViewMain button[title="View fullscreen"]:has(+ .stImage) {
                visibility: hidden;
            }
            .stAppViewMain [data-testid="stImageContainer"] img {
                width: 5%;
                margin-left: auto;
                margin-bottom: -5%;
            }
            [data-testid="stVerticalBlockBorderWrapper"]:has(.stImage) {
                border-color: rgb(79,166,251);
            }
            .stMarkdown hr {
                border-color: rgb(79,166,251) !important;
            }
            [data-testid="stIconMaterial"] {
                color: rgba(255, 255, 255, 0.7);
            }
            [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVegaLiteChart"]) {
                border-color: rgb(79,166,251);
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

def MDGetUsagesData(conn):
    df = conn.query("""
            SELECT 
                Year("ChatSentDate") as "Año"
                , MONTHNAME("ChatSentDate") as "Mes"
                , "ConsultationUserDescription" as "CustomerGroup"
                , "specialities"."SpecialityES" as "Speciality"
                , 'chat' as "Usage"
                , count(distinct "ChatMsgID") as "UsageAmount" 
            FROM "ChatConsultations"
            LEFT JOIN "specialities" using ("SpecialityID")
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2,3,4
            union all
            SELECT 
                Year("VcDate") as "Año"
                , MONTHNAME("VcDate") as "Mes"
                , "VcUserCustomerGroup" as "CustomerGroup"
                , "specialities"."SpecialityES" as "Speciality"
                , 'vc' as "Usage"
                , count(distinct "VcID") as "UsageAmount" 
            FROM "Videocalls"
            LEFT JOIN "specialities" using ("SpecialityID")
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            AND lower("VcStatus") = 'finished'
            GROUP BY 1,2,3,4
            union all
            SELECT 
                Year("PrescriptionDate") as "Año"
                , MONTHNAME("PrescriptionDate") as "Mes"
                , "PrescriptionUserCustomerGroup" as "CustomerGroup"
                , "specialities"."SpecialityES" as "Speciality"
                , 'prescription' as "Usage"
                , count(distinct "PrescriptionsPrimaryKey") as "UsageAmount" 
            FROM "ElectronicPrescriptions"
            LEFT JOIN "specialities" using ("SpecialityID")
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2,3,4
            ;
    """)

    return df

def MDGetNpsData(conn):
    df = conn.query("""
            SELECT 
                Year("NpsDate") as "Año"
                , MONTHNAME("NpsDate") as "Mes"
                , "NpsUserCustomerGroup" as "CustomerGroup"
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

def MDGetInstallsData(conn):
    df = conn.query("""
            SELECT 
                Year(try_cast("InstallDate" as date)) as "Año"
                , MONTHNAME(try_cast("InstallDate" as date)) as "Mes"
                , case 
                    when "InstallUserCustomerGroup" is null 
                    or "InstallUserCustomerGroup" = '' 
                        then 'N/A' 
                    else "InstallUserCustomerGroup" 
                end as "CustomerGroup"
                , count(distinct "InstallID") as "Installs" 
            FROM "installations"
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2,3
            ;
    """)

    return df

def MDGetregistersData(conn):
    df = conn.query("""
            SELECT 
                Year(try_cast("RegisterUserDate" as date)) as "Año"
                , MONTHNAME(try_cast("RegisterUserDate" as date)) as "Mes"
                , "RegisterUserCustomerGroup" as "CustomerGroup"
                , count(distinct "RegisterUserID") as "Registers" 
            FROM "Registrations"
            WHERE "ApiKey" = 'ccdf91e84fda3ccf'
            GROUP BY 1,2,3
            ;
    """) 

    return df

def filter_df(df, column):
    if years_selected:
        mask_years = df['Año'].isin(years_selected)
        df = df[mask_years]
    if month_selected:
        mask_months = df['Mes'].isin(month_selected)
        df = df[mask_months]
    if usergroups_selected:
        mask_groups = df['CustomerGroup'].str.capitalize().isin(usergroups_selected)
        df = df[mask_groups]
        
    if column:
        if especialidad_selected:
            mask_specialities = df[column].isin(especialidad_selected)
            df = df[mask_specialities]
    
    return df


MDSetAppCFG()
MDSidebar()

# cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])

# with cols[11]:
LogoMini = Image.open("images/logos/MDLogoMini.png")
st.container().image(LogoMini)


st.title('Meeting Doctors Analytics')
st.markdown(
    """
        ### Bienvenido a MD Analytics
        MD Analytics es un app mediante que permite el seguimiento y análisis básico de los distintos servicios contratados.

        👈 Mediante estos selectores puedes seleccionar el servicio que deseas analizar

        **IMPORTANTE: Este dashboard no dispone de datos real-time.** Los datos a analizar siempre son hasta último día cerrado

        *Si tienes cualquier duda o incidencia con el dashboard, ponte en contacto con nuestro equipo de [data](mailto:data@meetingdoctors.com)*
    """
  )

st.subheader('')
st.subheader('Indicadores generales')


# Nos conectamos a la base de datos
conn = MDConnection()


# Obtenemos los datos de uso directamente del dwh
usagesdf = MDGetUsagesData(conn)
npsdf = MDGetNpsData(conn)
installsdf = MDGetInstallsData(conn)
registersdf = MDGetregistersData(conn)


# Agrupamos los campos Año, Mes y CustomerGroup de todos los DataFrames
year_month_group_df = pd.DataFrame()
year_month_group_df[['Año','Mes','CustomerGroup','Speciality']] = pd.concat([usagesdf[['Año','Mes','CustomerGroup','Speciality']]
                                                 , npsdf[['Año','Mes','CustomerGroup','Speciality']]
                                                 , installsdf[['Año','Mes','CustomerGroup']]
                                                 , registersdf[['Año','Mes','CustomerGroup']]]
                                                 , ignore_index=True)


year_month_group_df['CustomerGroup'] = year_month_group_df['CustomerGroup'].str.capitalize()


# Generamos los filtros a partir de los datos de uso
years_selected = MDMultiselectFilter("Año",year_month_group_df.sort_values(by="Año", ascending=False)['Año'].unique())
# Ordenamos el df para poder mostrarlo correctamente
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
year_month_group_df['Mes'] = pd.Categorical(year_month_group_df['Mes'], categories=months, ordered=True)
month_selected = MDMultiselectFilter("Mes",year_month_group_df.sort_values(by="Mes", ascending=True)['Mes'].unique())
usergroups_selected = MDMultiselectFilter("Grupos de usuario",year_month_group_df['CustomerGroup'].unique())
especialidad_selected = MDMultiselectFilter("Especialidad",year_month_group_df['Speciality'].unique())


# Agrupamos los DataFrames en una lista para poder trabajrlos uno a uno en un bucle
dataframes = [[usagesdf, 'usages'],[npsdf, 'nps'],[installsdf, 'installs']]

for current in dataframes:
    current_df = current[0]
    current_df_name = current[1]

    # Pregutamos si hay algun filtro realizado, en caso de tenerlo, lo aplicamos al dataset para generar los gráficos
    if current_df_name == 'installs' or current_df_name == 'registers':
        current_df = filter_df(current_df, None)
    else:
        current_df = filter_df(current_df, 'Speciality')

    # Agrupamos el df por Mes para generar un chart mensual
    current_df["Año"] = current_df["Año"].astype(str)
    if years_selected and len(years_selected) <= 1:
        xAxisName = "Mes"
    else:
        xAxisName = "Año"

    if current_df_name == 'usages':
        # Hacemos un sum agrupando por el Axis X
        cy_current_df_date = current_df.groupby(xAxisName)['UsageAmount'].sum().reset_index(name ='UsageAmount')

        # Generamos el barchart mensual/anual
        st.subheader('Evolución de consultas Chat, Videoconsultas y Recetas Electrónicas - ' + xAxisName)
        st.container(border=True).bar_chart(cy_current_df_date, x=xAxisName, y="UsageAmount", color="#4fa6ff", x_label='', y_label='')
    
    elif current_df_name == 'nps':
        # Sumamos las encuestas agrupadas para calcular el NPS
        cy_current_df_date = current_df.groupby(xAxisName).agg({'promoters':'sum','detractors':'sum','surveys':'sum'})
        cy_current_df_date['Nps'] = ((cy_current_df_date['promoters'] - cy_current_df_date['detractors']) / cy_current_df_date['surveys'])*100
        cy_current_df_date = cy_current_df_date.groupby(xAxisName)['Nps'].mean().round(1).reset_index(name ='Nps')

        # Generamos el linechart mensual/anual
        st.subheader('Evolución de NPS - ' + xAxisName)
        if (cy_current_df_date[xAxisName].nunique() == 1) or (len(years_selected) == 1 and len(month_selected) == 1):
            st.container(border=True).scatter_chart(cy_current_df_date, x=xAxisName, y="Nps", color="#4fa6ff", x_label='', y_label='')
        else:
            st.container(border=True).line_chart(cy_current_df_date, x=xAxisName, y="Nps", color="#4fa6ff", x_label='', y_label='') 
    
    elif current_df_name == 'installs':
        # Sumamos el recuento de Instalaciones y Registros para obtener el ratio
        cy_current_df_date = current_df.groupby(xAxisName)['Installs'].sum().reset_index(name ='Installs')
        cy_registers_df_date = registersdf.groupby(xAxisName)['Registers'].sum().reset_index(name ='Registers')
        cy_current_df_date['ratio_regs'] = (cy_registers_df_date['Registers'] * 100) / cy_current_df_date['Installs'] 
        cy_current_df_date = cy_current_df_date.groupby(xAxisName)['ratio_regs'].mean().round(1).reset_index(name ='ratio_regs')

        # Generamos el linechart mensual/anual
        st.subheader('Evolución del % de Registros - ' + xAxisName)
        if (cy_current_df_date[xAxisName].nunique() == 1) or (len(years_selected) == 1 and len(month_selected) == 1):
            st.container(border=True).scatter_chart(cy_current_df_date, x=xAxisName, y="ratio_regs", color="#4fa6ff", x_label='', y_label='')
        else:
            st.container(border=True).line_chart(cy_current_df_date, x=xAxisName, y="ratio_regs", color="#4fa6ff", x_label='', y_label='') 

