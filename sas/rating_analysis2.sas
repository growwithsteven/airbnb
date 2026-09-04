/* 1. 환경 설정 및 라이브러리 지정 */
%let airbnb_path = ~/airbnb;
libname airbnb "&airbnb_path";

/* ====================================================================
   [1] 연속형 독립변수: 상관분석 및 산점도 행렬 (PROC CORR)
==================================================================== */
ods graphics on;
title "1. 평점 관련 연속형 변수들과 로그 가격(log_price) 간의 1:1 상관관계 및 산점도";
proc corr data=airbnb.airbnb_final_nightly_clean plots=matrix(histogram);
    /* 종속변수(Y)를 기준으로 8개의 평점/리뷰 독립변수(X)를 각각 비교합니다 */
    with log_price; 
    var rating_guestSatisfaction 
        rating_accuracy 
        rating_checking 
        rating_cleanliness 
        rating_communication 
        rating_location 
        rating_value 
        rating_reviewsCount;
run;
title;


/* ====================================================================
   [2] 연속형 독립변수: 1:1 단순선형회귀분석 (PROC REG)
   - 각 변수별로 모델(m1~m8)을 지정하여 개별적인 R제곱 및 회귀계수 산출
==================================================================== */
title "2. 평점 변수별 1:1 단순회귀분석 (R-Square 및 회귀계수 도출)";
proc reg data=airbnb.airbnb_final_nightly_clean plots(only)=fitplot;
    /* Fitplot 옵션을 통해 회귀선이 그려진 개별 산점도를 함께 출력합니다 */
    satisfaction:  model log_price = rating_guestSatisfaction;
    accuracy:      model log_price = rating_accuracy;
    checking:      model log_price = rating_checking;
    cleanliness:   model log_price = rating_cleanliness;
    communication: model log_price = rating_communication;
    location:      model log_price = rating_location;
    value:         model log_price = rating_value;
    reviewsCount:  model log_price = rating_reviewsCount;
run; quit;
title;

ods graphics off;
