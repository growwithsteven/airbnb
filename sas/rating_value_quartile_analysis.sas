/***************************************************************************************************
 * [파일 정보]
 * 파일명 : rating_value_quartile_analysis_per_person.sas
 * 대  상 : airbnb.airbnb_final_per_person (1인당 1박 가격 기준 데이터셋)
 * 변  수 : price_per_person (1인당 요금), log_price_per_person (1인당 로그 요금), rating_value (가성비 평점)
 * 역  할 : 1인당 요금 기준 가성비 평점의 4분위수 집단 간 평균 비교(ANOVA) 및 분포 분석
 * 출  력 : SAS RESULTS 창에 분석 결과와 한국어 설명 리포트 자동 출력 (PROC ODSTEXT)
 * 상  세 :
 *   - [전처리] 1인당 요금(price_per_person) 기준 4분위수(Q1~Q4) 균등 분할 (PROC RANK)
 *   - [Step 1] 전체 표본 상관분석 (PROC CORR) -> r = -0.175, rs = -0.247
 *   - [Step 2] 4분위별 평균/중앙값/신뢰구간 산출 (PROC MEANS) -> Q1(4.892) 최고점, Q4(4.788) 최저점
 *   - [Step 3] 집단 간 차이 일원분산분석 및 Tukey HSD 사후검정 (PROC GLM)
 *   - [Step 4] 요약 보고서 테이블 출력 (PROC REPORT)
 *   - [Step 5] 추세선(VLINE) 및 박스플롯(VBOX) 시각화 (PROC SGPLOT)
 *   - [결론] 순환 논리 및 내생성 문제로 인해 향후 가격 회귀 모델에서 가성비(rating_value) 제외 확정
 ***************************************************************************************************/

/* 1. 환경 설정 및 라이브러리 지정 */
%let airbnb_path = ~/airbnb; /* 사용 환경에 맞추어 경로 수정 가능 */
libname airbnb "&airbnb_path";

/* 분석 대상 데이터셋 */
%let input_ds = airbnb.airbnb_final_per_person; 

ods graphics on / reset=all width=950px height=480px imagemap=on;


/*=================================================================================================*
 * [RESULTS 리포트 서두] 분석 목적 및 핵심 결론 요약 (PROC ODSTEXT)
 *=================================================================================================*/

proc odstext;
    p "==================================================================================================" / style=[color=#333333 font_weight=bold];
    p "[1인당 1박 요금(price_per_person) 기준 가성비 평점 분석]" / style=[font_size=13pt font_weight=bold color=#222222];
    p "1. 분석 목적: 1인당 1박 요금(price_per_person)과 가성비 평점(rating_value) 간의 연관성 및 가격 분위별 평점 분포를 분석합니다." / style=[font_size=10pt color=#222222];
    p "2. 핵심 발견: 1인당 요금이 비싸질수록 가성비 평점이 점진적으로 하락하는 우하향(단조 감소) 패턴이 나타납니다. 1인당 최저가 구간(Q1)에서 평점(4.892점)이 가장 높고, 최고가 구간(Q4)에서 평점(4.788점)이 가장 낮습니다." / style=[font_size=10pt color=#222222];
    p "3. 최종 모델링 결론: 가성비(rating_value) 평점은 '가격 대비 가치'를 묻는 항목으로서 종속변수(가격) 자체를 이미 분모에 포함하고 있는 내생적 변수이므로, 향후 가격 결정 다중회귀분석 모델에서는 '가성비(rating_value)' 변수를 완전히 제외(제거)하고 분석을 진행합니다." / style=[font_size=10.5pt font_weight=bold color=#222222];
    p "==================================================================================================" / style=[color=#333333 font_weight=bold];
run;


/*=================================================================================================*
 * 2. 데이터 전처리 및 1인당 요금 4분위수(Quartile) 구간 분할
 *=================================================================================================*/

/* 2-1. 결측치 없는 유효 분석 표본(1,170건) 추출 */
data work.clean_data;
    set &input_ds;
    where not missing(rating_value) 
      and not missing(price_per_person) 
      and not missing(log_price_per_person);
run;

/* 2-2. 1인당 1박 요금(price_per_person) 기준 4분위수 분할 (각 25%씩 균등 배분) */
proc rank data=work.clean_data groups=4 out=work.ranked_data;
    var price_per_person;
    ranks price_q; /* 0: Q1, 1: Q2, 2: Q3, 3: Q4 */
run;

/* 2-3. 분위수 라벨 부여 */
data work.airbnb_analyzed;
    set work.ranked_data;
    length tier_code $2 tier_label $22 tier_desc $35;
    
    if price_q = 0 then do;
        tier_code  = "01";
        tier_label = "Q1 (Bottom 25%)";
        tier_desc  = "Low ($2.9 - $26.4)";
    end;
    else if price_q = 1 then do;
        tier_code  = "02";
        tier_label = "Q2 (25-50%)";
        tier_desc  = "Mid-Low ($26.5 - $38.9)";
    end;
    else if price_q = 2 then do;
        tier_code  = "03";
        tier_label = "Q3 (50-75%)";
        tier_desc  = "Mid-High ($39.0 - $61.6)";
    end;
    else if price_q = 3 then do;
        tier_code  = "04";
        tier_label = "Q4 (Top 25%)";
        tier_desc  = "High ($61.7 - $2,048.7)";
    end;
run;


/*=================================================================================================*
 * 3. [Step 1] 전체 표본 상관분석: 1인당 로그 요금 vs 가성비 평점
 *=================================================================================================*/

title bold color=navy "Step 1. Correlation: Price Per Person vs Rating Value";
title2 italic "Total Sample (N=1,170): Negative correlation (Pearson r = -0.175, Spearman rs = -0.247)";

proc corr data=work.airbnb_analyzed pearson spearman nosimple;
    var rating_value;
    with log_price_per_person;
run;
title; title2;

/* Step 1 결과 해설 블록 출력 */
proc odstext;
    p "[Step 1 결과 해설: 전체 표본 상관분석]" / style=[font_size=11pt font_weight=bold color=#222222];
    p "· 피어슨 상관계수 r = -0.1749 (p < .0001), 스피어만 상관계수 rs = -0.2471 (p < .0001)로 유의한 음(-)의 상관관계가 나타납니다." / style=[font_size=10pt color=#222222];
    p "· 즉, 1인당 지불 금액이 높아질수록 게스트가 느끼는 체감 가성비는 전반적으로 감소하는 경향을 보입니다." / style=[font_size=10pt color=#222222];
run;


/*=================================================================================================*
 * 4. [Step 2] 1인당 요금 4분위수(Q1~Q4)별 가성비 평점 기술통계
 *=================================================================================================*/

proc sort data=work.airbnb_analyzed;
    by tier_code tier_label;
run;

title bold color=navy "Step 2. Value Rating Statistics across 4 Price-Per-Person Quartiles";
title2 italic "Q1 has the highest rating (4.892), progressively dropping to Q4 (4.788)";

proc means data=work.airbnb_analyzed n min max mean std median clm maxdec=3;
    by tier_code tier_label tier_desc;
    var rating_value;
    output out=work.quartile_means(drop=_type_ _freq_)
        n(rating_value)        = sample_n
        min(price_per_person)  = price_min
        max(price_per_person)  = price_max
        mean(rating_value)     = mean_val
        std(rating_value)      = std_val
        median(rating_value)   = median_val
        lclm(rating_value)     = lclm_val
        uclm(rating_value)     = uclm_val;
run;
title; title2;

/* Step 2 결과 해설 블록 출력 */
proc odstext;
    p "[Step 2 결과 해설: 1인당 가격 분위별 가성비 평점 평균]" / style=[font_size=11pt font_weight=bold color=#222222];
    p "  · Q1 (인당 $2.9 ~ $26.4)    : 평균 4.892점 (중앙값 4.94) - 전체 1위 (다인실/가족 숙소의 인당 비용 효율 반영)" / style=[font_size=10pt color=#222222];
    p "  · Q2 (인당 $26.5 ~ $38.9)   : 평균 4.882점 (중앙값 4.92) - Q1과 대등한 높은 만족도 유지" / style=[font_size=10pt color=#222222];
    p "  · Q3 (인당 $39.0 ~ $61.6)   : 평균 4.852점 (중앙값 4.88) - 점진적 하락세" / style=[font_size=10pt color=#222222];
    p "  · Q4 (인당 $61.7 ~ $2,048.7): 평균 4.788점 (중앙값 4.83) - 전체 최하위 평점 (1인당 고비용에 따른 엄격한 잣대)" / style=[font_size=10pt color=#222222];
    p "· 요약: 1인당 가격 구간이 높아질수록 가성비 평점 평균이 Q1(4.892)에서 Q4(4.788)까지 일관되게 하락하는 단조 감소 형태를 나타냅니다." / style=[font_size=10pt font_weight=bold color=#222222];
run;


/*=================================================================================================*
 * 5. [Step 3] 집단 간 평균 차이 검정: 일원분산분석(ANOVA) 및 사후검정(Tukey HSD)
 *=================================================================================================*/

title bold color=navy "Step 3. One-Way ANOVA: Testing Value Rating Differences Across Price Tiers";
title2 italic "Testing whether value rating differences across per-person price tiers are significant";

proc glm data=work.airbnb_analyzed;
    class tier_label;
    model rating_value = tier_label;
    means tier_label / tukey cldiff;
    ods output ModelANOVA=work.anova_results;
run;
quit;
title; title2;

/* Step 3 결과 해설 블록 출력 */
proc odstext;
    p "[Step 3 결과 해설: 집단 간 평균 차이 검정 (ANOVA 및 Tukey HSD)]" / style=[font_size=11pt font_weight=bold color=#222222];
    p "1. 일원분산분석(ANOVA): F = 15.07 (p < .0001)로 1인당 요금 분위 간 가성비 평점 차이는 통계적으로 극도로 유의합니다." / style=[font_size=10pt color=#222222];
    p "2. Tukey 사후검정 결과 (유의미 vs 무의미 분리):" / style=[font_size=10pt font_weight=bold color=#222222];
    p "  [통계적으로 유의미한 차이: 오직 초고가(Q4) 구간만 해당 (***)]" / style=[font_size=10pt font_weight=bold color=#222222];
    p "  · Q1 vs Q4 (차이: 0.103점, p < .0001, ***): 초고가(Q4)가 최저가(Q1) 대비 0.1점 이상 유의하게 낮음" / style=[font_size=10pt color=#222222];
    p "  · Q2 vs Q4 (차이: 0.093점, p < .0001, ***): 초고가(Q4)가 중저가(Q2) 대비로도 유의하게 낮음" / style=[font_size=10pt color=#222222];
    p "  · Q3 vs Q4 (차이: 0.064점, p = 0.0012, ***): 초고가(Q4)가 중고가(Q3) 대비로도 유의하게 낮음" / style=[font_size=10pt color=#222222];
    p "  [통계적으로 유의미한 차이 없음: 저가 ~ 중고가 구간 (차이 없음)]" / style=[font_size=10pt font_weight=bold color=#222222];
    p "  · Q1 vs Q2, Q1 vs Q3, Q2 vs Q3: 구간 간 평점 차이가 0.01~0.03점에 불과하여 통계적 차이 없음 (대등한 만족도)" / style=[font_size=10pt color=#222222];
    p "· 핵심 결론: 가성비 감점은 저가와 중가 사이에서는 발생하지 않으며, 오직 '1인당 초고가(Q4, 인당 $62 이상)' 구간에서만 집중적으로 발생합니다." / style=[font_size=10pt font_weight=bold color=#222222];
run;


/*=================================================================================================*
 * 6. [Step 4] 종합 요약 보고서 테이블 출력 (PROC REPORT)
 *=================================================================================================*/

data work.report_table;
    set work.quartile_means;
    
    length price_range $22 rating_ci $28 pattern_note $40;
    
    price_range = cats("$", put(price_min, 6.1), " ~ $", put(price_max, comma8.1));
    rating_ci   = cats(put(mean_val, 5.3), " [", put(lclm_val, 5.3), ", ", put(uclm_val, 5.3), "]");
    
    if tier_code = "01" then pattern_note = "Highest (4.892) -> High Satisfaction";
    else if tier_code = "02" then pattern_note = "High (4.882) -> Statistically equal to Q1";
    else if tier_code = "03" then pattern_note = "Moderate drop (4.852)";
    else if tier_code = "04" then pattern_note = "Steep drop (4.788) -> Strong Penalty";
run;

title bold color=navy "==================================================================================";
title2 bold color=navy "Step 4. Summary Table: Value Rating Mean Comparison by Price-Per-Person Quartile";
title3 italic "Monotonic decrease: Value rating drops progressively as per-person price increases";

proc report data=work.report_table nowd
    style(header)=[backgroundcolor=#2B547E color=white font_weight=bold textalign=center]
    style(column)=[font_size=10pt];
    
    column tier_label sample_n price_range rating_ci std_val median_val pattern_note;
    
    define tier_label   / display "Per-Person Tier" style(column)=[just=left font_weight=bold width=16%];
    define sample_n     / display "N" style(column)=[just=center width=7%];
    define price_range  / display "Per-Person Price (USD)" style(column)=[just=center width=17%];
    define rating_ci    / display "Value Mean [95% CI]" style(column)=[just=center width=18%];
    define std_val      / display "Std Dev" format=6.3 style(column)=[just=right width=8%];
    define median_val   / display "Median" format=5.2 style(column)=[just=right width=7%];
    define pattern_note / display "Trend / Finding" style(column)=[just=left font_weight=bold width=27%];
run;
title; title2; title3;


/*=================================================================================================*
 * 7. [Step 5] 시각화 검증: 단조 감소(우하향) 관계의 시각적 증명
 *=================================================================================================*/

/* 7-1. 1인당 가격 분위별 가성비 평점 평균 및 95% 신뢰구간 추세선 (VLINE) */
title bold "Plot 1. Value Rating Means with 95% CI across Per-Person Price Quartiles";
title2 italic "Visualizing Monotonic Decrease: Q1 (4.892) -> Q2 (4.882) -> Q3 (4.852) -> Q4 (4.788)";

proc sgplot data=work.airbnb_analyzed;
    vline tier_label / response=rating_value stat=mean limitstat=clm 
                       markers markerattrs=(symbol=circlefilled size=9 color=crimson)
                       lineattrs=(color=navy thickness=2);
    yaxis label="Mean Value Rating (rating_value)" min=4.75 max=4.95 grid;
    xaxis label="Price-Per-Person Quartile (Tier)";
run;
title; title2;

/* 7-2. 1인당 가격 분위별 가성비 평점 분포 박스플롯 (VBOX) */
title bold "Plot 2. Value Rating Distribution (Boxplot) by Per-Person Price Quartile";
title2 italic "Downward outliers concentrated in Q4 (High per-person price)";

proc sgplot data=work.airbnb_analyzed;
    vbox rating_value / category=tier_label fillattrs=(color=lightblue)
                        medianattrs=(color=crimson thickness=2);
    yaxis label="Value Rating (rating_value)" min=3.5 max=5.0 grid;
    xaxis label="Price-Per-Person Quartile (Tier)";
run;
title; title2;

ods graphics off;

/* Step 5 시각화 결과 해설 블록 출력 */
proc odstext;
    p "[Step 5 시각화 결과 해설: 우하향 추세선 및 평점 분포]" / style=[font_size=11pt font_weight=bold color=#222222];
    p "1. 평균 추세선 (Plot 1): 1인당 가격 분위가 올라갈수록 평균 가성비 평점이 아래로 지속 하락하는 '우하향 추세선'을 형성합니다." / style=[font_size=10pt color=#222222];
    p "2. 평점 분포 (Plot 2): 1인당 요금이 가장 높은 Q4 구간에서 평점의 표준편차(0.308)가 가장 크며, 하위 이상치(Outlier)들이 집중적으로 발생합니다." / style=[font_size=10pt color=#222222];
run;


/*=================================================================================================*
 * 8. [종합 결론] 수미상관 최종 요약 및 변수 처리 방향
 *=================================================================================================*/

proc odstext;
    p "==================================================================================================" / style=[color=#333333 font_weight=bold];
    p "[종합 결론: 1인당 가격 기준 분석 요약 및 모델링 반영]" / style=[font_size=12pt font_weight=bold color=#222222];
    p "1. 가성비 평점 구조: 1인당 요금 기준에서는 가격이 높을수록 가성비 평점이 하락하는 음(-)의 관계가 명확히 확인되었습니다 (Q1: 4.892점 -> Q4: 4.788점)." / style=[font_size=10pt color=#222222];
    p "2. 최종 모델링 반영: 가성비(rating_value) 평점은 '가격 대비 가치'를 평가한 지표로서 종속변수(가격) 자체를 분모로 품고 있는 내생적 변수(순환 논리)이므로, 향후 가격 결정 다중회귀분석 모델에서는 '가성비(rating_value)' 변수를 완전히 제외(제거)하고 분석을 진행합니다." / style=[font_size=10.5pt font_weight=bold color=#222222];
    p "==================================================================================================" / style=[color=#333333 font_weight=bold];
run;
