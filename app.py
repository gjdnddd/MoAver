import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="주식 이평선 분석기 v9", layout="centered")

# 세션 상태 초기화 (결과 유지용)
if 'ma_df' not in st.session_state: st.session_state.ma_df = None
if 'convergence_text' not in st.session_state: st.session_state.convergence_text = ""

st.title("📈 주식 이평선 분석기 v9")

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

# 입력칸 자동 배분 및 동적 Step 설정
final_prices = []
col1, col2 = st.columns(2)
for i in range(8):
    label = "0일차 (최신)*" if i == 0 else f"D-{i}일차"
    # 텍스트 입력이 있으면 우선 적용, 없으면 0
    val_init = int(extracted_data[i]) if i < len(extracted_data) else 0
    
    # 동적 Step 계산 로직
    if val_init == 0: curr_step = 100
    elif val_init % 10 != 0: curr_step = 5
    elif val_init % 100 != 0: curr_step = 10
    else: curr_step = 100

    with col1 if i < 4 else col2:
        val = st.number_input(label, value=val_init, step=curr_step, format="%d", key=f"input_{i}")
        final_prices.append(val)

p0, p1 = final_prices[0], final_prices[1]

# --- [2] 이동평균선 및 자동 수렴가 분석 ---
st.divider()
st.subheader("2. 📊 이동평균선 및 수렴가 분석")

if st.button("🔄 분석 실행", type="secondary", use_container_width=True):
    if p0 == 0:
        st.error("최신 가격(0일차) 데이터가 필요합니다.")
    else:
        # 1. 이동평균선 계산 (입력된 데이터 개수에 따라)
        valid_prices = [p for p in final_prices if p > 0]
        data_count = len(valid_prices)
        ma_results = []
        
        # 가용한 데이터 범위 내에서만 이평선 계산 (최대 8일선)
        for n in [3, 5, 8]:
            if data_count >= n - 1: # 0일차 가중치 포함 계산 가능 여부
                sum_val = p0 * 2
                count = 2
                for j in range(1, n - 1):
                    if j < len(final_prices) and final_prices[j] > 0:
                        sum_val += final_prices[j]
                        count += 1
                ma_val = sum_val / n
                diff = ((ma_val / p0) - 1) * 100
                ma_results.append({"구분": f"{n}일선", "가격": f"{ma_val:,.0f}원", "변동률": f"{diff:>+7.2f}%"})
        
        st.session_state.ma_df = pd.DataFrame(ma_results)

        # 2. 자동 수렴가 계산 (+-0.5% 정밀도)
        if p0 > 0 and p1 > 0:
            sim_day = float(p0)
            found = False
            for _ in range(200000):
                c_ma3 = (sim_day + p0 + p1) / 3
                if abs(sim_day - c_ma3) / (c_ma3 if c_ma3 != 0 else 1) <= 0.005:
                    found = True; break
                if sim_day < c_ma3: sim_day += 1
                else: sim_day -= 1
            
            if found:
                c_diff = ((sim_day / p0) - 1) * 100
                st.session_state.convergence_text = f"**[자동 수렴가 결과]** \n1일차 수렴가: **{sim_day:,.0f}원** (0일차 대비 **{c_diff:>+4.2f}%**)  \n*조건: 3일선과 가격 차이 0.5% 이내*"
            else:
                st.session_state.convergence_text = "수렴 조건을 만족하는 값을 찾을 수 없습니다."

# 분석 결과 출력 (상태 유지)
if st.session_state.ma_df is not None:
    st.table(st.session_state.ma_df)
    st.success(st.session_state.convergence_text)

# --- [3] 1일차 시나리오 예측 ---
st.divider()
st.subheader("3. 🔮 1일차 시나리오 예측")
future_price = st.number_input("1일차 예상가 직접 입력:", value=p0 if p0 > 0 else 0, step=100, format="%d")

if st.button("🚀 시나리오 시뮬레이션", type="primary", use_container_width=True):
    if p0 > 0 and p1 > 0:
        u_diff = ((future_price / p0) - 1) * 100
        new_ma3 = (future_price + p0 + p1) / 3
        st.info(f"**[예측가 시나리오 결과]** \n입력가: **{future_price:,.0f}원** ({u_diff:>+4.2f}%)  \n예측 3일선: **{new_ma3:,.0f}원**")
    else:
        st.warning("먼저 데이터를 입력해주세요.")
