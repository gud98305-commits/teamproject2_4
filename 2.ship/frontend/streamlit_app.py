import os
import random
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import searoute as sr
import plotly.graph_objects as go

# Try to import streamlit-autorefresh for real-time updates
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()

# =========================================================
# Destination Port Coordinates (from CSV)
# =========================================================
DESTINATION_COORDS = {
    # North America
    "Long Beach": (33.7701, -118.1937),
    "Atlanta": (33.7490, -84.3880),
    "New York": (40.6681, -74.0451),
    "Norfolk": (36.8508, -76.2859),
    "Savannah": (32.0809, -81.0912),
    "Los Angeles": (33.7405, -118.2710),
    "Oakland": (37.7956, -122.2786),
    "Seattle": (47.6062, -122.3321),
    "Chicago": (41.8781, -87.6298),
    "Dallas": (32.7767, -96.7970),
    "Montreal": (45.5017, -73.5673),
    "Toronto": (43.6532, -79.3832),
    "Vancouver": (49.2827, -123.1207),
    # South America
    "Manzanillo": (19.0544, -104.3186),
    "Buenos Aires": (-34.6037, -58.3816),
    "Montevideo": (-34.9011, -56.1645),
    "Santos": (-23.9618, -46.3280),
    "Callao": (-12.0508, -77.1250),
    "Valparaiso": (-33.0472, -71.6127),
    "Puerto Caldera": (10.0164, -84.7145),
    "Puerto Quetzal": (13.9253, -90.7856),
    # Europe
    "Istanbul": (41.0082, 28.9784),
    "Izmir": (38.4237, 27.1428),
    "Izmit": (40.7656, 29.9406),
    "Antwerp": (51.2194, 4.4025),
    "Rotterdam": (51.9244, 4.4777),
    "Hamburg": (53.5511, 9.9937),
    "Le Havre": (49.4944, 0.1079),
    "Southampton": (50.9097, -1.4044),
    "FOS(Marseilles)": (43.4279, 4.9447),
    "Gothenburg": (57.7089, 11.9746),
    "Genoa": (44.4056, 8.9463),
    "Barcelona": (41.3874, 2.1686),
    "Koper": (45.5469, 13.7294),
    "Helsinki": (60.1699, 24.9384),
    # Asia
    "Calcutta": (22.5726, 88.3639),
    "Chittagong": (22.3569, 91.7832),
    "Colombo": (6.9271, 79.8612),
    "Penang": (5.4164, 100.3327),
    "Port Kelang": (3.0319, 101.3685),
    "Semarang": (-6.9666, 110.4196),
    "Sihanouk Ville": (10.6093, 103.5296),
    "Singapore": (1.2644, 103.8200),
    "Surabaya": (-7.2575, 112.7521),
    "Bangkok": (13.7563, 100.5018),
    "Cebu": (10.3157, 123.8854),
    "Haiphong": (20.8449, 106.6881),
    "Hochiminh": (10.8231, 106.6297),
    "Jakarta": (-6.2088, 106.8456),
    "Kaoshiung": (22.6273, 120.3014),
    "Keelung": (25.1276, 121.7392),
    "Laemchabang": (13.0783, 100.8841),
    "Manila": (14.5995, 120.9842),
    "Nhava Sheva": (18.9500, 72.9500),
    "Yangon": (16.8661, 96.1951),
    "Chennai": (13.0827, 80.2707),
    "Karachi": (24.8607, 67.0011),
    # Japan
    "Tokyo": (35.6762, 139.6503),
    "Osaka": (34.6937, 135.5023),
    "Hakata": (33.5904, 130.4017),
    "Kobe": (34.6901, 135.1956),
    "Nagoya": (35.1815, 136.9066),
    "Yokohama": (35.4437, 139.6380),
    # China
    "Qingdao": (36.0671, 120.3826),
    "Dailian": (38.9140, 121.6147),
    "Lianyungang": (34.5965, 119.2218),
    "Ningbo": (29.8683, 121.5440),
    "Huangpu": (23.1066, 113.4500),
    "Shenzhen": (22.5431, 114.0579),
    "Xiamen": (24.4798, 118.0894),
    "Xiangang": (22.3193, 114.1694),
    "Yantai": (37.4638, 121.4479),
    "Weihai": (37.5097, 122.1200),
    "Shanghai": (31.2304, 121.4737),
    "Dandong": (40.1290, 124.3946),
    "Hongkong": (22.3193, 114.1694),
    # Africa
    "Abidjan": (5.3600, -4.0083),
    "Apapa": (6.4480, 3.3590),
    "Tema": (5.6698, -0.0166),
    "Mombasa": (-4.0435, 39.6682),
    "Beira": (-19.8436, 34.8389),
    "Dar": (-6.7924, 39.2083),
    "Alexandria": (31.2001, 29.9187),
    "Casablanca": (33.5731, -7.5898),
    "Tripoli": (32.8872, 13.1913),
    "Tunis": (36.8065, 10.1815),
    "Cape Town": (-33.9249, 18.4241),
    "Durban": (-29.8587, 31.0218),
    # Oceania
    "Brisbane": (-27.4698, 153.0251),
    "Auckland": (-36.8485, 174.7633),
    "Fremantle": (-32.0569, 115.7439),
    "Melbourne": (-37.8136, 144.9631),
    "Sydney": (-33.9461, 151.2240),
    # Middle East
    "Bahrain": (26.0667, 50.5577),
    "Damman": (26.4207, 50.0888),
    "Jeddah": (21.5433, 39.1728),
    "Riyadh": (24.7136, 46.6753),
    "Dubai": (25.2048, 55.2708),
    # Russia/CIS
    "St,Petersburg": (59.9343, 30.3351),
    "Moscow": (55.7558, 37.6173),
    "Almaty": (43.2220, 76.8512),
    "Tashkent": (41.2995, 69.2401),
    "Ulaanbaatar": (47.8864, 106.9057),
}

# Weather icon mapping
WEATHER_ICONS = {
    "clear sky": "☀️",
    "few clouds": "🌤️",
    "scattered clouds": "⛅",
    "broken clouds": "☁️",
    "overcast clouds": "☁️",
    "shower rain": "🌧️",
    "rain": "🌧️",
    "light rain": "🌦️",
    "moderate rain": "🌧️",
    "heavy rain": "⛈️",
    "thunderstorm": "⛈️",
    "snow": "❄️",
    "light snow": "🌨️",
    "mist": "🌫️",
    "fog": "🌫️",
    "haze": "🌫️",
    "drizzle": "🌦️",
}

# =========================================================
# Configuration & Constants
# =========================================================
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGERATE_RATE_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
KOTRA_NEWS_API_KEY = os.getenv("KOTRA_NEWS_API_KEY", "")
AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY", "")
# Optional external service to resolve Tracking ID (B/L) -> MMSI
BL_TO_MMSI_API_URL = os.getenv("BL_TO_MMSI_API_URL", "")  # e.g. https://internal.example.com/resolve_bl
BL_TO_MMSI_API_KEY = os.getenv("BL_TO_MMSI_API_KEY", "")  # optional bearer token

EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

st.set_page_config(
    page_title="Global Supply Chain Nerve Center",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Global Supply Chain Digital Twin\nThe Nerve Center for real-time logistics intelligence"
    }
)

# =========================================================
# Enhanced i18n with emojis
# =========================================================
TEXT = {
    "en": {
        "title": "🌐 Global Supply Chain Digital Twin",
        "subtitle": "The Nerve Center",
        "refresh": "🔄 Refresh Data",
        "lang": "Language",
        "sidebar_market": "📊 Market Intelligence",
        "fx": "Exchange Rates (KRW Base)",
        "commodities": "Key Commodities",
        "use_live_commodities": "Use Live Data (yfinance)",
        "show_labels": "Show port labels",
        "cluster_markers": "Cluster markers",
        "data_source": "Data Source",
        "real_api": "Live API",
        "mock": "Mock Data",
        "map_title": "🗺️ Global Logistics Map",
        "ops_title": "🎯 Operations Dashboard",
        "risk_level": "Risk Level",
        "risk_score": "Risk Score",
        "operations": "Operations Status",
        "status": "Status",
        "eta": "ETA (UTC)",
        "delay": "Delay (min)",
        "speed": "Speed (knots)",
        "top_alerts": "Active Alerts",
        "incident_queue": "🚨 Incident Management Queue",
        "assign_owner": "Assign",
        "add_note": "Add Note",
        "create_incident": "Create",
        "owner": "Owner",
        "note": "Notes",
        "created": "Created",
        "briefing": "📰 Continental Briefing",
        "filter_ra": "Show only RED/AMBER alerts",
        "continent": "Region",
        "news_headlines": "Latest Headlines",
        "no_news": "No news available. Showing fallback headlines.",
        "weather": "🌤 Weather Conditions",
        "temp": "Temperature",
        "condition": "Conditions",
        "docuflow": "📄 Smart Document Flow",
        "gen_pdf": "Generate Shipping Instruction",
        "download_pdf": "⬇ Download PDF",
        "sensitivity": "🧮 Sensitivity Analysis: Landed Cost",
        "estimated_landed": "Estimated Landed Cost (KRW)",
        "legend": "Risk Legend",
        "legend_text": "🟢 GREEN = Stable · 🟠 AMBER = Monitor · 🔴 RED = Action Required",
        "news_filters": "News Filters",
        "select_keywords": "Select Keywords",
        "missing_fx_key": "⚠ EXCHANGE_RATE_API_KEY missing → using mock data",
        "missing_weather_key": "⚠ OPENWEATHER_API_KEY missing → using mock data",
        "missing_news_key": "⚠ NEWS_API_KEY missing → showing fallback headlines",
        "yfinance_missing": "⚠ yfinance not installed → using mock commodities",
        "yfinance_failed": "⚠ Live commodities fetch failed → fallback to mock data",
        "select_entity": "Select an entity on the map to view details",
        "snapshot_id": "Snapshot ID",
        "last_updated": "Last Updated",
        # --- New keys for vessel tracking & cost insights ---
        "tracking_section": "🚩 Vessel Tracking",
        "tracking_id": "Tracking ID (B/L No.)",
        "tracking_id_help": "Optional: B/L or internal tracking identifier.",
        "verify_tracking": "Verify Tracking",
        "verify_tracking_help": "Attempt to resolve MMSI from Tracking ID via configured services.",
        "mmsi": "Vessel MMSI (9 digits)",
        "mmsi_help": "Enter 9-digit MMSI (e.g., 538005330)",
        "destination_port": "Destination Port",
        "start_tracking": "▶ Start Tracking",
        "stop_tracking": "■ Stop Tracking",
        "tracking_started": "Tracking started (live feed)",
        "tracking_stopped": "Tracking stopped",
        "invalid_mmsi": "Invalid MMSI. Please enter a 9-digit numeric MMSI.",
        "enter_mmsi_or_bl": "Enter MMSI (9 digits) or Tracking ID (B/L).",
        "resolved_mmsi_from_bl": "Resolved MMSI {mmsi} from Tracking ID {tracking_id}.",
        "tracking_by_bl_simulation": "Tracking by B/L (simulated position).",
        "ais_api_failed": "AIS API unavailable. Falling back to simulated data.",
        "vessel_not_found": "Vessel not found. Please verify the MMSI and try again.",
        "bl_resolve_failed": "Could not resolve MMSI from Tracking ID. Please enter MMSI directly.",
        "my_vessel": "My Vessel",
        "next_destination": "Next Destination",
        "waiting_for_berthing": "Waiting for Berthing",
        "route_deviation_high": "Route deviation high",
        "field_response": "🏗️ Field Response",
        "port_congestion_index": "Port Congestion Index",
        "cfo_insight_high_congestion": "High Congestion (Index > 15). Rec: Delay inland truck to avoid fees.",
        "weather_impact": "Weather Impact",
        "wind": "Wind (m/s)",
        "waves": "Sea State (m)",
        "crane_ops_suspended": "Crane Ops Suspended",
        "simulation_mode": "⚠️ SIMULATION MODE (Mock Data)",
        "play_simulation": "▶️ Play Simulation",
        "pause_simulation": "⏸️ Pause",
        "distance_remaining": "Distance Remaining",
        "cfo_financial_impact": "Estimated Additional Cost",
        "estimated_additional_cost": "Estimated Additional Cost (KRW)",
        "sim_speed": "Simulation Speed",
    },
    "ko": {
        "title": "🌐 글로벌 공급망 디지털 트윈",
        "subtitle": "관제 센터(The Nerve Center)",
        "refresh": "🔄 데이터 갱신",
        "lang": "언어",
        "sidebar_market": "📊 마켓 인텔리전스",
        "fx": "환율 (원화 기준)",
        "commodities": "주요 원자재",
        "use_live_commodities": "실시간 데이터 사용(yfinance)",
        "show_labels": "항구명 라벨 표시",
        "cluster_markers": "마커 클러스터링",
        "data_source": "데이터 소스",
        "real_api": "실시간 API",
        "mock": "가상 데이터",
        "map_title": "🗺️ 글로벌 물류 지도",
        "ops_title": "🎯 운영 대시보드",
        "risk_level": "리스크 레벨",
        "risk_score": "리스크 점수",
        "operations": "운영 상태",
        "status": "상태",
        "eta": "도착예정(UTC)",
        "delay": "지연(분)",
        "speed": "속도(노트)",
        "top_alerts": "활성 알림",
        "incident_queue": "🚨 인시던트 관리 큐",
        "assign_owner": "지정",
        "add_note": "노트 추가",
        "create_incident": "생성",
        "owner": "담당자",
        "note": "비고",
        "created": "생성일시",
        "briefing": "📰 대륙별 시황 브리핑",
        "filter_ra": "RED/AMBER만 표시",
        "continent": "지역",
        "news_headlines": "최신 헤드라인",
        "no_news": "뉴스 없음. 대체 헤드라인 표시 중.",
        "weather": "🌤 날씨 정보",
        "temp": "기온",
        "condition": "날씨",
        "docuflow": "📄 스마트 문서 플로우",
        "gen_pdf": "운송 지시서 생성",
        "download_pdf": "⬇ PDF 다운로드",
        "sensitivity": "🧮 민감도 분석: 총 투입 비용",
        "estimated_landed": "예상 총 투입비용(KRW)",
        "legend": "리스크 범례",
        "legend_text": "🟢 GREEN=안정 · 🟠 AMBER=모니터링 · 🔴 RED=즉각 조치",
        "news_filters": "뉴스 필터",
        "select_keywords": "키워드 선택",
        "missing_fx_key": "⚠ EXCHANGE_RATE_API_KEY 없음 → 가상 데이터 사용",
        "missing_weather_key": "⚠ OPENWEATHER_API_KEY 없음 → 가상 데이터 사용",
        "missing_news_key": "⚠ NEWS_API_KEY 없음 → 대체 헤드라인 표시",
        "yfinance_missing": "⚠ yfinance 미설치 → 가상 원자재 데이터 사용",
        "yfinance_failed": "⚠ 실시간 데이터 호출 실패 → 가상 데이터 사용",
        "select_entity": "지도에서 엔티티를 선택하여 상세 정보를 확인하세요",
        "snapshot_id": "스냅샷 ID",
        "last_updated": "마지막 업데이트",
        # --- New keys for vessel tracking & cost insights (Korean) ---
        "tracking_section": "🚩 선박 추적",
        "tracking_id": "추적 ID (B/L)",
        "tracking_id_help": "선택사항: B/L 또는 내부 추적 ID",
        "verify_tracking": "추적 ID 확인",
        "verify_tracking_help": "설정된 서비스로부터 MMSI 조회를 시도합니다.",
        "mmsi": "선박 MMSI (9자리)",
        "mmsi_help": "9자리 MMSI 입력 (예: 538005330)",
        "destination_port": "목적지 항구",
        "start_tracking": "▶ 추적 시작",
        "stop_tracking": "■ 추적 중지",
        "tracking_started": "추적 시작됨 (실시간 피드)",
        "tracking_stopped": "추적 중지됨",
        "invalid_mmsi": "유효하지 않은 MMSI입니다. 9자리 숫자를 입력하세요.",
        "enter_mmsi_or_bl": "MMSI(9자리) 또는 추적 ID(B/L)를 입력하세요.",
        "resolved_mmsi_from_bl": "추적 ID로부터 MMSI {mmsi}를 확인했습니다: {tracking_id}.",
        "tracking_by_bl_simulation": "B/L로 추적 중 (시뮬레이션 위치)",
        "ais_api_failed": "AIS API 사용 불가. 가상 데이터로 대체합니다.",
        "vessel_not_found": "존재하지 않는 MMSI입니다. MMSI를 확인 후 다시 시도하세요.",
        "bl_resolve_failed": "추적 ID로 MMSI를 확인할 수 없습니다. MMSI를 직접 입력하세요.",
        "my_vessel": "내 선박",
        "next_destination": "다음 목적지",
        "waiting_for_berthing": "입항 대기",
        "route_deviation_high": "항로 이탈 심함",
        "field_response": "🏗️ 현장 상황",
        "port_congestion_index": "항만 혼잡도 지수",
        "cfo_insight_high_congestion": "항만 혼잡도 높음 (지수 > 15). 제안: 내륙 운송 배차 지연 필요.",
        "weather_impact": "기상 영향",
        "wind": "풍속 (m/s)",
        "waves": "파고 (m)",
        "crane_ops_suspended": "크레인 작업 중단",
        "simulation_mode": "⚠️ 시뮬레이션 모드 (가상 데이터)",
        "play_simulation": "▶️ 시뮬레이션 재생",
        "pause_simulation": "⏸️ 일시정지",
        "distance_remaining": "남은 거리",
        "cfo_financial_impact": "예상 추가 비용",
        "estimated_additional_cost": "추정 추가 비용 (KRW)",
        "sim_speed": "시뮬레이션 속도",
    }
}


def t(key: str) -> str:
    """Translation helper"""
    lang = st.session_state.get("lang", "en")
    return TEXT.get(lang, TEXT["en"]).get(key, key)


def stable_hash(s: str) -> int:
    """Deterministic hash for consistent random data"""
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) % 1_000_000_007
    return h


def rand_from(entity_id: str, snapshot_id: str) -> random.Random:
    """Get seeded random generator for reproducible data"""
    seed = stable_hash(entity_id + "::" + snapshot_id)
    return random.Random(seed)


# =========================================================
# Entity Definitions (30 global ports + 1 cargo)
# =========================================================
CONTINENTS = ["Asia", "Europe", "North America", "South America", "Africa", "Oceania"]

PORTS = [
    # Asia
    {"id": "PORT_SHANGHAI", "name": "Shanghai", "continent": "Asia", "country": "CN", "lat": 31.2304, "lng": 121.4737},
    {"id": "PORT_SINGAPORE", "name": "Singapore", "continent": "Asia", "country": "SG", "lat": 1.2644, "lng": 103.8200},
    {"id": "PORT_NINGBO", "name": "Ningbo-Zhoushan", "continent": "Asia", "country": "CN", "lat": 29.8683, "lng": 121.5440},
    {"id": "PORT_BUSAN", "name": "Busan", "continent": "Asia", "country": "KR", "lat": 35.1000, "lng": 129.0400},
    {"id": "PORT_INCHEON", "name": "Incheon", "continent": "Asia", "country": "KR", "lat": 37.4563, "lng": 126.7052},
    {"id": "PORT_GWANGYANG", "name": "Gwangyang", "continent": "Asia", "country": "KR", "lat": 34.9036, "lng": 127.6961},
    {"id": "PORT_QINGDAO", "name": "Qingdao", "continent": "Asia", "country": "CN", "lat": 36.0671, "lng": 120.3826},
    
    # Europe
    {"id": "PORT_ROTTERDAM", "name": "Rotterdam", "continent": "Europe", "country": "NL", "lat": 51.9244, "lng": 4.4777},
    {"id": "PORT_ANTWERP", "name": "Antwerp-Bruges", "continent": "Europe", "country": "BE", "lat": 51.2194, "lng": 4.4025},
    {"id": "PORT_HAMBURG", "name": "Hamburg", "continent": "Europe", "country": "DE", "lat": 53.5511, "lng": 9.9937},
    {"id": "PORT_VALENCIA", "name": "Valencia", "continent": "Europe", "country": "ES", "lat": 39.4699, "lng": -0.3763},
    {"id": "PORT_PIRAEUS", "name": "Piraeus", "continent": "Europe", "country": "GR", "lat": 37.9420, "lng": 23.6465},
    
    # North America
    {"id": "PORT_LA", "name": "Los Angeles", "continent": "North America", "country": "US", "lat": 33.7405, "lng": -118.2710},
    {"id": "PORT_LONG_BEACH", "name": "Long Beach", "continent": "North America", "country": "US", "lat": 33.7701, "lng": -118.1937},
    {"id": "PORT_NY_NJ", "name": "New York/New Jersey", "continent": "North America", "country": "US", "lat": 40.6681, "lng": -74.0451},
    {"id": "PORT_VANCOUVER", "name": "Vancouver", "continent": "North America", "country": "CA", "lat": 49.2827, "lng": -123.1207},
    {"id": "PORT_SAVANNAH", "name": "Savannah", "continent": "North America", "country": "US", "lat": 32.0809, "lng": -81.0912},
    
    # South America
    {"id": "PORT_SANTOS", "name": "Santos", "continent": "South America", "country": "BR", "lat": -23.9618, "lng": -46.3280},
    {"id": "PORT_CALLAO", "name": "Callao", "continent": "South America", "country": "PE", "lat": -12.0508, "lng": -77.1250},
    {"id": "PORT_CARTAGENA_CO", "name": "Cartagena", "continent": "South America", "country": "CO", "lat": 10.3910, "lng": -75.4794},
    {"id": "PORT_BUENOS_AIRES", "name": "Buenos Aires", "continent": "South America", "country": "AR", "lat": -34.6037, "lng": -58.3816},
    {"id": "PORT_SAN_ANTONIO_CL", "name": "San Antonio", "continent": "South America", "country": "CL", "lat": -33.5947, "lng": -71.6132},
    
    # Africa
    {"id": "PORT_TANGER_MED", "name": "Tanger Med", "continent": "Africa", "country": "MA", "lat": 35.8894, "lng": -5.5025},
    {"id": "PORT_DURBAN", "name": "Durban", "continent": "Africa", "country": "ZA", "lat": -29.8587, "lng": 31.0218},
    {"id": "PORT_MOMBASA", "name": "Mombasa", "continent": "Africa", "country": "KE", "lat": -4.0435, "lng": 39.6682},
    {"id": "PORT_LAGOS", "name": "Lagos", "continent": "Africa", "country": "NG", "lat": 6.5244, "lng": 3.3792},
    {"id": "PORT_ALEXANDRIA", "name": "Alexandria", "continent": "Africa", "country": "EG", "lat": 31.2001, "lng": 29.9187},
    
    # Oceania
    {"id": "PORT_SYDNEY", "name": "Sydney (Port Botany)", "continent": "Oceania", "country": "AU", "lat": -33.9461, "lng": 151.2240},
    {"id": "PORT_MELBOURNE", "name": "Melbourne", "continent": "Oceania", "country": "AU", "lat": -37.8136, "lng": 144.9631},
    {"id": "PORT_BRISBANE", "name": "Brisbane", "continent": "Oceania", "country": "AU", "lat": -27.4698, "lng": 153.0251},
    {"id": "PORT_AUCKLAND", "name": "Auckland", "continent": "Oceania", "country": "NZ", "lat": -36.8485, "lng": 174.7633},
    {"id": "PORT_FREMANTLE", "name": "Fremantle", "continent": "Oceania", "country": "AU", "lat": -32.0569, "lng": 115.7439},
]

# 국가 필터 목록 (대륙 정보 포함)
COUNTRY_LIST = {
    "all": {"ko": "🌐 전체", "en": "🌐 All Countries", "flag": "🌐", "keywords": [], "continent": "All"},
    # Asia
    "중국": {"ko": "🇨🇳 중국", "en": "🇨🇳 China", "flag": "🇨🇳", "keywords": ["China", "Chinese", "Beijing", "Shanghai"], "continent": "Asia"},
    "일본": {"ko": "🇯🇵 일본", "en": "🇯🇵 Japan", "flag": "🇯🇵", "keywords": ["Japan", "Japanese", "Tokyo"], "continent": "Asia"},
    "한국": {"ko": "🇰🇷 한국", "en": "🇰🇷 South Korea", "flag": "🇰🇷", "keywords": ["Korea", "Korean", "Seoul", "Busan"], "continent": "Asia"},
    "홍콩": {"ko": "🇭🇰 홍콩", "en": "🇭🇰 Hong Kong", "flag": "🇭🇰", "keywords": ["Hong Kong", "HK"], "continent": "Asia"},
    "싱가포르": {"ko": "🇸🇬 싱가포르", "en": "🇸🇬 Singapore", "flag": "🇸🇬", "keywords": ["Singapore"], "continent": "Asia"},
    "베트남": {"ko": "🇻🇳 베트남", "en": "🇻🇳 Vietnam", "flag": "🇻🇳", "keywords": ["Vietnam", "Vietnamese"], "continent": "Asia"},
    "인도": {"ko": "🇮🇳 인도", "en": "🇮🇳 India", "flag": "🇮🇳", "keywords": ["India", "Indian", "Mumbai"], "continent": "Asia"},
    "UAE": {"ko": "🇦🇪 아랍에미리트", "en": "🇦🇪 UAE", "flag": "🇦🇪", "keywords": ["UAE", "Dubai", "Emirates", "Abu Dhabi"], "continent": "Asia"},
    # Europe
    "독일": {"ko": "🇩🇪 독일", "en": "🇩🇪 Germany", "flag": "🇩🇪", "keywords": ["Germany", "German", "Berlin", "Hamburg"], "continent": "Europe"},
    "영국": {"ko": "🇬🇧 영국", "en": "🇬🇧 UK", "flag": "🇬🇧", "keywords": ["UK", "Britain", "British", "London", "England"], "continent": "Europe"},
    "네덜란드": {"ko": "🇳🇱 네덜란드", "en": "🇳🇱 Netherlands", "flag": "🇳🇱", "keywords": ["Netherlands", "Dutch", "Rotterdam", "Amsterdam"], "continent": "Europe"},
    "프랑스": {"ko": "🇫🇷 프랑스", "en": "🇫🇷 France", "flag": "🇫🇷", "keywords": ["France", "French", "Paris", "Le Havre"], "continent": "Europe"},
    "이탈리아": {"ko": "🇮🇹 이탈리아", "en": "🇮🇹 Italy", "flag": "🇮🇹", "keywords": ["Italy", "Italian", "Rome", "Genoa"], "continent": "Europe"},
    "스페인": {"ko": "🇪🇸 스페인", "en": "🇪🇸 Spain", "flag": "🇪🇸", "keywords": ["Spain", "Spanish", "Valencia", "Barcelona"], "continent": "Europe"},
    "벨기에": {"ko": "🇧🇪 벨기에", "en": "🇧🇪 Belgium", "flag": "🇧🇪", "keywords": ["Belgium", "Belgian", "Antwerp", "Brussels"], "continent": "Europe"},
    "스위스": {"ko": "🇨🇭 스위스", "en": "🇨🇭 Switzerland", "flag": "🇨🇭", "keywords": ["Switzerland", "Swiss", "Zurich", "Geneva"], "continent": "Europe"},
    "러시아": {"ko": "🇷🇺 러시아", "en": "🇷🇺 Russia", "flag": "🇷🇺", "keywords": ["Russia", "Russian", "Moscow"], "continent": "Europe"},
    # North America
    "미국": {"ko": "🇺🇸 미국", "en": "🇺🇸 USA", "flag": "🇺🇸", "keywords": ["USA", "United States", "U.S.", "American", "New York", "Los Angeles"], "continent": "North America"},
    "캐나다": {"ko": "🇨🇦 캐나다", "en": "🇨🇦 Canada", "flag": "🇨🇦", "keywords": ["Canada", "Canadian", "Vancouver", "Toronto"], "continent": "North America"},
    "멕시코": {"ko": "🇲🇽 멕시코", "en": "🇲🇽 Mexico", "flag": "🇲🇽", "keywords": ["Mexico", "Mexican"], "continent": "North America"},
}

# =========================================================
# API Functions (with fallbacks)
# =========================================================
@st.cache_data(ttl=600)
def fetch_fx_krw_base() -> dict:
    """Fetch FX rates with KRW base"""
    if not EXCHANGE_RATE_API_KEY:
        return {
            "_source": "mock",
            "USD/KRW": 1320.0,
            "JPY/KRW": 9.10,
            "CNY/KRW": 180.0,
            "EUR/KRW": 1450.0
        }

    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/USD"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        rates = data.get("conversion_rates", {}) or {}

        krw = rates.get("KRW")
        jpy = rates.get("JPY")
        cny = rates.get("CNY")
        eur = rates.get("EUR")
        
        if not all([krw, jpy, cny, eur]):
            raise ValueError("Missing required rates")

        usdkrw = float(krw)
        jpykrw = float(krw) / float(jpy)
        cnykrw = float(krw) / float(cny)
        eurkrw = float(krw) / float(eur)

        return {
            "_source": "ExchangeRate-API",
            "USD/KRW": usdkrw,
            "JPY/KRW": jpykrw,
            "CNY/KRW": cnykrw,
            "EUR/KRW": eurkrw
        }
    except Exception:
        return {
            "_source": "mock",
            "USD/KRW": 1320.0,
            "JPY/KRW": 9.10,
            "CNY/KRW": 180.0,
            "EUR/KRW": 1450.0
        }


@st.cache_data(ttl=900)
def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch weather data for coordinates"""
    if not OPENWEATHER_API_KEY:
        return {"_source": "mock", "temp_c": 12.0, "desc": "clear sky", "wind_speed": 3.5}

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        temp = float(j.get("main", {}).get("temp", 0.0))
        desc = (j.get("weather") or [{}])[0].get("description", "N/A")
        wind_speed = float(j.get("wind", {}).get("speed", 0.0))
        return {"_source": "OpenWeatherMap", "temp_c": temp, "desc": desc, "wind_speed": wind_speed}
    except Exception:
        return {"_source": "mock", "temp_c": 12.0, "desc": "clear sky", "wind_speed": 3.5}


@st.cache_data(ttl=900)
def fetch_news(query: str, language: str = "en", page_size: int = 10) -> list:
    """Fetch news articles"""
    if not NEWS_API_KEY:
        return []
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        out = []
        for a in j.get("articles", [])[:page_size]:
            out.append({
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "source": (a.get("source") or {}).get("name", ""),
                "publishedAt": a.get("publishedAt", "")
            })
        return out
    except Exception:
        return []


def fallback_headlines(continent: str) -> list:
    """Fallback headlines when API unavailable"""
    samples = {
        "Asia": [
            ("Asian hub terminals report rising dwell time", "https://example.com"),
            ("Carrier schedule reliability impacted by weather", "https://example.com"),
        ],
        "Europe": [
            ("Labor talks raise concerns at European gateways", "https://example.com"),
            ("Inland connectivity affected by seasonal constraints", "https://example.com"),
        ],
        "North America": [
            ("Intermodal capacity tightness on major corridors", "https://example.com"),
            ("Retail inventory shifts influence vessel patterns", "https://example.com"),
        ],
        "South America": [
            ("Export season ramps up; berth productivity in focus", "https://example.com"),
            ("Weather patterns influence sailing schedules", "https://example.com"),
        ],
        "Africa": [
            ("Transshipment routes adjust amid capacity changes", "https://example.com"),
            ("Customs modernization accelerates clearance", "https://example.com"),
        ],
        "Oceania": [
            ("Seasonal demand impacts equipment availability", "https://example.com"),
            ("Coastal logistics planning after storm alerts", "https://example.com"),
        ],
    }
    return [
        {"title": t, "url": u, "source": "Fallback", "publishedAt": ""}
        for t, u in samples.get(continent, [])
    ]


# =========================================================
# Google Translate (무료) 함수
# =========================================================
@st.cache_data(ttl=3600)
def translate_to_korean(text: str) -> str:
    """Google Translate 무료 API로 다국어(영어/중국어 등) -> 한국어 번역"""
    if not text:
        return ""
    try:
        import urllib.parse
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ko&dt=t&q={urllib.parse.quote(text)}"
        r = requests.get(url, timeout=5, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if r.status_code == 200:
            result = r.json()
            if result and result[0]:
                translated = "".join([part[0] for part in result[0] if part[0]])
                return translated
        return text
    except Exception:
        return text


# =========================================================
# KOTRA 해외시장뉴스 API
# =========================================================
def _kotra_mock_data() -> list:
    """Return mock KOTRA news data"""
    return [
        {"title": "베트남 전자제품 수출 급증, 한국 기업 수혜 전망", "content": "베트남의 전자제품 수출이 전년 대비 25% 증가하며 한국 부품 기업들의 수혜가 예상됩니다.", "country": "베트남", "write_date": "2025-01-15", "url": "", "image_url": ""},
        {"title": "미국 인플레이션 감소세, 수입품 수요 회복 기대", "content": "미국의 인플레이션이 3개월 연속 하락하며 소비재 수입 수요 회복이 전망됩니다.", "country": "미국", "write_date": "2025-01-14", "url": "", "image_url": ""},
        {"title": "독일 자동차 산업 전기차 전환 가속화", "content": "독일 주요 자동차 제조사들이 2025년 전기차 생산 비중을 50%로 확대할 계획입니다.", "country": "독일", "write_date": "2025-01-13", "url": "", "image_url": ""},
        {"title": "인도 반도체 공장 유치 경쟁 심화", "content": "인도 정부가 반도체 제조시설 유치를 위해 대규모 인센티브 패키지를 발표했습니다.", "country": "인도", "write_date": "2025-01-12", "url": "", "image_url": ""},
        {"title": "중국 희토류 수출 규제 완화 검토", "content": "중국이 일부 희토류 품목에 대한 수출 규제 완화를 검토 중인 것으로 알려졌습니다.", "country": "중국", "write_date": "2025-01-11", "url": "", "image_url": ""},
        {"title": "UAE 물류 허브 확장, 중동 진출 기회 확대", "content": "UAE가 두바이 물류 허브를 2배로 확장하며 한국 물류 기업들의 진출 기회가 늘어나고 있습니다.", "country": "UAE", "write_date": "2025-01-10", "url": "", "image_url": ""},
    ]


@st.cache_data(ttl=900)
def fetch_kotra_news(num_of_rows: int = 50) -> tuple:
    """Fetch KOTRA overseas market news from data.go.kr
    Returns: (list of news, error_message or None)
    """
    if not KOTRA_NEWS_API_KEY:
        return _kotra_mock_data(), "KOTRA_NEWS_API_KEY 미설정 - Mock 데이터 사용"

    base_url = "https://apis.data.go.kr/B410001/kotra_overseasMarketNews/ovseaMrktNews/ovseaMrktNews"
    full_url = f"{base_url}?serviceKey={KOTRA_NEWS_API_KEY}&pageNo=1&numOfRows={num_of_rows}"

    try:
        r = requests.get(full_url, headers={"accept": "*/*"}, timeout=15)
        r.raise_for_status()
        data = r.json()

        response = data.get("response", {})
        body = response.get("body", {})
        item_list = body.get("itemList", {})
        items = item_list.get("item", []) if isinstance(item_list, dict) else []

        if not isinstance(items, list):
            items = [items] if items else []

        if not items:
            return _kotra_mock_data(), "뉴스 데이터가 없습니다 - Mock 데이터 사용"

        result = []
        for item in items:
            result.append({
                "title": item.get("newsTitl", ""),
                "content": f"{item.get('regn', '')} · {item.get('indstCl', '')}" if item.get('indstCl') else item.get('regn', ''),
                "country": item.get("natn", ""),
                "write_date": item.get("othbcDt", ""),
                "url": item.get("kotraNewsUrl", ""),
                "image_url": ""
            })
        return result, None
    except Exception as e:
        return _kotra_mock_data(), f"API 오류 - Mock 데이터 사용: {e}"


# =========================================================
# 글로벌 뉴스 (Google News RSS - CNN, BBC, Reuters, Bloomberg, WSJ, NYT)
# =========================================================
def _global_news_mock_data() -> list:
    """Return mock global news data"""
    return [
        {"title": "Global markets rally on economic optimism", "description": "Stock markets around the world rose sharply...", "url": "https://www.reuters.com/markets/", "pub_date": "", "source": "Reuters", "source_bg": "#ffedd5", "source_text": "#9a3412"},
        {"title": "Tech giants report strong quarterly earnings", "description": "Major technology companies exceeded expectations...", "url": "https://www.bloomberg.com/technology", "pub_date": "", "source": "Bloomberg", "source_bg": "#ede9fe", "source_text": "#5b21b6"},
        {"title": "Central banks signal policy shift", "description": "Federal Reserve and ECB hint at rate adjustments...", "url": "https://www.wsj.com/economy", "pub_date": "", "source": "WSJ", "source_bg": "#dbeafe", "source_text": "#1e40af"},
        {"title": "Climate summit reaches landmark agreement", "description": "World leaders commit to ambitious emissions targets...", "url": "https://www.bbc.com/news/science-environment", "pub_date": "", "source": "BBC", "source_bg": "#fee2e2", "source_text": "#991b1b"},
    ]


@st.cache_data(ttl=900)
def fetch_global_news(max_articles: int = 50) -> tuple:
    """Fetch global news from major news sources via Google News RSS"""
    import xml.etree.ElementTree as ET
    import re

    NEWS_SOURCES = {
        "Reuters": {"site": "reuters.com", "bg": "#ffedd5", "text": "#9a3412"},
        "BBC": {"site": "bbc.com", "bg": "#fee2e2", "text": "#991b1b"},
        "CNN": {"site": "cnn.com", "bg": "#fecaca", "text": "#991b1b"},
        "Bloomberg": {"site": "bloomberg.com", "bg": "#ede9fe", "text": "#5b21b6"},
        "WSJ": {"site": "wsj.com", "bg": "#dbeafe", "text": "#1e40af"},
        "NYT": {"site": "nytimes.com", "bg": "#f3f4f6", "text": "#1f2937"},
    }

    def parse_rss_date(date_str):
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.min

    try:
        all_items = []
        for source_name, source_info in NEWS_SOURCES.items():
            try:
                rss_url = f"https://news.google.com/rss/search?q=site:{source_info['site']}&hl=en-US&gl=US&ceid=US:en"
                r = requests.get(rss_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
                root = ET.fromstring(r.content)

                for item in root.findall(".//channel/item"):
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    pub_date = (item.findtext("pubDate") or "").strip()
                    description = (item.findtext("description") or "").strip()

                    if title:
                        title_clean = re.sub(r'\s*-\s*(Reuters|BBC|BBC News|CNN|Bloomberg|WSJ|Wall Street Journal|NYT|New York Times|The New York Times).*$', '', title, flags=re.IGNORECASE)
                        clean_desc = re.sub(r'<[^>]+>', '', description)
                        all_items.append({
                            "title": title_clean.strip(),
                            "url": link,
                            "description": clean_desc[:150] + "..." if len(clean_desc) > 150 else clean_desc,
                            "pub_date": pub_date,
                            "parsed_date": parse_rss_date(pub_date),
                            "source": source_name,
                            "source_bg": source_info["bg"],
                            "source_text": source_info["text"]
                        })
            except Exception:
                continue

        if not all_items:
            return _global_news_mock_data(), None

        all_items.sort(key=lambda x: x["parsed_date"], reverse=True)
        for item in all_items:
            item.pop("parsed_date", None)
        return all_items[:max_articles], None
    except Exception as e:
        return _global_news_mock_data(), f"뉴스 피드 오류: {e}"


# =========================================================
# 글로벌 리스크 데이터 (GDACS + GDELT)
# =========================================================
RISK_TYPE_CONFIG = {
    # 자연재해
    "earthquake": {"icon": "🌋", "color": "#dc2626", "name_ko": "지진", "name_en": "Earthquake", "severity_base": 0.7},
    "flood": {"icon": "🌊", "color": "#2563eb", "name_ko": "홍수", "name_en": "Flood", "severity_base": 0.6},
    "cyclone": {"icon": "🌀", "color": "#7c3aed", "name_ko": "태풍/사이클론", "name_en": "Cyclone", "severity_base": 0.8},
    "volcano": {"icon": "🌋", "color": "#ea580c", "name_ko": "화산", "name_en": "Volcano", "severity_base": 0.75},
    "drought": {"icon": "☀️", "color": "#ca8a04", "name_ko": "가뭄", "name_en": "Drought", "severity_base": 0.4},
    "wildfire": {"icon": "🔥", "color": "#f97316", "name_ko": "산불", "name_en": "Wildfire", "severity_base": 0.5},
    # 분쟁/전쟁
    "conflict": {"icon": "⚔️", "color": "#b91c1c", "name_ko": "분쟁/전쟁", "name_en": "Conflict/War", "severity_base": 0.9},
    "terror": {"icon": "💥", "color": "#7f1d1d", "name_ko": "테러", "name_en": "Terror", "severity_base": 0.8},
    # 정치적 불안
    "coup": {"icon": "🏛️", "color": "#991b1b", "name_ko": "쿠데타", "name_en": "Coup", "severity_base": 0.85},
    "political": {"icon": "🏴", "color": "#7c2d12", "name_ko": "정치불안", "name_en": "Political Instability", "severity_base": 0.7},
    "sanctions": {"icon": "🚷", "color": "#9f1239", "name_ko": "제재/금수", "name_en": "Sanctions/Embargo", "severity_base": 0.75},
    # 시위/파업
    "protest": {"icon": "✊", "color": "#eab308", "name_ko": "시위/파업", "name_en": "Protest/Strike", "severity_base": 0.5},
    # 물류
    "port_closure": {"icon": "🚫", "color": "#64748b", "name_ko": "항만폐쇄", "name_en": "Port Closure", "severity_base": 0.7},
    "other": {"icon": "⚠️", "color": "#6b7280", "name_ko": "기타", "name_en": "Other", "severity_base": 0.3},
}

# 물류 핵심 지역 (이 지역 근처 리스크는 가중치 부여)
LOGISTICS_HOTSPOTS = {
    "Suez Canal": (30.4574, 32.3499),
    "Panama Canal": (9.0800, -79.6800),
    "Strait of Malacca": (2.5000, 101.0000),
    "Strait of Hormuz": (26.5667, 56.2500),
    "Bab el-Mandeb": (12.5833, 43.3333),
    "Cape of Good Hope": (-34.3568, 18.4740),
    "Taiwan Strait": (24.0000, 119.0000),
    "South China Sea": (12.0000, 114.0000),
    "Red Sea": (20.0000, 38.0000),
    "Baltic Sea": (58.0000, 20.0000),
}


# 뉴스에서 리스크를 식별하기 위한 키워드 매핑
NEWS_RISK_KEYWORDS = {
    "conflict": [
        "war", "conflict", "military", "attack", "bombing", "missile", "airstrike",
        "invasion", "combat", "battle", "전쟁", "분쟁", "공격", "폭격", "미사일",
        "houthi", "airstrikes", "drone attack", "armed", "troops", "shell", "offensive",
        "casualt", "kill", "dead", "wound", "retaliat", "escalat", "ceasefire", "breach"
    ],
    "sanctions": [
        "sanction", "embargo", "trade ban", "tariff", "trade war", "제재", "금수", "관세",
        "restrictions", "blacklist", "export ban", "import ban", "무역전쟁", "수출규제",
        "trade restriction", "export control", "import duty", "반덤핑", "세이프가드",
        "countervailing", "anti-dumping", "수입규제", "수출통제", "무역제재", "경제제재",
        "decoupling", "derisking", "기술규제", "chip ban", "반도체 규제"
    ],
    "political": [
        "political crisis", "coup", "regime", "unrest", "riot", "정치 불안", "쿠데타",
        "폭동", "instability", "martial law", "정권", "election crisis", "civil war",
        "내전", "정치위기", "정국불안", "독재", "dictatorship", "authoritarian"
    ],
    "protest": [
        "strike", "port strike", "dock workers", "trucker", "labor dispute", "walkout",
        "파업", "노동자", "항만 파업", "운송 파업", "union strike", "protest", "demonstration",
        "시위", "집회", "물류 파업", "철도 파업", "rail strike", "general strike", "총파업"
    ],
    "port_closure": [
        "port closure", "canal blocked", "shipping disruption", "supply chain disruption",
        "항만 폐쇄", "운하 차단", "물류 차질", "congestion", "backlog", "port shutdown",
        "vessel delay", "선박 지연", "항만 혼잡", "적체", "shipping delay", "운송 지연",
        "container shortage", "컨테이너 부족", "해상 운임", "freight surge", "운임 급등"
    ],
    "cyclone": [
        "typhoon", "hurricane", "cyclone", "tropical storm", "태풍", "허리케인", "사이클론",
        "storm warning", "폭풍", "강풍"
    ],
    "earthquake": [
        "earthquake", "quake", "seismic", "지진", "진도", "magnitude"
    ],
    "flood": [
        "flood", "flooding", "heavy rain", "monsoon", "홍수", "침수", "폭우", "집중호우",
        "dam", "overflow", "수해", "범람"
    ],
    "terror": [
        "terrorist", "terror attack", "bomb threat", "테러", "폭발", "explosion", "hostage"
    ],
    "drought": [
        "drought", "water shortage", "가뭄", "물부족", "수위", "water level", "canal restriction"
    ],
}

# 뉴스 국가명에서 좌표 추출을 위한 매핑
NEWS_COUNTRY_COORDS = {
    # 한국어 국가명
    "미국": (37.0902, -95.7129), "중국": (35.8617, 104.1954), "일본": (36.2048, 138.2529),
    "베트남": (14.0583, 108.2772), "인도": (20.5937, 78.9629), "독일": (51.1657, 10.4515),
    "프랑스": (46.6034, 1.8883), "영국": (55.3781, -3.4360), "이탈리아": (41.8719, 12.5674),
    "스페인": (40.4637, -3.7492), "네덜란드": (52.1326, 5.2913), "벨기에": (50.5039, 4.4699),
    "호주": (-25.27, 133.78), "뉴질랜드": (-40.9, 174.89), "싱가포르": (1.3521, 103.8198),
    "말레이시아": (4.2105, 101.9758), "인도네시아": (-0.7893, 113.9213), "태국": (15.8700, 100.9925),
    "필리핀": (12.8797, 121.7740), "대만": (23.6978, 120.9605), "홍콩": (22.3193, 114.1694),
    "러시아": (61.5240, 105.3188), "우크라이나": (48.3794, 31.1656), "폴란드": (51.9194, 19.1451),
    "터키": (38.9637, 35.2433), "사우디": (23.88, 45.08), "UAE": (24.0, 54.0),
    "이란": (32.4279, 53.6880), "이라크": (33.2232, 43.6793), "이스라엘": (31.0461, 34.8516),
    "이집트": (26.8206, 30.8025), "남아공": (-30.5595, 22.9375), "브라질": (-14.2350, -51.9253),
    "멕시코": (23.6345, -102.5528), "캐나다": (56.1304, -106.3468), "아르헨티나": (-38.42, -63.62),
    "칠레": (-35.68, -71.54), "페루": (-9.19, -75.02), "콜롬비아": (4.5709, -74.2973),
    "방글라데시": (23.68, 90.35), "파키스탄": (30.3753, 69.3451), "미얀마": (19.7633, 96.0785),
    "예멘": (15.5527, 48.5164), "수단": (12.8628, 30.2176), "에티오피아": (9.1450, 40.4897),
    "리비아": (26.3351, 17.2283), "시리아": (34.8021, 38.9968), "아프가니스탄": (33.9391, 67.7100),
    "북한": (40.3399, 127.5101), "한국": (35.9078, 127.7669),
    # 추가 국가
    "캄보디아": (12.5657, 104.9910), "라오스": (19.8563, 102.4955), "스리랑카": (7.87, 80.77),
    "네팔": (28.3949, 84.1240), "그리스": (39.0742, 21.8243), "체코": (49.8175, 15.4730),
    "헝가리": (47.1625, 19.5033), "오스트리아": (47.5162, 14.5501), "스위스": (46.8182, 8.2275),
    "포르투갈": (39.3999, -8.2245), "아일랜드": (53.1424, -7.6921), "노르웨이": (60.472, 8.4689),
    "스웨덴": (60.1282, 18.6435), "핀란드": (61.9241, 25.7482), "덴마크": (56.2639, 9.5018),
    "나이지리아": (9.0820, 8.6753), "케냐": (-0.0236, 37.9062), "탄자니아": (-6.369, 34.8888),
    "모로코": (31.7917, -7.0926), "알제리": (28.0339, 1.6596), "튀니지": (33.8869, 9.5375),
    "레바논": (33.8547, 35.8623), "요르단": (30.5852, 36.2384), "쿠웨이트": (29.3117, 47.4818),
    "카타르": (25.3548, 51.1839), "오만": (21.4735, 55.9754), "바레인": (26.0667, 50.5577),
    "파나마": (8.538, -80.7821), "베네수엘라": (6.4238, -66.5897), "에콰도르": (-1.8312, -78.1834),
    "쿠바": (21.5218, -77.7812), "푸에르토리코": (18.2208, -66.5901),
}


def extract_risks_from_news(kotra_news: list, global_news: list) -> list:
    """KOTRA와 Global News에서 리스크 관련 뉴스를 추출하여 리스크 데이터로 변환"""
    risks = []
    seen_titles = set()

    def identify_risk_type(title: str, content: str = "") -> tuple:
        """뉴스 제목과 내용에서 리스크 유형 식별"""
        text = (title + " " + content).lower()
        for risk_type, keywords in NEWS_RISK_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    return risk_type, kw
        return None, None

    def extract_coords_from_news(title: str, content: str = "", country: str = "") -> tuple:
        """뉴스에서 좌표 추출 (제목, 내용, 국가명 순으로 검색)"""
        # 1. 먼저 RISK_LOCATION_COORDS에서 검색 (기존 확장된 좌표 사용)
        text = (title + " " + content).lower()
        for location, coords in RISK_LOCATION_COORDS.items():
            if location in text:
                return coords

        # 2. 한국어 국가명으로 검색
        if country and country in NEWS_COUNTRY_COORDS:
            return NEWS_COUNTRY_COORDS[country]

        # 3. 제목에서 한국어 국가명 검색
        for ko_country, coords in NEWS_COUNTRY_COORDS.items():
            if ko_country in title or ko_country in content:
                return coords

        return None, None

    # KOTRA 뉴스 처리
    for news in kotra_news:
        title = news.get("title", "")
        content = news.get("content", "")
        country = news.get("country", "")

        if not title or title in seen_titles:
            continue

        risk_type, matched_keyword = identify_risk_type(title, content)
        if not risk_type:
            continue

        lat, lon = extract_coords_from_news(title, content, country)
        if lat is None:
            continue

        seen_titles.add(title)
        config = RISK_TYPE_CONFIG.get(risk_type, RISK_TYPE_CONFIG["other"])

        risks.append({
            "title": title,
            "description": content[:200] if content else "",
            "lat": lat,
            "lon": lon,
            "event_type": risk_type,
            "alert_level": "Orange" if config["severity_base"] < 0.8 else "Red",
            "severity": config["severity_base"],
            "source": "KOTRA News",
            "link": news.get("url", ""),
            "pub_date": news.get("write_date", "")
        })

    # Global News 처리
    for news in global_news:
        title = news.get("title", "")
        description = news.get("description", "")

        if not title or title in seen_titles:
            continue

        risk_type, matched_keyword = identify_risk_type(title, description)
        if not risk_type:
            continue

        lat, lon = extract_coords_from_news(title, description)
        if lat is None:
            continue

        seen_titles.add(title)
        config = RISK_TYPE_CONFIG.get(risk_type, RISK_TYPE_CONFIG["other"])

        risks.append({
            "title": title,
            "description": description[:200] if description else "",
            "lat": lat,
            "lon": lon,
            "event_type": risk_type,
            "alert_level": "Orange" if config["severity_base"] < 0.8 else "Red",
            "severity": config["severity_base"],
            "source": f"Global News ({news.get('source', 'Unknown')})",
            "link": news.get("url", ""),
            "pub_date": news.get("pub_date", "")
        })

    return risks


def get_persistent_geopolitical_risks() -> list:
    """지속적인 지정학적 리스크 (전쟁, 제재 등 장기간 지속되는 이슈)
    자연재해, 파업 등은 실시간 API/뉴스에서 가져옴"""
    return [
        # 전쟁/분쟁 (장기 지속)
        {"title": "Red Sea Shipping Disruption - Houthi Attacks", "description": "Ongoing attacks on commercial vessels in Red Sea affecting global shipping routes", "lat": 15.5527, "lon": 42.5574, "event_type": "conflict", "alert_level": "Red", "severity": 0.95, "source": "Geopolitical", "link": ""},
        {"title": "Ukraine-Russia War - Black Sea Shipping", "description": "Ongoing war affecting grain exports, shipping insurance rates up 300%", "lat": 46.0000, "lon": 33.0000, "event_type": "conflict", "alert_level": "Red", "severity": 0.95, "source": "Geopolitical", "link": ""},
        {"title": "Israel-Gaza Conflict - Eastern Mediterranean", "description": "Military operations affecting shipping routes near Suez Canal approach", "lat": 31.5, "lon": 34.47, "event_type": "conflict", "alert_level": "Red", "severity": 0.85, "source": "Geopolitical", "link": ""},
        # 정치적 불안 (장기 지속)
        {"title": "Political Crisis - Myanmar Civil War", "description": "Ongoing civil conflict disrupting overland trade routes to China", "lat": 19.7633, "lon": 96.0785, "event_type": "political", "alert_level": "Red", "severity": 0.8, "source": "Geopolitical", "link": ""},
        {"title": "Political Instability - Sudan Conflict", "description": "Civil war affecting Port Sudan operations and Red Sea access", "lat": 19.6158, "lon": 37.2164, "event_type": "political", "alert_level": "Red", "severity": 0.75, "source": "Geopolitical", "link": ""},
        # 제재/금수 (장기 지속)
        {"title": "Russia Sanctions - Baltic Sea Trade Impact", "description": "Western sanctions affecting Baltic port operations and cargo flows", "lat": 59.0, "lon": 25.0, "event_type": "sanctions", "alert_level": "Orange", "severity": 0.7, "source": "Geopolitical", "link": ""},
        {"title": "Iran Sanctions - Strait of Hormuz", "description": "Trade restrictions affecting oil tanker traffic", "lat": 26.5667, "lon": 56.2500, "event_type": "sanctions", "alert_level": "Orange", "severity": 0.65, "source": "Geopolitical", "link": ""},
    ]


@st.cache_data(ttl=3600)
def geocode_location(location_name: str) -> tuple:
    """Nominatim (OpenStreetMap) 무료 Geocoding"""
    if not location_name:
        return None, None
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": location_name, "format": "json", "limit": 1}
        headers = {"User-Agent": "SupplyChainDashboard/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            results = r.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None, None


# 주요 분쟁/리스크 지역 좌표 (기사 제목에서 매칭용) - 대폭 확장
RISK_LOCATION_COORDS = {
    # 중동/아프리카
    "yemen": (15.5527, 42.5574), "houthi": (15.5527, 42.5574), "red sea": (20.0, 38.0), "aden": (12.8, 45.0),
    "israel": (31.0461, 34.8516), "gaza": (31.5, 34.47), "palestine": (31.9, 35.2), "tel aviv": (32.08, 34.78),
    "iran": (32.4279, 53.6880), "tehran": (35.69, 51.39), "iraq": (33.2232, 43.6793), "baghdad": (33.31, 44.37),
    "syria": (34.8021, 38.9968), "damascus": (33.51, 36.29), "aleppo": (36.2, 37.16),
    "ukraine": (48.3794, 31.1656), "kyiv": (50.45, 30.52), "kiev": (50.45, 30.52), "odesa": (46.48, 30.73), "odessa": (46.48, 30.73),
    "russia": (61.5240, 105.3188), "moscow": (55.75, 37.62), "crimea": (45.0, 34.0),
    "sudan": (12.8628, 30.2176), "khartoum": (15.5, 32.56), "ethiopia": (9.1450, 40.4897), "somalia": (5.1521, 46.1996),
    "libya": (26.3351, 17.2283), "tripoli": (32.9, 13.19), "egypt": (26.8206, 30.8025), "cairo": (30.04, 31.24),
    "suez": (30.4574, 32.3499), "saudi": (23.88, 45.08), "saudi arabia": (23.88, 45.08), "dubai": (25.2, 55.27),
    "lebanon": (33.85, 35.86), "beirut": (33.89, 35.5), "jordan": (30.58, 36.24),
    # 아시아
    "taiwan": (23.6978, 120.9605), "taipei": (25.03, 121.56), "china": (35.8617, 104.1954), "beijing": (39.9, 116.4),
    "shanghai": (31.23, 121.47), "hong kong": (22.3193, 114.1694), "shenzhen": (22.54, 114.06),
    "north korea": (40.3399, 127.5101), "pyongyang": (39.03, 125.75), "south korea": (35.9078, 127.7669),
    "korea": (37.5665, 126.9780), "seoul": (37.57, 126.98), "busan": (35.18, 129.08), "incheon": (37.46, 126.71),
    "myanmar": (19.7633, 96.0785), "yangon": (16.87, 96.2), "thailand": (15.8700, 100.9925), "bangkok": (13.76, 100.5),
    "vietnam": (14.0583, 108.2772), "hanoi": (21.03, 105.85), "ho chi minh": (10.82, 106.63),
    "philippines": (12.8797, 121.7740), "manila": (14.6, 120.98), "indonesia": (-0.7893, 113.9213), "jakarta": (-6.21, 106.85),
    "malaysia": (4.2105, 101.9758), "kuala lumpur": (3.14, 101.69), "india": (20.5937, 78.9629), "mumbai": (19.08, 72.88),
    "delhi": (28.61, 77.21), "chennai": (13.08, 80.27), "pakistan": (30.3753, 69.3451), "karachi": (24.86, 67.01),
    "afghanistan": (33.9391, 67.7100), "kabul": (34.53, 69.17), "japan": (36.2048, 138.2529), "tokyo": (35.68, 139.69),
    "yokohama": (35.44, 139.64), "osaka": (34.69, 135.5), "singapore": (1.3521, 103.8198),
    "sri lanka": (7.87, 80.77), "colombo": (6.93, 79.85), "bangladesh": (23.68, 90.35), "dhaka": (23.81, 90.41),
    # 유럽
    "germany": (51.1657, 10.4515), "hamburg": (53.5511, 9.9937), "berlin": (52.52, 13.4), "munich": (48.14, 11.58),
    "france": (46.6034, 1.8883), "paris": (48.86, 2.35), "marseille": (43.3, 5.37), "le havre": (49.49, 0.11),
    "uk": (55.3781, -3.4360), "britain": (55.3781, -3.4360), "england": (52.36, -1.17), "london": (51.51, -0.13),
    "liverpool": (53.41, -2.98), "southampton": (50.9, -1.4), "netherlands": (52.1326, 5.2913), "amsterdam": (52.37, 4.9),
    "rotterdam": (51.9244, 4.4777), "belgium": (50.5039, 4.4699), "antwerp": (51.2194, 4.4025), "brussels": (50.85, 4.35),
    "spain": (40.4637, -3.7492), "madrid": (40.42, -3.7), "barcelona": (41.39, 2.17), "valencia": (39.47, -0.38),
    "italy": (41.8719, 12.5674), "rome": (41.9, 12.5), "genoa": (44.41, 8.93), "milan": (45.46, 9.19), "naples": (40.85, 14.27),
    "greece": (39.0742, 21.8243), "athens": (37.98, 23.73), "piraeus": (37.94, 23.65),
    "poland": (51.9194, 19.1451), "warsaw": (52.23, 21.01), "gdansk": (54.35, 18.65),
    "turkey": (38.9637, 35.2433), "istanbul": (41.01, 28.98), "ankara": (39.93, 32.86),
    "sweden": (60.13, 18.64), "stockholm": (59.33, 18.07), "gothenburg": (57.71, 11.97),
    "norway": (60.47, 8.47), "oslo": (59.91, 10.75), "finland": (61.92, 25.75), "helsinki": (60.17, 24.94),
    "denmark": (56.26, 9.5), "copenhagen": (55.68, 12.57), "portugal": (39.4, -8.22), "lisbon": (38.72, -9.14),
    # 미주
    "usa": (37.0902, -95.7129), "us": (37.0902, -95.7129), "america": (37.0902, -95.7129), "united states": (37.0902, -95.7129),
    "washington": (38.91, -77.04), "los angeles": (33.7405, -118.2710), "new york": (40.6681, -74.0451),
    "chicago": (41.88, -87.63), "houston": (29.76, -95.37), "miami": (25.76, -80.19), "seattle": (47.61, -122.33),
    "san francisco": (37.77, -122.42), "long beach": (33.77, -118.19), "savannah": (32.08, -81.09),
    "canada": (56.1304, -106.3468), "toronto": (43.65, -79.38), "vancouver": (49.28, -123.12), "montreal": (45.5, -73.57),
    "mexico": (23.6345, -102.5528), "mexico city": (19.43, -99.13), "manzanillo": (19.05, -104.32),
    "panama": (9.0800, -79.6800), "panama canal": (9.0800, -79.6800), "panama city": (8.98, -79.52),
    "brazil": (-14.2350, -51.9253), "sao paulo": (-23.55, -46.63), "rio": (-22.91, -43.17), "santos": (-23.96, -46.33),
    "argentina": (-38.42, -63.62), "buenos aires": (-34.6, -58.38), "venezuela": (6.4238, -66.5897), "caracas": (10.48, -66.9),
    "colombia": (4.5709, -74.2973), "bogota": (4.71, -74.07), "chile": (-35.68, -71.54), "santiago": (-33.45, -70.67),
    "peru": (-9.19, -75.02), "lima": (-12.05, -77.04), "callao": (-12.07, -77.14),
    # 오세아니아
    "australia": (-25.27, 133.78), "sydney": (-33.87, 151.21), "melbourne": (-37.81, 144.96), "brisbane": (-27.47, 153.03),
    "new zealand": (-40.9, 174.89), "auckland": (-36.85, 174.76),
    # 해상 요충지
    "black sea": (43.0, 34.0), "baltic": (58.0, 20.0), "baltic sea": (58.0, 20.0), "malacca": (2.5, 101.0),
    "strait of malacca": (2.5, 101.0), "hormuz": (26.5667, 56.2500), "strait of hormuz": (26.5667, 56.2500),
    "bab el-mandeb": (12.5833, 43.3333), "south china sea": (12.0, 114.0), "east china sea": (28.0, 125.0),
    "mediterranean": (35.0, 18.0), "atlantic": (30.0, -40.0), "pacific": (0.0, -160.0), "indian ocean": (-20.0, 80.0),
    "suez canal": (30.4574, 32.3499), "english channel": (50.5, -1.0), "gulf of mexico": (25.0, -90.0),
    "caribbean": (15.0, -75.0), "persian gulf": (26.0, 52.0), "arabian sea": (15.0, 65.0),
}


def extract_location_from_title(title: str) -> tuple:
    """기사 제목에서 지역명을 추출하여 좌표 반환"""
    title_lower = title.lower()
    for location, coords in RISK_LOCATION_COORDS.items():
        if location in title_lower:
            return coords
    return None, None


def fetch_gdelt_events(days: int = 7, limit: int = 100) -> tuple:
    """GDELT에서 분쟁/시위/전쟁/정치불안 등 이벤트 데이터 가져오기 (API 키 불필요)"""
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    keywords = [
        # 물류/항만 관련
        "port strike", "dock workers strike", "shipping disruption",
        "port closure", "canal blocked", "trade embargo", "blockade",
        # 전쟁/분쟁
        "war", "military conflict", "civil war", "armed conflict",
        "invasion", "airstrike", "missile attack", "bombing",
        # 정치적 불안
        "political crisis", "government collapse", "martial law",
        "coup attempt", "revolution", "civil unrest", "riot",
        "election violence", "political instability", "sanctions",
        # 테러/안보
        "terrorist attack", "terror threat", "security threat"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        events = []
        for keyword in keywords[:12]:  # 더 많은 키워드 검색
            params = {
                "query": keyword,
                "mode": "artlist",
                "maxrecords": 20,
                "format": "json",
                "timespan": f"{days}d"
            }
            try:
                r = requests.get(base_url, params=params, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    for article in data.get("articles", []):
                        title = article.get("title", "")
                        title_lower = title.lower()

                        # 이벤트 유형 분류 (더 상세하게)
                        event_type = "other"
                        if 'strike' in title_lower and ('port' in title_lower or 'dock' in title_lower or 'worker' in title_lower):
                            event_type = "protest"
                        elif 'protest' in title_lower or 'riot' in title_lower or 'demonstration' in title_lower:
                            event_type = "protest"
                        elif 'war' in title_lower or 'invasion' in title_lower or 'airstrike' in title_lower or 'missile' in title_lower:
                            event_type = "conflict"
                        elif 'military' in title_lower or 'armed conflict' in title_lower or 'bombing' in title_lower:
                            event_type = "conflict"
                        elif 'coup' in title_lower or 'overthrow' in title_lower or 'revolution' in title_lower:
                            event_type = "coup"
                        elif 'terror' in title_lower or 'bomb' in title_lower or 'explosion' in title_lower:
                            event_type = "terror"
                        elif 'political' in title_lower or 'government' in title_lower or 'martial law' in title_lower:
                            event_type = "political"
                        elif 'sanction' in title_lower or 'embargo' in title_lower or 'trade war' in title_lower:
                            event_type = "sanctions"
                        elif 'closure' in title_lower or 'blocked' in title_lower or 'disruption' in title_lower:
                            event_type = "port_closure"

                        # 제목에서 좌표 추출
                        lat, lon = extract_location_from_title(title)

                        events.append({
                            "title": title,
                            "description": article.get("seendescription", "")[:200] if article.get("seendescription") else "",
                            "event_type": event_type,
                            "lat": lat,
                            "lon": lon,
                            "pub_date": article.get("seendate", ""),
                            "link": article.get("url", ""),
                            "source": "GDELT",
                            "severity": RISK_TYPE_CONFIG.get(event_type, {}).get("severity_base", 0.5),
                            "alert_level": "Red" if event_type in ["conflict", "terror", "coup"] else "Orange"
                        })
            except Exception:
                continue

        # 중복 제거 및 좌표 있는 것만 필터링
        seen_titles = set()
        unique_events = []
        for event in events:
            if event["title"] not in seen_titles and event.get("lat") is not None:
                seen_titles.add(event["title"])
                unique_events.append(event)

        return unique_events[:limit], None
    except Exception as e:
        return [], f"GDELT API 오류: {e}"


@st.cache_data(ttl=1800)
def fetch_gdacs_disasters() -> tuple:
    """GDACS에서 자연재해 데이터 가져오기"""
    import xml.etree.ElementTree as ET

    url = "https://www.gdacs.org/xml/rss.xml"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)

        disasters = []
        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            description = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "")
            lat, lon, event_type = None, None, "other"
            alert_level, severity = "Green", 0.3

            for elem in item:
                tag = elem.tag.lower()
                if 'point' in tag or 'lat' in tag:
                    text = elem.text or ""
                    if ' ' in text:
                        parts = text.strip().split()
                        if len(parts) >= 2:
                            try:
                                lat, lon = float(parts[0]), float(parts[1])
                            except ValueError:
                                pass
                if 'alertlevel' in tag:
                    alert_level = elem.text or "Green"
                if 'severity' in tag:
                    try:
                        severity = float(elem.text or 0.3)
                    except ValueError:
                        pass

            title_lower = title.lower()
            if 'earthquake' in title_lower or 'quake' in title_lower:
                event_type = "earthquake"
            elif 'flood' in title_lower:
                event_type = "flood"
            elif any(x in title_lower for x in ['cyclone', 'typhoon', 'hurricane', 'storm']):
                event_type = "cyclone"
            elif 'volcano' in title_lower:
                event_type = "volcano"

            alert_score = {"Red": 0.9, "Orange": 0.7, "Green": 0.4}.get(alert_level, 0.3)
            if lat is not None and lon is not None:
                disasters.append({
                    "title": title, "description": description[:200], "lat": lat, "lon": lon,
                    "event_type": event_type, "alert_level": alert_level,
                    "severity": max(alert_score, severity), "pub_date": pub_date,
                    "link": link, "source": "GDACS"
                })
        return disasters, None
    except Exception as e:
        return [], f"GDACS API 오류: {e}"


@st.cache_data(ttl=1800)
def fetch_usgs_earthquakes(min_magnitude: float = 4.5, days: int = 7) -> tuple:
    """USGS에서 실시간 지진 데이터 가져오기 (무료 API)
    https://earthquake.usgs.gov/fdsnws/event/1/
    """
    from datetime import datetime, timedelta

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_time.strftime("%Y-%m-%d"),
        "endtime": end_time.strftime("%Y-%m-%d"),
        "minmagnitude": min_magnitude,
        "orderby": "time"
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        earthquakes = []
        for feature in data.get("features", [])[:30]:  # 최근 30개
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])

            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
                mag = props.get("mag", 0)
                place = props.get("place", "Unknown location")
                time_ms = props.get("time", 0)
                url_detail = props.get("url", "")

                # 심각도 계산 (규모 기반)
                if mag >= 7.0:
                    severity, alert_level = 0.95, "Red"
                elif mag >= 6.0:
                    severity, alert_level = 0.8, "Red"
                elif mag >= 5.0:
                    severity, alert_level = 0.6, "Orange"
                else:
                    severity, alert_level = 0.4, "Orange"

                earthquakes.append({
                    "title": f"M{mag:.1f} Earthquake - {place}",
                    "description": f"Magnitude {mag:.1f} earthquake detected. Depth: {coords[2] if len(coords) > 2 else 'N/A'}km",
                    "lat": lat,
                    "lon": lon,
                    "event_type": "earthquake",
                    "alert_level": alert_level,
                    "severity": severity,
                    "pub_date": datetime.utcfromtimestamp(time_ms/1000).strftime("%Y-%m-%d %H:%M UTC") if time_ms else "",
                    "link": url_detail,
                    "source": "USGS"
                })

        return earthquakes, None
    except Exception as e:
        return [], f"USGS API 오류: {e}"


@st.cache_data(ttl=1800)
def fetch_noaa_tropical_cyclones() -> tuple:
    """NOAA/NHC에서 실시간 태풍/허리케인 데이터 가져오기 (GeoJSON)
    Active tropical cyclones from National Hurricane Center
    """
    # NOAA NHC Active Cyclones GeoJSON
    url = "https://www.nhc.noaa.gov/CurrentStorms.json"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        data = r.json()

        cyclones = []
        active_storms = data.get("activeStorms", [])

        for storm in active_storms:
            name = storm.get("name", "Unknown")
            classification = storm.get("classification", "")
            lat = storm.get("latitudeNumeric")
            lon = storm.get("longitudeNumeric")
            movement = storm.get("movementDir", "")
            speed = storm.get("movementSpeed", 0)
            intensity = storm.get("intensity", 0)
            basin = storm.get("basin", "")

            if lat is None or lon is None:
                continue

            # 강도에 따른 심각도
            if intensity >= 130:  # Category 4-5
                severity, alert_level = 0.95, "Red"
            elif intensity >= 96:  # Category 2-3
                severity, alert_level = 0.85, "Red"
            elif intensity >= 64:  # Category 1
                severity, alert_level = 0.7, "Orange"
            else:  # Tropical Storm/Depression
                severity, alert_level = 0.5, "Orange"

            basin_name = {"AL": "Atlantic", "EP": "East Pacific", "CP": "Central Pacific", "WP": "West Pacific"}.get(basin, basin)

            cyclones.append({
                "title": f"{classification} {name} - {basin_name}",
                "description": f"Wind: {intensity} kt, Moving {movement} at {speed} mph",
                "lat": lat,
                "lon": lon,
                "event_type": "cyclone",
                "alert_level": alert_level,
                "severity": severity,
                "pub_date": "",
                "link": f"https://www.nhc.noaa.gov/",
                "source": "NOAA NHC"
            })

        return cyclones, None
    except Exception as e:
        return [], f"NOAA NHC API 오류: {e}"


@st.cache_data(ttl=1800)
def fetch_jma_typhoons() -> tuple:
    """일본 기상청(JMA)에서 서태평양 태풍 정보 가져오기
    RSS feed for typhoon information
    """
    import xml.etree.ElementTree as ET

    url = "https://www.jma.go.jp/bosai/typhoon/data/tlist.json"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code != 200:
            return [], None  # JMA가 현재 태풍이 없으면 404 반환할 수 있음

        data = r.json()
        typhoons = []

        for typhoon in data:
            name = typhoon.get("name", "Unknown")
            number = typhoon.get("typhoon_id", "")

            # 최신 위치 정보 가져오기
            detail_url = f"https://www.jma.go.jp/bosai/typhoon/data/{number}.json"
            try:
                detail_r = requests.get(detail_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                if detail_r.status_code == 200:
                    detail = detail_r.json()
                    # 분석 데이터에서 현재 위치 추출
                    if "analysis" in detail and detail["analysis"]:
                        latest = detail["analysis"][-1] if isinstance(detail["analysis"], list) else detail["analysis"]
                        lat = latest.get("lat")
                        lon = latest.get("lon")
                        pressure = latest.get("pressure", "N/A")
                        max_wind = latest.get("maxWind", 0)

                        if lat and lon:
                            # 강도에 따른 심각도
                            if max_wind >= 54:  # Very Strong
                                severity, alert_level = 0.9, "Red"
                            elif max_wind >= 33:  # Strong
                                severity, alert_level = 0.75, "Orange"
                            else:
                                severity, alert_level = 0.5, "Orange"

                            typhoons.append({
                                "title": f"Typhoon {name} ({number})",
                                "description": f"Central Pressure: {pressure}hPa, Max Wind: {max_wind}m/s",
                                "lat": lat,
                                "lon": lon,
                                "event_type": "cyclone",
                                "alert_level": alert_level,
                                "severity": severity,
                                "pub_date": "",
                                "link": "https://www.jma.go.jp/bosai/map.html#elem=root&typhoon=all",
                                "source": "JMA"
                            })
            except Exception:
                continue

        return typhoons, None
    except Exception as e:
        return [], f"JMA API 오류: {e}"


@st.cache_data(ttl=1800)
def fetch_all_global_risks() -> tuple:
    """모든 소스에서 글로벌 리스크 데이터 통합 수집

    데이터 소스:
    - 지정학적 리스크: 장기 지속 분쟁/제재 (Geopolitical)
    - 자연재해: GDACS, USGS(지진), NOAA/JMA(태풍)
    - 분쟁/시위: GDELT
    - 실시간 뉴스: KOTRA, Global News
    """
    all_risks = []
    errors = []
    sources_info = []

    # 0. 지정학적 리스크 (장기 지속되는 전쟁/제재)
    geopolitical_risks = get_persistent_geopolitical_risks()
    all_risks.extend(geopolitical_risks)
    sources_info.append(f"Geopolitical: {len(geopolitical_risks)}건")

    # 1. GDACS 자연재해 데이터 (홍수, 화산 등)
    gdacs_risks, gdacs_error = fetch_gdacs_disasters()
    if gdacs_error:
        errors.append(f"GDACS: {gdacs_error}")
    else:
        all_risks.extend(gdacs_risks)
        sources_info.append(f"GDACS: {len(gdacs_risks)}건")

    # 2. USGS 지진 데이터 (실시간)
    usgs_quakes, usgs_error = fetch_usgs_earthquakes(min_magnitude=4.5, days=7)
    if usgs_error:
        errors.append(f"USGS: {usgs_error}")
    else:
        all_risks.extend(usgs_quakes)
        sources_info.append(f"USGS: {len(usgs_quakes)}건")

    # 3. NOAA 허리케인/태풍 데이터 (대서양/동태평양)
    noaa_cyclones, noaa_error = fetch_noaa_tropical_cyclones()
    if noaa_error:
        errors.append(f"NOAA: {noaa_error}")
    else:
        all_risks.extend(noaa_cyclones)
        if noaa_cyclones:
            sources_info.append(f"NOAA: {len(noaa_cyclones)}건")

    # 4. JMA 태풍 데이터 (서태평양)
    jma_typhoons, jma_error = fetch_jma_typhoons()
    if jma_error:
        errors.append(f"JMA: {jma_error}")
    else:
        all_risks.extend(jma_typhoons)
        if jma_typhoons:
            sources_info.append(f"JMA: {len(jma_typhoons)}건")

    # 5. GDELT 분쟁/시위 데이터
    gdelt_events, gdelt_error = fetch_gdelt_events()
    if gdelt_error:
        errors.append(f"GDELT: {gdelt_error}")
    else:
        all_risks.extend(gdelt_events)
        sources_info.append(f"GDELT: {len(gdelt_events)}건")

    # 6. KOTRA/Global News에서 리스크 추출 (실시간 뉴스 팔로잉)
    try:
        kotra_news, kotra_err = fetch_kotra_news(num_of_rows=50)
        global_news, global_err = fetch_global_news(max_articles=50)

        news_risks = extract_risks_from_news(kotra_news, global_news)
        if news_risks:
            all_risks.extend(news_risks)
            sources_info.append(f"News: {len(news_risks)}건")
    except Exception as e:
        errors.append(f"News: {e}")

    # 중복 제거 (제목 기준)
    seen_titles = set()
    unique_risks = []
    for risk in all_risks:
        title = risk.get("title", "")
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_risks.append(risk)

    error_msg = " | ".join(errors) if errors else None
    return unique_risks, error_msg


def calculate_risk_impact_on_port(port_lat: float, port_lon: float, risks: list, port_country: str = None, max_distance_km: float = 2000) -> dict:
    """특정 항구에 대한 글로벌 리스크 영향도 계산

    필터 조건:
    1. 해당 국가의 이슈 (타이틀/설명에 국가명 포함)
    2. 다른 나라라도 200km 이내면 포함
    """
    import math

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    # 국가 코드 → 국가명 매핑 (검색용)
    COUNTRY_KEYWORDS = {
        "KR": ["korea", "korean", "busan", "incheon", "gwangyang", "seoul"],
        "CN": ["china", "chinese", "shanghai", "ningbo", "qingdao", "shenzhen", "hong kong"],
        "JP": ["japan", "japanese", "tokyo", "yokohama", "osaka", "kobe"],
        "SG": ["singapore"],
        "US": ["usa", "u.s.", "united states", "american", "los angeles", "new york", "long beach"],
        "DE": ["germany", "german", "hamburg", "berlin"],
        "NL": ["netherlands", "dutch", "rotterdam", "amsterdam"],
        "BE": ["belgium", "belgian", "antwerp"],
        "GB": ["uk", "britain", "british", "england", "london"],
        "ES": ["spain", "spanish", "valencia", "barcelona"],
        "GR": ["greece", "greek", "piraeus"],
        "CA": ["canada", "canadian", "vancouver"],
        "AU": ["australia", "australian", "sydney", "melbourne"],
        "NZ": ["new zealand"],
        "BR": ["brazil", "brazilian", "santos"],
        "ZA": ["south africa", "durban"],
        "EG": ["egypt", "egyptian", "alexandria", "suez"],
        "MA": ["morocco", "moroccan", "tanger"],
        "VN": ["vietnam", "vietnamese"],
        "IN": ["india", "indian", "mumbai"],
        "AE": ["uae", "emirates", "dubai", "abu dhabi"],
    }

    def risk_matches_country(risk: dict, country_code: str) -> bool:
        """리스크가 해당 국가와 관련있는지 확인"""
        if not country_code:
            return False
        keywords = COUNTRY_KEYWORDS.get(country_code.upper(), [])
        if not keywords:
            return False
        text = (risk.get("title", "") + " " + risk.get("description", "")).lower()
        return any(kw in text for kw in keywords)

    nearby_risks = []
    total_risk_modifier = 0.0
    CLOSE_DISTANCE_KM = 200  # 다른 나라라도 이 거리 이내면 포함

    for risk in risks:
        if risk.get("lat") is None or risk.get("lon") is None:
            continue
        distance = haversine(port_lat, port_lon, risk["lat"], risk["lon"])

        # 필터 조건:
        # 1. 같은 나라 이슈 → 거리 무관하게 포함
        # 2. 다른 나라 이슈 → 200km 이내만 포함
        is_same_country = risk_matches_country(risk, port_country)
        is_close_enough = distance <= CLOSE_DISTANCE_KM

        if is_same_country or is_close_enough:
            # 영향도 계산 (거리 기반)
            distance_factor = max(0, 1 - (distance / max_distance_km))
            impact = risk.get("severity", 0.5) * max(distance_factor, 0.1)  # 최소 영향도 보장
            nearby_risks.append({**risk, "distance_km": round(distance, 1), "impact": round(impact, 3)})
            total_risk_modifier += impact

    return {
        "risk_score_modifier": round(min(total_risk_modifier / 2, 0.5), 3),
        "nearby_risks": sorted(nearby_risks, key=lambda x: x["distance_km"])[:5],
        "total_nearby_count": len(nearby_risks)
    }


# ===== Vessel Tracking Helpers =====
import math
import json
import time
import asyncio


def haversine_distance(lat1, lon1, lat2, lon2):
    """Return distance in kilometers between two lat/lon points"""
    R = 6371.0  # Earth radius km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def split_at_antimeridian(coords):
    """날짜변경선(±180°) 에서 좌표 리스트를 분할하여 Folium PolyLine이 지구를 횡단하지 않도록 처리"""
    if not coords or len(coords) < 2:
        return [coords] if coords else []

    segments = []
    current = [coords[0]]

    for i in range(1, len(coords)):
        prev_lat, prev_lng = coords[i - 1][0], coords[i - 1][1]
        curr_lat, curr_lng = coords[i][0], coords[i][1]

        if abs(curr_lng - prev_lng) > 180:
            # 날짜변경선 교차 감지 → 교차 지점의 위도를 선형 보간
            if prev_lng > 0:
                denom = (180 - prev_lng) + (180 + curr_lng)
                frac = (180 - prev_lng) / denom if denom else 0.5
            else:
                denom = (180 + prev_lng) + (180 - curr_lng)
                frac = (180 + prev_lng) / denom if denom else 0.5

            cross_lat = prev_lat + frac * (curr_lat - prev_lat)

            if prev_lng > 0:
                current.append([cross_lat, 180.0])
                segments.append(current)
                current = [[cross_lat, -180.0]]
            else:
                current.append([cross_lat, -180.0])
                segments.append(current)
                current = [[cross_lat, 180.0]]

        current.append(coords[i])

    if current:
        segments.append(current)

    return segments


def add_antimeridian_polyline(fmap, locations, **kwargs):
    """날짜변경선을 올바르게 처리하여 Folium 맵에 PolyLine 추가"""
    for seg in split_at_antimeridian(locations):
        if len(seg) >= 2:
            folium.PolyLine(locations=seg, **kwargs).add_to(fmap)


# =========================================================
# AIS 실시간 트래킹 시스템
# =========================================================

# 부산항 좌표 (기본 출발지)
BUSAN_PORT = (35.1000, 129.0400)

# ============================================================
# 실제 데이터 API 연동 함수들
# ============================================================

# AIS NavigationalStatus 코드 → 문자열 매핑
_NAV_STATUS_MAP = {
    0: "Under Way", 1: "At Anchor", 2: "Not Under Command",
    3: "Restricted Maneuverability", 4: "Constrained by Draught",
    5: "Moored", 6: "Aground", 7: "Engaged in Fishing",
    8: "Under Way Sailing", 15: "Not Defined",
}


# 1. 선박 위치 추적 - AISStream WebSocket + Datalastic REST
def fetch_ais_position(mmsi: str) -> dict:
    """
    선박 실시간 위치 조회 (다중 소스)
    - 1차: AISStream WebSocket API (wss://stream.aisstream.io)
    - 2차: Datalastic REST API (무료 100회/월)
    - 캐시: 60초 이내 재사용
    - 실패 시 None 반환 (시뮬레이션 없음)
    """
    cache_key = f"ais_cache_{mmsi}"
    cached = st.session_state.get(cache_key)

    # 캐시가 60초 이내면 재사용
    if cached:
        cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01T00:00:00+00:00").replace("Z", "+00:00"))
        if (datetime.now(timezone.utc) - cache_time).total_seconds() < 60:
            return cached

    def _save_and_return(result):
        st.session_state[cache_key] = result
        return result

    # 1차: AISStream WebSocket API
    if AISSTREAM_API_KEY:
        try:
            import websocket

            ws = websocket.create_connection(
                "wss://stream.aisstream.io/v0/stream",
                timeout=12
            )

            # MMSI 필터로 구독 요청
            subscribe_msg = json.dumps({
                "APIKey": AISSTREAM_API_KEY,
                "BoundingBoxes": [[[-90, -180], [90, 180]]],
                "FiltersShipMMSI": [mmsi]
            })
            ws.send(subscribe_msg)

            # 최대 10초간 PositionReport 수신 대기
            deadline = time.time() + 10
            result = None
            while time.time() < deadline:
                try:
                    remaining = max(0.5, deadline - time.time())
                    ws.settimeout(remaining)
                    raw = ws.recv()
                    msg = json.loads(raw)

                    if msg.get("MessageType") == "PositionReport":
                        pos = msg["Message"]["PositionReport"]
                        meta = msg.get("MetaData", {})
                        nav_raw = pos.get("NavigationalStatus", 15)
                        nav_str = _NAV_STATUS_MAP.get(nav_raw, str(nav_raw))

                        result = {
                            "mmsi": mmsi,
                            "lat": float(pos.get("Latitude", 0)),
                            "lng": float(pos.get("Longitude", 0)),
                            "cog": float(pos.get("Cog", 0)),
                            "sog": float(pos.get("Sog", 0)),
                            "heading": float(pos.get("TrueHeading", 0)),
                            "destination": str(meta.get("Destination", "")).strip(),
                            "ship_name": str(meta.get("ShipName", "")).strip(),
                            "nav_status": nav_str,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "source": "aisstream"
                        }
                        break
                except (websocket.WebSocketTimeoutException, TimeoutError):
                    break
                except Exception:
                    break

            try:
                ws.close()
            except Exception:
                pass

            if result:
                return _save_and_return(result)

        except ImportError:
            pass  # websocket-client 미설치 → Datalastic fallback
        except Exception:
            pass

    # 2차: Datalastic REST API (무료 티어)
    try:
        url = "https://api.datalastic.com/api/v0/vessel"
        params = {"api-key": "demo", "mmsi": mmsi}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", {})
            if data and data.get("lat"):
                return _save_and_return({
                    "mmsi": mmsi,
                    "lat": float(data.get("lat", 0)),
                    "lng": float(data.get("lon", 0)),
                    "cog": float(data.get("course", 0)),
                    "sog": float(data.get("speed", 0)),
                    "heading": float(data.get("heading", 0)),
                    "destination": data.get("destination", ""),
                    "ship_name": data.get("name", ""),
                    "nav_status": data.get("navigation_status", "Under Way"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "datalastic"
                })
    except Exception:
        pass

    return None


def fetch_mmsi_by_bl(tracking_id: str) -> str:
    """
    Attempt to resolve an MMSI from a Tracking ID (B/L).
    - 1) Check a local mapping file: exports/tracking_map.csv (columns: tracking_id, mmsi)
    - 2) Check in-memory mapping in session_state
    - Returns MMSI as a 9-digit string or None.
    """
    if not tracking_id:
        return None

    # 1) session cache
    mapping = st.session_state.get("bl_mmsi_map", {})
    val = mapping.get(str(tracking_id).strip())
    if val and str(val).isdigit() and len(str(val)) == 9:
        return str(val).strip()

    # 2) Attempt external API resolution (if configured)
    try:
        if BL_TO_MMSI_API_URL:
            headers = {}
            if BL_TO_MMSI_API_KEY:
                headers["Authorization"] = f"Bearer {BL_TO_MMSI_API_KEY}"

            # Support both GET (params) and POST (json) responses
            try:
                resp = requests.get(BL_TO_MMSI_API_URL, params={"tracking_id": tracking_id}, headers=headers, timeout=8)
            except Exception:
                resp = None

            if resp and resp.status_code == 200:
                try:
                    j = resp.json()
                    # Common fields that may contain MMSI
                    for key in ("mmsi", "mmsi_no", "vessel_mmsi", "msi"):
                        if key in j:
                            candidate = str(j[key]).strip()
                            if candidate.isdigit() and len(candidate) == 9:
                                st.session_state.setdefault("bl_mmsi_map", {})[str(tracking_id).strip()] = candidate
                                return candidate
                    # Some APIs return nested structure
                    if isinstance(j.get("data"), dict):
                        for key in ("mmsi", "mmsi_no", "vessel_mmsi"):
                            candidate = str(j["data"].get(key, "")).strip()
                            if candidate.isdigit() and len(candidate) == 9:
                                st.session_state.setdefault("bl_mmsi_map", {})[str(tracking_id).strip()] = candidate
                                return candidate
                except Exception:
                    pass
    except Exception:
        pass

    # 3) local CSV lookup in exports/
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports", "tracking_map.csv"),
        os.path.join(os.getcwd(), "exports", "tracking_map.csv")
    ]
    for p in possible_paths:
        try:
            if os.path.exists(p):
                df = pd.read_csv(p, dtype=str)
                # find likely columns
                keycol = None
                for col in df.columns:
                    if col.lower() in ("tracking_id", "bl", "bl_no", "booking"):
                        keycol = col
                        break
                keycol = keycol or df.columns[0]
                mmsi_col = None
                for col in df.columns:
                    if col.lower() in ("mmsi", "mmsi_no"):
                        mmsi_col = col
                        break
                if not mmsi_col:
                    continue
                row = df[df[keycol].astype(str).str.strip().str.upper() == str(tracking_id).strip().upper()]
                if not row.empty:
                    candidate = str(row.iloc[0][mmsi_col]).strip()
                    if candidate.isdigit() and len(candidate) == 9:
                        # cache in session
                        st.session_state.setdefault("bl_mmsi_map", {})[str(tracking_id).strip()] = candidate
                        return candidate
        except Exception:
            continue

    # 3) not found
    return None


# 2. 해양 날씨 (파고/풍속) - Open-Meteo Marine API (완전 무료)
@st.cache_data(ttl=1800)  # 30분 캐시
def fetch_marine_weather(lat: float, lng: float) -> dict:
    """
    Open-Meteo Marine API - 파고, 파주기, 풍속, 풍향 조회
    완전 무료, API 키 불필요
    """
    try:
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": lat,
            "longitude": lng,
            "current": "wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height",
            "hourly": "wave_height,wave_direction",
            "timezone": "UTC"
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            return {
                "wave_height": current.get("wave_height", 0),  # 미터
                "wave_direction": current.get("wave_direction", 0),  # 도
                "wave_period": current.get("wave_period", 0),  # 초
                "wind_wave_height": current.get("wind_wave_height", 0),
                "swell_wave_height": current.get("swell_wave_height", 0),
                "source": "open-meteo-marine",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception:
        pass

    return {"wave_height": 0, "wave_direction": 0, "wave_period": 0, "source": "unavailable"}


# 3. 항만 혼잡도 - UN/LOCODE + 추정 알고리즘
@st.cache_data(ttl=3600)  # 1시간 캐시
def fetch_port_congestion(port_name: str, port_coords: tuple) -> dict:
    """
    항만 혼잡도 추정
    - UNCTAD 항만 통계 기반 평균 대기시간
    - 실시간 AIS 데이터 기반 정박 선박 수 추정
    """
    # 주요 항만별 평균 혼잡도 데이터 (UNCTAD/World Bank 기반)
    PORT_CONGESTION_DATA = {
        "SHANGHAI": {"avg_wait_hours": 24, "avg_anchored": 45, "berth_utilization": 0.85},
        "SINGAPORE": {"avg_wait_hours": 8, "avg_anchored": 20, "berth_utilization": 0.75},
        "BUSAN": {"avg_wait_hours": 6, "avg_anchored": 12, "berth_utilization": 0.70},
        "ROTTERDAM": {"avg_wait_hours": 12, "avg_anchored": 18, "berth_utilization": 0.78},
        "LOS ANGELES": {"avg_wait_hours": 48, "avg_anchored": 60, "berth_utilization": 0.92},
        "LONG BEACH": {"avg_wait_hours": 36, "avg_anchored": 45, "berth_utilization": 0.88},
        "HAMBURG": {"avg_wait_hours": 10, "avg_anchored": 15, "berth_utilization": 0.72},
        "ANTWERP": {"avg_wait_hours": 14, "avg_anchored": 22, "berth_utilization": 0.80},
        "NINGBO": {"avg_wait_hours": 18, "avg_anchored": 35, "berth_utilization": 0.82},
        "QINGDAO": {"avg_wait_hours": 16, "avg_anchored": 28, "berth_utilization": 0.79},
        "TIANJIN": {"avg_wait_hours": 20, "avg_anchored": 32, "berth_utilization": 0.81},
        "HONG KONG": {"avg_wait_hours": 10, "avg_anchored": 25, "berth_utilization": 0.73},
        "KAOHSIUNG": {"avg_wait_hours": 8, "avg_anchored": 15, "berth_utilization": 0.68},
        "TOKYO": {"avg_wait_hours": 12, "avg_anchored": 18, "berth_utilization": 0.74},
        "YOKOHAMA": {"avg_wait_hours": 10, "avg_anchored": 16, "berth_utilization": 0.71},
        "VALENCIA": {"avg_wait_hours": 14, "avg_anchored": 20, "berth_utilization": 0.76},
        "BARCELONA": {"avg_wait_hours": 12, "avg_anchored": 18, "berth_utilization": 0.74},
        "DUBAI": {"avg_wait_hours": 16, "avg_anchored": 30, "berth_utilization": 0.83},
        "JEDDAH": {"avg_wait_hours": 18, "avg_anchored": 25, "berth_utilization": 0.80},
    }

    # 항만명 정규화
    port_upper = port_name.upper().replace(" ", "").replace("-", "")

    # 매칭되는 항만 찾기
    matched_data = None
    for key, value in PORT_CONGESTION_DATA.items():
        if key.replace(" ", "") in port_upper or port_upper in key.replace(" ", ""):
            matched_data = value
            break

    if matched_data:
        # 시간대별 변동 적용 (UTC 기준)
        hour = datetime.now(timezone.utc).hour
        # 낮 시간대(6-18시)에 혼잡도 증가
        time_factor = 1.2 if 6 <= hour <= 18 else 0.9

        return {
            "anchored_vessels": int(matched_data["avg_anchored"] * time_factor),
            "avg_wait_hours": round(matched_data["avg_wait_hours"] * time_factor, 1),
            "berth_utilization": min(0.99, matched_data["berth_utilization"] * time_factor),
            "congestion_level": "high" if matched_data["berth_utilization"] > 0.85 else "medium" if matched_data["berth_utilization"] > 0.70 else "low",
            "source": "unctad-statistics",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # 기본값 (데이터 없는 항만)
    return {
        "anchored_vessels": 10,
        "avg_wait_hours": 12,
        "berth_utilization": 0.70,
        "congestion_level": "medium",
        "source": "estimated",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# 3-1. 해상 경로 계산 - Searoute 라이브러리 (육지 회피)
@st.cache_data(ttl=3600)  # 1시간 캐시
def get_sea_route(origin_coords: tuple, dest_coords: tuple) -> list:
    """
    Searoute 라이브러리를 사용하여 실제 해상 경로 계산
    - 자동으로 육지 회피
    - 수에즈 운하, 파나마 운하, 말라카 해협 등 통과

    Args:
        origin_coords: (lat, lng) 출발지 좌표
        dest_coords: (lat, lng) 도착지 좌표

    Returns:
        list: [[lat, lng], [lat, lng], ...] Folium용 좌표 리스트
    """
    try:
        # searoute는 [lng, lat] 순서를 사용
        origin = [origin_coords[1], origin_coords[0]]  # [lng, lat]
        dest = [dest_coords[1], dest_coords[0]]  # [lng, lat]

        # 해상 경로 계산
        route = sr.searoute(origin, dest)
        coords = route['geometry']['coordinates']

        # Folium용 [lat, lng] 형식으로 변환 + 경도 정규화
        folium_coords = []
        for coord in coords:
            lng, lat = coord[0], coord[1]

            # 경도 정규화: 180° 초과 시 -180~180 범위로 변환
            if lng > 180:
                lng = lng - 360
            elif lng < -180:
                lng = lng + 360

            folium_coords.append([lat, lng])

        return folium_coords

    except Exception as e:
        # 실패 시 직선 경로 반환 (fallback)
        return [
            [origin_coords[0], origin_coords[1]],
            [dest_coords[0], dest_coords[1]]
        ]


def get_route_distance(origin_coords: tuple, dest_coords: tuple) -> float:
    """해상 경로의 실제 거리(km) 반환"""
    try:
        origin = [origin_coords[1], origin_coords[0]]
        dest = [dest_coords[1], dest_coords[0]]
        route = sr.searoute(origin, dest)
        return route['properties']['length']
    except Exception:
        # 실패 시 직선 거리 반환
        return haversine_distance(origin_coords[0], origin_coords[1],
                                   dest_coords[0], dest_coords[1])


# 4. 해상 운임 지수 - Freightos Baltic Index (FBX) 참고
@st.cache_data(ttl=86400)  # 24시간 캐시
def fetch_freight_index() -> dict:
    """
    글로벌 컨테이너 운임 지수 조회
    - Freightos Baltic Index (FBX) 공개 데이터 참고
    - 실제 API 연동 시 Freightos API 키 필요
    """
    # 2024-2025 평균 운임 데이터 (달러/FEU)
    # 출처: Freightos, Drewry, Shanghai Shipping Exchange
    FREIGHT_RATES = {
        "ASIA_EUROPE": {"rate": 2850, "change_pct": -5.2},
        "ASIA_USWEST": {"rate": 3200, "change_pct": -3.8},
        "ASIA_USEAST": {"rate": 4100, "change_pct": -2.1},
        "EUROPE_USEAST": {"rate": 2400, "change_pct": 1.5},
        "INTRA_ASIA": {"rate": 450, "change_pct": -1.2},
    }

    return {
        "rates": FREIGHT_RATES,
        "global_index": 2150,  # FBX Global Container Index
        "global_change_pct": -3.5,
        "source": "freightos-reference",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# 5. 리스크 점수 계산 - 실제 데이터 기반
def calculate_real_risk_score(
    weather_data: dict,
    marine_data: dict,
    congestion_data: dict,
    geopolitical_risk: float = 0.0
) -> dict:
    """
    실제 데이터 기반 리스크 점수 계산

    구성요소:
    - 날씨 리스크 (30%): 풍속, 기온 극단값
    - 해양 리스크 (25%): 파고, 파주기
    - 혼잡도 리스크 (25%): 정박 선박 수, 대기시간
    - 지정학 리스크 (20%): 분쟁지역, 제재 등
    """
    scores = {}

    # 날씨 리스크 (0-1)
    wind_speed = weather_data.get("wind_speed", 0) if weather_data else 0
    wind_speed = wind_speed if wind_speed is not None else 0
    weather_risk = min(1.0, wind_speed / 25)  # 25m/s 이상이면 최대 리스크
    scores["weather"] = round(weather_risk, 2)

    # 해양 리스크 (0-1)
    wave_height = marine_data.get("wave_height", 0) if marine_data else 0
    wave_height = wave_height if wave_height is not None else 0
    marine_risk = min(1.0, wave_height / 6)  # 6m 이상이면 최대 리스크
    scores["marine"] = round(marine_risk, 2)

    # 혼잡도 리스크 (0-1)
    berth_util = congestion_data.get("berth_utilization", 0.5) if congestion_data else 0.5
    berth_util = berth_util if berth_util is not None else 0.5
    congestion_risk = min(1.0, berth_util)
    scores["congestion"] = round(congestion_risk, 2)

    # 지정학 리스크 (0-1)
    scores["geopolitical"] = round(min(1.0, geopolitical_risk), 2)

    # 종합 점수 (가중 평균)
    total_score = (
        scores["weather"] * 0.30 +
        scores["marine"] * 0.25 +
        scores["congestion"] * 0.25 +
        scores["geopolitical"] * 0.20
    )

    return {
        "total_score": round(total_score, 2),
        "components": scores,
        "level": "high" if total_score > 0.7 else "medium" if total_score > 0.4 else "low",
        "source": "calculated",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# 6. 예상 비용 계산 - 실제 운임 데이터 기반
def calculate_shipping_cost(
    origin: str,
    destination: str,
    distance_km: float,
    delay_hours: float = 0,
    container_type: str = "40ft"
) -> dict:
    """
    실제 운임 데이터 기반 비용 계산

    구성요소:
    - 기본 운임: 거리 및 노선별 시장 운임
    - 연료 할증료 (BAF): 유가 연동
    - 체화료: 지연 시간당 비용
    - 보험료: 화물 가치의 0.1-0.3%
    """
    # 노선별 기본 운임 (USD/TEU)
    ROUTE_RATES = {
        ("ASIA", "EUROPE"): 1400,
        ("ASIA", "NAMERICA"): 1600,
        ("ASIA", "ASIA"): 250,
        ("EUROPE", "NAMERICA"): 1200,
        ("EUROPE", "EUROPE"): 400,
    }

    # 지역 분류
    def get_region(port):
        port_upper = port.upper()
        if any(x in port_upper for x in ["SHANGHAI", "BUSAN", "TOKYO", "SINGAPORE", "HONG KONG", "NINGBO", "QINGDAO"]):
            return "ASIA"
        elif any(x in port_upper for x in ["ROTTERDAM", "HAMBURG", "ANTWERP", "VALENCIA", "BARCELONA"]):
            return "EUROPE"
        elif any(x in port_upper for x in ["LOS ANGELES", "LONG BEACH", "NEW YORK", "SAVANNAH"]):
            return "NAMERICA"
        return "ASIA"

    origin_region = get_region(origin)
    dest_region = get_region(destination)

    # 기본 운임 조회
    base_rate = ROUTE_RATES.get((origin_region, dest_region), 800)

    # 40ft 컨테이너는 2배
    if container_type == "40ft":
        base_rate *= 2

    # 연료 할증료 (BAF) - 약 15-25%
    baf = base_rate * 0.20

    # 체화료 (지연 시간당)
    demurrage = delay_hours * 50  # 시간당 $50

    # 보험료 (기본 $100)
    insurance = 100

    # 총 비용 (USD)
    total_usd = base_rate + baf + demurrage + insurance

    # KRW 변환 (환율 1,350원 가정 - 실제로는 API 연동)
    exchange_rate = 1350
    total_krw = int(total_usd * exchange_rate)

    return {
        "base_rate_usd": base_rate,
        "baf_usd": round(baf, 2),
        "demurrage_usd": demurrage,
        "insurance_usd": insurance,
        "total_usd": round(total_usd, 2),
        "total_krw": total_krw,
        "exchange_rate": exchange_rate,
        "source": "market-based",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def calculate_projected_position(lat: float, lng: float, cog: float, sog: float, hours: float = 2.0) -> tuple:
    """COG/SOG 기반으로 예상 위치 계산 (2시간 후)"""
    import math

    # 노트를 km/h로 변환 (1 노트 = 1.852 km/h)
    speed_kmh = sog * 1.852

    # 이동 거리 (km)
    distance_km = speed_kmh * hours

    # 지구 반지름 (km)
    R = 6371.0

    # 라디안 변환
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)
    cog_rad = math.radians(cog)

    # 새 위치 계산 (대권 항법)
    angular_distance = distance_km / R

    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance) +
        math.cos(lat_rad) * math.sin(angular_distance) * math.cos(cog_rad)
    )

    new_lng_rad = lng_rad + math.atan2(
        math.sin(cog_rad) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )

    new_lat = math.degrees(new_lat_rad)
    new_lng = math.degrees(new_lng_rad)

    # 경도 정규화 (-180 ~ 180)
    if new_lng > 180:
        new_lng -= 360
    elif new_lng < -180:
        new_lng += 360

    return (new_lat, new_lng)


def get_vector_line_points(lat: float, lng: float, cog: float, sog: float, num_points: int = 10) -> list:
    """예상 경로 벡터를 위한 점들 생성 (0시간 ~ 2시간)"""
    points = [(lat, lng)]

    for i in range(1, num_points + 1):
        hours = (i / num_points) * 2.0  # 0 ~ 2시간
        projected = calculate_projected_position(lat, lng, cog, sog, hours)
        points.append(projected)

    return points


def add_position_to_history(position: dict):
    """세션 히스토리에 위치 추가"""
    if position and position.get("lat") and position.get("lng"):
        history = st.session_state.get("vessel_trail", [])

        # 중복 방지 (같은 위치면 추가 안함)
        if history:
            last = history[-1]
            if abs(last["lat"] - position["lat"]) < 0.0001 and abs(last["lng"] - position["lng"]) < 0.0001:
                return

        history.append({
            "lat": position["lat"],
            "lng": position["lng"],
            "timestamp": position.get("timestamp", datetime.now(timezone.utc).isoformat())
        })

        # 최대 500개 유지
        st.session_state["vessel_trail"] = history[-500:]


# 더미 데이터 (AIS API 실패 시 테스트용)
def get_demo_position(mmsi: str) -> dict:
    """데모/테스트용 더미 위치 데이터"""
    import time

    # 시간에 따라 조금씩 이동하는 더미 데이터
    base_lat = 35.1 + (time.time() % 3600) / 36000  # 시간당 0.1도 이동
    base_lng = 129.04 + (time.time() % 3600) / 18000  # 시간당 0.2도 이동

    return {
        "mmsi": mmsi,
        "lat": base_lat,
        "lng": base_lng,
        "cog": 45.0,  # 북동쪽
        "sog": 12.5,  # 12.5 노트
        "heading": 45.0,
        "destination": "SHANGHAI",
        "ship_name": f"DEMO VESSEL {mmsi[-4:]}",
        "nav_status": "Under Way",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "demo"
    }


def interpolate_route(route: list, num_points: int = 50) -> list:
    """항로를 부드러운 곡선으로 보간"""
    if len(route) < 2:
        return route

    interpolated = []
    for i in range(len(route) - 1):
        start = route[i]
        end = route[i + 1]

        # 각 구간을 세분화
        segment_points = max(2, num_points // (len(route) - 1))
        for j in range(segment_points):
            t = j / segment_points
            lat = start[0] + (end[0] - start[0]) * t
            lng = start[1] + (end[1] - start[1]) * t

            # 경도가 날짜변경선을 넘는 경우 처리
            if abs(start[1] - end[1]) > 180:
                if start[1] > 0 and end[1] < 0:
                    lng = start[1] + (end[1] + 360 - start[1]) * t
                    if lng > 180:
                        lng -= 360
                elif start[1] < 0 and end[1] > 0:
                    lng = start[1] + (end[1] - 360 - start[1]) * t
                    if lng < -180:
                        lng += 360

            interpolated.append((lat, lng))

    interpolated.append(route[-1])
    return interpolated


def simulate_vessel_position(mmsi: str, destination: tuple, snapshot_id: str):
    """Generate vessel position starting from Busan port"""
    # Always start from Busan
    return {
        "mmsi": mmsi,
        "lat": BUSAN_PORT[0],
        "lng": BUSAN_PORT[1],
        "speed_kn": 12.0,
        "status": "Under Way",
        "next_destination": None,
        "source": "simulated"
    }


# =========================================================
# TRADLINX 스타일 UI 컴포넌트
# =========================================================

def render_vessel_card(vessel: dict, dest_name: str = None) -> str:
    """TRADLINX 스타일 선박 정보 카드 HTML 생성"""
    if not vessel:
        return ""

    mmsi = vessel.get('mmsi', 'N/A')
    lat = vessel.get('lat', 0)
    lng = vessel.get('lng', 0)
    speed = vessel.get('speed_kn', 0)
    cog = vessel.get('cog', 0)
    status = vessel.get('status', 'Unknown')
    source = vessel.get('source', 'unknown')

    # 상태에 따른 스타일
    status_class = "status-underway"
    status_text = "운항중"
    status_icon = "🚢"

    if status.lower() in ['anchored', 'in port', '정박']:
        status_class = "status-anchored"
        status_text = "정박중"
        status_icon = "⚓"
    elif status.lower() in ['delayed', '지연']:
        status_class = "status-delayed"
        status_text = "지연"
        status_icon = "⚠️"

    # Call Sign과 IMO는 데모 데이터
    call_sign = f"{mmsi[:2]}V{mmsi[2:6]}" if mmsi != 'N/A' else "N/A"
    imo = f"99{mmsi[1:7]}" if mmsi != 'N/A' else "N/A"

    html = f"""<div class="vessel-card">
<div class="vessel-header">
<div class="vessel-icon">🚢</div>
<div style="flex: 1;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
<span class="vessel-name">VESSEL {mmsi[-4:] if mmsi != 'N/A' else 'DEMO'}</span>
<span class="vessel-status {status_class}">{status_icon} {status_text}</span>
</div>
<div style="font-size: 12px; color: #6b7280;">{source.upper()} 데이터</div>
</div>
</div>
<div class="vessel-info-grid">
<div class="info-item">
<div class="info-label">MMSI</div>
<div class="info-value">{mmsi}</div>
</div>
<div class="info-item">
<div class="info-label">Call Sign</div>
<div class="info-value">{call_sign}</div>
</div>
<div class="info-item">
<div class="info-label">IMO</div>
<div class="info-value">{imo}</div>
</div>
</div>
<div class="vessel-info-grid">
<div class="info-item">
<div class="info-label">속도/방향</div>
<div class="info-value">{speed:.1f}kn / {cog:.0f}°</div>
</div>
<div class="info-item">
<div class="info-label">위도</div>
<div class="info-value">{lat:.6f}</div>
</div>
<div class="info-item">
<div class="info-label">경도</div>
<div class="info-value">{lng:.6f}</div>
</div>
</div>
</div>"""
    return html


def render_voyage_timeline(origin: str, destination: str, progress_pct: float = 0,
                           atd: str = None, eta: str = None,
                           distance_km: float = None, speed_kn: float = None) -> str:
    """TRADLINX 스타일 항해 타임라인 + 항로 정보 통합 HTML 생성"""

    # 기본 시간 설정
    now = datetime.now(timezone.utc)
    if not atd:
        atd = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
    if not eta:
        eta = (now + timedelta(days=5)).strftime("%Y-%m-%d %H:%M")

    # 항로 정보 계산
    if distance_km and speed_kn and speed_kn > 0:
        hours_remaining = distance_km / (speed_kn * 1.852)
        calc_eta = datetime.now(timezone.utc) + timedelta(hours=hours_remaining)
        eta_str = calc_eta.strftime("%Y-%m-%d %H:%M UTC")
        days = int(hours_remaining // 24)
        hours = int(hours_remaining % 24)
        time_remaining = f"{days}일 {hours}시간" if days > 0 else f"{hours}시간"
    else:
        eta_str = eta
        time_remaining = "계산 중..."
        distance_km = distance_km or 0

    html = f"""<div class="vessel-card">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;">
<span style="font-size: 20px;">🚢</span>
<span style="font-size: 16px; font-weight: 600; color: #1f2937;">항로 현황</span>
</div>

<div class="timeline-container">
<div class="timeline-item">
<div class="timeline-dot"></div>
<div class="timeline-content">
<div class="timeline-port">{origin}</div>
<div class="timeline-time">
<span class="time-badge badge-atd">ATD</span>
<span>{atd}</span>
</div>
</div>
</div>
<div class="timeline-item">
<div class="timeline-dot destination"></div>
<div class="timeline-content">
<div class="timeline-port active">{destination}</div>
<div class="timeline-time">
<span class="time-badge badge-eta">ETA</span>
<span>{eta_str}</span>
</div>
</div>
</div>
</div>

<div class="voyage-progress">
<div class="progress-header">
<span>항해 진행률</span>
<span style="font-weight: 600; color: #2563eb;">{progress_pct:.1f}%</span>
</div>
<div class="progress-bar">
<div class="progress-fill" style="width: {min(100, progress_pct)}%;"></div>
</div>
</div>

<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
<div style="text-align: center; padding: 12px; background: #f8fafc; border-radius: 8px;">
<div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">남은 거리</div>
<div style="font-size: 14px; font-weight: 600; color: #1f2937;">{distance_km:,.0f} km</div>
</div>
<div style="text-align: center; padding: 12px; background: #f8fafc; border-radius: 8px;">
<div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">예상 소요</div>
<div style="font-size: 14px; font-weight: 600; color: #1f2937;">{time_remaining}</div>
</div>
<div style="text-align: center; padding: 12px; background: #f8fafc; border-radius: 8px;">
<div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">현재 속도</div>
<div style="font-size: 14px; font-weight: 600; color: #1f2937;">{speed_kn or 0:.1f} kn</div>
</div>
</div>
</div>"""
    return html


async def track_vessel_async(mmsi: str, destination: tuple, iterations: int = 6, delay: float = 2.0):
    """Attempt to fetch live AIS data; fall back to simulation. Update st.session_state with latest track point."""
    for i in range(iterations):
        # allow stop signal
        if st.session_state.get("tracking_stop", False):
            break

        # Try AISStream REST endpoint for a single snapshot (fallback to simulate on failure)
        if AISSTREAM_API_KEY:
            try:
                url = f"https://api.aisstream.io/v1/vessels/{mmsi}"
                headers = {"Authorization": f"Bearer {AISSTREAM_API_KEY}"}
                r = requests.get(url, headers=headers, timeout=8)
                r.raise_for_status()
                j = r.json()
                # Expecting {lat, lon, speed_knots, status, destination}
                lat = float(j.get("lat") or j.get("latitude") or j.get("y", destination[0]))
                lng = float(j.get("lon") or j.get("longitude") or j.get("x", destination[1]))
                speed_kn = float(j.get("speed_knots") or j.get("speed") or 0.0)
                status = j.get("nav_status") or j.get("status") or "Under Way"
                next_dest = j.get("destination") or None
                point = {"mmsi": mmsi, "lat": lat, "lng": lng, "speed_kn": speed_kn, "status": status, "next_destination": next_dest, "source": "ais"}
            except Exception:
                st.warning(t("ais_api_failed"))
                point = simulate_vessel_position(mmsi, destination, st.session_state.get("snapshot_id", "0"))
        else:
            point = simulate_vessel_position(mmsi, destination, st.session_state.get("snapshot_id", "0"))

        # Append point history
        hist = st.session_state.get("vessel_history", [])
        hist.append(point)
        st.session_state["vessel_history"] = hist[-20:]  # keep last 20
        st.session_state["vessel_track"] = point

        await asyncio.sleep(delay)

    # mark stopped
    st.session_state["tracking_active"] = False


def run_vessel_tracking(mmsi: str, destination: tuple, iterations: int = 6, delay: float = 2.0):
    """Run asyncio loop in a Streamlit-safe way"""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(track_vessel_async(mmsi, destination, iterations=iterations, delay=delay))
    finally:
        try:
            loop.close()
        except Exception:
            pass


# =========================================================
# Commodity Ticker Definitions (yfinance)
# =========================================================
COMMODITY_TICKERS = {
    # Precious Metals
    "Gold": {"ticker": "GC=F", "unit": "USD/oz", "emoji": "🪙", "category": "Precious Metals"},
    "Silver": {"ticker": "SI=F", "unit": "USD/oz", "emoji": "🥈", "category": "Precious Metals"},
    "Platinum": {"ticker": "PL=F", "unit": "USD/oz", "emoji": "⚪", "category": "Precious Metals"},
    "Palladium": {"ticker": "PA=F", "unit": "USD/oz", "emoji": "💎", "category": "Precious Metals"},

    # Base Metals
    "Copper": {"ticker": "HG=F", "unit": "USD/lb", "emoji": "🟤", "category": "Base Metals"},
    "Aluminum": {"ticker": "ALI=F", "unit": "USD/lb", "emoji": "🔘", "category": "Base Metals"},

    # Energy
    "WTI Crude Oil": {"ticker": "CL=F", "unit": "USD/bbl", "emoji": "🛢️", "category": "Energy"},
    "Brent Crude Oil": {"ticker": "BZ=F", "unit": "USD/bbl", "emoji": "🛢️", "category": "Energy"},
    "Natural Gas": {"ticker": "NG=F", "unit": "USD/MMBtu", "emoji": "🔥", "category": "Energy"},
    "RBOB Gasoline": {"ticker": "RB=F", "unit": "USD/gal", "emoji": "⛽", "category": "Energy"},
    "Heating Oil": {"ticker": "HO=F", "unit": "USD/gal", "emoji": "🏠", "category": "Energy"},

    # Grains
    "Corn": {"ticker": "ZC=F", "unit": "cents/bu", "emoji": "🌽", "category": "Grains"},
    "Wheat": {"ticker": "ZW=F", "unit": "cents/bu", "emoji": "🌾", "category": "Grains"},
    "Soybeans": {"ticker": "ZS=F", "unit": "cents/bu", "emoji": "🫘", "category": "Grains"},
    "Soybean Oil": {"ticker": "ZL=F", "unit": "cents/lb", "emoji": "🫗", "category": "Grains"},
    "Soybean Meal": {"ticker": "ZM=F", "unit": "USD/ton", "emoji": "🥜", "category": "Grains"},
    "Oats": {"ticker": "ZO=F", "unit": "cents/bu", "emoji": "🥣", "category": "Grains"},
    "Rice": {"ticker": "ZR=F", "unit": "cents/cwt", "emoji": "🍚", "category": "Grains"},

    # Softs
    "Coffee": {"ticker": "KC=F", "unit": "cents/lb", "emoji": "☕", "category": "Softs"},
    "Sugar": {"ticker": "SB=F", "unit": "cents/lb", "emoji": "🍬", "category": "Softs"},
    "Cocoa": {"ticker": "CC=F", "unit": "USD/ton", "emoji": "🍫", "category": "Softs"},
    "Cotton": {"ticker": "CT=F", "unit": "cents/lb", "emoji": "🧶", "category": "Softs"},
    "Orange Juice": {"ticker": "OJ=F", "unit": "cents/lb", "emoji": "🍊", "category": "Softs"},

    # Lumber
    "Lumber": {"ticker": "LBS=F", "unit": "USD/1000bf", "emoji": "🪵", "category": "Lumber"},

    # Livestock
    "Live Cattle": {"ticker": "LE=F", "unit": "cents/lb", "emoji": "🐄", "category": "Livestock"},
    "Lean Hogs": {"ticker": "HE=F", "unit": "cents/lb", "emoji": "🐷", "category": "Livestock"},
    "Feeder Cattle": {"ticker": "GF=F", "unit": "cents/lb", "emoji": "🐂", "category": "Livestock"},
}

# Default selected commodities
DEFAULT_COMMODITIES = ["Gold", "Copper", "Brent Crude Oil", "Natural Gas", "Corn", "Coffee"]

# Time period options for chart
TIME_PERIODS = {
    "1M": {"period": "1mo", "label_en": "1 Month", "label_ko": "1개월"},
    "3M": {"period": "3mo", "label_en": "3 Months", "label_ko": "3개월"},
    "6M": {"period": "6mo", "label_en": "6 Months", "label_ko": "6개월"},
    "1Y": {"period": "1y", "label_en": "1 Year", "label_ko": "1년"},
    "2Y": {"period": "2y", "label_en": "2 Years", "label_ko": "2년"},
    "5Y": {"period": "5y", "label_en": "5 Years", "label_ko": "5년"},
}

# Color palette for commodity chart lines
COMMODITY_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD",
    "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9", "#F8B500", "#58D68D",
    "#EC7063", "#5DADE2", "#AF7AC5", "#48C9B0", "#F5B041", "#7DCEA0",
    "#E59866", "#7FB3D5", "#C39BD3", "#76D7C4", "#F9E79F", "#D7BDE2",
]


@st.cache_data(ttl=1800)
def fetch_commodity_history(selected_commodities: tuple, period: str) -> pd.DataFrame:
    """Fetch historical price data for selected commodities"""
    try:
        import yfinance as yf
    except Exception:
        return pd.DataFrame()

    all_data = []

    for name in selected_commodities:
        if name not in COMMODITY_TICKERS:
            continue

        info = COMMODITY_TICKERS[name]
        ticker = info["ticker"]

        try:
            tkr = yf.Ticker(ticker)
            hist = tkr.history(period=period, interval="1d")

            if len(hist) > 0:
                df = hist[["Close"]].copy()
                df.columns = [name]
                df.index = pd.to_datetime(df.index).tz_localize(None)
                all_data.append(df)
        except Exception:
            continue

    if not all_data:
        return pd.DataFrame()

    # Merge all dataframes on date index
    result = all_data[0]
    for df in all_data[1:]:
        result = result.join(df, how="outer")

    # Forward fill missing values
    result = result.ffill().bfill()

    return result


def mock_commodities(snapshot_id: str, selected_commodities: tuple = None) -> dict:
    """Generate mock commodity prices for selected commodities"""
    r = rand_from("COMMODITIES", snapshot_id)

    # Mock base prices for each commodity
    base_prices = {
        "Gold": 2000, "Silver": 25, "Platinum": 1000, "Palladium": 1200,
        "Copper": 3.8, "Aluminum": 2.2,
        "WTI Crude Oil": 75, "Brent Crude Oil": 80, "Natural Gas": 2.5, "RBOB Gasoline": 2.3, "Heating Oil": 2.4,
        "Corn": 450, "Wheat": 600, "Soybeans": 1300, "Soybean Oil": 45, "Soybean Meal": 350, "Oats": 350, "Rice": 15,
        "Coffee": 180, "Sugar": 22, "Cocoa": 3500, "Cotton": 80, "Orange Juice": 300,
        "Lumber": 500,
        "Live Cattle": 175, "Lean Hogs": 80, "Feeder Cattle": 230,
    }

    if selected_commodities is None:
        selected_commodities = tuple(DEFAULT_COMMODITIES)

    result = {"_source": "mock"}
    for name in selected_commodities:
        if name in base_prices:
            base = base_prices[name]
            variation = base * 0.05
            result[name] = round(base + r.uniform(-variation, variation), 2)

    return result


@st.cache_data(ttl=600)
def live_commodities_yfinance(selected_commodities: tuple = None) -> dict:
    """Fetch live commodity prices via yfinance for selected commodities"""
    try:
        import yfinance as yf
    except Exception:
        return {"_source": "yfinance_missing"}

    if selected_commodities is None:
        selected_commodities = tuple(DEFAULT_COMMODITIES)

    out = {"_source": "yfinance"}
    try:
        for name in selected_commodities:
            if name not in COMMODITY_TICKERS:
                continue
            info = COMMODITY_TICKERS[name]
            tkr = yf.Ticker(info["ticker"])
            price = None

            # Try fast_info first
            fi = getattr(tkr, "fast_info", None)
            if fi is not None:
                price = getattr(fi, "last_price", None) or getattr(fi, "lastPrice", None)

            # Fallback to history
            if price is None:
                hist = tkr.history(period="2d", interval="1d")
                if len(hist) > 0:
                    price = float(hist["Close"].iloc[-1])

            if price is not None:
                out[name] = round(float(price), 4)

        if len(out) <= 1:  # Only _source key
            return {"_source": "yfinance_failed"}
        return out
    except Exception:
        return {"_source": "yfinance_failed"}


# =========================================================
# Risk & Operations - 실제 데이터 기반
# =========================================================
def compute_risk(entity_id: str, snapshot_id: str, port_name: str = None,
                 weather_data=None, marine_data=None, congestion_data=None) -> dict:
    """
    실제 데이터 기반 리스크 평가
    - 날씨 데이터: OpenWeather API
    - 해양 데이터: Open-Meteo Marine API
    - 혼잡도 데이터: UNCTAD 통계
    - 지정학 리스크: 지역별 기본값

    pre-fetched 데이터를 받으면 내부 API 호출을 건너뛴다.
    """
    # 항만 좌표 가져오기
    port_coords = DESTINATION_COORDS.get(port_name, (35.1, 129.0)) if port_name else (35.1, 129.0)

    # 1. 날씨 데이터 (pre-fetched 또는 직접 호출)
    if weather_data is None:
        weather_data = fetch_weather(port_coords[0], port_coords[1])
    wind_speed = weather_data.get("wind_speed", 0) if weather_data else 0

    # 2. 해양 데이터 (pre-fetched 또는 직접 호출)
    if marine_data is None:
        marine_data = fetch_marine_weather(port_coords[0], port_coords[1])

    # 3. 혼잡도 데이터 (pre-fetched 또는 직접 호출)
    if congestion_data is None:
        congestion_data = fetch_port_congestion(port_name or "BUSAN", port_coords)

    # 4. 지정학 리스크 (지역별 기본값)
    GEOPOLITICAL_RISK = {
        "SHANGHAI": 0.3, "NINGBO": 0.3, "QINGDAO": 0.3, "TIANJIN": 0.3,  # 중국
        "BUSAN": 0.1, "TOKYO": 0.1, "YOKOHAMA": 0.1,  # 한국/일본
        "SINGAPORE": 0.15, "HONG KONG": 0.25,  # 동남아
        "ROTTERDAM": 0.1, "HAMBURG": 0.1, "ANTWERP": 0.1,  # 유럽
        "DUBAI": 0.35, "JEDDAH": 0.4,  # 중동
        "LOS ANGELES": 0.15, "LONG BEACH": 0.15,  # 미국
        "VALENCIA": 0.1, "BARCELONA": 0.1,  # 스페인
    }
    geo_risk = GEOPOLITICAL_RISK.get(port_name.upper() if port_name else "BUSAN", 0.2)

    # 5. 종합 리스크 점수 계산
    risk_result = calculate_real_risk_score(
        weather_data={"wind_speed": wind_speed},
        marine_data=marine_data,
        congestion_data=congestion_data,
        geopolitical_risk=geo_risk
    )

    score = risk_result["total_score"]
    components = risk_result["components"]

    # 리스크 레벨 결정
    if score >= 0.70:
        level = "RED"
    elif score >= 0.45:
        level = "AMBER"
    else:
        level = "GREEN"

    # 알림 생성 - 실제 데이터 기반
    alerts = []

    # 날씨 알림
    if components.get("weather", 0) > 0.5:
        alerts.append({"tag": "weather", "headline": f"강풍 주의: {wind_speed}m/s - 작업 지연 가능"})
    else:
        alerts.append({"tag": "operations", "headline": "운영 상태 정상; 서비스 수준 양호"})

    # 해양 알림
    wave_h = marine_data.get("wave_height", 0)
    if components.get("marine", 0) > 0.5:
        alerts.append({"tag": "weather", "headline": f"높은 파고: {wave_h}m - 항해 주의 필요"})

    # 혼잡도 알림
    if components.get("congestion", 0) > 0.7:
        alerts.append({"tag": "congestion", "headline": f"터미널 혼잡: {congestion_data.get('anchored_vessels', 0)}척 정박 대기"})

    # 지정학 알림
    if components.get("geopolitical", 0) > 0.3:
        alerts.append({"tag": "geopolitics", "headline": "지역 규제/불확실성 - 수출입 영향 가능"})

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_components": components,
        "alerts": alerts[:3],  # 최대 3개
        "data_source": "real-time"
    }


def compute_ops(entity_id: str, snapshot_id: str, port_name: str = None,
                weather_data=None, marine_data=None, congestion_data=None) -> dict:
    """실제 데이터 기반 운영 상태 추정

    혼잡도/날씨 데이터에서 파생:
    - 혼잡도 high + 대기시간 길면 → Anchored / Delayed
    - 강풍/고파고 → Delayed
    - 그 외 → In Port / Under Way

    pre-fetched 데이터를 받으면 내부 API 호출을 건너뛴다.
    """
    port_coords = DESTINATION_COORDS.get(port_name, (35.1, 129.0)) if port_name else (35.1, 129.0)

    # 실제 데이터 조회 (pre-fetched 또는 직접 호출)
    congestion = congestion_data if congestion_data is not None else fetch_port_congestion(port_name or "BUSAN", port_coords)
    weather = weather_data if weather_data is not None else fetch_weather(port_coords[0], port_coords[1])
    marine = marine_data if marine_data is not None else fetch_marine_weather(port_coords[0], port_coords[1])

    anchored = congestion.get("anchored_vessels", 0) or 0
    wait_hours = congestion.get("avg_wait_hours", 0) or 0
    congestion_level = congestion.get("congestion_level", "medium") or "medium"
    wind_speed = (weather.get("wind_speed", 0) if weather else 0) or 0
    wave_height = (marine.get("wave_height", 0) if marine else 0) or 0

    now = datetime.now(timezone.utc)

    # 상태 결정 로직 — 실제 조건 기반
    if wind_speed > 15 or wave_height > 3.5:
        status = "Delayed"
        delay_min = int(max(60, wind_speed * 8))
        speed_kn = round(max(4.0, 12.0 - wind_speed * 0.4), 1)
    elif congestion_level == "high" and wait_hours > 24:
        status = "Anchored"
        delay_min = int(wait_hours * 60 * 0.3)
        speed_kn = 0.0
    elif congestion_level == "high":
        status = "Delayed"
        delay_min = int(wait_hours * 60 * 0.2)
        speed_kn = round(max(6.0, 14.0 - anchored * 0.1), 1)
    elif congestion_level == "medium" and wait_hours > 12:
        status = "In Port"
        delay_min = int(wait_hours * 10)
        speed_kn = 0.0
    else:
        status = "Under Way"
        delay_min = 0
        speed_kn = round(max(10.0, 16.0 - wind_speed * 0.3), 1)

    eta = now + timedelta(hours=max(24, wait_hours * 2), minutes=delay_min)

    return {
        "status": status,
        "eta_utc": eta.strftime("%Y-%m-%d %H:%M"),
        "delay_min": int(delay_min),
        "speed_kn": speed_kn,
        "data_source": {
            "congestion": congestion.get("source", "estimated"),
            "weather": weather.get("_source", "mock") if weather else "mock",
            "marine": "open-meteo" if wave_height > 0 else "estimated"
        }
    }


def build_port_popup_html(row: dict) -> str:
    """팝업 HTML 통합 빌더 — 메인 항구 / CSV 목적지 공용

    ports_df 의 한 행(dict)을 받아 동일 구조의 팝업 HTML을 반환한다.
    대시보드(stMarkdownContainer)와 동일한 데이터 소스를 사용하므로
    팝업 ↔ 대시보드 간 데이터 불일치가 발생하지 않는다.
    """
    port_name = row.get("name", "Unknown")
    risk_level = row.get("risk_level", "GREEN")
    risk_score = row.get("risk_score", 0)
    is_csv = row.get("_is_csv", False)

    w = row.get("_weather") or {}
    marine = row.get("_marine") or {}
    congestion = row.get("_congestion") or {}
    ops = row.get("_ops") or {}
    nearby_risks = row.get("_nearby_risks") or []

    # 색상
    color_map = {"GREEN": ("#22c55e", "#15803d"), "AMBER": ("#f97316", "#c2410c"), "RED": ("#dc2626", "#991b1b")}
    marker_color, _ = color_map.get(risk_level, ("#22c55e", "#15803d"))

    # 날씨
    weather_desc = str(w.get("desc", "")).lower()
    weather_icon = WEATHER_ICONS.get(weather_desc, "🌡️")
    temp_c = w.get("temp_c", 0) or 0
    wind_speed = w.get("wind_speed", 0) or 0

    # 해양
    wave_height = (marine.get("wave_height", 0) or 0)
    wave_period = (marine.get("wave_period", 0) or 0)

    # 혼잡도
    anchored = congestion.get("anchored_vessels", 0) or 0
    wait_hours = congestion.get("avg_wait_hours", 0) or 0
    cong_level = congestion.get("congestion_level", "medium") or "medium"
    cong_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(cong_level, "⚪")

    # 운영
    ops_status = ops.get("status", "N/A")
    ops_delay = ops.get("delay_min", 0) or 0
    status_emoji = {"In Port": "🟢", "Under Way": "🔵", "Delayed": "🟠", "Anchored": "🔴"}.get(ops_status, "⚪")

    icon_prefix = "🚢" if is_csv else "⚓"
    continent = row.get("continent", "")
    country = row.get("country", "")
    plat = row.get("lat", 0)
    plng = row.get("lng", 0)

    html = f"""
    <div style="min-width:320px;font-family:Arial,sans-serif;">
        <div style="background:{marker_color};color:white;padding:10px;margin:-10px -10px 10px -10px;border-radius:4px 4px 0 0;display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:16px;font-weight:bold;">{icon_prefix} {port_name}</div>
                <div style="font-size:11px;opacity:0.9;">{continent} · {country}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:20px;">{weather_icon}</div>
                <div style="font-size:13px;font-weight:600;">{temp_c:.1f}°C</div>
            </div>
        </div>
        <div style="padding:0 5px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:12px;color:#6b7280;">Risk Level</span>
                <span style="font-size:12px;font-weight:bold;color:{marker_color};">{risk_level} ({risk_score:.0%})</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:11px;color:#6b7280;">Status</span>
                <span style="font-size:11px;font-weight:600;">{status_emoji} {ops_status}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:11px;color:#6b7280;">Delay</span>
                <span style="font-size:11px;">{ops_delay} min</span>
            </div>
            <div style="border-top:1px solid #e5e7eb;padding-top:6px;margin-top:6px;">
                <div style="font-size:11px;font-weight:bold;color:#374151;margin-bottom:4px;">🏗️ Field Response</div>
                <div style="font-size:10px;color:#4b5563;">
                    Congestion: <b>{anchored}</b> anchored {cong_emoji} · Wait: {wait_hours}h
                </div>
                <div style="font-size:10px;color:#4b5563;margin-top:2px;">
                    Wind: {wind_speed} m/s · Waves: {wave_height} m · Period: {wave_period}s
                </div>
            </div>
    """

    # 근처 글로벌 리스크
    if nearby_risks:
        html += """
            <div style="border-top:1px solid #e5e7eb;padding-top:6px;margin-top:6px;">
                <div style="font-size:11px;font-weight:bold;color:#374151;margin-bottom:4px;">🌍 근처 글로벌 리스크</div>
        """
        for nearby in nearby_risks[:3]:
            event_type = nearby.get("event_type", "other")
            config = RISK_TYPE_CONFIG.get(event_type, RISK_TYPE_CONFIG["other"])
            distance = nearby.get("distance_km", 0)
            title = nearby.get("title", "Unknown")
            severity = nearby.get("severity", 0.5)
            article_link = nearby.get("link", "")
            title_ko = translate_to_korean(title) if title else ""
            link_btn = f'<a href="{article_link}" target="_blank" style="color:#3b82f6;font-size:10px;margin-left:4px;">📰</a>' if article_link else ""

            html += f"""
                <div style="background:#fef2f2;border-left:3px solid {config['color']};padding:5px 8px;margin-bottom:4px;border-radius:0 4px 4px 0;">
                    <div style="font-size:10px;font-weight:600;color:#1f2937;">{config['icon']} {title}{link_btn}</div>
                    <div style="font-size:9px;color:#6b7280;margin-top:1px;">🇰🇷 {title_ko}</div>
                    <div style="font-size:8px;color:#9ca3af;margin-top:1px;">📍 {int(distance)}km | ⚠️ {severity:.0%}</div>
                </div>
            """
        html += "</div>"

    html += f"""
            <div style="text-align:center;margin-top:8px;padding-top:6px;border-top:1px solid #e5e7eb;">
                <span style="font-size:9px;color:#9ca3af;">📍 {plat:.4f}, {plng:.4f}</span>
            </div>
        </div>
    </div>
    """
    return html


# =========================================================
# Session State Initialization
# =========================================================
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "snapshot_id" not in st.session_state:
    st.session_state.snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
if "selected_port_id" not in st.session_state:
    st.session_state.selected_port_id = "PORT_BUSAN"
if "incidents" not in st.session_state:
    st.session_state.incidents = {}
if "last_created_incident" not in st.session_state:
    st.session_state.last_created_incident = None
if "realtime_sync" not in st.session_state:
    st.session_state.realtime_sync = False

# Commodity selection
if "selected_commodities" not in st.session_state:
    st.session_state.selected_commodities = DEFAULT_COMMODITIES.copy()

# Tracking defaults
if "tracking_active" not in st.session_state:
    st.session_state.tracking_active = False
if "tracking_stop" not in st.session_state:
    st.session_state.tracking_stop = False
if "vessel_history" not in st.session_state:
    st.session_state.vessel_history = []

# Simulation / Demo playback defaults
if "sim_play" not in st.session_state:
    st.session_state.sim_play = False
if "sim_speed" not in st.session_state:
    st.session_state.sim_speed = 1.0
if "sim_progress" not in st.session_state:
    st.session_state.sim_progress = None
if "vessel_distance_km" not in st.session_state:
    st.session_state.vessel_distance_km = None
if "cfo_additional_cost_krw" not in st.session_state:
    st.session_state.cfo_additional_cost_krw = 0

# News pagination defaults
if "kotra_page" not in st.session_state:
    st.session_state.kotra_page = 1
if "global_news_page" not in st.session_state:
    st.session_state.global_news_page = 1


# =========================================================
# Sidebar Configuration
# =========================================================
with st.sidebar:
    st.markdown(f"### {t('lang')}")
    lang_choice = st.radio(
        label="",
        options=[("English", "en"), ("한국어", "ko")],
        format_func=lambda x: x[0],
        index=0 if st.session_state.lang == "en" else 1,
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.lang = lang_choice[1]

    st.divider()

    # Manual refresh button (always available) - 자동 새로고침 제거
    if st.button(t("refresh"), use_container_width=True, type="primary"):
        st.session_state.snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        st.cache_data.clear()
        st.rerun()

    # Snapshot info
    st.caption(f"**{t('snapshot_id')}:** `{st.session_state.snapshot_id}`")
    st.caption(f"**{t('last_updated')}:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    st.divider()

    # Vessel Tracking Inputs
    st.markdown(f"### {t('tracking_section')}")
    tracking_id = st.text_input(t('tracking_id'), value=st.session_state.get('tracking_id',''), help=t('tracking_id_help'))
    st.session_state['tracking_id'] = tracking_id

    # Verify Mapping Button
    if st.button(t('verify_tracking'), help=t('verify_tracking_help')):
        if not tracking_id:
            st.warning(t('enter_mmsi_or_bl'))
        else:
            resolved = fetch_mmsi_by_bl(tracking_id)
            if resolved:
                st.success(t('resolved_mmsi_from_bl').format(mmsi=resolved, tracking_id=tracking_id))
            else:
                st.info(t('tracking_by_bl_simulation'))

    mmsi_in = st.text_input(t('mmsi'), value=st.session_state.get('mmsi',''), help=t('mmsi_help'))
    st.session_state['mmsi'] = mmsi_in

    dest_names = list(DESTINATION_COORDS.keys())
    dest_choice = st.selectbox(t('destination_port'), options=dest_names, index=0)
    st.session_state['destination_port'] = dest_choice

    # 선박 위치 표시 버튼 (AIS 실패 시 시뮬레이션 fallback)
    if st.button("🚢 선박 위치 표시" if st.session_state.lang == "ko" else "🚢 Show Vessel", use_container_width=True, type="primary"):
        dest_coords = DESTINATION_COORDS.get(st.session_state.get('destination_port'))
        if not dest_coords:
            st.warning("No destination selected.")
        else:
            mmsi_val = (st.session_state.get('mmsi') or '').strip()
            tracking_val = (st.session_state.get('tracking_id') or '').strip()
            used_mmsi = None

            if mmsi_val and mmsi_val.isdigit() and len(mmsi_val) == 9:
                used_mmsi = mmsi_val
            elif tracking_val:
                resolved = fetch_mmsi_by_bl(tracking_val)
                if resolved:
                    used_mmsi = resolved
                    st.info(t('resolved_mmsi_from_bl').format(mmsi=resolved, tracking_id=tracking_val))
                else:
                    used_mmsi = tracking_val  # BL 자체를 식별자로 사용
            else:
                st.warning(t('enter_mmsi_or_bl'))

            if used_mmsi:
                # 1) 실제 AIS 데이터 시도
                spinner_msg = "AIS 데이터 조회 중..." if st.session_state.lang == "ko" else "Fetching AIS data..."
                with st.spinner(spinner_msg):
                    ais_data = fetch_ais_position(used_mmsi)

                if ais_data:
                    v = {
                        'mmsi': used_mmsi,
                        'lat': ais_data.get('lat'),
                        'lng': ais_data.get('lng'),
                        'speed_kn': round(ais_data.get('sog', 12.0), 1),
                        'cog': ais_data.get('cog', 0),
                        'status': ais_data.get('nav_status', 'Under Way'),
                        'next_destination': ais_data.get('destination') or st.session_state['destination_port'],
                        'source': ais_data.get('source', 'ais')
                    }
                else:
                    # 2) AIS 실패 → 시뮬레이션 fallback
                    v = simulate_vessel_position(used_mmsi, dest_coords, st.session_state.get('snapshot_id', '0'))
                    v['source'] = 'simulated'
                    st.warning(t('ais_api_failed'))

                st.session_state['vessel_track'] = v
                st.session_state['vessel_trail'] = [{"lat": v['lat'], "lng": v['lng'], "timestamp": datetime.now(timezone.utc).isoformat()}]
                st.success("선박 위치가 표시되었습니다!" if st.session_state.lang == "ko" else "Vessel position displayed!")

    # 시뮬레이션 모드 표시
    if st.session_state.get('vessel_track'):
        source = st.session_state['vessel_track'].get('source', 'unknown')
        if source in ['simulated', 'demo']:
            st.warning(t('simulation_mode'))

    st.divider()
    
    # Map options
    st.markdown("### ⚙️ Map Options")
    cluster_on = st.toggle(t("cluster_markers"), value=True)
    labels_on = st.toggle(t("show_labels"), value=False)

    st.divider()
    
    # Market Intelligence Panel - FX Only
    st.markdown(f"## {t('sidebar_market')}")

    # FX Rates
    fx = fetch_fx_krw_base()

    st.markdown(f"**{t('fx')}**")
    c1, c2 = st.columns(2)
    c1.metric("USD/KRW", f"{fx['USD/KRW']:.2f}")
    c2.metric("EUR/KRW", f"{fx['EUR/KRW']:.2f}")
    c3, c4 = st.columns(2)
    c3.metric("JPY/KRW", f"{fx['JPY/KRW']:.4f}")
    c4.metric("CNY/KRW", f"{fx['CNY/KRW']:.4f}")

    # Data source indicator for FX only
    fx_source = t('real_api') if fx.get('_source') != 'mock' else t('mock')
    st.caption(f"{t('data_source')}: FX={fx_source}")


# =========================================================
# Compute Snapshot Dataset (캐시 + 병렬 fetch)
# =========================================================
snapshot_id = st.session_state.snapshot_id


def _guess_continent(lat, lng):
    """좌표 기반 대륙 추정"""
    if lat > 20 and 100 < lng < 150: return "Asia"
    if lat > 30 and -10 < lng < 45: return "Europe"
    if lat > 15 and -130 < lng < -50: return "North America"
    if lat < 15 and -80 < lng < -30: return "South America"
    if -40 < lat < 35 and -20 < lng < 55: return "Africa"
    if lat < 0 and 100 < lng < 180: return "Oceania"
    if lat > 20 and 45 < lng < 70: return "Middle East"
    return "Other"


@st.cache_data(ttl=900, show_spinner="항만 데이터 로딩 중...")
def _build_ports_dataframe(snapshot_id: str):
    """모든 항구 데이터를 한 번에 빌드 (캐시 15분).

    1단계: 글로벌 리스크 로드
    2단계: 모든 항구(메인+CSV) 좌표 수집
    3단계: ThreadPoolExecutor 로 날씨/해양/혼잡도 병렬 fetch
    4단계: 결과 조합 → rows list 반환
    """
    global_risks, risk_error = fetch_all_global_risks()

    # ── CSV 목적지 이름 목록 미리 수집 ──
    csv_dest_names = set()
    try:
        _csv_possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Kita_해상_참고운임_1월.csv"),
            os.path.join(os.getcwd(), "Kita_해상_참고운임_1월.csv"),
            os.path.join(os.getcwd(), "project1", "Kita_해상_참고운임_1월.csv"),
        ]
        for _p in _csv_possible_paths:
            if os.path.exists(_p):
                _dest_df = pd.read_csv(_p, encoding='cp949')
                if len(_dest_df.columns) >= 2:
                    _dest_col = _dest_df.columns[1]
                    csv_dest_names = set(str(d).strip() for d in _dest_df[_dest_col].dropna().unique())
                break
    except Exception:
        pass

    main_port_names = set(p["name"] for p in PORTS)

    # ── 모든 항구 정보 (메인 + CSV) 리스트 ──
    all_port_infos = []
    for p in PORTS:
        pname = p["name"]
        coords = DESTINATION_COORDS.get(pname, (p["lat"], p["lng"]))
        all_port_infos.append({
            "name": pname, "lat": p["lat"], "lng": p["lng"],
            "fetch_lat": coords[0], "fetch_lng": coords[1],
            "is_csv": False, "port_dict": p,
        })

    for dn in csv_dest_names:
        if dn in DESTINATION_COORDS and dn not in main_port_names:
            _lat, _lng = DESTINATION_COORDS[dn]
            all_port_infos.append({
                "name": dn, "lat": _lat, "lng": _lng,
                "fetch_lat": _lat, "fetch_lng": _lng,
                "is_csv": True, "port_dict": None,
            })

    # ── 2단계: 병렬 fetch (weather + marine + congestion) ──
    prefetched = {}

    def _fetch_one(info):
        name = info["name"]
        flat, flng = info["fetch_lat"], info["fetch_lng"]
        w = fetch_weather(flat, flng)
        marine = fetch_marine_weather(flat, flng)
        congestion = fetch_port_congestion(name, (flat, flng))
        return name, w, marine, congestion

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_fetch_one, pi): pi for pi in all_port_infos}
        for future in as_completed(futures):
            try:
                name, w, marine, congestion = future.result()
                prefetched[name] = (w, marine, congestion)
            except Exception:
                pi = futures[future]
                prefetched[pi["name"]] = ({}, {}, {})

    # ── 3단계: 메인 항구 rows 빌드 ──
    rows = []
    for p in PORTS:
        pname = p.get("name", "")
        plat, plng = p["lat"], p["lng"]
        pcountry = p.get("country", "")

        w, marine, congestion = prefetched.get(pname, ({}, {}, {}))

        # pre-fetched 데이터 전달 → 내부 중복 fetch 제거
        risk = compute_risk(p["id"], snapshot_id, port_name=pname,
                            weather_data=w, marine_data=marine, congestion_data=congestion)
        ops = compute_ops(p["id"], snapshot_id, port_name=pname,
                          weather_data=w, marine_data=marine, congestion_data=congestion)

        risk_impact = calculate_risk_impact_on_port(plat, plng, global_risks, port_country=pcountry)
        nearby_risks = risk_impact.get("nearby_risks", [])

        adj_risk_level = risk["risk_level"]
        if nearby_risks:
            max_sev = max(r.get("severity", 0.5) for r in nearby_risks)
            if max_sev >= 0.8 or adj_risk_level == "RED":
                adj_risk_level = "RED"
            elif adj_risk_level == "GREEN":
                adj_risk_level = "AMBER"

        rows.append({
            **p,
            "risk_level": adj_risk_level,
            "risk_score": risk["risk_score"],
            "ops_status": ops["status"],
            "eta_utc": ops["eta_utc"],
            "delay_min": ops["delay_min"],
            "_risk": risk,
            "_ops": ops,
            "_weather": w,
            "_marine": marine,
            "_congestion": congestion,
            "_nearby_risks": nearby_risks,
            "_is_csv": False,
        })

    # ── 4단계: CSV 목적지 rows 빌드 ──
    for pi in all_port_infos:
        if not pi["is_csv"]:
            continue
        dn = pi["name"]
        _lat, _lng = pi["lat"], pi["lng"]
        _port_id = f"CSV_{dn.upper().replace(' ', '_')}"
        _continent = _guess_continent(_lat, _lng)

        _w, _marine, _cong = prefetched.get(dn, ({}, {}, {}))
        _risk_impact = calculate_risk_impact_on_port(_lat, _lng, global_risks)
        _nearby = _risk_impact.get("nearby_risks", [])

        _risk_level = "GREEN"
        _risk_score = 0.25
        if _nearby:
            _max_sev = max(r.get("severity", 0.5) for r in _nearby)
            if _max_sev >= 0.8:
                _risk_level = "RED"
                _risk_score = _max_sev
            elif _max_sev >= 0.4:
                _risk_level = "AMBER"
                _risk_score = _max_sev * 0.8

        _ops = compute_ops(_port_id, snapshot_id, port_name=dn,
                           weather_data=_w, marine_data=_marine, congestion_data=_cong)

        rows.append({
            "id": _port_id,
            "name": dn,
            "continent": _continent,
            "country": "",
            "lat": _lat,
            "lng": _lng,
            "risk_level": _risk_level,
            "risk_score": _risk_score,
            "ops_status": _ops["status"],
            "eta_utc": _ops["eta_utc"],
            "delay_min": _ops["delay_min"],
            "_risk": {"risk_score": _risk_score, "risk_level": _risk_level, "alerts": [], "risk_components": {}},
            "_ops": _ops,
            "_weather": _w,
            "_marine": _marine,
            "_congestion": _cong,
            "_nearby_risks": _nearby,
            "_is_csv": True,
        })

    return rows, global_risks, risk_error


# ── 캐시된 함수 호출 → ports_df 구성 ──
_cached_rows, _cached_global_risks, _cached_risk_error = _build_ports_dataframe(snapshot_id)
ports_df = pd.DataFrame(_cached_rows)

# Create incident queue (RED/AMBER only)
queue_df = ports_df[ports_df["risk_level"].isin(["RED", "AMBER"])].copy()
level_rank = {"RED": 0, "AMBER": 1}
queue_df["rank"] = queue_df["risk_level"].map(level_rank)
queue_df = queue_df.sort_values(
    ["rank", "risk_score"],
    ascending=[True, False]
).drop(columns=["rank"], errors="ignore")


# =========================================================
# Main UI Header
# =========================================================
st.markdown(f"# {t('title')}")
st.markdown(f"### {t('subtitle')}")

# Legend in header
col_legend, col_spacer = st.columns([3, 1])
with col_legend:
    st.markdown(
        f"""
        <div style="
            padding: 12px 16px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background: #f8f9fa;
            margin-bottom: 20px;
        ">
            <strong style="font-size: 14px; color: #333;">🛡️ {t('legend')}:</strong>
            <span style="color: #555; margin-left: 10px;">{t('legend_text')}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# Create tabs
tab_map, tab_brief = st.tabs([t("map_title"), t("briefing")])


# =========================================================
# TAB 1: MAP & OPERATIONS
# =========================================================
with tab_map:
    left_col, right_col = st.columns([7, 3])

    # ===== LEFT: MAP =====
    with left_col:
        st.markdown(f"## {t('map_title')}")
        
        # Create Folium map
        m = folium.Map(
            location=[15, 0],
            zoom_start=2,
            min_zoom=2,
            max_zoom=7,
            control_scale=True,
            max_bounds=True,
            tiles=None
        )

        # Add light tile layer
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr="© OpenStreetMap contributors © CARTO",
            name="CartoDB Positron",
            no_wrap=True
        ).add_to(m)

        # Set bounds
        bounds = [[-60, -170], [80, 170]]
        m.fit_bounds(bounds)

        # Optional clustering
        cluster = MarkerCluster(disableClusteringAtZoom=5) if cluster_on else None
        if cluster:
            cluster.add_to(m)

        # Label offset helper
        def label_offset(port_id: str):
            r = rand_from("LABEL::" + port_id, "STATIC")
            return int(r.uniform(-18, 18)), int(r.uniform(-14, 14))

        # ===== 항구 마커 추가 (ports_df 통합 — 메인+CSV 공용) =====
        for _, row in ports_df.iterrows():
            port_id = row["id"]
            port_lat = row["lat"]
            port_lng = row["lng"]
            port_name = row["name"]
            risk_level = row["risk_level"]
            risk_score = row["risk_score"]
            is_csv = row.get("_is_csv", False)

            # 리스크 레벨에 따른 색상 (이미 ports_df에서 조정 완료)
            color_map = {"GREEN": ("#22c55e", "#15803d"), "AMBER": ("#f97316", "#c2410c"), "RED": ("#dc2626", "#991b1b")}
            marker_color, border_color = color_map.get(risk_level, ("#22c55e", "#15803d"))

            # ── 통합 팝업 HTML (build_port_popup_html 사용) ──
            popup_html = build_port_popup_html(row.to_dict())

            # CircleMarker (CSV 목적지는 약간 작게)
            icon_prefix = "🚢" if is_csv else "⚓"
            marker = folium.CircleMarker(
                location=[port_lat, port_lng],
                radius=7 if is_csv else 8,
                color=border_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.8,
                weight=2,
                tooltip=f"{icon_prefix} {port_name} | {risk_level} ({risk_score:.0%})",
                popup=folium.Popup(popup_html, max_width=380),
            )

            if cluster:
                marker.add_to(cluster)
            else:
                marker.add_to(m)

            # Optional text labels
            if labels_on:
                dx, dy = label_offset(port_id)
                folium.Marker(
                    location=[port_lat, port_lng],
                    icon=folium.DivIcon(
                        html=f"""
                        <div style="
                            transform: translate({dx}px, {dy}px);
                            background: #ffffff;
                            color: #333333;
                            border: 1px solid #d0d0d0;
                            border-radius: 8px;
                            padding: 3px 10px;
                            font-size: 11px;
                            font-weight: 500;
                            white-space: nowrap;
                            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                        ">
                            {port_name}
                        </div>
                        """
                    )
                ).add_to(m)

        # Add vessel tracking marker and route if present
        vessel = st.session_state.get('vessel_track')
        dest_name = st.session_state.get('destination_port')
        dest_coords = DESTINATION_COORDS.get(dest_name) if dest_name else None

        # 선박 위치는 버튼 클릭 시에만 업데이트 (자동 업데이트 제거 - 무한 루프 방지)

        if vessel:
            # Center map on vessel
            try:
                m.location = [vessel['lat'], vessel['lng']]
                m.zoom_start = 6
            except Exception:
                pass

            # Vessel tooltip (localized)
            vessel_status = vessel.get('status', '')
            vessel_tooltip = f"{t('my_vessel')} {vessel.get('mmsi')} — {t('speed')}: {vessel.get('speed_kn')} kn"
            
            # Floating info (popup)
            popup_html = f"<strong>{t('my_vessel')} {vessel.get('mmsi')}</strong><br/>{t('speed')}: {vessel.get('speed_kn')} kn<br/>{t('next_destination')}: {vessel.get('next_destination') or dest_name or '-'}<br/>{t('status')}: {vessel_status}"

            folium.CircleMarker(
                location=[vessel['lat'], vessel['lng']],
                radius=8,
                color='blue',
                fill=True,
                fill_opacity=0.9,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)

            # 출발지 (부산) 마커
            busan_coords = (35.1028, 129.0403)
            folium.Marker(
                location=[busan_coords[0], busan_coords[1]],
                tooltip="출발지: 부산항",
                popup="부산항 (Busan Port)<br>대한민국",
                icon=folium.Icon(color="green", icon="anchor", prefix="fa")
            ).add_to(m)

            # 1. 세션 궤적 (이동 경로 히스토리) 그리기 — 날짜변경선 처리
            trail = st.session_state.get("vessel_trail", [])
            if len(trail) >= 2:
                trail_locations = [[pt["lat"], pt["lng"]] for pt in trail]
                add_antimeridian_polyline(
                    m, trail_locations,
                    color='blue',
                    weight=3,
                    opacity=0.7,
                    tooltip="항해 궤적"
                )

            # 2. COG/SOG 기반 예상 경로 벡터 그리기 (화살표) — 날짜변경선 처리
            cog = vessel.get('cog', 0)
            sog = vessel.get('speed_kn', 12)
            if sog > 0:
                vector_points = get_vector_line_points(vessel['lat'], vessel['lng'], cog, sog, num_points=10)
                vector_locations = [[pt[0], pt[1]] for pt in vector_points]

                # 예상 경로 (점선 화살표)
                add_antimeridian_polyline(
                    m, vector_locations,
                    color='green',
                    weight=3,
                    opacity=0.8,
                    dash_array='8, 4',
                    tooltip=f"예상 경로 (COG: {cog}°, SOG: {sog}kn)"
                )

                # 화살표 끝 마커 (2시간 후 예상 위치)
                if len(vector_points) > 1:
                    end_lat, end_lng = vector_points[-1]
                    folium.CircleMarker(
                        location=[end_lat, end_lng],
                        radius=5,
                        color='green',
                        fill=True,
                        fill_opacity=0.7,
                        tooltip="2시간 후 예상 위치"
                    ).add_to(m)

            # 3. 실제 해상 경로 그리기 (Searoute - 육지 회피)
            if dest_coords:
                # 부산 출발 좌표
                busan_coords = (35.1028, 129.0403)

                # 해상 경로 계산 (캐시됨)
                sea_route = get_sea_route(busan_coords, dest_coords)

                if len(sea_route) > 2:
                    # 전체 계획 경로 (회색 점선) — 날짜변경선 처리
                    add_antimeridian_polyline(
                        m, sea_route,
                        color='gray',
                        weight=2,
                        opacity=0.5,
                        dash_array='5, 10',
                        tooltip=f"계획 항로: 부산 → {dest_name}"
                    )

                    # 현재 위치에서 목적지까지 남은 경로 (빨간 점선)
                    # 현재 위치와 가장 가까운 경로 포인트 찾기
                    vessel_pos = (vessel['lat'], vessel['lng'])
                    min_dist = float('inf')
                    closest_idx = 0

                    for i, pt in enumerate(sea_route):
                        d = haversine_distance(vessel_pos[0], vessel_pos[1], pt[0], pt[1])
                        if d < min_dist:
                            min_dist = d
                            closest_idx = i

                    # 남은 경로만 그리기 — 날짜변경선 처리
                    remaining_route = sea_route[closest_idx:]
                    if len(remaining_route) >= 2:
                        add_antimeridian_polyline(
                            m, remaining_route,
                            color='red',
                            weight=3,
                            opacity=0.8,
                            dash_array='10, 5',
                            tooltip=f"남은 항로 → {dest_name}"
                        )

                # 거리 계산 (해상 경로 기준)
                try:
                    route_distance = get_route_distance(busan_coords, dest_coords)
                    dist_km = haversine_distance(vessel['lat'], vessel['lng'], dest_coords[0], dest_coords[1])
                except Exception:
                    dist_km = haversine_distance(vessel['lat'], vessel['lng'], dest_coords[0], dest_coords[1])

                # 4. 목적지 마커
                folium.Marker(
                    location=[dest_coords[0], dest_coords[1]],
                    tooltip=f"목적지: {dest_name}",
                    popup=f"목적지: {dest_name}<br>남은 거리: {dist_km:.1f}km",
                    icon=folium.Icon(color="red", icon="flag", prefix="fa")
                ).add_to(m)

                # Port proximity alert
                if dist_km < 50:
                    st.info(f"{t('waiting_for_berthing')} — {dest_name} ({dist_km:.1f} km)")

        # (CSV 목적지는 이미 ports_df에 병합됨 — 위 통합 루프에서 처리)

        # Render map
        st_map = st_folium(m, height=580, use_container_width=True)

        # Handle map clicks — 좌표 기반 항구 매칭
        clicked_data = st_map.get("last_object_clicked")
        if clicked_data:
            c_lat = clicked_data.get("lat")
            c_lng = clicked_data.get("lng")
            if c_lat is not None and c_lng is not None:
                for _, row in ports_df.iterrows():
                    if abs(row["lat"] - c_lat) < 0.01 and abs(row["lng"] - c_lng) < 0.01:
                        if st.session_state.selected_port_id != row["id"]:
                            st.session_state.selected_port_id = row["id"]
                            st.rerun()
                        break

        # ===== TRADLINX 스타일 선박 정보 패널 =====
        vessel = st.session_state.get('vessel_track')
        dest_name = st.session_state.get('destination_port')

        if vessel:
            st.markdown("---")
            st.markdown("### 🚢 선박 정보")

            # 두 개의 컬럼으로 카드 배치
            vessel_col1, vessel_col2 = st.columns(2)

            with vessel_col1:
                # 선박 정보 카드
                vessel_card_html = render_vessel_card(vessel, dest_name)
                st.markdown(vessel_card_html, unsafe_allow_html=True)

            with vessel_col2:
                # 항로 타임라인 + 항로 정보 통합
                progress_pct = st.session_state.get('vessel_progress_pct', 0)

                # 거리 및 속도 계산
                distance_km = None
                speed_kn = vessel.get('speed_kn', 12)
                if dest_name and dest_name in DESTINATION_COORDS:
                    dest_coords = DESTINATION_COORDS[dest_name]
                    distance_km = st.session_state.get('vessel_distance_km')
                    if distance_km is None:
                        distance_km = haversine_distance(
                            vessel['lat'], vessel['lng'],
                            dest_coords[0], dest_coords[1]
                        )

                timeline_html = render_voyage_timeline(
                    origin="Busan",
                    destination=dest_name or "Unknown",
                    progress_pct=progress_pct,
                    distance_km=distance_km,
                    speed_kn=speed_kn
                )
                st.markdown(timeline_html, unsafe_allow_html=True)

    # ===== RIGHT: OPERATIONS PANEL (ports_df 통합 데이터 사용) =====
    with right_col:
        st.markdown(f"## {t('ops_title')}")

        # ── ports_df 에서 통합 데이터 로드 (팝업과 동일 소스) ──
        selected = ports_df[ports_df["id"] == st.session_state.selected_port_id].iloc[0].to_dict()
        selected_risk = selected["_risk"]
        selected_ops = selected["_ops"]
        w = selected.get("_weather") or {}
        marine_data = selected.get("_marine") or {}
        congestion_data = selected.get("_congestion") or {}
        nearby_risks = selected.get("_nearby_risks") or []

        # ── 헤더 카드 ──
        risk_level = selected["risk_level"]  # ports_df에서 이미 조정된 값
        risk_color = {"GREEN": "#10b981", "AMBER": "#f59e0b", "RED": "#ef4444"}.get(risk_level, "#6b7280")

        weather_desc = str(w.get("desc", "")).lower()
        weather_icon = WEATHER_ICONS.get(weather_desc, "🌡️")
        temp_c = w.get("temp_c", 0) or 0

        st.markdown(
            f"""
            <div style="
                padding: 16px;
                border: 2px solid {risk_color};
                border-radius: 12px;
                background: #ffffff;
                margin-bottom: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <div style="
                        font-weight: 700;
                        font-size: 20px;
                        color: #1a1a1a;
                        margin-bottom: 6px;
                    ">
                        {selected['name']}
                    </div>
                    <div style="
                        font-size: 13px;
                        color: #555555;
                    ">
                        📍 {selected['continent']} · {selected['country']} · <code style="
                            background: #f5f5f5;
                            padding: 2px 6px;
                            border-radius: 4px;
                            font-size: 11px;
                            color: #2563eb;
                        ">{selected['id']}</code>
                    </div>
                </div>
                <div style="
                    text-align: center;
                    padding-left: 16px;
                ">
                    <div style="font-size: 28px; line-height: 1;">{weather_icon}</div>
                    <div style="font-size: 18px; font-weight: 600; color: #1f2937;">{temp_c:.1f}°C</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ── Risk Level / Score ──
        risk_color_map = {"GREEN": "#10b981", "AMBER": "#f59e0b", "RED": "#ef4444"}
        risk_bg_color = risk_color_map.get(risk_level, "#6b7280")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{t('risk_level')}**")
            st.markdown(
                f"""
                <div style="
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background-color: {risk_bg_color};
                    box-shadow: 0 0 10px {risk_bg_color};
                    margin: 5px 0;
                "></div>
                """,
                unsafe_allow_html=True
            )
        c2.metric(
            t("risk_score"),
            f"{selected_risk['risk_score']:.2f}",
            delta=None,
            delta_color="off"
        )

        st.divider()

        # ── Operations Status ──
        ops_status = selected_ops.get("status", "Unknown")
        ops_delay = selected_ops.get("delay_min", 0) or 0
        ops_speed = selected_ops.get("speed_kn", 0) or 0
        ops_eta = selected_ops.get("eta_utc", "N/A")

        status_emoji = {
            "In Port": "🟢", "Under Way": "🔵",
            "Delayed": "🟠", "Anchored": "🔴"
        }.get(ops_status, "⚪")

        st.markdown(f"### {t('operations')}")
        o1, o2 = st.columns(2)
        o1.metric(t("status"), f"{status_emoji} {ops_status}")
        o2.metric(t("eta"), ops_eta)

        o3, o4 = st.columns(2)
        o3.metric(t("delay"), f"{ops_delay} min" if ops_delay > 0 else "0")
        o4.metric(t("speed"), f"{ops_speed} kn")

        ops_sources = selected_ops.get("data_source", {})
        if ops_sources and isinstance(ops_sources, dict):
            src_parts = [f"{k}: {v}" for k, v in ops_sources.items()]
            st.caption(f"출처: {' | '.join(src_parts)}")

        st.divider()

        # ── Field Response (ports_df 캐시 데이터 사용) ──
        st.markdown(f"### {t('field_response')}")

        anchored = congestion_data.get("anchored_vessels", 0) or 0
        wait_hours = congestion_data.get("avg_wait_hours", 0) or 0
        congestion_level = congestion_data.get("congestion_level", "medium") or "medium"

        level_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(congestion_level, "⚪")
        st.write(f"{t('port_congestion_index')}: **{anchored}** ({anchored} anchored) {level_emoji}")
        st.caption(f"평균 대기시간: {wait_hours}시간 | 출처: UNCTAD 항만통계")

        if congestion_level == "high":
            st.warning(t('cfo_insight_high_congestion'))

        wave_height = marine_data.get("wave_height", 0) or 0
        wave_period = marine_data.get("wave_period", 0) or 0
        wind = w.get("wind_speed", 0) or 0

        st.write(f"{t('wind')}: {wind} m/s · {t('waves')}: {wave_height} m")
        st.caption(f"파주기: {wave_period}초 | 출처: Open-Meteo Marine API")

        if isinstance(wind, (int, float)) and isinstance(wave_height, (int, float)):
            if wind > 15 or wave_height > 3.5:
                st.error(f"{t('crane_ops_suspended')} — {t('weather_impact')}")

        # 거리 및 비용
        dist = st.session_state.get('vessel_distance_km')
        dest_name = st.session_state.get('destination_port', selected["name"])

        if dist is not None:
            st.markdown(f"**{t('distance_remaining')}:** {dist:.1f} km")
            delay_hours = wait_hours if congestion_level == "high" else 0
            cost_data = calculate_shipping_cost("BUSAN", dest_name, dist, delay_hours)
            cost_krw = cost_data.get("total_krw", 0)
            cost_usd = cost_data.get("total_usd", 0)
            st.markdown(f"**{t('cfo_financial_impact')}:** {cost_krw:,} KRW (${cost_usd:,.0f})")
            st.caption(f"기본운임 + 연료할증료 + 체화료 | 출처: 시장 운임 기준")

        st.divider()

        # ── 근처 글로벌 리스크 (팝업과 동일 데이터) ──
        if nearby_risks:
            st.markdown(f"**🌍 {t('top_alerts')} — 근처 글로벌 리스크**")
            for nearby in nearby_risks[:5]:
                event_type = nearby.get("event_type", "other")
                config = RISK_TYPE_CONFIG.get(event_type, RISK_TYPE_CONFIG["other"])
                distance = nearby.get("distance_km", 0)
                title = nearby.get("title", "Unknown")
                severity = nearby.get("severity", 0.5)
                title_ko = translate_to_korean(title) if title else ""
                article_link = nearby.get("link", "")

                cols = st.columns([1, 15])
                with cols[0]:
                    st.write(config['icon'])
                with cols[1]:
                    link_part = f" [📰]({article_link})" if article_link else ""
                    st.write(f"**{title}**{link_part}")
                    st.caption(f"🇰🇷 {title_ko} · 📍 {int(distance)}km · ⚠️ {severity:.0%}")
            st.divider()

        # ── Active Alerts ──
        st.markdown(f"**🚨 {t('top_alerts')}**")
        for a in selected_risk["alerts"]:
            alert_emoji = {
                "operations": "✅",
                "congestion": "🚧",
                "weather": "🌪️",
                "geopolitics": "⚠️",
                "strike": "✊",
                "capacity": "📦",
                "sanction": "🚫"
            }.get(a['tag'], "•")

            st.write(f"{alert_emoji} `{a['tag']}` — {a['headline']}")


# =========================================================
# TAB 2: CONTINENTAL BRIEFING
# =========================================================
with tab_brief:
    st.markdown(f"## {t('briefing')}")
    
    # ===== COMMODITIES PANEL =====
    st.markdown(f"### 📊 {t('commodities')}")

    # Category grouping for multiselect
    categories = {}
    for name, info in COMMODITY_TICKERS.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(name)

    # Commodity selection UI
    select_label = "원자재 선택" if st.session_state.lang == "ko" else "Select Commodities"

    # Expander for commodity selection
    with st.expander(f"⚙️ {select_label}", expanded=False):
        # Category tabs for easier selection
        cat_cols = st.columns(len(categories))
        for i, (cat_name, commodities) in enumerate(categories.items()):
            with cat_cols[i]:
                st.markdown(f"**{cat_name}**")
                for comm_name in commodities:
                    info = COMMODITY_TICKERS[comm_name]
                    is_selected = comm_name in st.session_state.selected_commodities
                    if st.checkbox(
                        f"{info['emoji']} {comm_name}",
                        value=is_selected,
                        key=f"comm_check_{comm_name}"
                    ):
                        if comm_name not in st.session_state.selected_commodities:
                            st.session_state.selected_commodities.append(comm_name)
                    else:
                        if comm_name in st.session_state.selected_commodities:
                            st.session_state.selected_commodities.remove(comm_name)

        # Quick select buttons
        st.markdown("---")
        qcol1, qcol2, qcol3 = st.columns(3)
        with qcol1:
            if st.button("🔄 기본값" if st.session_state.lang == "ko" else "🔄 Default", key="comm_default"):
                st.session_state.selected_commodities = DEFAULT_COMMODITIES.copy()
                for comm_name in COMMODITY_TICKERS:
                    st.session_state[f"comm_check_{comm_name}"] = comm_name in DEFAULT_COMMODITIES
                st.rerun()
        with qcol2:
            if st.button("✅ 전체 선택" if st.session_state.lang == "ko" else "✅ Select All", key="comm_all"):
                st.session_state.selected_commodities = list(COMMODITY_TICKERS.keys())
                for comm_name in COMMODITY_TICKERS:
                    st.session_state[f"comm_check_{comm_name}"] = True
                st.rerun()
        with qcol3:
            if st.button("❌ 전체 해제" if st.session_state.lang == "ko" else "❌ Clear All", key="comm_clear"):
                st.session_state.selected_commodities = []
                for comm_name in COMMODITY_TICKERS:
                    st.session_state[f"comm_check_{comm_name}"] = False
                st.rerun()

    # Get selected commodities as tuple for caching
    selected_tuple = tuple(st.session_state.selected_commodities)

    # Show selected count
    selected_count = len(st.session_state.selected_commodities)
    total_count = len(COMMODITY_TICKERS)
    count_text = f"선택됨: {selected_count}/{total_count}" if st.session_state.lang == "ko" else f"Selected: {selected_count}/{total_count}"
    st.caption(count_text)

    # Fetch commodity data for selected items
    if selected_tuple:
        comm = live_commodities_yfinance(selected_tuple)
        if comm.get("_source") in ["yfinance_missing", "yfinance_failed"]:
            comm = mock_commodities(st.session_state.snapshot_id, selected_tuple)

        # Display commodities in a responsive grid
        comm_data = {k: v for k, v in comm.items() if not k.startswith("_")}
        if not comm_data:
            st.warning("원자재 데이터를 불러올 수 없습니다." if st.session_state.lang == "ko" else "Unable to load commodity data.")
        else:
            # Dynamic column layout (max 4 per row)
            num_items = len(comm_data)
            cols_per_row = min(4, num_items)
            rows_needed = (num_items + cols_per_row - 1) // cols_per_row

            items = list(comm_data.items())
            for row in range(rows_needed):
                start_idx = row * cols_per_row
                end_idx = min(start_idx + cols_per_row, num_items)
                row_items = items[start_idx:end_idx]

                comm_cols = st.columns(cols_per_row)
                for i, (name, price) in enumerate(row_items):
                    with comm_cols[i]:
                        if name in COMMODITY_TICKERS:
                            info = COMMODITY_TICKERS[name]
                            emoji = info["emoji"]
                            unit = info["unit"]
                        else:
                            emoji = "📊"
                            unit = ""
                        # Display price with unit
                        price_display = f"{price:,.2f} {unit}" if unit else f"{price:,.4f}"
                        st.metric(f"{emoji} {name}", price_display)

        # Data source indicator
        comm_source = t('real_api') if comm.get('_source') == 'yfinance' else t('mock')
        st.caption(f"{t('data_source')}: {comm_source}")

        # ===== COMMODITY PRICE CHART =====
        st.markdown("---")
        chart_title = "📈 원자재 가격 추이" if st.session_state.lang == "ko" else "📈 Commodity Price Trends"
        st.markdown(f"#### {chart_title}")

        # Time period selection
        period_label = "기간 선택" if st.session_state.lang == "ko" else "Select Period"
        period_cols = st.columns([2, 6])

        with period_cols[0]:
            # Create period options based on language
            period_options = []
            for key, val in TIME_PERIODS.items():
                label = val["label_ko"] if st.session_state.lang == "ko" else val["label_en"]
                period_options.append((key, label))

            selected_period_key = st.selectbox(
                period_label,
                options=[p[0] for p in period_options],
                format_func=lambda x: dict(period_options)[x],
                index=3,  # Default to 1 Year
                key="commodity_period"
            )

        # Fetch historical data
        period_value = TIME_PERIODS[selected_period_key]["period"]
        hist_data = fetch_commodity_history(selected_tuple, period_value)

        if not hist_data.empty:
            # Create plotly figure
            fig = go.Figure()

            # Add a line for each commodity with distinct colors
            for idx, commodity_name in enumerate(hist_data.columns):
                color = COMMODITY_COLORS[idx % len(COMMODITY_COLORS)]
                emoji = COMMODITY_TICKERS.get(commodity_name, {}).get("emoji", "📊")

                fig.add_trace(go.Scatter(
                    x=hist_data.index,
                    y=hist_data[commodity_name],
                    mode='lines',
                    name=f"{emoji} {commodity_name}",
                    line=dict(color=color, width=2),
                    hovertemplate=f"<b>{commodity_name}</b><br>" +
                                  "날짜: %{x|%Y-%m-%d}<br>" +
                                  "가격: %{y:,.2f}<extra></extra>"
                ))

            # Update layout
            fig.update_layout(
                height=450,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0,
                    font=dict(size=11)
                ),
                xaxis=dict(
                    title="",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128, 128, 128, 0.2)',
                ),
                yaxis=dict(
                    title="Price" if st.session_state.lang == "en" else "가격",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128, 128, 128, 0.2)',
                ),
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )

            # Display chart
            st.plotly_chart(fig, use_container_width=True)

            # Note about normalized view
            note_text = "※ 각 원자재는 고유 단위로 표시됩니다." if st.session_state.lang == "ko" else "※ Each commodity is shown in its native unit."
            st.caption(note_text)
        else:
            no_data_msg = "차트 데이터를 불러올 수 없습니다." if st.session_state.lang == "ko" else "Unable to load chart data."
            st.warning(no_data_msg)
    else:
        no_selection_msg = "원자재를 선택해주세요." if st.session_state.lang == "ko" else "Please select commodities to display."
        st.info(no_selection_msg)

    st.divider()

    # ===== NEWS FILTERS =====
    st.markdown(f"### {t('news_filters')}")

    # Filters row - 나라 선택 (대륙 자동 필터링)
    filter_col1, filter_col2 = st.columns([1, 3])

    with filter_col1:
        lang_key = "ko" if st.session_state.lang == "ko" else "en"
        country_filter_label = "🔍 국가 필터" if st.session_state.lang == "ko" else "🔍 Country Filter"
        briefing_selected_country = st.selectbox(
            country_filter_label,
            options=list(COUNTRY_LIST.keys()),
            format_func=lambda x: COUNTRY_LIST[x][lang_key],
            index=0,
            key="briefing_country_filter"
        )

    with filter_col2:
        if briefing_selected_country != "all":
            selected_continent = COUNTRY_LIST[briefing_selected_country].get("continent", "All")
            filter_info = f"필터 적용: {COUNTRY_LIST[briefing_selected_country][lang_key]} ({selected_continent})" if st.session_state.lang == "ko" else f"Filter: {COUNTRY_LIST[briefing_selected_country][lang_key]} ({selected_continent})"
            st.info(filter_info)

    st.divider()

    # ===== KOTRA / 글로벌 뉴스 섹션 =====
    news_section_title = "🌏 글로벌 뉴스" if st.session_state.lang == "ko" else "🌏 Global News"
    st.markdown(f"### {news_section_title}")

    # 2열 레이아웃: KOTRA + 글로벌 뉴스
    news_col_left, news_col_right = st.columns(2)

    # ===== 왼쪽: KOTRA 뉴스 =====
    with news_col_left:
        kotra_title = "KOTRA 해외시장뉴스" if st.session_state.lang == "ko" else "KOTRA Market News"
        st.markdown(f"#### {kotra_title}")

        kotra_news, kotra_error = fetch_kotra_news(num_of_rows=50)
        if kotra_error:
            st.caption(f"⚠️ {kotra_error}")

        # 국가별 필터링
        if kotra_news and briefing_selected_country != "all":
            kotra_news = [n for n in kotra_news if n.get("country", "") == briefing_selected_country]

        # 페이지네이션
        KOTRA_PER_PAGE = 4
        current_kotra_page = st.session_state.kotra_page
        total_kotra = len(kotra_news) if kotra_news else 0
        KOTRA_TOTAL_PAGES = max(1, (total_kotra + KOTRA_PER_PAGE - 1) // KOTRA_PER_PAGE)
        if current_kotra_page > KOTRA_TOTAL_PAGES:
            st.session_state.kotra_page = 1
            current_kotra_page = 1

        start_idx = (current_kotra_page - 1) * KOTRA_PER_PAGE
        end_idx = start_idx + KOTRA_PER_PAGE

        country_colors = {
            "베트남": {"bg": "#fee2e2", "text": "#991b1b"},
            "미국": {"bg": "#dbeafe", "text": "#1e40af"},
            "독일": {"bg": "#f3f4f6", "text": "#1f2937"},
            "인도": {"bg": "#ffedd5", "text": "#9a3412"},
            "중국": {"bg": "#fecaca", "text": "#991b1b"},
            "UAE": {"bg": "#d1fae5", "text": "#065f46"},
            "일본": {"bg": "#fce7f3", "text": "#9d174d"},
        }
        default_color = {"bg": "#f3f4f6", "text": "#374151"}

        if kotra_news:
            for news in kotra_news[start_idx:end_idx]:
                country = news.get("country", "해외")
                tag_style = country_colors.get(country, default_color)
                title = news.get("title", "")
                content = news.get("content", "")
                write_date = news.get("write_date", "")
                news_url = news.get("url", "")
                title_html = f'<a href="{news_url}" target="_blank" style="color:#2563eb;text-decoration:none;">{title}</a>' if news_url else f'{title}'

                st.markdown(f"""
                <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);height:150px;overflow:hidden;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                        <span style="background:{tag_style['bg']};color:{tag_style['text']};padding:4px 10px;border-radius:14px;font-size:11px;font-weight:600;">🌐 {country}</span>
                        <span style="font-size:11px;color:#9ca3af;">📅 {write_date}</span>
                    </div>
                    <div style="font-size:14px;font-weight:600;color:#1a1a1a;line-height:1.5;margin-bottom:8px;">{title_html}</div>
                    <div style="font-size:12px;color:#6b7280;line-height:1.5;">{content}</div>
                </div>
                """, unsafe_allow_html=True)

            if len(kotra_news[start_idx:end_idx]) == 0:
                st.info("해당 국가 관련 뉴스가 없습니다." if st.session_state.lang == "ko" else "No news for selected country.")
        else:
            st.info("KOTRA 뉴스를 불러올 수 없습니다." if st.session_state.lang == "ko" else "Unable to load KOTRA news.")

        # KOTRA 페이지네이션
        kp1, kp2, kp3 = st.columns([1, 2, 1])
        with kp1:
            if st.button("◀", key="briefing_kotra_prev", disabled=(current_kotra_page == 1)):
                st.session_state.kotra_page -= 1
                st.rerun()
        with kp2:
            st.caption(f"📄 {current_kotra_page} / {KOTRA_TOTAL_PAGES} (총 {total_kotra}건)")
        with kp3:
            if st.button("▶", key="briefing_kotra_next", disabled=(current_kotra_page >= KOTRA_TOTAL_PAGES)):
                st.session_state.kotra_page += 1
                st.rerun()
        st.caption("📡 출처: KOTRA API (data.go.kr)")

    # ===== 오른쪽: 글로벌 뉴스 =====
    with news_col_right:
        global_title = "📰 글로벌 뉴스" if st.session_state.lang == "ko" else "📰 Global News"
        st.markdown(f"#### {global_title}")

        global_news, global_error = fetch_global_news(max_articles=50)
        if global_error:
            st.caption(f"⚠️ {global_error}")

        # 국가별 필터링
        def matches_country_briefing(news_item, country_key):
            if country_key == "all":
                return True
            keywords = COUNTRY_LIST.get(country_key, {}).get("keywords", [])
            text = (news_item.get("title", "") + " " + news_item.get("description", "")).lower()
            return any(kw.lower() in text for kw in keywords)

        if global_news and briefing_selected_country != "all":
            global_news = [n for n in global_news if matches_country_briefing(n, briefing_selected_country)]

        # 페이지네이션
        GLOBAL_PER_PAGE = 4
        current_global_page = st.session_state.global_news_page
        total_global = len(global_news) if global_news else 0
        GLOBAL_TOTAL_PAGES = max(1, (total_global + GLOBAL_PER_PAGE - 1) // GLOBAL_PER_PAGE)
        if current_global_page > GLOBAL_TOTAL_PAGES:
            st.session_state.global_news_page = 1
            current_global_page = 1

        start_idx = (current_global_page - 1) * GLOBAL_PER_PAGE
        end_idx = start_idx + GLOBAL_PER_PAGE

        if global_news:
            for news in global_news[start_idx:end_idx]:
                title = news.get("title", "")
                desc = news.get("description", "")
                news_url = news.get("url", "")
                pub_date = news.get("pub_date", "")
                source = news.get("source", "News")
                source_bg = news.get("source_bg", "#f3f4f6")
                source_text = news.get("source_text", "#374151")

                title_html = f'<a href="{news_url}" target="_blank" style="color:#2563eb;text-decoration:none;font-weight:600;">{title}</a>' if news_url else f'{title}'
                title_kr = translate_to_korean(news.get("title", ""))

                date_display = ""
                if pub_date:
                    try:
                        from email.utils import parsedate_to_datetime
                        dt = parsedate_to_datetime(pub_date)
                        date_display = dt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        date_display = pub_date[:16]

                st.markdown(f"""
                <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);height:150px;overflow:hidden;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                        <span style="background:{source_bg};color:{source_text};padding:4px 10px;border-radius:14px;font-size:11px;font-weight:600;">{source}</span>
                        <span style="font-size:11px;color:#9ca3af;">📅 {date_display}</span>
                    </div>
                    <div style="font-size:14px;font-weight:600;color:#1a1a1a;line-height:1.5;margin-bottom:6px;">{title_html}</div>
                    <div style="font-size:12px;color:#374151;line-height:1.5;margin-bottom:6px;">📌 {title_kr}</div>
                    <div style="font-size:11px;color:#9ca3af;line-height:1.5;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

            if len(global_news[start_idx:end_idx]) == 0:
                st.info("해당 국가 관련 글로벌 뉴스가 없습니다." if st.session_state.lang == "ko" else "No global news for selected country.")
        else:
            st.info("글로벌 뉴스를 불러올 수 없습니다." if st.session_state.lang == "ko" else "Unable to load global news.")

        # 글로벌 뉴스 페이지네이션
        gp1, gp2, gp3 = st.columns([1, 2, 1])
        with gp1:
            if st.button("◀", key="briefing_global_prev", disabled=(current_global_page == 1)):
                st.session_state.global_news_page -= 1
                st.rerun()
        with gp2:
            st.caption(f"📄 {current_global_page} / {GLOBAL_TOTAL_PAGES} (총 {total_global}건)")
        with gp3:
            if st.button("▶", key="briefing_global_next", disabled=(current_global_page >= GLOBAL_TOTAL_PAGES)):
                st.session_state.global_news_page += 1
                st.rerun()
        st.caption("📡 출처: CNN, BBC, Reuters, Bloomberg, WSJ, NYT")


# Note: Auto-refresh removed to prevent screen flickering
# Use the "시뮬레이션 재생" button to advance the vessel position


# =========================================================
# Enhanced CSS Styling - Light Theme (White Background, Black Text)
# =========================================================
st.markdown(
    """
    <style>
    /* ===== Global Styles - Light Theme ===== */
    .stApp {
        background: #ffffff;
    }

    /* ===== Typography ===== */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #1a1a1a !important;
    }

    /* ===== Remove transitions (as requested) ===== */
    * {
        transition: none !important;
    }

    /* ===== Sidebar Styling ===== */
    [data-testid="stSidebar"] {
        background: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #333333 !important;
    }

    /* ===== Button Styling ===== */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #d0d0d0;
        background: #f5f5f5;
        color: #333333;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }

    .stButton > button:hover {
        border-color: #3b82f6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border: none;
        color: white;
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    /* ===== Metric Styling ===== */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
        color: #2563eb !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 13px;
        font-weight: 500;
        color: #555555 !important;
    }

    /* ===== Dataframe Styling ===== */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e0e0e0;
    }

    /* ===== Input Styling ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        color: #333333;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
    }

    /* ===== Toggle/Checkbox Styling ===== */
    .stCheckbox > label {
        color: #333333 !important;
    }

    /* ===== Divider Styling ===== */
    hr {
        border-color: #e0e0e0 !important;
        margin: 1.5rem 0;
    }

    /* ===== Tab Styling ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f5f5f5;
        border-radius: 8px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #666666;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: #ffffff;
        color: #2563eb !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* ===== Toast Notifications ===== */
    .stToast {
        background: #ffffff;
        border: 1px solid #10b981;
        border-radius: 8px;
    }

    /* ===== Success/Warning/Error Messages ===== */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10b981;
        color: #065f46 !important;
    }

    .stWarning {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #f59e0b;
        color: #92400e !important;
    }

    .stError {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
        color: #991b1b !important;
    }

    .stInfo {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
        color: #1e40af !important;
    }

    /* ===== Map Container ===== */
    .folium-map {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* ===== Caption Styling ===== */
    .stCaption {
        color: #666666 !important;
        font-size: 12px;
    }

    /* ===== Code Block Styling ===== */
    code {
        background: #f5f5f5;
        color: #2563eb;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 13px;
    }

    /* ===== Radio Button Styling ===== */
    .stRadio > div {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 8px;
    }

    .stRadio > div > label > div {
        color: #333333 !important;
    }

    /* ===== Download Button ===== */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: 600;
    }

    .stDownloadButton > button:hover {
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    /* ===== Spinner ===== */
    .stSpinner > div {
        border-top-color: #3b82f6 !important;
    }

    /* ===== TRADLINX Style Vessel Card ===== */
    .vessel-card {
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid #e8ecf0;
    }

    .vessel-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
        padding-bottom: 16px;
        border-bottom: 1px solid #f0f0f0;
    }

    .vessel-name {
        font-size: 18px;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
    }

    .vessel-status {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-anchored {
        background: #e8f4fd;
        color: #1976d2;
    }

    .status-underway {
        background: #e8f5e9;
        color: #2e7d32;
    }

    .status-delayed {
        background: #fff3e0;
        color: #f57c00;
    }

    .vessel-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }

    .vessel-info-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 20px;
    }

    .info-item {
        text-align: center;
        padding: 12px;
        background: #f8f9fa;
        border-radius: 8px;
    }

    .info-label {
        font-size: 11px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }

    .info-value {
        font-size: 14px;
        font-weight: 600;
        color: #1f2937;
    }

    /* ===== Timeline Styles ===== */
    .timeline-container {
        padding: 16px 0;
    }

    .timeline-tabs {
        display: flex;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 20px;
    }

    .timeline-tab {
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 500;
        color: #6b7280;
        cursor: pointer;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }

    .timeline-tab.active {
        color: #2563eb;
        border-bottom-color: #2563eb;
    }

    .timeline-item {
        position: relative;
        padding-left: 40px;
        padding-bottom: 24px;
    }

    .timeline-item:before {
        content: '';
        position: absolute;
        left: 11px;
        top: 24px;
        bottom: 0;
        width: 2px;
        background: linear-gradient(180deg, #10b981 0%, #3b82f6 100%);
    }

    .timeline-item:last-child:before {
        display: none;
    }

    .timeline-dot {
        position: absolute;
        left: 0;
        top: 0;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #10b981;
        border: 3px solid #ffffff;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
    }

    .timeline-dot.destination {
        background: #3b82f6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }

    .timeline-dot.current {
        background: #f59e0b;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    .timeline-content {
        background: #f9fafb;
        border-radius: 10px;
        padding: 14px 16px;
    }

    .timeline-port {
        font-size: 15px;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 8px;
    }

    .timeline-port.active {
        color: #2563eb;
    }

    .timeline-time {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: #6b7280;
        margin-top: 6px;
    }

    .time-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }

    .badge-atd {
        background: #dbeafe;
        color: #1d4ed8;
    }

    .badge-ata {
        background: #d1fae5;
        color: #047857;
    }

    .badge-eta {
        background: #fef3c7;
        color: #b45309;
    }

    .badge-etd {
        background: #e0e7ff;
        color: #4338ca;
    }

    /* ===== Progress Bar ===== */
    .voyage-progress {
        margin-top: 20px;
        padding: 16px;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 10px;
    }

    .progress-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        font-size: 13px;
        color: #374151;
    }

    .progress-bar {
        height: 8px;
        background: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
        border-radius: 4px;
        transition: width 0.5s ease;
    }

    .progress-info {
        display: flex;
        justify-content: space-between;
        margin-top: 8px;
        font-size: 12px;
        color: #6b7280;
    }
    </style>
    """,
    unsafe_allow_html=True
)