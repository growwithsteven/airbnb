/*
데이터셋 개요:
- 데이터셋 이름: AIRBNB.AIRBNB_FINAL_NIGHTLY_CLEAN
- 관측치(Observations) 수: 1,247개
- 변수(Variables) 수: 28개

주요 변수 분석 및 카테고리:

1. 가격 관련 변수 (Target Variables)
   - price_numeric: 요금 (숫자형)
   - log_price: 요금에 로그를 취한 값 (정규화 및 왜도 감소를 위해 변환된 것으로 보임, 회귀 분석 시 종속 변수로 사용하기 적합함)

2. 숙소 물리적 특성 (Property & Room Features)
   - propertyType (Char): 숙소 유형 (아파트, 주택 등)
   - roomType (Char): 방 유형 (집 전체, 개인실 등)
   - personCapacity: 수용 가능 인원
   - subdesc_baths: 욕실 수
   - subdesc_bedrooms: 침실 수
   - subdesc_beds: 침대 수
   - subdesc_guests: 게스트 수 (personCapacity와 유사한 의미로 보임)

3. 호스트 관련 정보 (Host Information)
   - host_ratingAverage: 호스트 평균 평점
   - host_ratingCount: 호스트 평가 개수
   - host_response_rate: 호스트 응답률
   - host_response_time (Char): 호스트 응답 시간 (예: 'within an hour')
   - host_total_months: 호스트로 활동한 총 개월 수 (호스트의 경력)

4. 세부 평점 및 리뷰 (Ratings & Reviews)
   - rating_guestSatisfaction: 전반적인 게스트 만족도
   - rating_accuracy: 정보 정확성 평점
   - rating_checking: 체크인 과정 평점
   - rating_cleanliness: 청결도 평점
   - rating_communication: 의사소통 평점
   - rating_location: 위치 평점
   - rating_value: 가격 대비 가치 평점
   - rating_reviewsCount: 리뷰 총 개수

5. 지리적 특성 및 입지 (Location & Surroundings)
   - dist_to_subway_m: 가장 가까운 지하철역까지의 거리 (미터)
   - dist_to_tourist_m: 가장 가까운 관광지까지의 거리 (미터)
   - count_tourist_2000m: 반경 2,000m 이내의 관광지 개수

6. 파생 변수 (Principal Components)
   - Prin1, Prin2, Prin3: 주성분 분석(PCA)을 통해 추출된 요인들. 변수가 많은 평점(rating_*) 관련 데이터나 다른 연속형 다중공선성 변수들을 축소해 놓은 결과로 추정됨.

분석 방향 제안:
- 가격 예측 모델링: `log_price`를 종속 변수로 두고, 입지, 숙소 특성, 호스트 특성이 가격에 미치는 영향 분석 (다중선형회귀 등).
- 주성분(Prin) 확인: 이전에 수행된 분석에서 Prin1~3이 각각 어떤 원래 변수들을 대표하고 있는지(예: '전반적인 만족도 요인', '접근성 요인' 등) 파악 후 모델에 적용하는 것이 좋음.
*/

/* 1. 환경 설정 및 라이브러리 지정 */
%let airbnb_path = ~/airbnb;
libname airbnb "&airbnb_path";

/* =========================================================
   [분석 1] 평점(rating_*) 관련 변수 일변량 분석 (Univariate Analysis)
   ========================================================= */

PROC MEANS DATA=AIRBNB.AIRBNB_FINAL_NIGHTLY_CLEAN N NMISS MIN MEAN MEDIAN MAX STD;
    VAR rating_: ;
    TITLE "평점 관련 변수들의 기초 통계량 및 결측치 확인";
RUN;

PROC UNIVARIATE DATA=AIRBNB.AIRBNB_FINAL_NIGHTLY_CLEAN NORMAL;
    VAR rating_guestSatisfaction 
        rating_accuracy 
        rating_checking 
        rating_cleanliness 
        rating_communication 
        rating_location 
        rating_value 
        rating_reviewsCount;
    
    HISTOGRAM rating_guestSatisfaction 
              rating_accuracy 
              rating_checking 
              rating_cleanliness 
              rating_communication 
              rating_location 
              rating_value 
              rating_reviewsCount / NORMAL(COLOR=RED);
    TITLE "평점 관련 변수들의 상세 분포 및 정규성 검정";
RUN;
TITLE; /* 타이틀 초기화 */

/* =========================================================
   [분석 2] 평점(rating_*) 변수와 종속변수(log_price) 간 이변량 분석 (Bivariate Analysis)
   ========================================================= */

/* ODS Graphics를 활성화하여 PROC CORR에서 직접 산점도(Scatter Plot)를 출력합니다. */
ODS GRAPHICS ON;

TITLE "평점 변수들과 log_price 간의 상관분석 및 산점도 (PROC CORR)";
PROC CORR DATA=AIRBNB.AIRBNB_FINAL_NIGHTLY_CLEAN PEARSON SPEARMAN NOSIMPLE RANK PLOTS=SCATTER(NVAR=ALL);
    VAR log_price;
    WITH rating_guestSatisfaction 
         rating_accuracy 
         rating_checking 
         rating_cleanliness 
         rating_communication 
         rating_location 
         rating_value 
         rating_reviewsCount;
RUN;

ODS GRAPHICS OFF;
TITLE; /* 타이틀 초기화 */
