import streamlit as st
import re
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="주식 이평선 분석기 v7", layout="centered")

st.title("📈 엑셀 데이터 이평선 분석기")
st.caption("엑셀 붙여넣기 최적화 및 시뮬레이션 도구")

# [1] 데이터 입력 구간
st.subheader("1. 데이터 입력")
raw_input = st.text_area("엑셀에서 복사한 가격들을 아래에 붙여넣으세요:", height=150, help="줄바꿈이나 공백으로 구분된 숫자들을 인식합니다.")

# 데이터 전처리 함수
def extract_prices(text):
    if not text:
        return []
    
    # 1. 먼저 줄바꿈이나 탭(Tab)으로 각 행을 분리합니다.
    # (콤마는 여기서 분리 기준으로 쓰지 않습니다)
    lines = re.split(r'[\n\r\t]+', text.strip())
    
    prices = []
    for line in lines:
        # 각 줄에서 숫자와 관련된 것(숫자, 마침표)만 남기고 나머지는 제거
        # 콤마(,)를 제거하여 '67,400'을 '67400'으로 만듭니다.
        clean = line.replace(',', '').strip()
        
        # 만약 한 줄에 공백으로 여러 숫자가 있다면 다시 분리
        sub_parts = clean.split()
        for part in sub_parts:
            # 숫자만 추출 (정수 형태)
            match = re.search(r'\d+', part)
            if match:
                prices.append(float(match.group()))
                
    return prices

extracted_data = extract_prices(raw_input)

# [2] 개별 확인 및 수정 (입력창에 자동 배분)
st.subheader("2. 데이터 확인 및 수정")
col1, col2 = st.columns(2)

# 8개까지 데이터 매핑
final_prices = []
for i in range(8):
    label = "0일차 (최신)*" if i == 0 else f"D-{i}일차"
    default_val = int(extracted_data[i]) if i < len(extracted_data) else 0
    
    with col1 if i < 4 else col2:
        val = st.number_input(label, value=default_val, step=100, format="%d")
        final_prices.append(val)

# [3] 시나리오 분석
st.divider()
st.subheader("3. 1일차 시나리오 예측")
p0 = final_prices[0]
p1 = final_prices[1]

future_price = st.number_input("1일차 예상가 입력:", value=p0, step=100, format="%d")

if st.button("🚀 시뮬레이션 결과 보기", type="primary", use_container_width=True):
    if p0 == 0 or p1 == 0:
        st.error("0일차와 D-1일차 가격은 필수입니다.")
    else:
        # 이평선 계산 결과
        st.markdown("### 📊 이동평균선 분석 (0일차 가중치 적용)")
        ma_results = []
        for n in [3, 5, 10, 20]:
            # 데이터 개수가 부족하면 계산 제외
            relevant_prices = [p for p in final_prices[:n] if p > 0]
            if len(relevant_prices) >= 2: # 최소 2개 이상 데이터가 있을 때
                # 기존 로직: 0일차 가중치(2배) 적용 및 평균
                sum_val = p0 * 2
                count = 2
                for j in range(1, min(n - 1, len(final_prices))):
                    if final_prices[j] > 0:
                        sum_val += final_prices[j]
                        count += 1
                
                ma_val = sum_val / n
                diff = ((ma_val / p0) - 1) * 100
                ma_results.append({
                    "구분": f"{n}일선",
                    "예상 가격": f"{ma_val:,.0f}원",
                    "변동률": f"{diff:>+7.2f}%"
                })
        
        st.table(pd.DataFrame(ma_results))

        # 시나리오 결과
        st.markdown("### 🔮 시나리오 결과")
        c1, c2 = st.columns(2)
        
        with c1:
            u_diff = ((future_price / p0) - 1) * 100
            new_ma3 = (future_price + p0 + p1) / 3
            st.info(f"**[예측가 시나리오]**\n\n- 예측가: {future_price:,.0f}원 ({u_diff:>+4.2f}%)\n- 예측 3일선: {new_ma3:,.0f}원")

        with c2:
            # 수렴점 찾기 로직
            sim_day = float(p0)
            found = False
            for _ in range(200000):
                c_ma3 = (sim_day + p0 + p1) / 3
                if abs(sim_day - c_ma3) / (c_ma3 if c_ma3 != 0 else 1) <= 0.005:
                    found = True
                    break
                if sim_day < c_ma3: sim_day += 1
                else: sim_day -= 1
            
            if found:
                c_diff = ((sim_day / p0) - 1) * 100
                st.success(f"**[자동 수렴가 결과]**\n\n- 1일차 수렴가: {sim_day:,.0f}원\n- 0일차 대비: {c_diff:>+4.2f}%")
