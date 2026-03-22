import streamlit as st
import re
import pandas as pd

# 페이지 설정 및 글자 크기 통일용 CSS 추가
st.set_page_config(page_title="주식 이평선 분석기 v13", layout="centered")
st.markdown("""
    <style>
    /* 전체 글자 크기를 작게 통일 (분석 박스 수준) */
    html, body, [class*="st-"] {
        font-size: 14px !important;
    }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.1rem !important; }
    /* 간격 축소 */
    .stTextInput, .stNumberInput { margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

if 'prices' not in st.session_state:
    st.session_state.prices = [0.0] * 8

st.title("📈 주식 이평선 분석기 v13")

# --- [1] 데이터 입력 구간 ---
st.subheader("1. 데이터 입력")

def sync_data():
    raw_text = st.session_state.raw_data_input
    if raw_text:
        lines = re.split(r'[\n\r\t]+', raw_text.strip())
        extracted = []
        for line in lines:
            clean = line.replace(',', '').strip()
            for part in clean.split():
                match = re.search(r'\d+', part)
                if match: extracted.append(float(match.group()))
        for i in range(8):
            if i < len(extracted):
                st.session_state[f"num_input_{i}"] = extracted[i]
                st.session_state.prices[i] = extracted[i]

st.text_area("엑셀 데이터를 여기에 붙여넣으세요:", height=80, key="raw_data_input", on_change=sync_data)

col1, col2 = st.columns(2)
final_prices = []

for i in range(8):
    label = "0일차*" if i == 0 else f"D-{i}"
    if f"num_input_{i}" not in st.session_state:
        st.session_state[f"num_input_{i}"] = 0.0

    curr_val = st.session_state[f"num_input_{i}"]
    # 동적 Step 로직 (1원 단위 소선 배려 반영)
    if curr_val == 0: curr_step = 100.0
    elif curr_val % 10 != 0: curr_step = 5.0
    elif curr_val % 100 != 0: curr_step = 10.0
    else: curr_step = 100.0

    with col1 if i < 4 else col2:
        val = st.number_input(label, step=curr_step, format="%f", key=f"num_input_{i}")
        final_prices.append(val)

p0 = final_prices[0]

# --- [2] 분석 결과 구간 ---
st.divider()
st.subheader("2. 📊 분석 결과")

if st.button("🔄 분석 실행", type="secondary", use_container_width=True):
    if p0 == 0:
        st.error("데이터가 필요합니다.")
    else:
        valid_count = len([p for p in final_prices if p > 0])
        ma_results = []
        conv_outputs = []
        
        for n in [3, 5, 8]:
            if valid_count >= n - 1:
                sum_val = p0 * 2
                for j in range(1, n - 1): sum_val += final_prices[j]
                ma_val = sum_val / n
                diff = ((ma_val / p0) - 1) * 100
                ma_results.append({"구분": f"{n}일선", "가격": f"{ma_val:,.0f}원", "변동률": f"{diff:>+7.2f}%"})
        
        st.session_state.result_df = pd.DataFrame(ma_results)

        for n in [3, 8]:
            if valid_count >= n - 1:
                sim_day = float(p0)
                for _ in range(200000):
                    temp_list = [sim_day] + final_prices[:n-1]
                    c_ma = sum(temp_list) / n
                    if abs(sim_day - c_ma) / (c_ma if c_ma != 0 else 1) <= 0.005:
                        c_diff = ((sim_day / p0) - 1) * 100
                        gap_val = sim_day - c_ma
                        gap_rate = (gap_val / c_ma) * 100
                        conv_outputs.append(f"**[{n}일선 수렴가]** 1일차: **{sim_day:,.0f}원** ({c_diff:>+4.2f}%) / 예측 {n}일선: **{c_ma:,.0f}원** (괴리율 **{gap_rate:>+4.2f}%**)")
                        break
                    if sim_day < c_ma: sim_day += 1
                    else: sim_day -= 1
        st.session_state.result_conv = conv_outputs

if 'result_df' in st.session_state:
    st.table(st.session_state.result_df)
    for text in st.session_state.result_conv:
        st.success(text)

# --- [3] 시나리오 예측 ---
st.divider()
st.subheader("3. 🔮 시나리오")
f_price = st.number_input("1일차 예상가:", value=p0 if p0 > 0 else 0.0, step=100.0, format="%f")

if st.button("🚀 실행", type="primary", use_container_width=True):
    if p0 > 0 and final_prices[1] > 0:
        u_diff = ((f_price / p0) - 1) * 100
        n_ma3 = (f_price + p0 + final_prices[1]) / 3
        g_rate3 = ((f_price / n_ma3) - 1) * 100
        st.info(f"**[예측]** 입력: **{f_price:,.0f}원** ({u_diff:>+4.2f}%) / 3일선: **{n_ma3:,.0f}원** (괴리 **{g_rate3:>+4.2f}%**)")
