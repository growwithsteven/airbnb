 
 1          OPTIONS NONOTES NOSTIMER NOSOURCE NOSYNTAXCHECK;
 ERROR: At least one file associated with fileref _HTMLOUT is still in use.
 ERROR: Error in the FILENAME statement.
 NOTE: ODS statements in the SAS Studio environment may disable some output features.
 69         
 70         /*
 71           Independent SAS 9.4 + SAS/STAT program. UTF-8 source.
 72           INPUT: airbnb_final_nightly.sas7bdat (NOT the per-person dataset).
 73           SAS Studio input location (as shown in the supplied screenshot):
 74           Files (Home)/airbnb/airbnb_final_nightly.sas7bdat.
 75           Both paths below refer to the SAS SERVER, not the browser computer.
 76           Results default to that same existing folder. Original data are never modified.
 77         
 78           관측 단위: 숙소. 같은 ID의 리뷰 값이 일치할 때만 가격 로그를 평균한다.
 79           log_price 평균은 원가격의 기하평균에 대응한다. 가격의 산술평균 로그가 아니다.
 80           같은 ID의 평점/리뷰 수가 다르거나 결측 상태가 다르면 자동 중단한다.
 81           결측 대체, 이상치 자동 삭제, 리뷰 수에 따른 가중치는 사용하지 않는다.
 82           주 분석은 Y와 지정 X가 모두 있는 동일 표본; 리뷰>=5는 보조 분석이다.
 83           Pearson p값은 한 표본 내 지정 X 전체를 한 검정군으로 Bonferroni 보정한다.
 84           기타 회귀/Spearman/보조 분석의 p값은 탐색적으로 해석한다.
 85           SAS/STAT 문법 참고:
 86           https://support.sas.com/documentation/cdl/en/procstat/66703/HTML/default/procstat_corr_syntax01.htm
 87           https://support.sas.com/documentation/cdl/en/statug/63347/HTML/default/statug_reg_sect013.htm
 88         */
 89         options nodate nonumber validvarname=v7;
 90         /* SAS Studio Files (Home)/airbnb. If uploaded elsewhere, copy that folder's
 91            server path from its Properties into data_dir. Do not use a local Mac path.
 92            To save results elsewhere, set out_dir to an existing writable server folder. */
 93         %let data_dir=%sysget(HOME)/airbnb;
 94         %let out_dir=&data_dir;
 95         %let details=rating_accuracy rating_checking rating_cleanliness
 96                      rating_communication rating_location rating_value;
 97         %let reviews=&details rating_guestSatisfaction rating_reviewsCount;
 98         %let y=log_price;
 99         %let xs=&reviews;
 100        %let prefix=01_nightly_price_review_analysis;
 101        
 102        /* Validate server paths before assigning SRC or opening the HTML destination.
 103           A missing upload must not cascade into library, ODS, and CSV errors. */
 104        %macro validate_paths;
 105            %local rc dirid;
 106            %put NOTE: Input file = &data_dir/airbnb_final_nightly.sas7bdat;
 107            %put NOTE: Output folder = &out_dir;
 108            %if not %sysfunc(fileexist(%superq(data_dir)/airbnb_final_nightly.sas7bdat)) %then %do;
 109                %put ERROR: The nightly input file was not found on the SAS server.;
 110                %put ERROR: Upload airbnb_final_nightly.sas7bdat to Files (Home)/airbnb;
 111                %put ERROR: or set data_dir to its actual server folder shown in Properties.;
 112                %abort cancel;
 113            %end;
 114            %let rc=%sysfunc(filename(_outdir,%superq(out_dir)));
 115            %let dirid=0;
 116            %if &rc=0 %then %let dirid=%sysfunc(dopen(_outdir));
 117            %if &dirid=0 %then %do;
 118                %put ERROR: Output folder does not exist or cannot be accessed: &out_dir;
 119                %put ERROR: Set out_dir to an existing writable folder on the SAS server.;
 120                %let rc=%sysfunc(filename(_outdir));
 121                %abort cancel;
 122            %end;
 123            %let rc=%sysfunc(dclose(&dirid));
 124            %let rc=%sysfunc(filename(_outdir));
 125        %mend;
 126        %validate_paths;
 NOTE: Input file = /home/u64574512/airbnb/airbnb_final_nightly.sas7bdat
 NOTE: Output folder = /home/u64574512/airbnb
 ERROR: Output folder does not exist or cannot be accessed: /home/u64574512/airbnb
 ERROR: Set out_dir to an existing writable folder on the SAS server.
 
 ERROR: Execution canceled by an %ABORT CANCEL statement.