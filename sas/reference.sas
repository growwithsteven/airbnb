/* ====================================================================
   [1] 연속형 독립변수: 상관분석 및 산점도 행렬 (PROC CORR)
==================================================================== */
ods graphics on;
title "1. 연속형 변수와 로그 가격(log_price) 간의 1:1 상관관계 및 산점도";
proc corr data=airbnb2.airbnb_final_nightly_clean plots=matrix(histogram);
    /* 종속변수(Y)를 기준으로 10개의 독립변수(X)를 각각 비교합니다 */
    with log_price; 
    var prin1 prin2 prin3 
        count_tourist_2000m dist_to_subway_m dist_to_tourist_m
        host_ratingAverage host_ratingCount host_response_rate host_total_months;
run;
title;


/* ====================================================================
   [2] 연속형 독립변수: 1:1 단순선형회귀분석 (PROC REG)
   - 각 변수별로 모델(m1~m10)을 지정하여 개별적인 R제곱 및 회귀계수 산출
==================================================================== */
title "2. 연속형 변수별 1:1 단순회귀분석 (R-Square 및 회귀계수 도출)";
proc reg data=airbnb2.airbnb_final_nightly_clean plots(only)=fitplot;
    /* Fitplot 옵션을 통해 회귀선이 그려진 개별 산점도를 함께 출력합니다 */
    prin1:  model log_price = prin1;
    prin2:  model log_price = prin2;
    prin3:  model log_price = prin3;
    count_tourist_2000m:  model log_price = count_tourist_2000m;
    dist_to_subway_m:  model log_price = dist_to_subway_m;
    dist_to_tourist_m:  model log_price = dist_to_tourist_m;
    host_ratingAverage:  model log_price = host_ratingAverage;
    host_ratingCount:  model log_price = host_ratingCount;
    host_response_rate:  model log_price = host_response_rate;
    host_total_months: model log_price = host_total_months;
run; quit;
title;


/* ====================================================================
   [3] 범주형 변수 (3집단 이상): 일원분산분석 ANOVA (PROC GLM)
   - host_response_time 집단 간 가격 차이 검정 및 사후 분석
==================================================================== */
title "3. 범주형(3집단 이상) 변수: 응답 시간(host_response_time)에 따른 가격 차이 (ANOVA)";
proc glm data=airbnb2.airbnb_final_nightly_clean plots=diagnostics;
    class host_response_time;
    model log_price = host_response_time;
    
    /* 집단 간 평균 차이가 유의할 경우, 구체적으로 어느 집단끼리 다른지 Tukey 사후검정 수행 */
    means host_response_time / tukey hovtest=levene; 
run; quit;
title;


/* ====================================================================
   [4] 범주형 변수 (2집단): 독립표본 T-검정 (PROC TTEST) 템플릿
   - 현재 목록에는 없으나, 추후 이진 변수(예: 슈퍼호스트 여부 등) 
     분석 시 아래 템플릿의 변수명만 수정하여 사용하시면 됩니다.
==================================================================== */
/*
title "4. 범주형(2집단) 변수: 집단 간 가격 차이 검정 (T-Test)";
proc ttest data=airbnb2.airbnb_final_nightly_clean;
    class 이진범주형_변수명; /* 예: host_is_superhost */
    var log_price;
run;
title;
*/
ods graphics off;