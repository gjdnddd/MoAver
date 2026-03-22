import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="주식 이평선 분석기 v10", layout="centered")

if 'ma_df' not in st.session_state: st.session_state.ma_df = None
if 'conv_results' not in st.session_state: st.session_state.conv_results = []

st.title("📈 주식 이평선 분석기 v10")

# --- [1] 데이터 입력 구간 ---
st.subheader("1. 데이터 입력 및 확인")
raw_input = st.text_area("엑셀 데이터를 붙여넣으세요:", height=100)

def extract_prices(text):
    if not text: return []
    lines = re.split(r'[\n\r\t]+', text.strip())
    prices = []
    for line in lines:
        clean = line.replace(',', '').strip()
        for part in clean.split():
            match = re.search(r'\d+', part)
            if match: prices.append(float(match.group()))
    return prices

extracted_data = extract_prices(raw_input)

final_prices = []
col1, col2 = st.columns(2)
for i in range(8):
    label = "0일차 (최신)*" if i == 0 else f"D-{i}일차"
    val_init = int(extracted_data[i]) if i < len(extracted_data) else 0
    
    # 동적 Step 설정
    if val_init == 0: curr_step = 100
    elif val_init % 10 != 0: curr_step = 5
    elif val_init % 100 != 0: curr_step = 10
    else: curr_step = 100

    with col1 if i < 4 else col2:
        val = st.number_input(label, value=val_init, step=curr_step, format="%d", key=f"input_{i}")
        final_prices.append(val)

p0 = final_prices[0]

# --- [2] 이동평균선 및 수렴가 분석 ---
st.divider()
st.subheader("2. 📊 이동평균선 및 수렴 분석 결과")

if st.button("🔄 분석 실행", type="secondary", use_container_width=True):
    if p0 == 0:
        st.error("최신 가격(0일차) 데이터가 필요합니다.")
    else:
        valid_prices = [p for p in final_prices if p > 0]
        data_count = len(valid_prices)
        ma_results = []
        st.session_state.conv_results = []
        
        # 1. 이동평균선 계산
        calculated_mas = {}
        for n in [3, 5, 8]:
            if data_count >= n - 1:
                sum_val = p0 * 2
                for j in range(1, n - 1):
                    if j < len(final_prices) and final_prices[j] > 0:
                        sum_val += final_prices[j]
                ma_val = sum_val / n
                calculated_mas[n] = ma_val
                diff = ((ma_val / p0) - 1) * 100
                ma_results.append({"구분": f"{n}일선", "가격": f"{ma_val:,.0f}원", "변동률": f"{diff:>+7.2f}%"})
        
        st.session_state.ma_df = pd.DataFrame(ma_results)

        # 2. 수렴가 계산 함수 (3일선, 8일선 용)
        def find_convergence(target_n):
            if data_count < target_n - 1: return None
            sim_day = float(p0)
            for _ in range(200000):
                # 타겟 n일선 예측치 계산 (가중치 미적용 순수 평균)
                # 1일차(sim_day) + 0일차(p0) + ... 나머지
                temp_list = [sim_day] + final_prices[:target_n-1]
                c_ma = sum(temp_list) / target_n
                
                if abs(sim_day - c_ma) / (c_ma if c_ma != 0 else 1) <= 0.005:
                    return sim_day, c_ma
                if sim_day < c_ma: sim_day += 1
                else: sim_day -= 1
            return None

        for n in [3, 8]:
            res = find_convergence(n)
            if res:
                conv_p, ma_p = res
                c_diff_p0 = ((conv_p / p0) - 1) * 100
                gap_val = conv_p - ma_p
                gap_rate = (gap_val / ma_p) * 100
                st.session_state.conv_results.append({
                    "title": f"[{n}일선 수렴가 결과]",
                    "text": f"1일차 수렴가: **{conv_p:,.0f}원** (0일차 대비 **{c_diff_p0:>+4.2f}%**)  \n"
                            f"당시 예측 {n}일선: **{ma_p:,.0f}원** (이평선 대비 **{gap_rate:>+4.2f}%**, 차이: {gap_val:,.0f}원)"
                })

# 결과 표시 (상태 유지)
if st.session_state.ma_df is not None:
    st.table(st.session_state.ma_df)
    for res in st.session_state.conv_results:
        st.success(f"**{res['title']}** \n{res['text']}")

# --- [3] 1일차 시나리오 예측 ---
st.divider()
st.subheader("3. 🔮 1일차 시나리오 예측")
future_price = st.number_input("1일차 예상가 직접 입력:", value=p0 if p0 > 0 else 0, step=100, format="%d")

if st.button("🚀 시나리오 시뮬레이션", type="primary", use_container_width=True):
    if p0 > 0 and len([p for p in final_prices if p > 0]) >= 2:
        u_diff = ((future_price / p0) - 1) * 100
        # 3일선 예측
        new_ma3 = (future_price + p0 + final_prices[1]) / 3
        gap_ma3 = future_price - new_ma3
        gap_rate3 = (gap_ma3 / new_ma3) * 100
        
        st.info(f"**[예측가 시나리오 결과]** \n"
                f"입력가: **{future_price:,.0f}원** (0일차 대비 **{u_diff:>+4.2f}%**)  \n"
                f"예측 3일선: **{new_ma3:,.0f}원** (3일선 대비 **{gap_rate3:>+4.2f}%**, 차이: {gap_ma3:,.0f}원)")
    else:
        st.warning("분석을 위해 최소 0일차와 D-1일차 데이터가 필요합니다.")
