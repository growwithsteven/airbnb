/*
목적: 리뷰 관련 변수 8개를 각각 숙소 가격과 비교한다.
Y: log_price / X: 세부 평점 6개, 종합 평점, 리뷰 수
방법: 변수별 상관분석·단순회귀 및 산점도와 선형회귀선
*/
options nodate nonumber;
libname src "%sysget(HOME)/airbnb" access=readonly;
ods graphics on;
title1 'Nightly Price and Review Variables';

/* 출력 해석은 검토한 2026-09-07 결과 기준이며, 데이터 변경 시 갱신한다. */
proc odstext;
    p '결론: 리뷰 관련 변수 8개는 각각의 단순회귀에서 가격 설명력이 매우 낮으므로, 후속 가격 예측모형의 후보에서 모두 제외한다.';
    p '로그 가격의 변동 설명률은 약 0~3.39%이다. 제외 판단의 근거를 보여주기 위해 아래 분석과 그래프는 8개 모두 유지한다.';
run;

/* 1. 입력 변수와 결측 수 확인 */
data work.raw;
    set src.airbnb_final_nightly(keep=listing_id
        log_price rating_accuracy rating_checking rating_cleanliness
        rating_communication rating_location rating_value rating_guestSatisfaction
        rating_reviewsCount
    );
run;

proc means data=work.raw n nmiss mean std min max;
    var
        log_price rating_accuracy rating_checking rating_cleanliness
        rating_communication rating_location rating_value rating_guestSatisfaction
        rating_reviewsCount;
run;

/* 2. 동일 ID를 변수별 평균으로 통합해 숙소당 한 행을 만든다.
   현재 중복 숙소의 평점·리뷰 수는 동일하다. log_price는 로그값을 평균한다.
   ID 결측은 제외하며, Y·X 중 하나라도 결측인 숙소는 분석에서 제외한다. */
proc means data=work.raw nway noprint;
    where not missing(listing_id);
    class listing_id;
    var
        log_price rating_accuracy rating_checking rating_cleanliness
        rating_communication rating_location rating_value rating_guestSatisfaction
        rating_reviewsCount;
    output out=work.listings(drop=_type_ _freq_) mean=;
run;

data work.analysis;
    set work.listings;
    if nmiss(of
        log_price rating_accuracy rating_checking rating_cleanliness
        rating_communication rating_location rating_value rating_guestSatisfaction
        rating_reviewsCount) = 0;
run;

/* 3. Y와 각 X의 상관분석 */
title2 'Pearson and Spearman Correlations';
proc corr data=work.analysis pearson spearman fisher(biasadj=no) nosimple;
    var
        rating_accuracy rating_checking rating_cleanliness rating_communication
        rating_location rating_value rating_guestSatisfaction rating_reviewsCount;
    with log_price;
run;

proc odstext;
    p '유의성 기준: 보정하지 않은 p값 0.05.';
    p 'Pearson에서 유의하지 않은 변수: rating_checking(p=0.9372), rating_communication(p=0.2477), rating_reviewsCount(p=0.4789). 개별 선형 관계의 유의성 기준에 따라 후속 후보에서 제외한다.';
    p 'Spearman에서 유의하지 않은 변수: rating_value(p=0.0530). 순위 상관의 유의성 기준을 적용하면 제외 대상이다.';
    p '두 검정의 제외 대상은 서로 다르다. 최종적으로는 아래 단순회귀의 낮은 R²를 근거로 8개 모두를 후속 후보에서 제외하며, 근거 제시를 위한 분석은 유지한다.';
run;

/* 4. 변수별 단순회귀 결과표와 산점도 */
title2 'log_price vs rating_accuracy';
proc reg data=work.analysis plots=none;
    model log_price = rating_accuracy / clb stb;
run;
quit;

proc odstext;
    p 'rating_accuracy: R²=0.0033, 로그 가격 변동 설명률은 0.33%로 매우 낮다. 단독 선형 설명력이 부족하므로 후속 가격 예측모형의 후보에서 제외한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_accuracy y=log_price / transparency=0.6;
    reg x=rating_accuracy y=log_price / nomarkers lineattrs=(color=red);
run;

title2 'log_price vs rating_checking';
proc reg data=work.analysis plots=none;
    model log_price = rating_checking / clb stb;
run;
quit;

proc odstext;
    p 'rating_checking: R²=0.0000, 로그 가격 변동 설명률은 약 0%로 매우 낮다. 단독 선형 설명력이 부족하므로 후속 가격 예측모형의 후보에서 제외한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_checking y=log_price / transparency=0.6;
    reg x=rating_checking y=log_price / nomarkers lineattrs=(color=red);
run;

title2 'log_price vs rating_cleanliness';
proc reg data=work.analysis plots=none;
    model log_price = rating_cleanliness / clb stb;
run;
quit;

proc odstext;
    p 'rating_cleanliness: R²=0.0339로 로그 가격 변동의 3.39%를 설명하며, 평점 관련 지표 중 설명력이 가장 높다.';
    p '다만 별도 상세 분석에서는 숙소 타입과 높은 다중공선성이 나타났다. 단독 숙소는 청결 평점이 높고 도미토리는 낮은 경향을 보여, 청결 평점과 가격의 관계에는 숙소 타입의 차이가 반영되어 있을 수 있다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_cleanliness y=log_price / transparency=0.6;
    reg x=rating_cleanliness y=log_price / nomarkers lineattrs=(color=red);
run;

title2 'log_price vs rating_communication';
proc reg data=work.analysis plots=none;
    model log_price = rating_communication / clb stb;
run;
quit;

proc odstext;
    p 'rating_communication: R²=0.0011, 로그 가격 변동 설명률은 0.11%로 매우 낮다. 단독 선형 설명력이 부족하므로 후속 가격 예측모형의 후보에서 제외한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_communication y=log_price / transparency=0.6;
    reg x=rating_communication y=log_price / nomarkers lineattrs=(color=red);
run;

title2 'log_price vs rating_location';
proc reg data=work.analysis plots=none;
    model log_price = rating_location / clb stb;
run;
quit;

proc odstext;
    p 'rating_location: R²=0.0089, 로그 가격 변동 설명률은 0.89%로 매우 낮다. 단독 선형 설명력이 부족하므로 후속 가격 예측모형의 후보에서 제외한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_location y=log_price / transparency=0.6;
    reg x=rating_location y=log_price / nomarkers lineattrs=(color=red);
run;

title2 'log_price vs rating_value';
proc reg data=work.analysis plots=none;
    model log_price = rating_value / clb stb;
run;
quit;

proc odstext;
    p 'rating_value: R²=0.0103, 로그 가격 변동 설명률은 1.03%로 매우 낮다. 단독 선형 설명력이 부족하므로 후속 가격 예측모형의 후보에서 제외한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_value y=log_price / transparency=0.6;
    reg x=rating_value y=log_price / nomarkers lineattrs=(color=red);
run;

title2 'log_price vs rating_guestSatisfaction';
proc reg data=work.analysis plots=none;
    model log_price = rating_guestSatisfaction / clb stb;
run;
quit;

proc odstext;
    p 'rating_guestSatisfaction: R²=0.0056, 로그 가격 변동 설명률은 0.56%로 매우 낮다. 단독 선형 설명력이 부족하므로 후속 가격 예측모형의 후보에서 제외한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_guestSatisfaction y=log_price / transparency=0.6;
    reg x=rating_guestSatisfaction y=log_price / nomarkers lineattrs=(color=red);
run;

title2 'log_price vs rating_reviewsCount';
proc reg data=work.analysis plots=none;
    model log_price = rating_reviewsCount / clb stb;
run;
quit;

proc odstext;
    p 'rating_reviewsCount: R²=0.0004, 로그 가격 변동 설명률은 0.04%로 매우 낮다. 단독 선형 설명력이 부족하므로 후속 가격 예측모형의 후보에서 제외한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_reviewsCount y=log_price / transparency=0.6;
    reg x=rating_reviewsCount y=log_price / nomarkers lineattrs=(color=red);
run;

title;
ods graphics off;
libname src clear;
