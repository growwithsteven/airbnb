/*
목적: 각 세부 평점과 종합 평점의 관련성을 확인한다.
Y: rating_guestSatisfaction / X: 정확성·체크인·청결·소통·위치·가성비 평점
방법: 상관분석·단순회귀·다중회귀 및 산점도와 선형회귀선
*/
options nodate nonumber;
libname src "%sysget(HOME)/airbnb" access=readonly;
ods graphics on;
title1 'Overall Satisfaction and Detailed Ratings';

proc odstext;
    p '분석 목적: 세부 평점 6개가 각각 종합 평점과 얼마나 관련되는지 확인한다.';
    p '판단 기준: p값으로 관계의 유의성을, R²로 종합 평점의 변동 설명률을 평가한다. 변수의 유지·제외 결론은 실행 결과를 확인한 후 결정한다.';
run;

/* 1. 입력 변수와 결측 수 확인 */
data work.raw;
    set src.airbnb_final_nightly(keep=listing_id
        rating_guestSatisfaction rating_accuracy rating_checking rating_cleanliness
        rating_communication rating_location rating_value
    );
run;

proc means data=work.raw n nmiss mean std min max;
    var
        rating_guestSatisfaction rating_accuracy rating_checking rating_cleanliness
        rating_communication rating_location rating_value;
run;

/* 2. 동일 ID를 변수별 평균으로 통합해 숙소당 한 행을 만든다.
   현재 중복 숙소의 종합 평점과 세부 평점은 동일하다.
   ID 결측은 제외하며, Y·X 중 하나라도 결측인 숙소는 분석에서 제외한다. */
proc means data=work.raw nway noprint;
    where not missing(listing_id);
    class listing_id;
    var
        rating_guestSatisfaction rating_accuracy rating_checking rating_cleanliness
        rating_communication rating_location rating_value;
    output out=work.listings(drop=_type_ _freq_) mean=;
run;

data work.analysis;
    set work.listings;
    if nmiss(of
        rating_guestSatisfaction rating_accuracy rating_checking rating_cleanliness
        rating_communication rating_location rating_value) = 0;
run;

/* 3. Y와 각 X의 상관분석 */
title2 'Pearson and Spearman Correlations';
proc corr data=work.analysis pearson spearman fisher(biasadj=no) nosimple;
    var
        rating_accuracy rating_checking rating_cleanliness rating_communication
        rating_location rating_value;
    with rating_guestSatisfaction;
run;

proc odstext;
    p '상관분석 해석: Pearson은 선형 관계, Spearman은 순위에 따른 관계를 보여준다. 두 검정의 p값은 각각 확인한다.';
    p '보정하지 않은 p값이 0.05 이상이면 해당 검정에서 유의한 관계가 확인되지 않은 것이다. 상관계수의 크기와 아래 R²를 함께 확인한다.';
run;

/* 4. 변수별 단순회귀 결과표·해석 안내·산점도 */
title2 'rating_guestSatisfaction vs rating_accuracy';
proc reg data=work.analysis plots=none;
    model rating_guestSatisfaction = rating_accuracy / clb stb;
run;
quit;

proc odstext;
    p '정확성 평점(rating_accuracy): R² × 100은 이 평점 하나로 설명되는 종합 평점 변동의 백분율이다.';
    p '해당 변수 행의 회귀계수는 세부 평점이 1점 높을 때의 종합 평점 차이이며, p값은 그 기울기가 0과 다른지 검정한다. 유의성과 설명력을 구분해 판단한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_accuracy y=rating_guestSatisfaction / transparency=0.6;
    reg x=rating_accuracy y=rating_guestSatisfaction / nomarkers lineattrs=(color=red);
run;

title2 'rating_guestSatisfaction vs rating_checking';
proc reg data=work.analysis plots=none;
    model rating_guestSatisfaction = rating_checking / clb stb;
run;
quit;

proc odstext;
    p '체크인 평점(rating_checking): R² × 100은 이 평점 하나로 설명되는 종합 평점 변동의 백분율이다.';
    p '해당 변수 행의 회귀계수는 세부 평점이 1점 높을 때의 종합 평점 차이이며, p값은 그 기울기가 0과 다른지 검정한다. 유의성과 설명력을 구분해 판단한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_checking y=rating_guestSatisfaction / transparency=0.6;
    reg x=rating_checking y=rating_guestSatisfaction / nomarkers lineattrs=(color=red);
run;

title2 'rating_guestSatisfaction vs rating_cleanliness';
proc reg data=work.analysis plots=none;
    model rating_guestSatisfaction = rating_cleanliness / clb stb;
run;
quit;

proc odstext;
    p '청결 평점(rating_cleanliness): R² × 100은 이 평점 하나로 설명되는 종합 평점 변동의 백분율이다.';
    p '해당 변수 행의 회귀계수는 세부 평점이 1점 높을 때의 종합 평점 차이이며, p값은 그 기울기가 0과 다른지 검정한다. 유의성과 설명력을 구분해 판단한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_cleanliness y=rating_guestSatisfaction / transparency=0.6;
    reg x=rating_cleanliness y=rating_guestSatisfaction / nomarkers lineattrs=(color=red);
run;

title2 'rating_guestSatisfaction vs rating_communication';
proc reg data=work.analysis plots=none;
    model rating_guestSatisfaction = rating_communication / clb stb;
run;
quit;

proc odstext;
    p '소통 평점(rating_communication): R² × 100은 이 평점 하나로 설명되는 종합 평점 변동의 백분율이다.';
    p '해당 변수 행의 회귀계수는 세부 평점이 1점 높을 때의 종합 평점 차이이며, p값은 그 기울기가 0과 다른지 검정한다. 유의성과 설명력을 구분해 판단한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_communication y=rating_guestSatisfaction / transparency=0.6;
    reg x=rating_communication y=rating_guestSatisfaction / nomarkers lineattrs=(color=red);
run;

title2 'rating_guestSatisfaction vs rating_location';
proc reg data=work.analysis plots=none;
    model rating_guestSatisfaction = rating_location / clb stb;
run;
quit;

proc odstext;
    p '위치 평점(rating_location): R² × 100은 이 평점 하나로 설명되는 종합 평점 변동의 백분율이다.';
    p '해당 변수 행의 회귀계수는 세부 평점이 1점 높을 때의 종합 평점 차이이며, p값은 그 기울기가 0과 다른지 검정한다. 유의성과 설명력을 구분해 판단한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_location y=rating_guestSatisfaction / transparency=0.6;
    reg x=rating_location y=rating_guestSatisfaction / nomarkers lineattrs=(color=red);
run;

title2 'rating_guestSatisfaction vs rating_value';
proc reg data=work.analysis plots=none;
    model rating_guestSatisfaction = rating_value / clb stb;
run;
quit;

proc odstext;
    p '가성비 평점(rating_value): R² × 100은 이 평점 하나로 설명되는 종합 평점 변동의 백분율이다.';
    p '해당 변수 행의 회귀계수는 세부 평점이 1점 높을 때의 종합 평점 차이이며, p값은 그 기울기가 0과 다른지 검정한다. 유의성과 설명력을 구분해 판단한다.';
run;

proc sgplot data=work.analysis;
    scatter x=rating_value y=rating_guestSatisfaction / transparency=0.6;
    reg x=rating_value y=rating_guestSatisfaction / nomarkers lineattrs=(color=red);
run;

/* 5. 다른 X를 함께 고려한 다중회귀: VIF로 다중공선성 확인 */
title2 'Multiple Linear Regression';
proc reg data=work.analysis plots=none;
    model rating_guestSatisfaction =
        rating_accuracy rating_checking rating_cleanliness rating_communication
        rating_location rating_value
        / clb stb vif;
run;
quit;

proc odstext;
    p '다중회귀 해석: 각 계수는 다른 세부 평점을 같게 두었을 때의 관련성이다. 앞의 변수별 단순회귀와는 다른 질문에 답한다.';
    p '이 표의 R²는 세부 평점 6개가 함께 설명하는 비율이다. VIF가 높으면 변수들이 공유하는 정보가 많으므로 계수만으로 중요도를 단정하지 않는다.';
run;

title;
ods graphics off;
libname src clear;
