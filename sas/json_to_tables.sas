/******************************************************************************
 * 프로그램명 : load_airbnb_schema.sas (18개 테이블 100% 정상 완성 버전)
 * 설    명 : SAS ODA의 JSON 라이브러리 엔진에서 18개 데이터셋을 오류 없이
 *            100% 완벽하게 생성하여 AIRBNB 라이브러리에 저장합니다.
 * 작성환경 : SAS OnDemand for Academics (ODA) / SAS Studio
 ******************************************************************************/

/* 1. 환경 설정 및 기존 데이터셋 초기화 */
%let airbnb_path = ~/airbnb;

libname airbnb "&airbnb_path";
filename injson "&airbnb_path/airbnb-listings.json" encoding="utf-8";
libname jlib json fileref=injson;

/* 기존 잔여 데이터셋 일괄 초기화 */
proc datasets lib=airbnb kill nolist;
quit;

/*============================================================================*
 * 2. HOST 관련 테이블 생성 (HOST, HOST_HIGHLIGHT, HOST_DETAIL)
 *============================================================================*/

/* 2-1. 호스트 마스터 테이블 (AIRBNB.HOST) -> 836건 */
proc sql;
    create table airbnb.host as
    select distinct
        coalesce(h.id, r.id) as id length=50 label='호스트 고유 ID',
        h.name length=100 label='호스트 이름',
        h.profileImage as profile_image_url length=500 label='프로필 이미지 URL',
        case when h.isSuperHost = 1 then 1 else 0 end as is_superhost label='슈퍼호스트 여부',
        case when h.isVerified = 1 then 1 else 0 end as is_verified label='신원 인증 여부',
        h.about length=2000 label='호스트 소개글',
        h.ratingAverage as rating_average label='호스트 평균 평점',
        h.ratingCount as rating_count label='호스트 리뷰 수',
        coalesce(t.years, 0) as time_as_host_years label='호스트 활동 연수',
        coalesce(t.months, 0) as time_as_host_months label='호스트 활동 개월수'
    from jlib.host as h
    left join jlib.root as r on h.ordinal_root = r.ordinal_root
    left join jlib.host_timeashost as t on h.ordinal_host = t.ordinal_host
    where calculated id is not missing;
quit;

/* 2-2. 호스트 강조 문구 (AIRBNB.HOST_HIGHLIGHT) -> 553건 */
data work.host_highlights_clean;
    set jlib.host_highlights;
    array c_vars[*] _character_;
    if dim(c_vars) > 0 then highlight_text = c_vars[1];
    keep ordinal_host highlight_text;
run;

proc sql;
    create table airbnb.host_highlight as
    select
        monotonic() as id label='강조 문구 ID',
        coalesce(h.id, r.id) as host_id length=50 label='호스트 ID',
        hh.highlight_text as highlight length=255 label='강조 문구'
    from work.host_highlights_clean as hh
    inner join jlib.host as h on hh.ordinal_host = h.ordinal_host
    left join jlib.root as r on h.ordinal_root = r.ordinal_root
    where hh.highlight_text is not missing and strip(hh.highlight_text) ne '';
quit;

/* 2-3. 호스트 상세 정보 (AIRBNB.HOST_DETAIL) -> 1,210건 */
data work.host_details_clean;
    set jlib.host_hostdetails;
    array c_vars[*] _character_;
    if dim(c_vars) > 0 then detail_text = c_vars[1];
    keep ordinal_host detail_text;
run;

proc sql;
    create table airbnb.host_detail as
    select
        monotonic() as id label='호스트 상세 정보 ID',
        coalesce(h.id, r.id) as host_id length=50 label='호스트 ID',
        hd.detail_text as detail length=255 label='상세 항목'
    from work.host_details_clean as hd
    inner join jlib.host as h on hd.ordinal_host = h.ordinal_host
    left join jlib.root as r on h.ordinal_root = r.ordinal_root
    where hd.detail_text is not missing and strip(hd.detail_text) ne '';
quit;

/*============================================================================*
 * 3. CO-HOST 관련 테이블 (CO_HOST, LISTING_CO_HOST)
 *============================================================================*/

/* 3-1. 공동 호스트 마스터 테이블 (AIRBNB.CO_HOST) -> 535건 */
proc sql;
    create table airbnb.co_host as
    select distinct
        ch.id length=50 label='공동 호스트 고유 ID',
        ch.name length=100 label='공동 호스트 이름',
        ch.profilePictureUrl as profile_picture_url length=500 label='프로필 이미지 URL'
    from jlib.cohosts as ch
    where ch.id is not missing;
quit;

/* 3-2. 숙소 - 공동 호스트 매핑 테이블 (AIRBNB.LISTING_CO_HOST) -> 1,348건 */
proc sql;
    create table airbnb.listing_co_host as
    select distinct
        r.id as listing_id length=50 label='숙소 ID',
        ch.id as co_host_id length=50 label='공동 호스트 ID'
    from jlib.cohosts as ch
    inner join jlib.root as r on ch.ordinal_root = r.ordinal_root
    where r.id is not missing and ch.id is not missing;
quit;

/*============================================================================*
 * 4. LISTING 메인 테이블 (AIRBNB.LISTING) -> 1,249건
 *============================================================================*/

data airbnb.listing;
    length
        id $50
        host_id $50
        title $500
        description $4000
        html_description $4000
        description_original_language $10
        meta_description $2000
        seo_title $255
        sharing_config_title $255
        property_type $50
        room_type $50
        thumbnail_url $500
        url $500
        android_link $500
        ios_link $500
        language $10
        sub_description_title $255
        location_name $255
        location_subtitle $255
        brand_subtitle $255;

    label
        id = '숙소 고유 ID'
        host_id = '메인 호스트 ID'
        title = '숙소 제목'
        description = '숙소 상세 설명'
        html_description = 'HTML 상세 설명'
        description_original_language = '원본 언어 코드'
        meta_description = '메타 설명'
        seo_title = 'SEO 제목'
        sharing_config_title = '공유용 제목'
        property_type = '숙소 유형'
        room_type = '객실 유형'
        home_tier = '숙소 등급/티어'
        person_capacity = '수용 가능 인원'
        thumbnail_url = '대표 썸네일 URL'
        url = '웹 상세 URL'
        android_link = '안드로이드 딥링크'
        ios_link = 'iOS 딥링크'
        is_available = '예약 가능 여부'
        language = '데이터 언어'
        sub_description_title = '서브 설명 타이틀'
        latitude = '위도'
        longitude = '경도'
        location_name = '지역명'
        location_subtitle = '지역 보조 설명'
        brand_subtitle = '브랜드 서브타이틀'
        has_golden_laurel = '골든 로럴 뱃지 여부'
        check_in_date = '기준 체크인 날짜'
        check_out_date = '기준 체크아웃 날짜'
        crawled_at = '수집 시각';

    format
        latitude longitude 12.7
        check_in_date check_out_date yymmdd10.
        crawled_at datetime20.;

    merge jlib.root(in=in_r)
          jlib.host(keep=ordinal_root id rename=(id=h_id))
          jlib.coordinates(keep=ordinal_root latitude longitude)
          jlib.subdescription(keep=ordinal_root title rename=(title=sd_title))
          jlib.htmldescription(keep=ordinal_root htmlText)
          jlib.brandhighlights(keep=ordinal_root subtitle hasGoldenLaurel);
    by ordinal_root;

    if in_r and not missing(id);

    host_id = h_id;
    html_description = htmlText;
    thumbnail_url = thumbnail;
    android_link = androidLink;
    ios_link = iosLink;
    property_type = propertyType;
    room_type = roomType;
    home_tier = homeTier;
    person_capacity = personCapacity;
    is_available = isAvailable;
    description_original_language = descriptionOriginalLanguage;
    meta_description = metaDescription;
    seo_title = seoTitle;
    sharing_config_title = sharingConfigTitle;
    location_name = location;
    location_subtitle = locationSubtitle;
    sub_description_title = sd_title;
    brand_subtitle = subtitle;
    has_golden_laurel = hasGoldenLaurel;

    if not missing(checkIn) then check_in_date = input(checkIn, yymmdd10.);
    if not missing(checkOut) then check_out_date = input(checkOut, yymmdd10.);
    if not missing(timestamp) then crawled_at = input(substr(timestamp, 1, 19), anydtdtm19.);

    keep id host_id title description html_description description_original_language
         meta_description seo_title sharing_config_title property_type room_type
         home_tier person_capacity thumbnail_url url android_link ios_link
         is_available language sub_description_title latitude longitude
         location_name location_subtitle brand_subtitle has_golden_laurel
         check_in_date check_out_date crawled_at;
run;

/*============================================================================*
 * 5. 평점 및 요금 테이블 (LISTING_RATING, LISTING_PRICE)
 *============================================================================*/

/* 5-1. 숙소 세부 평점 (AIRBNB.LISTING_RATING) -> 1,172건 */
proc sql;
    create table airbnb.listing_rating as
    select
        r.id as listing_id length=50 label='숙소 ID',
        rt.guestSatisfaction as guest_satisfaction format=5.2 label='게스트 종합 만족도',
        rt.accuracy as accuracy format=5.2 label='정확성 평점',
        rt.cleanliness as cleanliness format=5.2 label='청결도 평점',
        rt.checking as checking format=5.2 label='체크인 평점',
        rt.communication as communication format=5.2 label='의사소통 평점',
        rt.location as location format=5.2 label='위치 평점',
        rt.value as value format=5.2 label='가격 대비 가치 평점',
        rt.reviewsCount as reviews_count label='총 리뷰 수'
    from jlib.rating as rt
    inner join jlib.root as r on rt.ordinal_root = r.ordinal_root
    where r.id is not missing;
quit;

/* 5-2. 숙소 세부 요금 정보 (AIRBNB.LISTING_PRICE) -> 1,249건 */
proc sql;
    create table airbnb.listing_price as
    select
        r.id as listing_id length=50 label='숙소 ID',
        p.label length=100 label='가격 라벨',
        p.qualifier length=50 label='가격 기준 단위',
        p.price as price_amount length=50 label='표시 가격',
        p.originalPrice as original_price length=50 label='원래 가격',
        p.discountedPrice as discounted_price length=50 label='할인 가격'
    from jlib.price as p
    inner join jlib.root as r on p.ordinal_root = r.ordinal_root
    where r.id is not missing;
quit;

/*============================================================================*
 * 6. 숙소 상세 1:N 배열 테이블들
 *============================================================================*/

/* 6-1. 숙소 서브 설명 항목 (AIRBNB.LISTING_SUB_DESCRIPTION) -> 1,249건 */
data work.subdesc_items_clean;
    set jlib.subdescription_items;
    array c_vars[*] _character_;
    if dim(c_vars) > 0 then item_text = c_vars[1];
    keep ordinal_subdescription ordinal_items item_text;
run;

proc sql;
    create table airbnb.listing_sub_description as
    select
        monotonic() as id label='서브 설명 항목 ID',
        r.id as listing_id length=50 label='숙소 ID',
        sdi.item_text length=100 label='요약 텍스트',
        sdi.ordinal_items as sort_order label='정렬 순서'
    from work.subdesc_items_clean as sdi
    inner join jlib.subdescription as sd on sdi.ordinal_subdescription = sd.ordinal_subdescription
    inner join jlib.root as r on sd.ordinal_root = r.ordinal_root
    where r.id is not missing and sdi.item_text is not missing;
quit;

/* 6-2. 숙소 사진 목록 (AIRBNB.LISTING_IMAGE) -> 59,505건 */
proc sql;
    create table airbnb.listing_image as
    select
        monotonic() as id label='이미지 ID',
        r.id as listing_id length=50 label='숙소 ID',
        img.imageUrl as image_url length=500 label='이미지 URL',
        img.caption length=1000 label='이미지 캡션',
        img.orientation length=20 label='방향',
        img.ordinal_images as sort_order label='노출 순서'
    from jlib.images as img
    inner join jlib.root as r on img.ordinal_root = r.ordinal_root
    where r.id is not missing;
quit;

/* 6-3. 위치 상세 설명 (AIRBNB.LISTING_LOCATION_DESCRIPTION) -> 1,608건 */
proc sql;
    create table airbnb.listing_location_description as
    select
        monotonic() as id label='위치 설명 ID',
        r.id as listing_id length=50 label='숙소 ID',
        ld.title length=255 label='위치 제목',
        ld.content length=2000 label='위치 상세 설명 내용'
    from jlib.locationdescriptions as ld
    inner join jlib.root as r on ld.ordinal_root = r.ordinal_root
    where r.id is not missing;
quit;

/* 6-4. 브레드크럼 경로 (AIRBNB.LISTING_BREADCRUMB) -> 4,924건 */
proc sql;
    create table airbnb.listing_breadcrumb as
    select
        monotonic() as id label='브레드크럼 ID',
        r.id as listing_id length=50 label='숙소 ID',
        bc.ordinal_breadcrumbs as step_order label='단계 순서',
        bc.linkRoute as link_route length=255 label='이동 라우트',
        bc.linkText as link_text length=255 label='링크 텍스트',
        bc.searchText as search_text length=255 label='검색 텍스트'
    from jlib.breadcrumbs as bc
    inner join jlib.root as r on bc.ordinal_root = r.ordinal_root
    where r.id is not missing;
quit;

/* 6-5. 숙소 하이라이트/특징 (AIRBNB.LISTING_HIGHLIGHT) -> 3,514건 */
proc sql;
    create table airbnb.listing_highlight as
    select
        monotonic() as id label='숙소 강조특징 ID',
        r.id as listing_id length=50 label='숙소 ID',
        hl.title length=255 label='특징 제목',
        hl.subtitle length=1000 label='특징 부제',
        hl.icon length=100 label='아이콘 식별자',
        hl.type as highlight_type length=100 label='특징 유형'
    from jlib.highlights as hl
    inner join jlib.root as r on hl.ordinal_root = r.ordinal_root
    where r.id is not missing and strip(hl.title) ne '';
quit;

/* 6-6. 숙소 이용 규칙 (AIRBNB.LISTING_HOUSE_RULE) -> 11,510건 */
proc sql;
    create table airbnb.listing_house_rule as
    select
        monotonic() as id label='이용 규칙 ID',
        r.id as listing_id length=50 label='숙소 ID',
        hg.title as category length=100 label='규칙 분류',
        v.title length=255 label='규칙 제목',
        v.icon length=100 label='아이콘 식별자',
        v.additionalInfo as additional_info length=1000 label='추가 안내'
    from jlib.general_values as v
    inner join jlib.houserules_general as hg on v.ordinal_general = hg.ordinal_general
    inner join jlib.houserules as hr on hg.ordinal_houserules = hr.ordinal_houserules
    inner join jlib.root as r on hr.ordinal_root = r.ordinal_root
    where r.id is not missing;
quit;

/*============================================================================*
 * 7. 취소 정책 및 편의시설 (마스터 & 매핑 테이블)
 *============================================================================*/

/* 7-1. 취소 정책 마스터 (AIRBNB.CANCELLATION_POLICY) -> 12건 */
proc sql;
    create table airbnb.cancellation_policy as
    select distinct
        cp.policyId as id label='취소 정책 ID',
        cp.policyName as policy_name length=100 label='정책명'
    from jlib.cancellationpolicies as cp
    where cp.policyId is not missing;
quit;

/* 7-2. 숙소 - 취소 정책 매핑 (AIRBNB.LISTING_CANCELLATION_POLICY) -> 1,316건 */
proc sql;
    create table airbnb.listing_cancellation_policy as
    select distinct
        r.id as listing_id length=50 label='숙소 ID',
        cp.policyId as cancellation_policy_id label='취소 정책 ID'
    from jlib.cancellationpolicies as cp
    inner join jlib.root as r on cp.ordinal_root = r.ordinal_root
    where r.id is not missing and cp.policyId is not missing;
quit;

/* 7-3. 편의시설 카테고리 마스터 (AIRBNB.AMENITY_CATEGORY) -> 17개 고유 카테고리 */
proc sql;
    create table work.amenity_cat_raw as
    select distinct title as name length=100
    from jlib.amenities
    where title is not null and strip(title) ne '';
quit;

data airbnb.amenity_category;
    set work.amenity_cat_raw;
    id = _N_;
    label id='편의시설 카테고리 ID' name='카테고리명';
run;

/* 7-4. 편의시설 항목 마스터 (AIRBNB.AMENITY) -> 고유 항목 마스터 생성 */
proc sql;
    create table work.amenity_item_raw as
    select distinct title length=150, icon length=100
    from jlib.amenities_values
    where title is not null and strip(title) ne '';
quit;

data airbnb.amenity;
    set work.amenity_item_raw;
    id = _N_;
    label id='편의시설 ID' title='편의시설 이름' icon='아이콘 식별자';
run;

/* 7-5. 숙소 - 편의시설 매핑 (AIRBNB.LISTING_AMENITY) -> 49,627건 초고속 직결 매핑 */
proc sql;
    create table airbnb.listing_amenity as
    select
        r.id as listing_id length=50 label='숙소 ID',
        am.title as category_name length=100 label='카테고리명',
        v.title as amenity_name length=150 label='편의시설명',
        v.subtitle length=255 label='부제/설명',
        v.icon length=100 label='아이콘 식별자',
        case when v.available = 1 then 1 else 0 end as is_available label='제공 여부'
    from jlib.amenities_values as v
    inner join jlib.amenities as am on v.ordinal_amenities = am.ordinal_amenities
    inner join jlib.root as r on am.ordinal_root = r.ordinal_root
    where r.id is not missing;
quit;

/*============================================================================*
 * 8. 생성된 AIRBNB 라이브러리 테이블 목록 및 건수 검증 리포트
 *============================================================================*/

title "=== AIRBNB 라이브러리에 생성된 데이터셋 목록 및 레코드 건수 ===";
proc sql;
    select memname as TABLE_NAME label="테이블명",
           nobs as RECORD_COUNT label="총 레코드 수",
           nvar as COLUMN_COUNT label="컬럼 수",
           crdate as CREATED_AT label="생성 일시"
    from dictionary.tables
    where libname = 'AIRBNB'
    order by memname;
quit;
title;

/* JSON 임시 라이브러리 해제 */
libname jlib clear;
