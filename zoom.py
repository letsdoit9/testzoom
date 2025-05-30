import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta
from ta.trend import EMAIndicator, SMAIndicator, ADXIndicator
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.volatility import BollingerBands
from ta.trend import MACD
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import io
warnings.filterwarnings('ignore')

# ⚙️ CONFIGURATION
st.set_page_config(
    page_title="⚡ Lightning Stock Scanner",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Technical Stock Scanner with 12 Daily Conditions")
st.markdown("**Professional technical analysis with 12 specific daily conditions**")

# Display the 12 conditions
with st.expander("🔍 12 Daily Technical Conditions", expanded=False):
    st.markdown("""
    1. **EMA (5, 13, 26)** of daily close > 20
    2. **SMA (50, 100, 200)** of daily close > 20  
    3. **ADX(10)**: DI+ ≥ DI−
    4. **MACD (14,5,3)**: MACD line ≥ MACD signal
    5. **RSI(14)** > 40
    6. **StochRSI(14)** < 30
    7. **Bollinger Bands (20, 2)**: Daily close ≥ Upper Band
    8. **Bullish candle**: Daily close > open
    9. **Volume** > 100,000
    10. **Breakout**: Daily close × 1.05 > 200-day high
    11. **Momentum**: Daily close > previous close
    12. **Volume Strength**: Daily volume > 50-day SMA(volume)
    
    **Minimum**: 8 out of 12 conditions must be met
    """)

# Configuration in sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    access_token = st.text_input(
        "Upstox Access Token", 
        value='eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJBSzg0NzUiLCJqdGkiOiI2ODM5YjBkYzlmNGI5ODM2OWViMWQ2MWUiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc0ODYxMTI5MiwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzQ4NjQyNDAwfQ.F1ReJU8IXj7ahZTZtqMmR95CUYn_uHx2hHIEAWtWN6U',
        type="password"
    )
    
    min_conditions = st.slider(
        "Minimum Conditions Met",
        min_value=1,
        max_value=12,
        value=8,
        help="Minimum number of technical conditions that must be met (default: 8)"
    )
    
    max_workers = st.slider(
        "Concurrent Threads",
        min_value=5,
        max_value=20,
        value=15,
        help="Number of concurrent API requests"
    )
    
    use_cache = st.checkbox("Use Cache", value=True, help="Cache results for faster runs")

base_url = 'https://api.upstox.com/v3/historical-candle'

# Stock instruments
instruments_data = {
    'NSE_EQ|INE585B01010': 'MARUTI', 'NSE_EQ|INE139A01034': 'NATIONALUM', 'NSE_EQ|INE763I01026': 'TARIL', 'NSE_EQ|INE970X01018': 'LEMONTREE', 'NSE_EQ|INE522D01027': 'MANAPPURAM', 'NSE_EQ|INE427F01016': 'CHALET', 'NSE_EQ|INE00R701025': 'DALBHARAT', 'NSE_EQ|INE917I01010': 'BAJAJ-AUTO', 'NSE_EQ|INE146L01010': 'KIRLOSENG', 'NSE_EQ|INE267A01025': 'HINDZINC', 'NSE_EQ|INE466L01038': '360ONE', 'NSE_EQ|INE070A01015': 'SHREECEM', 'NSE_EQ|INE242C01024': 'ANANTRAJ', 'NSE_EQ|INE883F01010': 'AADHARHFC', 'NSE_EQ|INE749A01030': 'JINDALSTEL', 'NSE_EQ|INE171Z01026': 'BDL', 'NSE_EQ|INE591G01017': 'COFORGE', 'NSE_EQ|INE903U01023': 'SIGNATURE', 'NSE_EQ|INE160A01022': 'PNB', 'NSE_EQ|INE640A01023': 'SKFINDIA', 'NSE_EQ|INE814H01011': 'ADANIPOWER', 'NSE_EQ|INE736A01011': 'CDSL', 'NSE_EQ|INE301A01014': 'RAYMOND', 'NSE_EQ|INE102D01028': 'GODREJCP', 'NSE_EQ|INE600L01024': 'LALPATHLAB', 'NSE_EQ|INE134E01011': 'PFC', 'NSE_EQ|INE269A01021': 'SONATSOFTW', 'NSE_EQ|INE009A01021': 'INFY', 'NSE_EQ|INE962Y01021': 'IRCON', 'NSE_EQ|INE048G01026': 'NAVINFLUOR', 'NSE_EQ|INE918Z01012': 'KAYNES', 'NSE_EQ|INE376G01013': 'BIOCON', 'NSE_EQ|INE00M201021': 'SWSOLAR', 'NSE_EQ|INE619A01035': 'PATANJALI', 'NSE_EQ|INE465A01025': 'BHARATFORG', 'NSE_EQ|INE589A01014': 'NLCINDIA', 'NSE_EQ|INE463A01038': 'BERGEPAINT', 'NSE_EQ|INE622W01025': 'ACMESOLAR', 'NSE_EQ|INE256A01028': 'ZEEL', 'NSE_EQ|INE540L01014': 'ALKEM', 'NSE_EQ|INE237A01028': 'KOTAKBANK', 'NSE_EQ|INE126A01031': 'EIDPARRY', 'NSE_EQ|INE482A01020': 'CEATLTD', 'NSE_EQ|INE850D01014': 'GODREJAGRO', 'NSE_EQ|INE361B01024': 'DIVISLAB', 'NSE_EQ|INE517B01013': 'TTML', 'NSE_EQ|INE385C01021': 'SARDAEN', 'NSE_EQ|INE811K01011': 'PRESTIGE', 'NSE_EQ|INE01EA01019': 'VMM', 'NSE_EQ|INE510A01028': 'ENGINERSIN', 'NSE_EQ|INE030A01027': 'HINDUNILVR', 'NSE_EQ|INE872J01023': 'DEVYANI', 'NSE_EQ|INE476A01022': 'CANBK', 'NSE_EQ|INE419U01012': 'HAPPSTMNDS', 'NSE_EQ|INE691A01018': 'UCOBANK', 'NSE_EQ|INE745G01035': 'MCX', 'NSE_EQ|INE0W2G01015': 'SAGILITY', 'NSE_EQ|INE531E01026': 'HINDCOPPER', 'NSE_EQ|INE483C01032': 'TANLA', 'NSE_EQ|INE721A01047': 'SHRIRAMFIN', 'NSE_EQ|INE028A01039': 'BANKBARODA', 'NSE_EQ|INE670K01029': 'LODHA', 'NSE_EQ|INE039A01010': 'IFCI', 'NSE_EQ|INE914M01019': 'ASTERDM', 'NSE_EQ|INE570L01029': 'SAILIFE', 'NSE_EQ|INE158A01026': 'HEROMOTOCO', 'NSE_EQ|INE112L01020': 'METROPOLIS', 'NSE_EQ|INE405E01023': 'UNOMINDA', 'NSE_EQ|INE777K01022': 'RRKABEL', 'NSE_EQ|INE123W01016': 'SBILIFE', 'NSE_EQ|INE192A01025': 'TATACONSUM', 'NSE_EQ|INE398R01022': 'SYNGENE', 'NSE_EQ|INE118A01012': 'BAJAJHLDNG', 'NSE_EQ|INE371A01025': 'GRAPHITE', 'NSE_EQ|INE373A01013': 'BASF', 'NSE_EQ|INE674K01013': 'ABCAPITAL', 'NSE_EQ|INE094A01015': 'HINDPETRO', 'NSE_EQ|INE410P01011': 'NH', 'NSE_EQ|INE203A01020': 'ASTRAZEN', 'NSE_EQ|INE528G01035': 'YESBANK', 'NSE_EQ|INE248A01017': 'ITI', 'NSE_EQ|INE531F01015': 'NUVAMA', 'NSE_EQ|INE093I01010': 'OBEROIRLTY', 'NSE_EQ|INE616N01034': 'INOXINDIA', 'NSE_EQ|INE726G01019': 'ICICIPRULI', 'NSE_EQ|INE901L01018': 'APLLTD', 'NSE_EQ|INE271B01025': 'MAHSEAMLES', 'NSE_EQ|INE073K01018': 'SONACOMS', 'NSE_EQ|INE006I01046': 'ASTRAL', 'NSE_EQ|INE142M01025': 'TATATECH', 'NSE_EQ|INE036D01028': 'KARURVYSYA', 'NSE_EQ|INE885A01032': 'ARE&M', 'NSE_EQ|INE233B01017': 'BLUEDART', 'NSE_EQ|INE169A01031': 'COROMANDEL', 'NSE_EQ|INE235A01022': 'FINCABLES', 'NSE_EQ|INE668F01031': 'JYOTHYLAB', 'NSE_EQ|INE849A01020': 'TRENT', 'NSE_EQ|INE669C01036': 'TECHM', 'NSE_EQ|INE322A01010': 'GILLETTE', 'NSE_EQ|INE216A01030': 'BRITANNIA', 'NSE_EQ|INE002S01010': 'MGL', 'NSE_EQ|INE111A01025': 'CONCOR', 'NSE_EQ|INE531A01024': 'KANSAINER', 'NSE_EQ|INE062A01020': 'SBIN', 'NSE_EQ|INE180C01042': 'CGCL', 'NSE_EQ|INE128S01021': 'FIVESTAR', 'NSE_EQ|INE672A01018': 'TATAINVEST', 'NSE_EQ|INE216P01012': 'AAVAS', 'NSE_EQ|INE220B01022': 'KPIL', 'NSE_EQ|INE081A01020': 'TATASTEEL', 'NSE_EQ|INE007A01025': 'CRISIL', 'NSE_EQ|INE883A01011': 'MRF', 'NSE_EQ|INE824G01012': 'JSWHL', 'NSE_EQ|INE075A01022': 'WIPRO', 'NSE_EQ|INE498L01015': 'LTF', 'NSE_EQ|INE377N01017': 'WAAREEENER', 'NSE_EQ|INE484J01027': 'GODREJPROP', 'NSE_EQ|INE979A01025': 'SAREGAMA', 'NSE_EQ|INE188A01015': 'FACT', 'NSE_EQ|INE205A01025': 'VEDL', 'NSE_EQ|INE027H01010': 'MAXHEALTH', 'NSE_EQ|INE298J01013': 'NAM-INDIA', 'NSE_EQ|INE101D01020': 'GRANULES', 'NSE_EQ|INE212H01026': 'AIAENG', 'NSE_EQ|INE967H01025': 'KIMS', 'NSE_EQ|INE121A01024': 'CHOLAFIN', 'NSE_EQ|INE010J01012': 'TEJASNET', 'NSE_EQ|INE474Q01031': 'MEDANTA', 'NSE_EQ|INE839M01018': 'SCHNEIDER', 'NSE_EQ|INE074A01025': 'PRAJIND', 'NSE_EQ|INE974X01010': 'TIINDIA', 'NSE_EQ|INE854D01024': 'UNITDSPR', 'NSE_EQ|INE220G01021': 'JSL', 'NSE_EQ|INE742F01042': 'ADANIPORTS', 'NSE_EQ|INE226A01021': 'VOLTAS', 'NSE_EQ|INE0NT901020': 'NETWEB', 'NSE_EQ|INE292B01021': 'HBLENGINE', 'NSE_EQ|INE047A01021': 'GRASIM', 'NSE_EQ|INE326A01037': 'LUPIN', 'NSE_EQ|INE584A01023': 'NMDC', 'NSE_EQ|INE085A01013': 'CHAMBLFERT', 'NSE_EQ|INE03Q201024': 'ALIVUS', 'NSE_EQ|INE836A01035': 'BSOFT', 'NSE_EQ|INE548A01028': 'HFCL', 'NSE_EQ|INE501A01019': 'DEEPAKFERT', 'NSE_EQ|INE414G01012': 'MUTHOOTFIN', 'NSE_EQ|INE669E01016': 'IDEA', 'NSE_EQ|INE743M01012': 'RHIM', 'NSE_EQ|INE324A01032': 'JINDALSAW', 'NSE_EQ|INE211B01039': 'PHOENIXLTD', 'NSE_EQ|INE813H01021': 'TORNTPOWER', 'NSE_EQ|INE066P01011': 'INOXWIND', 'NSE_EQ|INE880J01026': 'JSWINFRA', 'NSE_EQ|INE358A01014': 'ABBOTINDIA', 'NSE_EQ|INE868B01028': 'NCC', 'NSE_EQ|INE172A01027': 'CASTROLIND', 'NSE_EQ|INE213A01029': 'ONGC', 'NSE_EQ|INE825A01020': 'VTL', 'NSE_EQ|INE0FS801015': 'MSUMI', 'NSE_EQ|INE335Y01020': 'IRCTC', 'NSE_EQ|INE406M01024': 'ERIS', 'NSE_EQ|INE725A01030': 'NAVA', 'NSE_EQ|INE00WC01027': 'AFFLE', 'NSE_EQ|INE931S01010': 'ADANIENSOL', 'NSE_EQ|INE704P01025': 'COCHINSHIP', 'NSE_EQ|INE053F01010': 'IRFC', 'NSE_EQ|INE127D01025': 'HDFCAMC', 'NSE_EQ|INE021A01026': 'ASIANPAINT', 'NSE_EQ|INE671A01010': 'HONAUT', 'NSE_EQ|INE356A01018': 'MPHASIS', 'NSE_EQ|INE571A01038': 'IPCALAB', 'NSE_EQ|INE733E01010': 'NTPC', 'NSE_EQ|INE230A01023': 'EIHOTEL', 'NSE_EQ|INE565A01014': 'IOB', 'NSE_EQ|INE022Q01020': 'IEX', 'NSE_EQ|INE115A01026': 'LICHSGFIN', 'NSE_EQ|INE475E01026': 'CAPLIPOINT', 'NSE_EQ|INE463V01026': 'ANANDRATHI', 'NSE_EQ|INE596I01012': 'CAMS', 'NSE_EQ|INE684F01012': 'FSL', 'NSE_EQ|INE702C01027': 'APLAPOLLO', 'NSE_EQ|INE017A01032': 'GESHIP', 'NSE_EQ|INE388Y01029': 'NYKAA', 'NSE_EQ|INE348B01021': 'CENTURYPLY', 'NSE_EQ|INE117A01022': 'ABB', 'NSE_EQ|INE239A01024': 'NESTLEIND', 'NSE_EQ|INE02ID01020': 'RAYMONDLSL', 'NSE_EQ|INE980O01024': 'JYOTICNC', 'NSE_EQ|INE228A01035': 'USHAMART', 'NSE_EQ|INE437A01024': 'APOLLOHOSP', 'NSE_EQ|INE245A01021': 'TATAPOWER', 'NSE_EQ|INE288B01029': 'DEEPAKNTR', 'NSE_EQ|INE053A01029': 'INDHOTEL', 'NSE_EQ|INE927D01051': 'JBMA', 'NSE_EQ|INE995S01015': 'NIVABUPA', 'NSE_EQ|INE100A01010': 'ATUL', 'NSE_EQ|INE665A01038': 'SWANENERGY', 'NSE_EQ|INE196A01026': 'MARICO', 'NSE_EQ|INE338H01029': 'CONCORDBIO', 'NSE_EQ|INE152M01016': 'TRITURBINE', 'NSE_EQ|INE121J01017': 'INDUSTOWER', 'NSE_EQ|INE140A01024': 'PEL', 'NSE_EQ|INE389H01022': 'KEC', 'NSE_EQ|INE399L01023': 'ATGL', 'NSE_EQ|INE055A01016': 'ABREL', 'NSE_EQ|INE024L01027': 'GRAVITA', 'NSE_EQ|INE615H01020': 'TITAGARH', 'NSE_EQ|INE121E01018': 'JSWENERGY', 'NSE_EQ|INE019A01038': 'JSWSTEEL', 'NSE_EQ|INE0IX101010': 'DATAPATTNS', 'NSE_EQ|INE450U01017': 'ROUTE', 'NSE_EQ|INE151A01013': 'TATACOMM', 'NSE_EQ|INE522F01014': 'COALINDIA', 'NSE_EQ|INE382Z01011': 'GRSE', 'NSE_EQ|INE095N01031': 'NBCC', 'NSE_EQ|INE296A01024': 'BAJFINANCE', 'NSE_EQ|INE066F01020': 'HAL', 'NSE_EQ|INE002A01018': 'RELIANCE', 'NSE_EQ|INE462A01022': 'BAYERCROP', 'NSE_EQ|INE961O01016': 'RAINBOW', 'NSE_EQ|INE203G01027': 'IGL', 'NSE_EQ|INE619B01017': 'NEWGEN', 'NSE_EQ|INE109A01011': 'SCI', 'NSE_EQ|INE183A01024': 'FINPIPE', 'NSE_EQ|INE113A01013': 'GNFC', 'NSE_EQ|INE467B01029': 'TCS', 'NSE_EQ|INE573A01042': 'JKTYRE', 'NSE_EQ|INE806T01020': 'SAPPHIRE', 'NSE_EQ|INE473A01011': 'LINDEINDIA', 'NSE_EQ|INE153T01027': 'BLS', 'NSE_EQ|INE258A01016': 'BEML', 'NSE_EQ|INE759A01021': 'MASTEK', 'NSE_EQ|INE0ONG01011': 'NTPCGREEN', 'NSE_EQ|INE149A01033': 'CHOLAHLDNG', 'NSE_EQ|INE192B01031': 'WELSPUNLIV', 'NSE_EQ|INE079A01024': 'AMBUJACEM', 'NSE_EQ|INE457L01029': 'PGEL', 'NSE_EQ|INE0J1Y01017': 'LICI', 'NSE_EQ|INE260B01028': 'GODFRYPHLP', 'NSE_EQ|INE299U01018': 'CROMPTON', 'NSE_EQ|INE040A01034': 'HDFCBANK', 'NSE_EQ|INE200A01026': 'GVT&D', 'NSE_EQ|INE121A08PJ0': 'CHOLAFIN', 'NSE_EQ|INE270A01029': 'ALOKINDS', 'NSE_EQ|INE371P01015': 'AMBER', 'NSE_EQ|INE205B01031': 'ELECON', 'NSE_EQ|INE486A01021': 'CESC', 'NSE_EQ|INE399G01023': 'RKFORGE', 'NSE_EQ|INE603J01030': 'PIIND', 'NSE_EQ|INE202E01016': 'IREDA', 'NSE_EQ|INE663F01032': 'NAUKRI', 'NSE_EQ|INE066A01021': 'EICHERMOT', 'NSE_EQ|INE844O01030': 'GUJGASLTD', 'NSE_EQ|INE481N01025': 'HOMEFIRST', 'NSE_EQ|INE421D01022': 'CCL', 'NSE_EQ|INE752E01010': 'POWERGRID', 'NSE_EQ|INE271C01023': 'DLF', 'NSE_EQ|INE318A01026': 'PIDILITIND', 'NSE_EQ|INE208C01025': 'AEGISLOG', 'NSE_EQ|INE520A01027': 'ZENSARTECH', 'NSE_EQ|INE818H01020': 'LTFOODS', 'NSE_EQ|INE499A01024': 'DCMSHRIRAM', 'NSE_EQ|INE306R01017': 'INTELLECT', 'NSE_EQ|INE042A01014': 'ESCORTS', 'NSE_EQ|INE176A01028': 'BATAINDIA', 'NSE_EQ|INE064C01022': 'TRIDENT', 'NSE_EQ|INE285K01026': 'TECHNOE', 'NSE_EQ|INE256C01024': 'TRIVENI', 'NSE_EQ|INE274F01020': 'WESTLIFE', 'NSE_EQ|INE947Q01028': 'LAURUSLABS', 'NSE_EQ|INE913H01037': 'ENDURANCE', 'NSE_EQ|INE918I01026': 'BAJAJFINSV', 'NSE_EQ|INE758E01017': 'JIOFIN', 'NSE_EQ|INE089A01031': 'DRREDDY', 'NSE_EQ|INE251B01027': 'ZENTEC', 'NSE_EQ|INE575P01011': 'STARHEALTH', 'NSE_EQ|INE195J01029': 'PNCINFRA', 'NSE_EQ|INE834M01019': 'RTNINDIA', 'NSE_EQ|INE848E01016': 'NHPC', 'NSE_EQ|INE852O01025': 'APTUS', 'NSE_EQ|INE545A01024': 'HEG', 'NSE_EQ|INE982J01020': 'PAYTM', 'NSE_EQ|INE205C01021': 'POLYMED', 'NSE_EQ|INE634I01029': 'KNRCON', 'NSE_EQ|INE761H01022': 'PAGEIND', 'NSE_EQ|INE342J01019': 'ZFCVINDIA', 'NSE_EQ|INE494B01023': 'TVSMOTOR', 'NSE_EQ|INE673O01025': 'TBOTEK', 'NSE_EQ|INE646L01027': 'INDIGO', 'NSE_EQ|INE0V6F01027': 'HYUNDAI', 'NSE_EQ|INE010B01027': 'ZYDUSLIFE', 'NSE_EQ|INE302A01020': 'EXIDEIND', 'NSE_EQ|INE0BY001018': 'JUBLINGREA', 'NSE_EQ|INE810G01011': 'SHYAMMETL', 'NSE_EQ|INE351F01018': 'JPPOWER', 'NSE_EQ|INE634S01028': 'MANKIND', 'NSE_EQ|INE191B01025': 'WELCORP', 'NSE_EQ|INE397D01024': 'BHARTIARTL', 'NSE_EQ|INE192R01011': 'DMART', 'NSE_EQ|INE686F01025': 'UBL', 'NSE_EQ|INE123F01029': 'MMTC', 'NSE_EQ|INE008A01015': 'IDBI', 'NSE_EQ|INE321T01012': 'DOMS', 'NSE_EQ|INE775A08105': 'MOTHERSON', 'NSE_EQ|INE933S01016': 'INDIAMART', 'NSE_EQ|INE732I01013': 'ANGELONE', 'NSE_EQ|INE059A01026': 'CIPLA', 'NSE_EQ|INE00E101023': 'BIKAJI', 'NSE_EQ|INE660A01013': 'SUNDARMFIN', 'NSE_EQ|INE03QK01018': 'COHANCE', 'NSE_EQ|INE138Y01010': 'KFINTECH', 'NSE_EQ|INE377Y01014': 'BAJAJHFL', 'NSE_EQ|INE168P01015': 'EMCURE', 'NSE_EQ|INE343G01021': 'BHARTIHEXA', 'NSE_EQ|INE481Y01014': 'GICRE', 'NSE_EQ|INE797F01020': 'JUBLFOOD', 'NSE_EQ|INE180A01020': 'MFSL', 'NSE_EQ|INE949L01017': 'AUBANK', 'NSE_EQ|INE881D01027': 'OFSS', 'NSE_EQ|INE795G01014': 'HDFCLIFE', 'NSE_EQ|INE439A01020': 'ASAHIINDIA', 'NSE_EQ|INE148I01020': 'SAMMAANCAP', 'NSE_EQ|INE823G01014': 'JKCEMENT', 'NSE_EQ|INE987B01026': 'NATCOPHARM', 'NSE_EQ|INE280A01028': 'TITAN', 'NSE_EQ|INE227W01023': 'CLEAN', 'NSE_EQ|INE716A01013': 'WHIRLPOOL', 'NSE_EQ|INE03JT01014': 'GODIGIT', 'NSE_EQ|INE298A01020': 'CUMMINSIND', 'NSE_EQ|INE470Y01017': 'NIACL', 'NSE_EQ|INE769A01020': 'AARTIIND', 'NSE_EQ|INE155A01022': 'TATAMOTORS', 'NSE_EQ|INE119A01028': 'BALRAMCHIN', 'NSE_EQ|INE258G01013': 'SUMICHEM', 'NSE_EQ|INE930H01031': 'KPRMILL', 'NSE_EQ|INE614G01033': 'RPOWER', 'NSE_EQ|INE274J01014': 'OIL', 'NSE_EQ|INE372A01015': 'APARINDS', 'NSE_EQ|INE02RE01045': 'FIRSTCRY', 'NSE_EQ|INE285A01027': 'ELGIEQUIP', 'NSE_EQ|INE383A01012': 'INDIACEM', 'NSE_EQ|INE012A01025': 'ACC', 'NSE_EQ|INE0NNS01018': 'NSLNISP', 'NSE_EQ|INE944F01028': 'RADICO', 'NSE_EQ|INE572E01012': 'PNBHOUSING', 'NSE_EQ|INE281B01032': 'LLOYDSME', 'NSE_EQ|INE050A01025': 'BBTC', 'NSE_EQ|INE095A01012': 'INDUSINDBK', 'NSE_EQ|INE09N301011': 'FLUOROCHEM', 'NSE_EQ|INE513A01022': 'SCHAEFFLER', 'NSE_EQ|INE562A01011': 'INDIANB', 'NSE_EQ|INE780C01023': 'JMFINANCIL', 'NSE_EQ|INE195A01028': 'SUPREMEIND', 'NSE_EQ|INE049B01025': 'WOCKPHARMA', 'NSE_EQ|INE483A01010': 'CENTRALBK', 'NSE_EQ|INE136B01020': 'CYIENT', 'NSE_EQ|INE043W01024': 'VIJAYA', 'NSE_EQ|INE209L01016': 'JWL', 'NSE_EQ|INE168A01041': 'J&KBANK', 'NSE_EQ|INE870H01013': 'NETWORK18', 'NSE_EQ|INE118H01025': 'BSE', 'NSE_EQ|INE364U01010': 'ADANIGREEN', 'NSE_EQ|INE101I01011': 'AFCONS', 'NSE_EQ|INE238A01034': 'AXISBANK', 'NSE_EQ|INE065X01017': 'INDGN', 'NSE_EQ|INE044A01036': 'SUNPHARMA', 'NSE_EQ|INE177H01039': 'GPIL', 'NSE_EQ|INE470A01017': '3MINDIA', 'NSE_EQ|INE338I01027': 'MOTILALOFS', 'NSE_EQ|INE935N01020': 'DIXON', 'NSE_EQ|INE002L01015': 'SJVN', 'NSE_EQ|INE038A01020': 'HINDALCO', 'NSE_EQ|INE031A01017': 'HUDCO', 'NSE_EQ|INE027A01015': 'RCF', 'NSE_EQ|INE242A01010': 'IOC', 'NSE_EQ|INE0DK501011': 'PPLPHARMA', 'NSE_EQ|INE0BV301023': 'MAPMYINDIA', 'NSE_EQ|INE131A01031': 'GMDCLTD', 'NSE_EQ|INE692A01016': 'UNIONBANK', 'NSE_EQ|INE477A01020': 'CANFINHOME', 'NSE_EQ|INE739E01017': 'CERA', 'NSE_EQ|INE04I401011': 'KPITTECH', 'NSE_EQ|INE061F01013': 'FORTIS', 'NSE_EQ|INE010V01017': 'LTTS', 'NSE_EQ|INE263A01024': 'BEL', 'NSE_EQ|INE120A01034': 'CARBORUNIV', 'NSE_EQ|INE020B01018': 'RECLTD', 'NSE_EQ|INE685A01028': 'TORNTPHARM', 'NSE_EQ|INE647A01010': 'SRF', 'NSE_EQ|INE491A01021': 'CUB', 'NSE_EQ|INE517F01014': 'GPPL', 'NSE_EQ|INE860A01027': 'HCLTECH', 'NSE_EQ|INE0BS701011': 'PREMIERENE', 'NSE_EQ|INE00H001014': 'SWIGGY', 'NSE_EQ|INE178A01016': 'CHENNPETRO', 'NSE_EQ|INE457A01014': 'MAHABANK', 'NSE_EQ|INE891D01026': 'REDINGTON', 'NSE_EQ|INE671H01015': 'SOBHA', 'NSE_EQ|INE278Y01022': 'CAMPUS', 'NSE_EQ|INE171A01029': 'FEDERALBNK', 'NSE_EQ|INE976G01028': 'RBLBANK', 'NSE_EQ|INE262H01021': 'PERSISTENT', 'NSE_EQ|INE084A01016': 'BANKINDIA', 'NSE_EQ|INE775A01035': 'MOTHERSON', 'NSE_EQ|INE217B01036': 'KAJARIACER', 'NSE_EQ|INE878B01027': 'KEI', 'NSE_EQ|INE599M01018': 'JUSTDIAL', 'NSE_EQ|INE325A01013': 'TIMKEN', 'NSE_EQ|INE741K01010': 'CREDITACC', 'NSE_EQ|INE018E01016': 'SBICARD', 'NSE_EQ|INE0LXG01040': 'OLAELEC', 'NSE_EQ|INE776C01039': 'GMRAIRPORT', 'NSE_EQ|INE417T01026': 'POLICYBZR', 'NSE_EQ|INE068V01023': 'GLAND', 'NSE_EQ|INE115Q01022': 'IKS', 'NSE_EQ|INE602A01031': 'PCBL', 'NSE_EQ|INE879I01012': 'DBREALTY', 'NSE_EQ|INE415G01027': 'RVNL', 'NSE_EQ|INE791I01019': 'BRIGADE', 'NSE_EQ|INE821I01022': 'IRB', 'NSE_EQ|INE323A01026': 'BOSCHLTD', 'NSE_EQ|INE320J01015': 'RITES', 'NSE_EQ|INE182A01018': 'PFIZER', 'NSE_EQ|INE548C01032': 'EMAMILTD', 'NSE_EQ|INE214T01019': 'LTIM', 'NSE_EQ|INE176B01034': 'HAVELLS', 'NSE_EQ|INE404A01024': 'ABSLAMC', 'NSE_EQ|INE545U01014': 'BANDHANBNK', 'NSE_EQ|INE152A01029': 'THERMAX', 'NSE_EQ|INE511C01022': 'POONAWALLA', 'NSE_EQ|INE150B01039': 'ALKYLAMINE', 'NSE_EQ|INE249Z01020': 'MAZDOCK', 'NSE_EQ|INE0DD101019': 'RAILTEL', 'NSE_EQ|INE087H01022': 'RENUKA', 'NSE_EQ|INE343H01029': 'SOLARINDS', 'NSE_EQ|INE732A01036': 'KIRLOSBROS', 'NSE_EQ|INE191H01014': 'PVRINOX', 'NSE_EQ|INE094J01016': 'UTIAMC', 'NSE_EQ|INE530B01024': 'IIFL', 'NSE_EQ|INE758T01015': 'ETERNAL', 'NSE_EQ|INE154A01025': 'ITC', 'NSE_EQ|INE455K01017': 'POLYCAB', 'NSE_EQ|INE406A01037': 'AUROPHARMA', 'NSE_EQ|INE387A01021': 'SUNDRMFAST', 'NSE_EQ|INE101A01026': 'M&M', 'NSE_EQ|INE208A01029': 'ASHOKLEY', 'NSE_EQ|INE303R01014': 'KALYANKJIL', 'NSE_EQ|INE148O01028': 'DELHIVERY', 'NSE_EQ|INE331A01037': 'RAMCOCEM', 'NSE_EQ|INE090A01021': 'ICICIBANK', 'NSE_EQ|INE472A01039': 'BLUESTARCO', 'NSE_EQ|INE628A01036': 'UPL', 'NSE_EQ|INE159A01016': 'GLAXO', 'NSE_EQ|INE787D01026': 'BALKRISIND', 'NSE_EQ|INE040H01021': 'SUZLON', 'NSE_EQ|INE09XN01023': 'AKUMS', 'NSE_EQ|INE018A01030': 'LT', 'NSE_EQ|INE092T01019': 'IDFCFIRSTB', 'NSE_EQ|INE700A01033': 'JUBLPHARMA', 'NSE_EQ|INE347G01014': 'PETRONET', 'NSE_EQ|INE103A01014': 'MRPL', 'NSE_EQ|INE067A01029': 'CGPOWER', 'NSE_EQ|INE438A01022': 'APOLLOTYRE', 'NSE_EQ|INE260D01016': 'OLECTRA', 'NSE_EQ|INE794A01010': 'NEULANDLAB', 'NSE_EQ|INE423A01024': 'ADANIENT', 'NSE_EQ|INE259A01022': 'COLPAL', 'NSE_EQ|INE07Y701011': 'POWERINDIA', 'NSE_EQ|INE765G01017': 'ICICIGI', 'NSE_EQ|INE257A01026': 'BHEL', 'NSE_EQ|INE774D01024': 'M&MFIN', 'NSE_EQ|INE206F01022': 'AIIL', 'NSE_EQ|INE424H01027': 'SUNTV', 'NSE_EQ|INE842C01021': 'MINDACORP', 'NSE_EQ|INE246F01010': 'GSPL', 'NSE_EQ|INE699H01024': 'AWL', 'NSE_EQ|INE647O01011': 'ABFRL', 'NSE_EQ|INE019C01026': 'HSCL', 'NSE_EQ|INE129A01019': 'GAIL', 'NSE_EQ|INE825V01034': 'MANYAVAR', 'NSE_EQ|INE731H01025': 'ACE', 'NSE_EQ|INE423Y01016': 'SBFC', 'NSE_EQ|INE481G01011': 'ULTRACEMCO', 'NSE_EQ|INE572A01036': 'JBCHEPHARM', 'NSE_EQ|INE0I7C01011': 'LATENTVIEW', 'NSE_EQ|INE233A01035': 'GODREJIND', 'NSE_EQ|INE114A01011': 'SAIL', 'NSE_EQ|INE031B01049': 'AJANTPHARM', 'NSE_EQ|INE774D08MG3': 'M&MFIN', 'NSE_EQ|INE935A01035': 'GLENMARK', 'NSE_EQ|INE003A01024': 'SIEMENS', 'NSE_EQ|INE029A01011': 'BPCL', 'NSE_EQ|INE670A01012': 'TATAELXSI', 'NSE_EQ|INE951I01027': 'VGUARD', 'NSE_EQ|INE092A01019': 'TATACHEM', 'NSE_EQ|INE200M01039': 'VBL', 'NSE_EQ|INE0DYJ01015': 'SYRMA', 'NSE_EQ|INE738I01010': 'ECLERX', 'NSE_EQ|INE00LO01017': 'CRAFTSMAN', 'NSE_EQ|INE0J5401028': 'HONASA', 'NSE_EQ|INE0Q9301021': 'IGIL', 'NSE_EQ|INE016A01026': 'DABUR', 'NSE_EQ|INE596F01018': 'PTCIL'
}

# Pre-calculate date range (need more data for 200-day indicators)
TO_DATE = datetime.today().strftime('%Y-%m-%d')
FROM_DATE = (datetime.today() - timedelta(days=400)).strftime('%Y-%m-%d')  # Increased for 200-day SMA

@st.cache_data(ttl=600 if use_cache else 1)
def fetch_single_stock_data_fast(instrument_key, symbol, access_token):
    """Fetch single stock data with proper error handling"""
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Connection': 'keep-alive'
    }
    
    encoded_key = instrument_key.replace('|', '%7C')
    url = f"{base_url}/{encoded_key}/days/1/{TO_DATE}/{FROM_DATE}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            candles = data.get('data', {}).get('candles', [])
            
            if len(candles) < 250:  # Need enough data for 200-day indicators
                return None
                
            # Create proper DataFrame
            candles_array = np.array(candles)
            df = pd.DataFrame({
                'date': pd.to_datetime(candles_array[:, 0]),
                'open': candles_array[:, 1].astype(float),
                'high': candles_array[:, 2].astype(float),
                'low': candles_array[:, 3].astype(float),
                'close': candles_array[:, 4].astype(float),
                'volume': candles_array[:, 5].astype(int)
            })
            
            # Sort by date (oldest first) for proper technical analysis
            df = df.sort_values('date').reset_index(drop=True)
            
            return {
                'symbol': symbol,
                'instrument_key': instrument_key,
                'df': df
            }
        else:
            st.error(f"API Error for {symbol}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Error fetching {symbol}: {str(e)}")
        return None

def fetch_all_stock_data_parallel(access_token, max_workers=15):
    """Parallel data fetching with progress tracking"""
    all_data = {}
    
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    total_stocks = len(instruments_data)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_single_stock_data_fast, key, symbol, access_token): symbol 
            for key, symbol in instruments_data.items()
        }
        
        for future in as_completed(futures):
            result = future.result()
            completed += 1
            
            if result:
                all_data[result['symbol']] = result
                status_text.text(f"✅ Loaded: {result['symbol']} ({completed}/{total_stocks})")
            
            progress_bar.progress(completed / total_stocks)
    
    progress_container.empty()
    return all_data

def calculate_12_conditions(stock_data):
    """Calculate the exact 12 technical conditions as specified"""
    df = stock_data['df']
    symbol = stock_data['symbol']
    
    if len(df) < 250:  # Need sufficient data for all indicators
        return None
    
    try:
        # Extract OHLCV data
        close = df['close']
        high = df['high']
        low = df['low']
        open_price = df['open']
        volume = df['volume']
        
        # Get current values (most recent)
        current_close = close.iloc[-1]
        current_open = open_price.iloc[-1]
        current_vol = volume.iloc[-1]
        previous_close = close.iloc[-2] if len(close) > 1 else current_close
        
        # Initialize conditions
        conditions = {}
        
        # 1. EMA (5, 13, 26) of daily close > 20
        ema_5 = EMAIndicator(close=close, window=5).ema_indicator().iloc[-1]
        ema_13 = EMAIndicator(close=close, window=13).ema_indicator().iloc[-1]
        ema_26 = EMAIndicator(close=close, window=26).ema_indicator().iloc[-1]
        conditions['ema_condition'] = all([ema_5 > 20, ema_13 > 20, ema_26 > 20])
        
        # 2. SMA (50, 100, 200) of daily close > 20
        sma_50 = SMAIndicator(close=close, window=50).sma_indicator().iloc[-1]
        sma_100 = SMAIndicator(close=close, window=100).sma_indicator().iloc[-1]
        sma_200 = SMAIndicator(close=close, window=200).sma_indicator().iloc[-1]
        conditions['sma_condition'] = all([sma_50 > 20, sma_100 > 20, sma_200 > 20])
        
        # 3. ADX(10): DI+ ≥ DI−
        adx_indicator = ADXIndicator(high=high, low=low, close=close, window=10)
        di_plus = adx_indicator.adx_pos().iloc[-1]
        di_minus = adx_indicator.adx_neg().iloc[-1]
        conditions['adx_condition'] = di_plus >= di_minus
        
        # 4. MACD (14,5,3): MACD line ≥ MACD signal
        macd_indicator = MACD(close=close, window_slow=14, window_fast=5, window_sign=3)
        macd_line = macd_indicator.macd().iloc[-1]
        macd_signal = macd_indicator.macd_signal().iloc[-1]
        conditions['macd_condition'] = macd_line >= macd_signal
        
        # 5. RSI(14) > 40
        rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]
        conditions['rsi_condition'] = rsi > 40
        
        # 6. StochRSI(14) < 30
        stoch_rsi = StochRSIIndicator(close=close, window=14, smooth1=3, smooth2=3)
        stoch_rsi_k = stoch_rsi.stochrsi_k().iloc[-1]
        conditions['stochrsi_condition'] = stoch_rsi_k < 30
        
        # 7. Bollinger Bands (20, 2): Daily close ≥ Upper Band
        bb = BollingerBands(close=close, window=20, window_dev=2)
        bb_upper = bb.bollinger_hband().iloc[-1]
        conditions['bb_condition'] = current_close >= bb_upper
        
        # 8. Bullish candle: Daily close > open
        conditions['bullish_candle'] = current_close > current_open
        
        # 9. Volume > 100,000
        conditions['volume_condition'] = current_vol > 100000
        
        # 10. Breakout: Daily close × 1.05 > 200-day high
        high_200 = high.rolling(200).max().iloc[-1]
        conditions['breakout_condition'] = (current_close * 1.05) > high_200
        
        # 11. Momentum: Daily close > previous close
        conditions['momentum_condition'] = current_close > previous_close
        
        # 12. Volume Strength: Daily volume > 50-day SMA(volume)
        volume_sma_50 = volume.rolling(50).mean().iloc[-1]
        conditions['volume_strength'] = current_vol > volume_sma_50
        
        # Count conditions met
        conditions_met = sum(conditions.values())
        
        # Calculate percentage change
        pct_change = ((current_close - previous_close) / previous_close) * 100 if previous_close > 0 else 0
        
        return {
            'symbol': symbol,
            'conditions_met': conditions_met,
            'pct_change': pct_change,
            'ltp': current_close,
            'volume': current_vol,
            'rsi': rsi,
            'date': df['date'].iloc[-1],
            'conditions': conditions,
            'individual_values': {
                'ema_5': ema_5, 'ema_13': ema_13, 'ema_26': ema_26,
                'sma_50': sma_50, 'sma_100': sma_100, 'sma_200': sma_200,
                'di_plus': di_plus, 'di_minus': di_minus,
                'macd_line': macd_line, 'macd_signal': macd_signal,
                'rsi': rsi, 'stoch_rsi': stoch_rsi_k,
                'bb_upper': bb_upper, 'high_200': high_200, 'volume_sma_50': volume_sma_50
            }
        }
        
    except Exception as e:
        st.error(f"Error calculating indicators for {symbol}: {str(e)}")
        return None

def analyze_stocks_with_12_conditions(stock_data_dict, min_conditions):
    """Analyze all stocks using the 12 specific conditions"""
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_stocks = len(stock_data_dict)
    processed = 0
    
    for symbol, data in stock_data_dict.items():
        result = calculate_12_conditions(data)
        processed += 1
        
        if result:
            status_text.text(f"📊 Analyzed: {symbol} ({result['conditions_met']}/12 conditions) - {processed}/{total_stocks}")
            
            if result['conditions_met'] >= min_conditions:
                results.append(result)
        else:
            status_text.text(f"⚠️ Skipped: {symbol} (insufficient data) - {processed}/{total_stocks}")
        
        progress_bar.progress(processed / total_stocks)
    
    progress_bar.empty()
    status_text.text(f"✅ Analysis complete: {len(results)} stocks meet criteria ({min_conditions}+ conditions)")
    
    return results

def main():
    """Main application"""
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔍 SCAN WITH 12 CONDITIONS", type="primary", use_container_width=True):
            scan_stocks()
    with col2:
        if st.button("🔄 Clear Cache"):
            st.cache_data.clear()
            st.rerun()

def scan_stocks():
    """Main scanning function with 12 conditions"""
    if not access_token:
        st.error("⚠️ Please provide your Upstox access token")
        return
    
    start_time = time.time()
    
    # Step 1: Fetch data
    with st.spinner("📊 Fetching historical data (need 250+ days for all indicators)..."):
        stock_data_dict = fetch_all_stock_data_parallel(access_token, max_workers)
    
    if not stock_data_dict:
        st.error("❌ No data retrieved. Check API connection.")
        return
    
    st.success(f"✅ Loaded {len(stock_data_dict)} stocks in {time.time() - start_time:.1f}s")
    
    # Step 2: Apply 12 conditions
    analysis_start = time.time()
    with st.spinner("🔍 Applying 12 technical conditions..."):
        results = analyze_stocks_with_12_conditions(stock_data_dict, min_conditions)
    
    analysis_time = time.time() - analysis_start
    
    # Step 3: Display results
    if not results:
        st.error(f"❌ No stocks meet criteria ({min_conditions}/12 conditions)")
        
        with st.expander("🔍 Debug Information"):
            st.write(f"**Analysis Summary:**")
            st.write(f"- Total stocks loaded: {len(stock_data_dict)}")
            st.write(f"- Minimum conditions required: {min_conditions}/12")
            st.write("- Try reducing minimum conditions to see partial matches")
            
            # Show sample analysis
            if stock_data_dict:
                sample_stock = list(stock_data_dict.keys())[0]
                sample_result = calculate_12_conditions(stock_data_dict[sample_stock])
                if sample_result:
                    st.write(f"**Sample Analysis ({sample_stock}):**")
                    st.write(f"- Conditions met: {sample_result['conditions_met']}/12")
                    
                    # Show individual condition results
                    condition_names = [
                        "EMA (5,13,26) > 20", "SMA (50,100,200) > 20", "ADX: DI+ ≥ DI−",
                        "MACD ≥ Signal", "RSI > 40", "StochRSI < 30", "Close ≥ BB Upper",
                        "Bullish Candle", "Volume > 100K", "Breakout", "Momentum", "Volume Strength"
                    ]
                    
                    for i, (condition, name) in enumerate(zip(sample_result['conditions'].values(), condition_names)):
                        status = "✅" if condition else "❌"
                        st.write(f"  {status} {name}")
        
        return
    
    # Sort by conditions met, then by percentage change
    results.sort(key=lambda x: (x['conditions_met'], x['pct_change']), reverse=True)
    
    # Create results table in the specified format
    df_results = pd.DataFrame([
        {
            'Sr. No': i + 1,
            'Stock Name': r['symbol'],
            'Symbol': f"{r['symbol']}.NS",  # Adding .NS as per NSE format
            '% Change': f"{r['pct_change']:.2f}%",
            'LTP': f"₹{r['ltp']:.2f}",
            'Volume': f"{r['volume']:,}",
            'Conditions Met': f"{r['conditions_met']}/12",
            'RSI': f"{r['rsi']:.1f}"
        }
        for i, r in enumerate(results)
    ])
    
    # Display results table
    st.subheader(f"🏆 Stocks Meeting {min_conditions}+ Conditions ({len(results)} found)")
    
    # Color coding for conditions
    def highlight_conditions(val):
        if isinstance(val, str) and '/12' in val:
            try:
                num = int(val.split('/')[0])
                if num >= 10:
                    return 'background-color: #00ff00; color: black; font-weight: bold'
                elif num >= 8:
                    return 'background-color: #90EE90; color: black'
                elif num >= 6:
                    return 'background-color: #FFFF99; color: black'
                else:
                    return 'background-color: #FFB6C1; color: black'
            except:
                pass
        return ''
    
    st.dataframe(
        df_results.style.applymap(highlight_conditions),
        use_container_width=True,
        height=400
    )
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⚡ Total Time", f"{time.time() - start_time:.1f}s")
    with col2:
        st.metric("📊 Analysis Time", f"{analysis_time:.1f}s")
    with col3:
        st.metric("🎯 Success Rate", f"{len(results)}/{len(stock_data_dict)}")
    with col4:
        if results:
            best_stock = results[0]
            st.metric("🏆 Top Stock", f"{best_stock['symbol']} ({best_stock['conditions_met']}/12)")
    
    # Export functionality
    if st.button("📥 Export Results", use_container_width=True):
        csv_data = df_results.to_csv(index=False)
        st.download_button(
            "💾 Download CSV",
            csv_data,
            f"technical_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )
    
    # Detailed breakdown
    with st.expander("📋 Detailed Technical Analysis", expanded=False):
        condition_names = [
            "EMA (5,13,26) > 20", "SMA (50,100,200) > 20", "ADX: DI+ ≥ DI−",
            "MACD ≥ Signal", "RSI > 40", "StochRSI < 30", "Close ≥ BB Upper",
            "Bullish Candle", "Volume > 100K", "Breakout", "Momentum", "Volume Strength"
        ]
        
        for result in results[:5]:  # Show top 5
            st.write(f"**{result['symbol']} - {result['conditions_met']}/12 conditions met**")
            
            # Show individual conditions with values
            col1, col2 = st.columns(2)
            
            conditions_list = list(result['conditions'].items())
            mid_point = len(conditions_list) // 2
            
            with col1:
                for i, ((condition_key, condition_result), name) in enumerate(zip(conditions_list[:mid_point], condition_names[:mid_point])):
                    status = "✅" if condition_result else "❌"
                    st.write(f"{status} **{name}**")
            
            with col2:
                for i, ((condition_key, condition_result), name) in enumerate(zip(conditions_list[mid_point:], condition_names[mid_point:])):
                    status = "✅" if condition_result else "❌"
                    st.write(f"{status} **{name}**")
            
            # Show key technical values
            st.write("**Key Values:**")
            values = result['individual_values']
            st.write(f"RSI: {values['rsi']:.1f} | EMA(5): ₹{values['ema_5']:.2f} | SMA(50): ₹{values['sma_50']:.2f} | Volume: {result['volume']:,}")
            
            st.divider()

if __name__ == "__main__":
    main()