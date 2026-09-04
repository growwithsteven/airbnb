/*
   Airbnb 평점·리뷰 이변량분석
   입력: airbnb_final_per_person.sas7bdat
   목적: 종합 만족도(guest_satisfaction)를 기준으로 세부 평점 및 리뷰 수와의
         관계를 상관분석, 산점도, 단순선형회귀로 확인한다.
*/

options nodate nonumber validvarname=any;
ods graphics on;

/* SAS Studio Files(Home)/airbnb 폴더를 자동으로 가리킵니다. */
%let data_dir=%sysget(HOME)/airbnb;
libname indata "&data_dir";

data work.airbnb;
    set indata.airbnb_final_per_person(
        rename=(
            rating_guestSatisfaction=guest_satisfaction
            rating_accuracy=accuracy
            rating_cleanliness=cleanliness
            rating_checking=checking
            rating_communication=communication
            rating_location=location
            rating_value=value
            rating_reviewsCount=reviews_count
        )
    );
    label
        guest_satisfaction = '종합 만족도'
        accuracy           = '정확성'
        cleanliness        = '청결도'
        checking           = '체크인 편의성'
        communication      = '의사소통'
        location           = '위치'
        value              = '가성비'
        reviews_count      = '총 리뷰 수';
run;

title1 'Airbnb 평점·리뷰 이변량분석';
title2 '입력 데이터 및 변수 품질 점검';

proc contents data=work.airbnb varnum;
run;

proc means data=work.airbnb n nmiss mean std min p25 median p75 max maxdec=3;
    var guest_satisfaction accuracy cleanliness checking communication location value
        reviews_count;
run;

/* 종합 만족도와 각 세부 평점·리뷰 수의 Pearson/Spearman 상관 */
title2 '종합 만족도와 세부 변수의 상관분석';
proc corr data=work.airbnb pearson spearman nosimple;
    var guest_satisfaction;
    with accuracy cleanliness checking communication location value
         reviews_count;
run;

/* 세부 평점 전체의 상호 상관행렬 */
title2 '세부 평점 변수 간 상관행렬';
proc corr data=work.airbnb pearson spearman nosimple;
    var accuracy cleanliness checking communication location value guest_satisfaction;
run;

/* 종합 만족도를 결과변수로 한 단순선형회귀 */
title2 '종합 만족도 단순선형회귀';
proc reg data=work.airbnb plots(only)=(fitplot residualplot qqplot);
    model guest_satisfaction = accuracy / clb stb vif;
    model guest_satisfaction = cleanliness / clb stb vif;
    model guest_satisfaction = checking / clb stb vif;
    model guest_satisfaction = communication / clb stb vif;
    model guest_satisfaction = location / clb stb vif;
    model guest_satisfaction = value / clb stb vif;
    model guest_satisfaction = reviews_count / clb stb vif;
run;
quit;

/* 변수별 이변량 그래프: 산점도 + 선형회귀선 + LOESS 추세선 */
%macro bivar_plot(x=, label=);
    title2 "종합 만족도와 &label";
    proc sgplot data=work.airbnb;
        scatter x=&x y=guest_satisfaction / transparency=0.55;
        reg x=&x y=guest_satisfaction / cli lineattrs=(color=red thickness=2);
        loess x=&x y=guest_satisfaction / lineattrs=(color=blue pattern=shortdash);
        xaxis label="&label";
        yaxis label='종합 만족도';
    run;
%mend;

%bivar_plot(x=accuracy,      label=정확성);
%bivar_plot(x=cleanliness,   label=청결도);
%bivar_plot(x=checking,      label=체크인 편의성);
%bivar_plot(x=communication, label=의사소통);
%bivar_plot(x=location,      label=위치);
%bivar_plot(x=value,         label=가성비);
%bivar_plot(x=reviews_count, label=총 리뷰 수);

/* 8개 지정 변수의 전체 쌍별 산점도 행렬 */
title2 '평점 변수 전체 산점도 행렬';
proc sgscatter data=work.airbnb;
    matrix guest_satisfaction accuracy cleanliness checking communication location value reviews_count
        / reg;
run;

title;
ods graphics off;
