import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
from fpdf import FPDF
import requests # For making HTTP requests to Gemini API
import json # For handling JSON responses

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="Dashboard Pemasaran Gemini")

# Custom CSS for styling (similar to React app's Tailwind-like styling)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #333;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 9999px; /* Tailwind rounded-full */
            padding: 10px 20px;
            font-weight: bold;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* Tailwind shadow-lg */
            transition: all 0.3s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); /* Tailwind shadow-xl */
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .stMarkdown h1 {
            color: #4338CA; /* Indigo-700 */
            text-align: center;
            font-size: 2.5rem; /* text-4xl */
            font-weight: 700; /* font-bold */
            margin-bottom: 2rem;
            border-radius: 0.5rem; /* rounded-lg */
            padding: 0.5rem;
        }
        .stMarkdown h2 {
            color: #312E81; /* Indigo-800 or Blue-800 or Purple-800 */
            font-size: 1.5rem; /* text-2xl */
            font-weight: 600; /* font-semibold */
            margin-bottom: 1rem;
        }
        .stMarkdown h3 {
            color: #1F2937; /* Gray-900 */
            font-size: 1.25rem; /* text-xl */
            font-weight: 500; /* font-medium */
            text-align: center;
            margin-bottom: 0.75rem;
        }
        .stMarkdown h4 {
            color: #374151; /* Gray-800 */
            font-size: 1rem; /* text-md */
            font-weight: 600; /* font-semibold */
            margin-bottom: 0.5rem;
        }
        .stMarkdown ul {
            list-style-type: disc;
            margin-left: 1.25rem;
            color: #4B5563; /* Gray-700 */
        }
        .stMarkdown li {
            margin-bottom: 0.25rem;
        }
        .stAlert {
            border-radius: 0.5rem;
        }
        .stFileUploader {
            border-radius: 0.5rem;
        }
        .stSelectbox>div>div {
            border-radius: 0.375rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        .stDateInput>div>div {
            border-radius: 0.375rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        .container-bg-indigo-50 {
            background-color: #EEF2FF; /* indigo-50 */
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06); /* shadow-inner */
            margin-bottom: 2rem;
        }
        .container-bg-blue-50 {
            background-color: #EFF6FF; /* blue-50 */
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
            margin-bottom: 2rem;
        }
        .container-bg-purple-50 {
            background-color: #F5F3FF; /* purple-50 */
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
            margin-bottom: 2rem;
        }
        .chart-card {
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); /* shadow-md */
            transition: box-shadow 0.3s ease-in-out;
            margin-bottom: 1rem;
        }
        .chart-card:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-lg */
        }
        .summary-button button {
            background-color: #8B5CF6; /* purple-600 */
            color: white;
            border-radius: 9999px;
            padding: 8px 24px;
            font-weight: bold;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease-in-out;
        }
        .summary-button button:hover:not(:disabled) {
            background-color: #7C3AED; /* purple-700 */
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .summary-button button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
    </style>
""", unsafe_allow_html=True)

# Function to clean data
def clean_data(df):
    # Convert 'Date' to datetime, coerce errors to NaT
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Fill empty 'Engagements' with 0, convert to int
    df['Engagements'] = pd.to_numeric(df['Engagements'], errors='coerce').fillna(0).astype(int)

    # Fill missing categorical data with 'Unknown' or 'Neutral' or 'Other'
    df['Platform'] = df['Platform'].fillna('Unknown')
    df['Sentiment'] = df['Sentiment'].fillna('Netral')
    # FIX: Changed 'Media Type' to 'Media_Type' to match CSV header
    df['Media_Type'] = df['Media_Type'].fillna('Lainnya')
    df['Location'] = df['Location'].fillna('Unknown')

    return df

# Static insights for each chart (translated to Indonesian)
def get_insights(chart_name):
    insights = []
    if chart_name == 'sentiment':
        insights = [
            '1. Identifikasi sentimen dominan: Porsi sentimen positif yang besar menunjukkan konten yang sukses.',
            '2. Analisis sentimen negatif: Porsi negatif yang signifikan menunjukkan area untuk perbaikan dalam konten atau produk.',
            '3. Pantau sentimen netral: Persentase netral yang tinggi mungkin berarti konten tidak terlalu beresonansi, memberikan kesempatan untuk menyempurnakan pesan.',
        ]
    elif chart_name == 'engagement_trend':
        insights = [
            '1. Temukan puncak engagement: Lonjakan menunjukkan kampanye atau rilis konten yang sangat sukses.',
            '2. Identifikasi palung engagement: Penurunan menunjukkan kelelahan konten atau kampanye yang kurang efektif selama periode tersebut.',
            '3. Amati musiman: Pola berulang mungkin mengungkapkan tren mingguan, bulanan, atau tahunan yang dapat menginformasikan penjadwalan di masa mendatang.',
        ]
    elif chart_name == 'platform':
        insights = [
            '1. Temukan platform berkinerja terbaik: Fokuskan sumber daya di mana engagement tertinggi.',
            '2. Identifikasi platform berkinerja rendah: Evaluasi strategi konten atau penargetan audiens untuk platform ini.',
            '3. Temukan tren spesifik platform: Platform yang berbeda mungkin menunjukkan pola engagement yang unik, membutuhkan konten yang disesuaikan.',
        ]
    elif chart_name == 'media_type':
        insights = [
            '1. Tentukan format media yang disukai: Investasikan lebih banyak pada jenis media yang menghasilkan engagement lebih tinggi.',
            '2. Diversifikasi strategi konten: Jika satu jenis media mendominasi, pertimbangkan untuk bereksperimen dengan yang lain untuk menjangkau audiens baru.',
            '3. Nilai efektivitas biaya: Bandingkan engagement berbagai jenis media dengan biaya produksinya.',
        ]
    elif chart_name == 'locations':
        insights = [
            '1. Identifikasi pasar geografis utama: Fokuskan upaya pemasaran pada lokasi dengan engagement tinggi.',
            '2. Temukan pasar yang belum dimanfaatkan: Lokasi dengan engagement lebih rendah mungkin mewakili peluang untuk kampanye yang ditargetkan.',
            '3. Pahami preferensi regional: Lokasi yang berbeda mungkin merespons lebih baik terhadap tema atau bahasa konten tertentu.',
        ]
    return "\n".join([f"- {i}" for i in insights])

# Function to generate campaign summary using Gemini API
def generate_gemini_summary(api_key, filtered_data_metrics):
    if not api_key:
        return "Kunci API Gemini tidak ada. Silakan masukkan kunci API."

    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    # Extract metrics for the prompt
    sentiment_counts = filtered_data_metrics['sentiment_counts']
    top_sentiment = sentiment_counts.index[0] if not sentiment_counts.empty else 'Tidak Diketahui'

    platform_engagements = filtered_data_metrics['platform_engagements']
    top_platform = platform_engagements.index[0] if not platform_engagements.empty else 'Tidak Diketahui'

    media_type_counts = filtered_data_metrics['media_type_counts']
    top_media_type = media_type_counts.index[0] if not media_type_counts.empty else 'Tidak Diketahui'

    location_engagements = filtered_data_metrics['location_engagements']
    top_locations = location_engagements.head(2).index.tolist() if not location_engagements.empty else ['Tidak Diketahui']

    engagement_trend = filtered_data_metrics['engagement_trend']
    max_engagement_date = engagement_trend.loc[engagement_trend['Total Engagements'].idxmax()]['Date'].strftime('%Y-%m-%d') if not engagement_trend.empty else 'tanggal tidak diketahui'

    prompt = f"""Berdasarkan data kampanye pemasaran berikut:
- Sentimen paling dominan: {top_sentiment}
- Platform dengan engagement tertinggi: {top_platform}
- Tipe media yang paling banyak digunakan: {top_media_type}
- Lokasi dengan engagement tertinggi: {', '.join(top_locations)}
- Tanggal dengan engagement puncak: {max_engagement_date}

Buat ringkasan strategi kampanye pemasaran yang komprehensif, menyoroti tindakan utama dan rekomendasi yang dapat ditindaklanjutifor meningkatkan kinerja. Fokus pada pemanfaatan kekuatan, mitigasi kelemahan, dan kapitalisasi peluang yang disorot oleh data. Ringkasan ini harus berisi sekitar 3-5 poin utama. Gunakan bahasa Indonesia.
"""

    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {"contents": chat_history}

    try:
        response = requests.post(API_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        result = response.json()

        if result.get('candidates') and len(result['candidates']) > 0 and \
           result['candidates'][0].get('content') and \
           result['candidates'][0]['content'].get('parts') and \
           len(result['candidates'][0]['content']['parts']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Gagal menghasilkan ringkasan. Respons tidak terstruktur atau kosong."
    except requests.exceptions.RequestException as e:
        return f"Error memanggil API Gemini: {e}. Pastikan kunci API Anda benar dan memiliki izin."
    except json.JSONDecodeError:
        return "Error: Respons API Gemini bukan JSON yang valid."
    except Exception as e:
        return f"Terjadi kesalahan yang tidak terduga: {e}"

# --- Streamlit App Layout ---

st.title("Dashboard Pemasaran Gemini")

# File Upload Section
st.markdown('<div class="container-bg-indigo-50">', unsafe_allow_html=True)
st.markdown('<h2>Unggah Data CSV</h2>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Unggah file CSV Anda di sini", type=["csv"])
st.markdown('</div>', unsafe_allow_html=True)

df = None
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df = clean_data(df.copy()) # Clean a copy of the dataframe
        st.success("CSV berhasil dimuat dan diproses!")
    except Exception as e:
        st.error(f"Error memuat atau memproses CSV: {e}")

# Initialize session state for API key and summary
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ''
if 'campaign_summary' not in st.session_state:
    st.session_state.campaign_summary = "Tekan 'Hasilkan Ringkasan' untuk mendapatkan ringkasan strategi kampanye yang didukung AI."
if 'summary_error' not in st.session_state:
    st.session_state.summary_error = ''

if df is not None and not df.empty:
    # --- Filters Section ---
    st.markdown('<div class="container-bg-blue-50">', unsafe_allow_html=True)
    st.markdown('<h2>Filter Data</h2>', unsafe_allow_html=True)

    # Get unique values for filters
    all_platforms = ['Semua'] + sorted(df['Platform'].unique().tolist())
    all_sentiments = ['Semua'] + sorted(df['Sentiment'].unique().tolist())
    # FIX: Changed 'Media Type' to 'Media_Type' for filter options
    all_media_types = ['Semua'] + sorted(df['Media_Type'].unique().tolist())
    all_locations = ['Semua'] + sorted(df['Location'].unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_platform = st.selectbox("Platform", all_platforms)
    with col2:
        selected_sentiment = st.selectbox("Sentimen", all_sentiments)
    with col3:
        selected_media_type = st.selectbox("Tipe Media", all_media_types)

    col4, col5 = st.columns(2)
    with col4:
        selected_location = st.selectbox("Lokasi", all_locations)
    with col5:
        # Date range filter
        min_date = df['Date'].min() if not df['Date'].isnull().all() else pd.to_datetime('2020-01-01')
        max_date = df['Date'].max() if not df['Date'].isnull().all() else pd.to_datetime('2025-12-31')

        # Ensure min_date and max_date are not NaT
        if pd.isna(min_date):
            min_date = pd.to_datetime('2020-01-01')
        if pd.isna(max_date):
            max_date = pd.to_datetime('2025-12-31')

        try:
            date_range = st.date_input(
                "Rentang Tanggal",
                value=(min_date.date(), max_date.date()), # Pass datetime.date objects
                min_value=min_date.date(),
                max_value=max_date.date()
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
                # Ensure end_date includes the entire day
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            else:
                start_date = min_date
                end_date = max_date
        except Exception as e:
            st.warning(f"Tidak dapat memparse rentang tanggal, menampilkan semua tanggal: {e}")
            start_date = min_date
            end_date = max_date


    # Apply filters
    filtered_df = df.copy()
    if selected_platform != 'Semua':
        filtered_df = filtered_df[filtered_df['Platform'] == selected_platform]
    if selected_sentiment != 'Semua':
        filtered_df = filtered_df[filtered_df['Sentiment'] == selected_sentiment]
    # FIX: Changed 'Media Type' to 'Media_Type' when applying filter
    if selected_media_type != 'Semua':
        filtered_df = filtered_df[filtered_df['Media_Type'] == selected_media_type]
    if selected_location != 'Semua':
        filtered_df = filtered_df[filtered_df['Location'] == selected_location]

    # Date filtering
    filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

    st.markdown('</div>', unsafe_allow_html=True) # Close filters div

    # --- Dashboard Content ---
    st.markdown('<div class="chart-section">', unsafe_allow_html=True) # Wrapper for charts

    st.markdown('<h2>Ikhtisar Dashboard</h2>', unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("Tidak ada data yang cocok dengan kriteria filter saat ini. Coba sesuaikan filter Anda.")
        # Clear summary if no data
        st.session_state.campaign_summary = "Tidak ada data yang difilter untuk menghasilkan ringkasan."
        st.session_state.summary_error = ''
    else:
        # Create a list to store Plotly figures for PDF export
        figs_for_pdf = []
        metrics_for_gemini = {}

        # 1. Sentiment Breakdown (Pie Chart)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<h3>Analisis Sentimen</h3>', unsafe_allow_html=True)
        sentiment_counts = filtered_df['Sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']
        fig_sentiment = px.pie(sentiment_counts, values='Count', names='Sentiment',
                                 title='Analisis Sentimen', hole=0.4,
                                 color_discrete_map={'Positive':'#4CAF50', 'Netral':'#FFC107', 'Negative':'#F44336'})
        fig_sentiment.update_traces(textinfo='percent+label', pull=[0.05 if s == 'Positive' else 0 for s in sentiment_counts['Sentiment']])
        fig_sentiment.update_layout(height=350, margin=dict(t=50, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig_sentiment, use_container_width=True)
        st.markdown('<h4>Wawasan Utama:</h4>')
        st.markdown(get_insights('sentiment'), unsafe_allow_html=True)
        figs_for_pdf.append(fig_sentiment)
        metrics_for_gemini['sentiment_counts'] = sentiment_counts.set_index('Sentiment')['Count']
        st.markdown('</div>', unsafe_allow_html=True)


        # 2. Engagement Trend over Time (Line Chart)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<h3>Tren Engagement Seiring Waktu</h3>', unsafe_allow_html=True)
        engagement_trend = filtered_df.groupby(filtered_df['Date'].dt.date)['Engagements'].sum().reset_index()
        engagement_trend.columns = ['Date', 'Total Engagements']
        fig_engagement_trend = px.line(engagement_trend, x='Date', y='Total Engagements',
                                         title='Tren Engagement Seiring Waktu')
        fig_engagement_trend.update_traces(mode='lines+markers', line=dict(color='#2196F3', width=2), marker=dict(size=6))
        fig_engagement_trend.update_layout(height=350, margin=dict(t=50, b=80, l=60, r=20))
        st.plotly_chart(fig_engagement_trend, use_container_width=True)
        st.markdown('<h4>Wawasan Utama:</h4>')
        st.markdown(get_insights('engagement_trend'), unsafe_allow_html=True)
        figs_for_pdf.append(fig_engagement_trend)
        metrics_for_gemini['engagement_trend'] = engagement_trend
        st.markdown('</div>', unsafe_allow_html=True)


        # 3. Platform Engagements (Bar Chart)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<h3>Engagement Berdasarkan Platform</h3>', unsafe_allow_html=True)
        platform_engagements = filtered_df.groupby('Platform')['Engagements'].sum().reset_index()
        platform_engagements = platform_engagements.sort_values(by='Engagements', ascending=False)
        fig_platform = px.bar(platform_engagements, x='Platform', y='Engagements',
                                 title='Engagement Berdasarkan Platform', color_discrete_sequence=['#FF9800'])
        fig_platform.update_layout(height=350, margin=dict(t=50, b=60, l=60, r=20))
        st.plotly_chart(fig_platform, use_container_width=True)
        st.markdown('<h4>Wawasan Utama:</h4>')
        st.markdown(get_insights('platform'), unsafe_allow_html=True)
        figs_for_pdf.append(fig_platform)
        metrics_for_gemini['platform_engagements'] = platform_engagements.set_index('Platform')['Engagements']
        st.markdown('</div>', unsafe_allow_html=True)


        # 4. Media Type Mix (Pie Chart)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<h3>Distribusi Tipe Media</h3>', unsafe_allow_html=True)
        # FIX: Changed 'Media Type' to 'Media_Type' for value_counts
        media_type_counts = filtered_df['Media_Type'].value_counts().reset_index()
        media_type_counts.columns = ['Media Type', 'Count'] # Column name for display in chart remains 'Media Type'
        fig_media_type = px.pie(media_type_counts, values='Count', names='Media Type',
                                 title='Distribusi Tipe Media', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_media_type.update_traces(textinfo='percent+label')
        fig_media_type.update_layout(height=350, margin=dict(t=50, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig_media_type, use_container_width=True)
        st.markdown('<h4>Wawasan Utama:</h4>')
        st.markdown(get_insights('media_type'), unsafe_allow_html=True)
        figs_for_pdf.append(fig_media_type)
        # Use 'Media Type' for index in metrics_for_gemini to match prompt expectations
        metrics_for_gemini['media_type_counts'] = media_type_counts.set_index('Media Type')['Count']
        st.markdown('</div>', unsafe_allow_html=True)


        # 5. Top 5 Locations (Bar Chart)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<h3>Top 5 Lokasi Berdasarkan Engagement</h3>', unsafe_allow_html=True)
        location_engagements = filtered_df.groupby('Location')['Engagements'].sum().reset_index()
        top_5_locations = location_engagements.sort_values(by='Engagements', ascending=False).head(5)
        fig_locations = px.bar(top_5_locations, x='Location', y='Engagements',
                                 title='Top 5 Lokasi Berdasarkan Engagement', color_discrete_sequence=['#673AB7'])
        fig_locations.update_layout(height=350, margin=dict(t=50, b=60, l=60, r=20))
        st.plotly_chart(fig_locations, use_container_width=True)
        st.markdown('<h4>Wawasan Utama:</h4>')
        st.markdown(get_insights('locations'), unsafe_allow_html=True)
        figs_for_pdf.append(fig_locations)
        metrics_for_gemini['location_engagements'] = location_engagements.set_index('Location')['Engagements'].sort_values(ascending=False)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Close charts section wrapper

    # --- Campaign Strategy Summary - Now dynamic with Gemini API ---
    st.markdown('<div class="container-bg-purple-50">', unsafe_allow_html=True)
    st.markdown('<h2>Ringkasan Strategi Kampanye (Didukung AI)</h2>', unsafe_allow_html=True)
    st.session_state.gemini_api_key = st.text_input(
        "Kunci API Gemini",
        type="password",
        value="AIzaSyAuIF8FP5E9FkOG7AGHZ_oEVCJNH3N25M0", # Pre-fill with the provided API key
        placeholder="Masukkan kunci API Gemini Anda di sini"
    )

    if st.button("Hasilkan Ringkasan", key="generate_summary_button"):
        if not st.session_state.gemini_api_key:
            st.session_state.summary_error = 'Kunci API Gemini tidak ada. Silakan masukkan kunci API.'
            st.session_state.campaign_summary = "Ringkasan gagal dihasilkan karena kunci API tidak ada."
        elif filtered_df.empty:
            st.session_state.summary_error = 'Tidak ada data yang difilter untuk menghasilkan ringkasan.'
            st.session_state.campaign_summary = "Ringkasan gagal dihasilkan karena tidak ada data yang difilter."
        else:
            with st.spinner('Menghasilkan ringkasan strategi kampanye...'):
                st.session_state.summary_error = ''
                summary = generate_gemini_summary(st.session_state.gemini_api_key, metrics_for_gemini)
                st.session_state.campaign_summary = summary
                if "Error" in summary or "Gagal" in summary:
                    st.session_state.summary_error = summary

    if st.session_state.summary_error:
        st.error(st.session_state.summary_error)

    st.markdown(f'<p class="text-gray-700 leading-relaxed mt-4 whitespace-pre-wrap">{st.session_state.campaign_summary}</p>', unsafe_allow_html=True)
    st.markdown("""
    <p class="text-sm text-gray-500 italic mt-4">
        Ringkasan ini dihasilkan secara dinamis menggunakan API Gemini.
    </p>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Export PDF Button ---
    @st.cache_data
    def create_pdf(figures, summary_text):
        pdf = FPDF(format='A4')
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(200, 10, txt="Dashboard Pemasaran Gemini", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.ln(10)

        # Add strategy summary
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 5, txt="Ringkasan Strategi Kampanye (Didukung AI):", align='L')
        pdf.set_font("Arial", '', 10)
        pdf.ln(2)
        pdf.multi_cell(0, 5, txt=summary_text, align='L')
        pdf.ln(10)

        # Add images of plots
        for i, fig in enumerate(figures):
            # For PDF export, convert Plotly figure to static image bytes
            img_bytes = fig.to_image(format="png", width=800, height=400, scale=2) # Higher resolution for PDF
            try:
                # Add image to PDF. Adjust width to fit A4.
                # A4 width is 210mm. If image is 800px, 800px / 3.7795 = ~211mm. Too wide.
                # Let's scale it to fit within 190mm with margins (A4 is 210mm wide)
                pdf.image(BytesIO(img_bytes), x=10, w=190)
                pdf.ln(5) # Small line break after each image
            except Exception as e:
                st.error(f"Error menambahkan gambar ke PDF: {e}")
                pdf.multi_cell(0, 5, txt=f"Error memuat gambar grafik: {e}", align='C')
                pdf.ln(5)
            # Add a new page if the next content won't fit well or after every 2 charts
            if (i + 1) % 2 == 0 or pdf.get_y() > (pdf.h - 60): # If less than 60mm space left
                pdf.add_page()

        return pdf.output(dest='S').encode('latin1') # Return as bytes

    if st.button("Ekspor Dashboard sebagai PDF"):
        if figs_for_pdf:
            with st.spinner("Menghasilkan PDF..."):
                # Pass current summary text to PDF function
                pdf_output = create_pdf(figs_for_pdf, st.session_state.campaign_summary)
                st.download_button(
                    label="Unduh PDF",
                    data=pdf_output,
                    file_name="dashboard_pemasaran_gemini.pdf",
                    mime="application/pdf"
                )
                st.success("PDF berhasil dibuat!")
        else:
            st.warning("Tidak ada grafik untuk diekspor. Harap unggah data dan terapkan filter terlebih dahulu.")

else:
    st.info("Harap unggah file CSV untuk memulai.")
