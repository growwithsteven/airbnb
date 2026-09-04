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
        guest_satisfaction = 'Overall Satisfaction'
        accuracy           = 'Accuracy'
        cleanliness        = 'Cleanliness'
        checking           = 'Check-in Convenience'
        communication      = 'Communication'
        location           = 'Location'
        value              = 'Value'
        reviews_count      = 'Review Count';
run;

title1 'Airbnb Rating and Review Bivariate Analysis';
title2 'Input Data and Variable Quality Check';

proc contents data=work.airbnb varnum;
run;

proc means data=work.airbnb n nmiss mean std min p25 median p75 max maxdec=3;
    var guest_satisfaction accuracy cleanliness checking communication location value
        reviews_count;
run;

/* 종합 만족도와 각 세부 평점·리뷰 수의 Pearson/Spearman 상관 */
title2 'Correlation with Overall Satisfaction';
proc corr data=work.airbnb pearson spearman nosimple;
    var guest_satisfaction;
    with accuracy cleanliness checking communication location value
         reviews_count;
run;

/* 세부 평점 전체의 상호 상관행렬 */
title2 'Correlation Matrix of Rating Variables';
proc corr data=work.airbnb pearson spearman nosimple;
    var accuracy cleanliness checking communication location value guest_satisfaction;
run;

/* 종합 만족도를 결과변수로 한 단순선형회귀 */
title2 'Simple Linear Regression for Overall Satisfaction';
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
    title2 "Overall Satisfaction vs &label";
    proc sgplot data=work.airbnb;
        scatter x=&x y=guest_satisfaction / transparency=0.55;
        reg x=&x y=guest_satisfaction / cli lineattrs=(color=red thickness=2);
        loess x=&x y=guest_satisfaction / lineattrs=(color=blue pattern=shortdash);
        xaxis label="&label";
        yaxis label='Overall Satisfaction';
    run;
%mend;

%bivar_plot(x=accuracy,      label=Accuracy);
%bivar_plot(x=cleanliness,   label=Cleanliness);
%bivar_plot(x=checking,      label=Check-in Convenience);
%bivar_plot(x=communication, label=Communication);
%bivar_plot(x=location,      label=Location);
%bivar_plot(x=value,         label=Value);
%bivar_plot(x=reviews_count, label=Review Count);

/* 8개 지정 변수의 전체 쌍별 산점도 행렬 */
title2 'Scatterplot Matrix of Selected Variables';
proc sgscatter data=work.airbnb;
    matrix guest_satisfaction accuracy cleanliness checking communication location value reviews_count
        ;
run;

title;
ods graphics off;
