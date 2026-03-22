import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="주식 이평선 분석기 v8", layout="centered")

st.title("📈 주식 이평선 분석기 v8")

# --- [1] 데이터 입력 구간 ---
st.subheader("1. 데이터 입력 및 확인")
raw_input = st.text_area("엑셀 데이터를 붙여넣으세요 (콤마 포함 가능):", height=120)

def extract_prices(text):
    if not text: return []
    lines = re.split(r'[\n\r\t]+', text.strip())
    prices = []
    for line in lines:
        clean = line.replace(',', '').strip()
        sub_parts = clean.split()
        for part in sub_parts:
            match = re.search(r'\d+', part)
            if match: prices.append(float(match.group()))
    return prices

extracted_data = extract_prices(raw_input)

col1, col2 = st.columns(2)
final_prices = []
for i in range(8):
    label = "0일차 (최신)*" if i == 0 else f"D-{i}일차"
    default_val = int(extracted_data[i]) if i < len(extracted_data) else 0
    with col1 if i < 4 else col2:
        val = st.number_input(label, value=default_val, step=100, format="%d", key=f"input_{i}")
        final_prices.append(val)

p0, p1 = final_prices[0], final_prices[1]

# --- [2] 이동평균선 분석 (고정 결과) ---
st.divider()
st.subheader("2. 📊 이동평균선 분석 (현재 기준)")

if st.button("🔄 이평선 데이터 업데이트", type="secondary", use_container_width=True):
    if p0 == 0:
        st.error("최신 가격(0일차)을 입력해주세요.")
    else:
        ma_results = []
        for n in [3, 5, 10, 20]:
            if len([p for p in final_prices[:n] if p > 0]) >= 2:
                sum_val = p0 * 2 # 0일차 가중치
                count = 2
                for j in range(1, min(n - 1, len(final_prices))):
                    if final_prices[j] > 0:
                        sum_val += final_prices[j]
                        count += 1
                ma_val = sum_val / n
                diff = ((ma_val / p0) - 1) * 100
                ma_results.append({"구분": f"{n}일선", "가격": f"{ma_val:,.0f}원", "변동률": f"{diff:>+7.2f}%"})
        st.table(pd.DataFrame(ma_results))

# --- [3] 1일차 시나리오 예측 (독립 작동) ---
st.divider()
st.subheader("3. 🔮 1일차 시나리오 예측")
st.caption("이평선 분석과 별개로 시나리오만 변경하며 시뮬레이션할 수 있습니다.")

sc_col1, sc_col2 = st.columns([2, 1])
with sc_col1:
    future_price = st.number_input("1일차 예상가 직접 입력:", value=p0, step=100, format="%d")

if st.button("🚀 시나리오 시뮬레이션 실행", type="primary", use_container_width=True):
    if p0 == 0 or p1 == 0:
        st.warning("분석을 위해 0일차와 D-1일차 데이터가 필요합니다.")
    else:
        res1, res2 = st.columns(2)
        
        with res1:
            u_diff = ((future_price / p0) - 1) * 100
            new_ma3 = (future_price + p0 + p1) / 3
            st.info(f"**[입력가 시나리오]**\n\n- 예측가: {future_price:,.0f}원 ({u_diff:>+4.2f}%)\n- 예측 3일선: {new_ma3:,.0f}원")

        with res2:
            # 수렴점 찾기 (오차 0.5% 미만 타겟)
            sim_day = float(p0)
            target_error = 0.005 # +-0.5%
            found = False
            
            # 수렴 방향 설정 (3일선과의 괴리를 좁히는 방향으로 최대 30만번 연산)
            for _ in range(300000):
                c_ma3 = (sim_day + p0 + p1) / 3
                current_error = abs(sim_day - c_ma3) / (c_ma3 if c_ma3 != 0 else 1)
                
                if current_error <= target_error:
                    found = True
                    break
                
                # 1일차 가격이 3일선보다 낮으면 올리고, 높으면 내림
                if sim_day < c_ma3: sim_day += 1
                else: sim_day -= 1
            
            if found:
                c_diff = ((sim_day / p0) - 1) * 100
                st.success(f"**[자동 수렴가 결과]**\n\n- 1일차 수렴가: {sim_day:,.0f}원\n- 0일차 대비: {c_diff:>+4.2f}%\n- 조건: 오차범위 0.5% 이내")
            else:
                st.warning("수렴값을 찾지 못했습니다. 데이터를 확인해주세요.")
