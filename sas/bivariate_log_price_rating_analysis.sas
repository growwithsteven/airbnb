/*
   Airbnb 평점·리뷰 수 이변량 분석
   입력: airbnb_final_per_person.sas7bdat (동일 원본 데이터베이스)
   Y   : log_price_per_person (1인당 1박 요금의 자연로그)
   X   : guest_satisfaction, accuracy, cleanliness, checking,
         communication, location, value, reviews_count
*/

options nodate nonumber validvarname=any;
ods graphics on / reset=all width=900px height=520px imagemap=on;

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
    /* 리뷰 수가 0이어도 유효하므로 log(1+x)를 사용한다. 보조 시각화용 변수이다. */
    if reviews_count >= 0 then log1p_reviews_count=log(1 + reviews_count);
    label
        log_price_per_person = 'Log Price per Person'
        guest_satisfaction   = 'Overall Satisfaction'
        accuracy             = 'Accuracy'
        cleanliness          = 'Cleanliness'
        checking             = 'Check-in Convenience'
        communication        = 'Communication'
        location             = 'Location'
        value                = 'Value for Money'
        reviews_count        = 'Review Count'
        log1p_reviews_count  = 'Log(1 + Review Count)';
run;

title1 'Airbnb Bivariate Analysis: Ratings/Reviews vs Log Price per Person';
title2 'Input Data and Variable Quality Check';
proc contents data=work.airbnb varnum;
run;

proc means data=work.airbnb n nmiss mean std min p25 median p75 max maxdec=3;
    var log_price_per_person guest_satisfaction accuracy cleanliness checking
        communication location value reviews_count;
run;

/* Pearson은 선형 관계, Spearman은 단조 관계를 점검한다. */
title2 'Correlation with Log Price per Person';
proc corr data=work.airbnb pearson spearman nosimple;
    var log_price_per_person;
    with guest_satisfaction accuracy cleanliness checking communication location
         value reviews_count;
run;

title2 'Correlation Matrix of Rating and Review Variables';
proc corr data=work.airbnb pearson spearman nosimple;
    var guest_satisfaction accuracy cleanliness checking communication location
        value reviews_count;
run;

title2 'Simple Linear Regressions: Log Price per Person as Y';
proc reg data=work.airbnb plots(only)=(fitplot residualplot qqplot);
    model log_price_per_person = guest_satisfaction / clb stb;
    model log_price_per_person = accuracy / clb stb;
    model log_price_per_person = cleanliness / clb stb;
    model log_price_per_person = checking / clb stb;
    model log_price_per_person = communication / clb stb;
    model log_price_per_person = location / clb stb;
    model log_price_per_person = value / clb stb;
    model log_price_per_person = reviews_count / clb stb;
run;
quit;

/* 관측치, 선형회귀선(빨강), 비선형 LOESS 추세선(파랑)을 함께 표시한다. */
%macro rating_plot(x=, label=);
    title2 "Log Price per Person vs &label";
    proc sgplot data=work.airbnb;
        scatter x=&x y=log_price_per_person / transparency=0.62 markerattrs=(symbol=circlefilled size=6);
        reg x=&x y=log_price_per_person / cli lineattrs=(color=red thickness=2);
        loess x=&x y=log_price_per_person / lineattrs=(color=blue pattern=shortdash thickness=2);
        xaxis label="&label";
        yaxis label='Log Price per Person';
    run;
%mend;

%rating_plot(x=guest_satisfaction, label=Overall Satisfaction);
%rating_plot(x=accuracy,            label=Accuracy);
%rating_plot(x=cleanliness,         label=Cleanliness);
%rating_plot(x=checking,            label=Check-in Convenience);
%rating_plot(x=communication,       label=Communication);
%rating_plot(x=location,            label=Location);
%rating_plot(x=value,               label=Value for Money);
%rating_plot(x=reviews_count,       label=Review Count);

/* reviews_count의 긴 우측 꼬리를 보기 위한 보조 그래프(분석 X는 원자료 그대로). */
title2 'Log Price per Person vs Log(1 + Review Count)';
proc sgplot data=work.airbnb;
    scatter x=log1p_reviews_count y=log_price_per_person / transparency=0.62 markerattrs=(symbol=circlefilled size=6);
    reg x=log1p_reviews_count y=log_price_per_person / cli lineattrs=(color=red thickness=2);
    loess x=log1p_reviews_count y=log_price_per_person / lineattrs=(color=blue pattern=shortdash thickness=2);
    xaxis label='Log(1 + Review Count)';
    yaxis label='Log Price per Person';
run;

title2 'Scatterplot Matrix: Log Price per Person and X Variables';
proc sgscatter data=work.airbnb;
    matrix log_price_per_person guest_satisfaction accuracy cleanliness checking
           communication location value reviews_count;
run;

proc odstext;
    p 'Interpretation note:' / style=[font_weight=bold];
    p 'The value-for-money rating is included as requested, but it is a descriptive association only: its concept includes price, so it should not be interpreted as an independent causal driver of price.';
    p 'Pearson measures linear association; Spearman is useful when review counts are highly skewed or the relationship is monotonic but non-linear.';
run;

title;
ods graphics off;

/*============================================================================*
  민감도 분석: 리뷰가 5개 이상인 숙소만 대상으로 전체 분석을 동일하게 반복한다.
  목적: 리뷰 수가 매우 적은 숙소의 불안정한 평점이 결론에 영향을 주는지 점검한다.
 *============================================================================*/
ods graphics on / reset=all width=900px height=520px imagemap=on;

data work.airbnb_review5plus;
    set work.airbnb;
    where reviews_count >= 5;
run;

title1 'Sensitivity Analysis: Listings with 5 or More Reviews';
title2 'Input Data and Variable Quality Check';
proc means data=work.airbnb_review5plus n nmiss mean std min p25 median p75 max maxdec=3;
    var log_price_per_person guest_satisfaction accuracy cleanliness checking
        communication location value reviews_count;
run;

/* 전체 표본과 같은 Pearson/Spearman 상관분석 */
title2 'Correlation with Log Price per Person (Reviews >= 5)';
proc corr data=work.airbnb_review5plus pearson spearman nosimple;
    var log_price_per_person;
    with guest_satisfaction accuracy cleanliness checking communication location
         value reviews_count;
run;

title2 'Correlation Matrix of Rating and Review Variables (Reviews >= 5)';
proc corr data=work.airbnb_review5plus pearson spearman nosimple;
    var guest_satisfaction accuracy cleanliness checking communication location
        value reviews_count;
run;

/* 전체 표본과 같은 X별 단순선형회귀 */
title2 'Simple Linear Regressions: Log Price per Person as Y (Reviews >= 5)';
proc reg data=work.airbnb_review5plus plots(only)=(fitplot residualplot qqplot);
    model log_price_per_person = guest_satisfaction / clb stb;
    model log_price_per_person = accuracy / clb stb;
    model log_price_per_person = cleanliness / clb stb;
    model log_price_per_person = checking / clb stb;
    model log_price_per_person = communication / clb stb;
    model log_price_per_person = location / clb stb;
    model log_price_per_person = value / clb stb;
    model log_price_per_person = reviews_count / clb stb;
run;
quit;

/* 전체 표본과 같은 변수별 산점도: 빨강=선형회귀선, 파랑=LOESS 추세선 */
%macro rating_plot_review5(x=, label=);
    title2 "Log Price per Person vs &label (Reviews >= 5)";
    proc sgplot data=work.airbnb_review5plus;
        scatter x=&x y=log_price_per_person / transparency=0.62 markerattrs=(symbol=circlefilled size=6);
        reg x=&x y=log_price_per_person / cli lineattrs=(color=red thickness=2);
        loess x=&x y=log_price_per_person / lineattrs=(color=blue pattern=shortdash thickness=2);
        xaxis label="&label";
        yaxis label='Log Price per Person';
    run;
%mend;

%rating_plot_review5(x=guest_satisfaction, label=Overall Satisfaction);
%rating_plot_review5(x=accuracy,            label=Accuracy);
%rating_plot_review5(x=cleanliness,         label=Cleanliness);
%rating_plot_review5(x=checking,            label=Check-in Convenience);
%rating_plot_review5(x=communication,       label=Communication);
%rating_plot_review5(x=location,            label=Location);
%rating_plot_review5(x=value,               label=Value for Money);
%rating_plot_review5(x=reviews_count,       label=Review Count);

title2 'Log Price per Person vs Log(1 + Review Count) (Reviews >= 5)';
proc sgplot data=work.airbnb_review5plus;
    scatter x=log1p_reviews_count y=log_price_per_person / transparency=0.62 markerattrs=(symbol=circlefilled size=6);
    reg x=log1p_reviews_count y=log_price_per_person / cli lineattrs=(color=red thickness=2);
    loess x=log1p_reviews_count y=log_price_per_person / lineattrs=(color=blue pattern=shortdash thickness=2);
    xaxis label='Log(1 + Review Count)';
    yaxis label='Log Price per Person';
run;

title2 'Scatterplot Matrix: Log Price per Person and X Variables (Reviews >= 5)';
proc sgscatter data=work.airbnb_review5plus;
    matrix log_price_per_person guest_satisfaction accuracy cleanliness checking
           communication location value reviews_count;
run;

proc odstext;
    p 'Sensitivity-analysis note:' / style=[font_weight=bold];
    p 'This section includes only listings with at least five reviews. Compare its correlation coefficients and regression slopes with the full-sample section above to assess whether conclusions are robust to excluding very-low-review listings.';
run;

title;
ods graphics off;
