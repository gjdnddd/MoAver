import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="주식 이평선 분석기 v12", layout="centered")

# --- [0] 세션 상태 초기화 (핵심: 모든 입력을 세션에서 관리) ---
if 'prices' not in st.session_state:
    st.session_state.prices = [0.0] * 8

st.title("📈 주식 이평선 분석기 v12")

# --- [1] 데이터 입력 구간 ---
st.subheader("1. 데이터 입력 및 확인")

# 데이터 추출 및 세션 업데이트 함수
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
        
        # 추출된 데이터를 세션 가격 리스트에 반영 (최대 8개)
        for i in range(8):
            if i < len(extracted):
                st.session_state[f"num_input_{i}"] = extracted[i]
                st.session_state.prices[i] = extracted[i]

# 텍스트 입력창 (on_change를 통해 즉시 배분)
st.text_area(
    "엑셀 데이터를 여기에 붙여넣으세요:", 
    height=100, 
    key="raw_data_input", 
    on_change=sync_data
)

# 입력칸 8개 자동 생성
col1, col2 = st.columns(2)
final_prices = []

for i in range(8):
    label = "0일차 (최신)*" if i == 0 else f"D-{i}일차"
    
    # 세션 상태에 키가 없으면 초기화
    if f"num_input_{i}" not in st.session_state:
        st.session_state[f"num_input_{i}"] = 0.0

    # 현재 값에 따른 동적 Step 계산
    curr_val = st.session_state[f"num_input_{i}"]
    if curr_val == 0: curr_step = 100.0
    elif curr_val % 10 != 0: curr_step = 5.0
    elif curr_val % 100 != 0: curr_step = 10.0
    else: curr_step = 100.0

    with col1 if i < 4 else col2:
        val = st.number_input(
            label, 
            step=curr_step, 
            format="%f", 
            key=f"num_input_{i}" # 키를 지정하여 세션과 직접 연결
        )
        final_prices.append(val)

p0 = final_prices[0]

# --- [2] 분석 결과 구간 (상태 유지) ---
st.divider()
st.subheader("2. 📊 분석 결과")

# 분석 실행 버튼을 누를 때만 결과 생성
if st.button("🔄 분석 실행", type="secondary", use_container_width=True):
    if p0 == 0:
        st.error("최신 가격(0일차) 데이터가 필요합니다.")
    else:
        valid_count = len([p for p in final_prices if p > 0])
        ma_results = []
        conv_outputs = []
        
        # 이평선 계산 (3, 5, 8일선)
        for n in [3, 5, 8]:
            if valid_count >= n - 1:
                sum_val = p0 * 2
                for j in range(1, n - 1):
                    sum_val += final_prices[j]
                ma_val = sum_val / n
                diff = ((ma_val / p0) - 1) * 100
                ma_results.append({"구분": f"{n}일선", "가격": f"{ma_val:,.0f}원", "변동률": f"{diff:>+7.2f}%"})
        
        st.session_state.result_df = pd.DataFrame(ma_results)

        # 수렴가 계산 (3, 8일선)
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
                        conv_outputs.append(f"**[{n}일선 수렴가]** \n1일차 수렴가: **{sim_day:,.0f}원** (0일차 대비 **{c_diff:>+4.2f}%**)  \n당시 예측 {n}일선: **{c_ma:,.0f}원** (괴리율 **{gap_rate:>+4.2f}%**, 차이: {gap_val:,.0f}원)")
                        break
                    if sim_day < c_ma: sim_day += 1
                    else: sim_day -= 1
        st.session_state.result_conv = conv_outputs

# 결과 출력
if 'result_df' in st.session_state:
    st.table(st.session_state.result_df)
    for text in st.session_state.result_conv:
        st.success(text)

# --- [3] 1일차 시나리오 예측 ---
st.divider()
st.subheader("3. 🔮 1일차 시나리오 예측")
f_price = st.number_input("1일차 예상가 직접 입력:", value=p0 if p0 > 0 else 0.0, step=100.0, format="%f")

if st.button("🚀 시나리오 시뮬레이션", type="primary", use_container_width=True):
    if p0 > 0 and final_prices[1] > 0:
        u_diff = ((f_price / p0) - 1) * 100
        n_ma3 = (f_price + p0 + final_prices[1]) / 3
        g_ma3 = f_price - n_ma3
        g_rate3 = (g_ma3 / n_ma3) * 100
        st.info(f"**[예측가 결과]** \n입력가: **{f_price:,.0f}원** (0일차 대비 **{u_diff:>+4.2f}%**)  \n예측 3일선: **{n_ma3:,.0f}원** (괴리율 **{g_rate3:>+4.2f}%**, 차이: {g_ma3:,.0f}원)")
    else:
        st.warning("데이터(0일차, D-1일차)를 먼저 확인해주세요.")
