/******************************************************************************
 * 프로그램명 : eda_airbnb.sas (일변량 분석 PROC UNIVARIATE 포함 완성형 EDA)
 * 설    명 : AIRBNB 라이브러리의 18개 정규화 데이터셋을 결합하여
 *            1) 심층 일변량 분석 (분포, 왜도, 첨도, 정규성 검정, 극단값 탐지)
 *            2) 이변량/다변량 분석 (가격, 만족도, 호스트 요인 간 관계) 수행
 * 작성환경 : SAS OnDemand for Academics (ODA) / SAS Studio
 ******************************************************************************/

/* 1. 환경 설정 및 라이브러리 지정 */
%let airbnb_path = ~/airbnb;
libname airbnb "&airbnb_path";

/* ODS Graphics 차트 옵션 활성화 */
ods graphics on / reset=all width=850px height=520px imagemap=on;

/*============================================================================*
 * 2. EDA용 통합 분석 마트(WORK.AIRBNB_EDA) 구축
 *============================================================================*/

/* 2-1. 숙소별 1:N 하위 테이블 집계 지표 계산 */
proc sql;
    /* 숙소별 등록 사진 개수 */
    create table work.agg_images as
    select listing_id, count(*) as photo_count
    from airbnb.listing_image
    group by listing_id;

    /* 숙소별 제공 편의시설 개수 */
    create table work.agg_amenities as
    select listing_id, count(*) as amenity_count
    from airbnb.listing_amenity
    where is_available = 1
    group by listing_id;

    /* 숙소별 이용 규칙(하우스 룰) 개수 */
    create table work.agg_rules as
    select listing_id, count(*) as rule_count
    from airbnb.listing_house_rule
    group by listing_id;

    /* 숙소별 공동 호스트 수 */
    create table work.agg_cohosts as
    select listing_id, count(*) as cohost_count
    from airbnb.listing_co_host
    group by listing_id;
quit;

/* 2-2. 마스터 분석 데이터셋(WORK.AIRBNB_EDA) 결합 및 변수 정제 */
proc sql;
    create table work.airbnb_eda as
    select
        l.id as listing_id label='Listing ID',
        l.title label='Listing Title',
        l.property_type label='Property Type',
        l.room_type label='Room Type',
        l.home_tier label='Home Tier',
        l.person_capacity label='Person Capacity',
        l.latitude label='Latitude',
        l.longitude label='Longitude',
        l.location_name label='Location',
        l.is_available label='Is Available',
        
        /* 가격 문자열 -> 숫자형 변환 ($522 -> 522) */
        input(compress(p.price_amount, '$, '), best12.) as price label='Price (USD)',
        
        /* 1인당 숙박비 파생변수 */
        case 
            when l.person_capacity > 0 then calculated price / l.person_capacity 
            else . 
        end as price_per_person label='Price Per Person (USD)' format=8.2,

        /* 평점 지표 (6대 세부 평점 및 종합 만족도) */
        r.guest_satisfaction label='Overall Satisfaction' format=5.2,
        r.accuracy label='Accuracy' format=5.2,
        r.cleanliness label='Cleanliness' format=5.2,
        r.checking label='Check-in' format=5.2,
        r.communication label='Communication' format=5.2,
        r.location as location_rating label='Location' format=5.2,
        r.value as value_rating label='Value' format=5.2,
        coalesce(r.reviews_count, 0) as reviews_count label='Reviews Count',

        /* 호스트 지표 */
        h.id as host_id label='Host ID',
        h.name as host_name label='Host Name',
        h.is_superhost label='Superhost (1=Yes, 0=No)',
        h.is_verified as is_host_verified label='Host Verified (1=Yes, 0=No)',
        h.rating_average as host_rating label='Host Avg Rating' format=5.2,
        h.rating_count as host_review_count label='Host Review Count',
        (h.time_as_host_years * 12 + h.time_as_host_months) as host_experience_months label='Host Experience (Months)',

        /* 집계 파생 지표 결합 */
        coalesce(img.photo_count, 0) as photo_count label='Photo Count',
        coalesce(am.amenity_count, 0) as amenity_count label='Amenity Count',
        coalesce(rul.rule_count, 0) as rule_count label='House Rule Count',
        coalesce(coh.cohost_count, 0) as cohost_count label='Co-host Count'

    from airbnb.listing as l
    left join airbnb.listing_price as p on l.id = p.listing_id
    left join airbnb.listing_rating as r on l.id = r.listing_id
    left join airbnb.host as h on l.host_id = h.id
    left join work.agg_images as img on l.id = img.listing_id
    left join work.agg_amenities as am on l.id = am.listing_id
    left join work.agg_rules as rul on l.id = rul.listing_id
    left join work.agg_cohosts as coh on l.id = coh.listing_id;
quit;

/*============================================================================*
 * 3. [신규 추가] 심층 일변량 분석 (Univariate Analysis - PROC UNIVARIATE)
 *
 *  ※ 일변량 분석이란?
 *    변수 하나(1개)의 특성을 집중 분석하는 기법으로,
 *    1) 중심 경향(평균, 중위수, 최빈수)
 *    2) 산포도(표준편차, 사분위범위 IQR, 분산)
 *    3) 분포의 형태(왜도 Skewness: 좌우 비대칭도, 첨도 Kurtosis: 뾰족한 정도)
 *    4) 정규성 검정(Shapiro-Wilk, Kolmogorov-Smirnov)
 *    5) 극단값/이상치(Extreme Values: 상/하위 5개 관측치)를 완벽히 파악합니다.
 *============================================================================*/

/* 3-1. 핵심 수치형 변수 일변량 정밀 분석 및 정규성 검정 */
title1 "=================================================================";
title2 " [Univariate 1] In-depth Univariate Analysis & Normality Tests";
title3 "=================================================================";
proc univariate data=work.airbnb_eda normal;
    var price price_per_person guest_satisfaction reviews_count amenity_count photo_count;
    id listing_id title; /* 극단값 관측치 식별용 */
    
    /* 가격 및 만족도에 대한 정규/커널 밀도곡선 히스토그램 */
    histogram price price_per_person guest_satisfaction / normal kernel;
    inset mean std median q1 q3 skewness kurtosis / position=ne;
    
    /* 정규 확률도 (Q-Q Plot) */
    probplot price guest_satisfaction / normal(mu=est sigma=est);
run;
title;

/* 3-2. 범주형 변수 일변량 빈도 분포 분석 */
title1 " [Univariate 2] Univariate Frequency Distribution of Categorical Variables";
proc freq data=work.airbnb_eda order=freq;
    tables room_type property_type is_superhost home_tier is_host_verified / nocum plots=FreqPlot;
run;
title;

/*============================================================================*
 * 4. 이변량 및 다변량 분석 (Bivariate & Multivariate EDA)
 *============================================================================*/

/* --------------------------------------------------------------------------
 * [1] 숙소 가격(Price) 결정 요인 분석
 * -------------------------------------------------------------------------- */

/* 1-1. 객실 유형 및 슈퍼호스트 여부에 따른 평균 가격 비교 */
title1 " [Bivariate 1] Average Price by Room Type and Superhost Status";
proc means data=work.airbnb_eda n mean std median min max maxdec=1;
    class room_type is_superhost;
    var price price_per_person;
run;
title;

/* 1-2. 수용 인원별 숙박 요금 분포 요약 */
title1 " [Bivariate 2] Price Summary by Person Capacity";
proc means data=work.airbnb_eda mean median std p25 p75 maxdec=1;
    class person_capacity;
    var price price_per_person;
run;
title;

/* 1-3. 슈퍼호스트(1) vs 일반호스트(0) 가격 차이 독립표본 T-검정 */
title1 " [Hypothesis Test] Two-Sample T-Test: Price by Superhost Status";
proc ttest data=work.airbnb_eda;
    class is_superhost;
    var price price_per_person;
run;
title;

/* 1-4. 숙소 가격과 주요 수치형 변수 간 상관분석 (Pearson & Spearman) */
title1 " [Correlation 1] Pearson & Spearman Correlation with Listing Price";
proc corr data=work.airbnb_eda pearson spearman nosimple rank;
    var price;
    with person_capacity photo_count amenity_count reviews_count 
         host_experience_months guest_satisfaction cleanliness;
run;
title;

/* --------------------------------------------------------------------------
 * [2] 게스트 만족도(Rating) 결정 요인 분석
 * -------------------------------------------------------------------------- */

/* 2-1. 6대 세부 평점과 종합 만족도 간의 다변량 상관분석 */
title1 " [Correlation 2] Correlation Matrix of Sub-ratings with Overall Satisfaction";
proc corr data=work.airbnb_eda pearson nosimple;
    var guest_satisfaction;
    with accuracy cleanliness checking communication location_rating value_rating;
run;
title;

/* 2-2. 숙소 가격 결정 요인 다중 회귀분석 및 다중공선성(VIF) 진단 */
title1 " [Regression] Multiple Linear Regression Model for Listing Price";
proc reg data=work.airbnb_eda;
    model price = person_capacity amenity_count photo_count 
                  is_superhost host_experience_months reviews_count / vif;
run;
quit;
title;

/*============================================================================*
 * 5. EDA 핵심 시각화 차트 (ODS Graphics & SGPLOT)
 *   ※ 차트 내부 라벨/타이틀은 폰트 깨짐 방지를 위해 영문 유지
 *============================================================================*/

/* 5-1. 숙소 가격 분포 히스토그램 & 커널 밀도 곡선 */
title1 " [Chart 1] Distribution of Listing Price";
proc sgplot data=work.airbnb_eda;
    histogram price / binwidth=50 fillattrs=(color=CX3498DB);
    density price / type=kernel lineattrs=(color=CXE74C3C thickness=2);
    xaxis label="Listing Price (USD)" values=(0 to 1500 by 100);
    yaxis label="Frequency (Number of Listings)";
run;
title;

/* 5-2. 객실 유형별 가격 분포 박스플롯 */
title1 " [Chart 2] Price Distribution by Room Type";
proc sgplot data=work.airbnb_eda;
    vbox price / category=room_type fillattrs=(color=CX2ECC71);
    yaxis label="Listing Price (USD)" min=0 max=1200;
    xaxis label="Room Type";
run;
title;

/* 5-3. 제공 편의시설 개수와 숙소 가격 간의 산점도 및 회귀 추세선 */
title1 " [Chart 3] Amenity Count vs Listing Price";
proc sgplot data=work.airbnb_eda;
    scatter x=amenity_count y=price / markerattrs=(symbol=circlefilled size=7 color=CX2980B9) transparency=0.4;
    reg x=amenity_count y=price / lineattrs=(color=CXE67E22 thickness=2) clm;
    xaxis label="Number of Available Amenities";
    yaxis label="Listing Price (USD)" min=0 max=1200;
run;
title;

/* 5-4. 수용 인원별 평균 가격 추세 (슈퍼호스트 그룹별 비교) */
title1 " [Chart 4] Mean Price by Person Capacity and Superhost Status";
proc sgplot data=work.airbnb_eda;
    vline person_capacity / response=price stat=mean group=is_superhost 
          markers lineattrs=(thickness=2);
    xaxis label="Person Capacity";
    yaxis label="Mean Price (USD)";
    keylegend / title="Superhost (1=Yes, 0=No)" position=topright;
run;
title;

/* 5-5. 6대 평점 세부 요소 산점도 매트릭스 */
title1 " [Chart 5] Scatter Plot Matrix of Sub-ratings";
proc sgscatter data=work.airbnb_eda;
    matrix guest_satisfaction cleanliness communication location_rating value_rating / 
           markerattrs=(size=4 color=CX8E44AD) diagonal=(histogram kernel);
run;
title;
