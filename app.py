# --- [3] 시나리오 예측 (1일차 기능) ---
st.divider()
st.subheader("3. 🔮 1일차 시나리오 비교 (3개)")

# 결과를 유지하기 위한 session_state 초기화
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = {1: None, 2: None, 3: None}

# 시나리오 입력을 위한 3개 컬럼
sc_cols = st.columns(3)

for i, col in enumerate(sc_cols, 1):
    with col:
        st.markdown(f"**시나리오 {i}**")
        # 개별 입력창 (기본값은 p0)
        input_key = f"sc_input_{i}"
        f_price = st.number_input(f"예상가 {i}:", value=p0 if p0 > 0 else 0.0, step=100.0, format="%f", key=input_key)
        
        if st.button(f"🚀 실행 {i}", key=f"btn_{i}", type="primary", use_container_width=True):
            if p0 > 0 and final_prices[1] > 0:
                # 계산 로직
                u_diff = ((f_price / p0) - 1) * 100
                n_ma2 = (f_price + p0) / 2
                n_ma3 = (f_price + p0 + final_prices[1]) / 3
                n_ma2_5 = (n_ma2 + n_ma3) / 2 # 2일선과 3일선의 평균 (2.5일선)
                
                # 결과 텍스트 생성 및 저장
                res_text = f"""
                **[결과 {i}]** {f_price:,.0f}원 ({u_diff:>+4.2f}%)
                * 2일선: **{n_ma2:,.0f}원**
                * 3일선: **{n_ma3:,.0f}원**
                * **평균(2.5): {n_ma2_5:,.0f}원**
                """
                st.session_state.scenarios[i] = res_text
            else:
                st.error("데이터 부족")

# 저장된 결과 출력 (다른 동작을 해도 유지됨)
st.write("---")
res_cols = st.columns(3)
for i, col in enumerate(res_cols, 1):
    with col:
        if st.session_state.scenarios[i]:
            st.info(st.session_state.scenarios[i])
