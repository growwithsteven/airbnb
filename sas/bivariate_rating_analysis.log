 
 1          OPTIONS NONOTES NOSTIMER NOSOURCE NOSYNTAXCHECK;
 NOTE: ODS statements in the SAS Studio environment may disable some output features.
 69         
 70         /*
 71            Airbnb 평점·리뷰 이변량분석
 72            입력: airbnb_final_per_person.sas7bdat
 73            목적: 종합 만족도(guest_satisfaction)를 기준으로 세부 평점 및 리뷰 수와의
 74                  관계를 상관분석, 산점도, 단순선형회귀로 확인한다.
 75         */
 76         
 77         options nodate nonumber validvarname=any;
 78         ods graphics on;
 79         
 80         /* SAS Studio Files(Home)/airbnb 폴더를 자동으로 가리킵니다. */
 81         %let data_dir=%sysget(HOME)/airbnb;
 82         libname indata "&data_dir";
 NOTE: Libref INDATA refers to the same physical library as _TEMP0.
 NOTE: Libref INDATA was successfully assigned as follows: 
       Engine:        V9 
       Physical Name: /home/u64574512/airbnb
 83         
 84         data work.airbnb;
 85             set indata.airbnb_final_per_person(
 86                 rename=(
 87                     rating_guestSatisfaction=guest_satisfaction
 88                     rating_accuracy=accuracy
 89                     rating_cleanliness=cleanliness
 90                     rating_checking=checking
 91                     rating_communication=communication
 92                     rating_location=location
 93                     rating_value=value
 94                     rating_reviewsCount=reviews_count
 95                 )
 96             );
 97             label
 98                 guest_satisfaction = '종합 만족도'
 99                 accuracy           = '정확성'
 100                cleanliness        = '청결도'
 101                checking           = '체크인 편의성'
 102                communication      = '의사소통'
 103                location           = '위치'
 104                value              = '가성비'
 105                reviews_count      = '총 리뷰 수';
 106        run;
 
 NOTE: There were 1247 observations read from the data set INDATA.AIRBNB_FINAL_PER_PERSON.
 NOTE: The data set WORK.AIRBNB has 1247 observations and 28 variables.
 NOTE: DATA statement used (Total process time):
       real time           0.00 seconds
       user cpu time       0.00 seconds
       system cpu time     0.01 seconds
       memory              1783.78k
       OS Memory           21672.00k
       Timestamp           09/04/2026 08:01:04 AM
       Step Count                        24  Switch Count  2
       Page Faults                       0
       Page Reclaims                     343
       Page Swaps                        0
       Voluntary Context Switches        15
       Involuntary Context Switches      0
       Block Input Operations            0
       Block Output Operations           1032
       
 
 107        
 108        title1 'Airbnb 평점·리뷰 이변량분석';
 109        title2 '입력 데이터 및 변수 품질 점검';
 110        
 111        proc contents data=work.airbnb varnum;
 112        run;
 
 NOTE: PROCEDURE CONTENTS used (Total process time):
       real time           0.03 seconds
       user cpu time       0.04 seconds
       system cpu time     0.00 seconds
       memory              2276.75k
       OS Memory           22696.00k
       Timestamp           09/04/2026 08:01:04 AM
       Step Count                        25  Switch Count  0
       Page Faults                       0
       Page Reclaims                     390
       Page Swaps                        0
       Voluntary Context Switches        3
       Involuntary Context Switches      2
       Block Input Operations            0
       Block Output Operations           24
       
 
 113        
 114        proc means data=work.airbnb n nmiss mean std min p25 median p75 max maxdec=3;
 115            var guest_satisfaction accuracy cleanliness checking communication location value
 116                reviews_count;
 117        run;
 
 NOTE: There were 1247 observations read from the data set WORK.AIRBNB.
 NOTE: PROCEDURE MEANS used (Total process time):
       real time           0.04 seconds
       user cpu time       0.05 seconds
       system cpu time     0.00 seconds
       memory              6855.65k
       OS Memory           28088.00k
       Timestamp           09/04/2026 08:01:04 AM
       Step Count                        26  Switch Count  1
       Page Faults                       0
       Page Reclaims                     1722
       Page Swaps                        0
       Voluntary Context Switches        25
       Involuntary Context Switches      2
       Block Input Operations            0
       Block Output Operations           0
       
 
 118        
 119        /* 종합 만족도와 각 세부 평점·리뷰 수의 Pearson/Spearman 상관 */
 120        title2 '종합 만족도와 세부 변수의 상관분석';
 121        proc corr data=work.airbnb pearson spearman nosimple;
 122            var guest_satisfaction;
 123            with accuracy cleanliness checking communication location value
 124                 reviews_count;
 125        run;
 
 NOTE: PROCEDURE CORR used (Total process time):
       real time           0.03 seconds
       user cpu time       0.03 seconds
       system cpu time     0.00 seconds
       memory              1480.81k
       OS Memory           23204.00k
       Timestamp           09/04/2026 08:01:04 AM
       Step Count                        27  Switch Count  0
       Page Faults                       0
       Page Reclaims                     178
       Page Swaps                        0
       Voluntary Context Switches        3
       Involuntary Context Switches      2
       Block Input Operations            0
       Block Output Operations           16
       
 
 126        
 127        /* 세부 평점 전체의 상호 상관행렬 */
 128        title2 '세부 평점 변수 간 상관행렬';
 129        proc corr data=work.airbnb pearson spearman nosimple;
 130            var accuracy cleanliness checking communication location value guest_satisfaction;
 131        run;
 
 NOTE: PROCEDURE CORR used (Total process time):
       real time           0.08 seconds
       user cpu time       0.09 seconds
       system cpu time     0.00 seconds
       memory              1414.34k
       OS Memory           23204.00k
       Timestamp           09/04/2026 08:01:04 AM
       Step Count                        28  Switch Count  0
       Page Faults                       0
       Page Reclaims                     123
       Page Swaps                        0
       Voluntary Context Switches        3
       Involuntary Context Switches      3
       Block Input Operations            0
       Block Output Operations           32
       
 
 132        
 133        /* 종합 만족도를 결과변수로 한 단순선형회귀 */
 134        title2 '종합 만족도 단순선형회귀';
 135        proc reg data=work.airbnb plots(only)=(fitplot residualplot qqplot);
 136            model guest_satisfaction = accuracy / clb stb vif;
 137            model guest_satisfaction = cleanliness / clb stb vif;
 138            model guest_satisfaction = checking / clb stb vif;
 139            model guest_satisfaction = communication / clb stb vif;
 140            model guest_satisfaction = location / clb stb vif;
 141            model guest_satisfaction = value / clb stb vif;
 142            model guest_satisfaction = reviews_count / clb stb vif;
 143        run;
 
 144        quit;
 
 NOTE: PROCEDURE REG used (Total process time):
       real time           4.67 seconds
       user cpu time       0.95 seconds
       system cpu time     0.15 seconds
       memory              19069.70k
       OS Memory           40928.00k
       Timestamp           09/04/2026 08:01:09 AM
       Step Count                        29  Switch Count  86
       Page Faults                       0
       Page Reclaims                     53019
       Page Swaps                        0
       Voluntary Context Switches        3508
       Involuntary Context Switches      42
       Block Input Operations            56
       Block Output Operations           13992
       
 
 145        
 146        /* 변수별 이변량 그래프: 산점도 + 선형회귀선 + LOESS 추세선 */
 147        %macro bivar_plot(x=, label=);
 148            title2 "종합 만족도와 &label";
 149            proc sgplot data=work.airbnb;
 150                scatter x=&x y=guest_satisfaction / transparency=0.55;
 151                reg x=&x y=guest_satisfaction / cli lineattrs=(color=red thickness=2);
 152                loess x=&x y=guest_satisfaction / lineattrs=(color=blue pattern=shortdash);
 153                xaxis label="&label";
 154                yaxis label='종합 만족도';
 155            run;
 156        %mend;
 157        
 158        %bivar_plot(x=accuracy,      label=정확성);
 
 NOTE: PROCEDURE SGPLOT used (Total process time):
       real time           0.22 seconds
       user cpu time       0.10 seconds
       system cpu time     0.01 seconds
       memory              2632.15k
       OS Memory           33836.00k
       Timestamp           09/04/2026 08:01:09 AM
       Step Count                        30  Switch Count  1
       Page Faults                       1
       Page Reclaims                     398
       Page Swaps                        0
       Voluntary Context Switches        218
       Involuntary Context Switches      3
       Block Input Operations            496
       Block Output Operations           584
       
 NOTE: There were 1247 observations read from the data set WORK.AIRBNB.
 
 159        %bivar_plot(x=cleanliness,   label=청결도);
 
 NOTE: PROCEDURE SGPLOT used (Total process time):
       real time           0.19 seconds
       user cpu time       0.12 seconds
       system cpu time     0.00 seconds
       memory              2987.03k
       OS Memory           33836.00k
       Timestamp           09/04/2026 08:01:09 AM
       Step Count                        31  Switch Count  1
       Page Faults                       0
       Page Reclaims                     358
       Page Swaps                        0
       Voluntary Context Switches        215
       Involuntary Context Switches      2
       Block Input Operations            0
       Block Output Operations           592
       
 NOTE: There were 1247 observations read from the data set WORK.AIRBNB.
 
 160        %bivar_plot(x=checking,      label=체크인 편의성);
 
 NOTE: PROCEDURE SGPLOT used (Total process time):
       real time           0.17 seconds
       user cpu time       0.09 seconds
       system cpu time     0.00 seconds
       memory              2997.37k
       OS Memory           33836.00k
       Timestamp           09/04/2026 08:01:09 AM
       Step Count                        32  Switch Count  1
       Page Faults                       0
       Page Reclaims                     357
       Page Swaps                        0
       Voluntary Context Switches        216
       Involuntary Context Switches      1
       Block Input Operations            0
       Block Output Operations           584
       
 NOTE: There were 1247 observations read from the data set WORK.AIRBNB.
 
 161        %bivar_plot(x=communication, label=의사소통);
 
 NOTE: PROCEDURE SGPLOT used (Total process time):
       real time           0.16 seconds
       user cpu time       0.08 seconds
       system cpu time     0.01 seconds
       memory              3046.75k
       OS Memory           33836.00k
       Timestamp           09/04/2026 08:01:09 AM
       Step Count                        33  Switch Count  1
       Page Faults                       0
       Page Reclaims                     356
       Page Swaps                        0
       Voluntary Context Switches        215
       Involuntary Context Switches      3
       Block Input Operations            0
       Block Output Operations           576
       
 NOTE: There were 1247 observations read from the data set WORK.AIRBNB.
 
 162        %bivar_plot(x=location,      label=위치);
 
 NOTE: PROCEDURE SGPLOT used (Total process time):
       real time           0.21 seconds
       user cpu time       0.12 seconds
       system cpu time     0.01 seconds
       memory              3014.81k
       OS Memory           33836.00k
       Timestamp           09/04/2026 08:01:10 AM
       Step Count                        34  Switch Count  1
       Page Faults                       0
       Page Reclaims                     356
       Page Swaps                        0
       Voluntary Context Switches        215
       Involuntary Context Switches      4
       Block Input Operations            0
       Block Output Operations           592
       
 NOTE: There were 1247 observations read from the data set WORK.AIRBNB.
 
 163        %bivar_plot(x=value,         label=가성비);
 
 NOTE: PROCEDURE SGPLOT used (Total process time):
       real time           0.20 seconds
       user cpu time       0.10 seconds
       system cpu time     0.00 seconds
       memory              3113.06k
       OS Memory           33836.00k
       Timestamp           09/04/2026 08:01:10 AM
       Step Count                        35  Switch Count  1
       Page Faults                       0
       Page Reclaims                     356
       Page Swaps                        0
       Voluntary Context Switches        215
       Involuntary Context Switches      4
       Block Input Operations            0
       Block Output Operations           584
       
 NOTE: There were 1247 observations read from the data set WORK.AIRBNB.
 
 164        %bivar_plot(x=reviews_count, label=총 리뷰 수);
 
 NOTE: PROCEDURE SGPLOT used (Total process time):
       real time           0.28 seconds
       user cpu time       0.23 seconds
       system cpu time     0.01 seconds
       memory              3002.53k
       OS Memory           34092.00k
       Timestamp           09/04/2026 08:01:10 AM
       Step Count                        36  Switch Count  1
       Page Faults                       0
       Page Reclaims                     385
       Page Swaps                        0
       Voluntary Context Switches        216
       Involuntary Context Switches      4
       Block Input Operations            0
       Block Output Operations           520
       
 NOTE: There were 1247 observations read from the data set WORK.AIRBNB.
 
 165        
 166        /* 8개 지정 변수의 전체 쌍별 산점도 행렬 */
 167        title2 '평점 변수 전체 산점도 행렬';
 168        proc sgscatter data=work.airbnb;
 169            matrix guest_satisfaction accuracy cleanliness checking communication location value reviews_count
 170                / reg;
                      ___
                      22
                      202
 ERROR 22-322: Syntax error, expecting one of the following: ;, ATTRID, COLORMODEL, COLORRESPONSE, DATALABEL, DATALABELPOS, 
               DIAGONAL, ELLIPSE, GRADLEGEND, GROUP, LEGEND, MARKERATTRS, NOGRADLEGEND, NOLEGEND, RATTRID, SPLITCHAR, 
               SPLITCHARNODROP, SPLITJUSTIFY, START, TIP, TIPFORMAT, TIPLABEL, TRANSPARENCY.  
 ERROR 202-322: The option or parameter is not recognized and will be ignored.
 171        run;
 
 NOTE: The SAS System stopped processing this step because of errors.
 NOTE: PROCEDURE SGSCATTER used (Total process time):
       real time           0.00 seconds
       user cpu time       0.00 seconds
       system cpu time     0.00 seconds
       memory              879.03k
       OS Memory           33188.00k
       Timestamp           09/04/2026 08:01:10 AM
       Step Count                        37  Switch Count  0
       Page Faults                       0
       Page Reclaims                     130
       Page Swaps                        0
       Voluntary Context Switches        0
       Involuntary Context Switches      0
       Block Input Operations            0
       Block Output Operations           0
       
 172        
 173        title;
 174        ods graphics off;
 175        
 176        
 177        OPTIONS NONOTES NOSTIMER NOSOURCE NOSYNTAXCHECK;
 187        