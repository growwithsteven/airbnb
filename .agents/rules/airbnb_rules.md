# Airbnb Project Rules & Context

이 문서는 Airbnb 프로젝트를 진행할 때 에이전트가 반드시 기억하고 준수해야 하는 규칙과 컨텍스트를 담고 있습니다.

## 1. SAS 환경 규칙 (SAS Environment)
- 이 프로젝트에서 SAS 코드를 작성할 때, 라이브러리 이름(Libref)은 반드시 **`airbnb`**를 사용해야 합니다. 
- 임의의 가짜 라이브러리(예: `mylib`, `work`)를 사용하지 마십시오.
- (예시) `airbnb.LISTING`, `airbnb.HOST_HIGHLIGHT`

## 2. 데이터베이스 스키마 및 아키텍처 (Database Architecture)
- 이 프로젝트의 목표는 비정규화된 `airbnb-listings.json` 원본 데이터를 18개의 테이블로 3차 정규화(3NF)하여 `airbnb.db` (SQLite)로 파싱하는 것입니다.
- 파이썬 기반의 메인 ETL 스크립트는 `build_db.py` (또는 `json_to_tables.py`) 입니다.
- 프로젝트의 **공식 ERD 및 데이터 사전(Data Dictionary)**은 `view_schema.html`에 통합되어 있습니다. 테이블 구조나 관계에 대한 의문이 생기면 이 HTML 파일을 가장 먼저 참고하십시오. (이전에 존재하던 SCHEMA.md는 삭제 및 통합되었습니다.)

## 3. 정합성 검증 (Data Parity Testing)
- SAS 스크립트(`load_airbnb_schema.sas`)와 Python 스크립트(`build_db.py`)의 산출물이 100% 동일한지 검증하기 위한 테스트 코드로 `test_parity.py`를 사용합니다.
- 검증 기준은 '코드의 형태'가 아니라 추출된 '결과물(데이터 행/열 단위)'입니다.
- 이 환경에서는 `pandas`가 설치되어 있지 않을 수 있으므로, ETL 검증 스크립트 작성 시에는 가급적 파이썬 내장 라이브러리(`sqlite3`, `csv`)를 활용하여 검증 로직을 구성합니다.

## 4. 주요 파싱 주의 사항 (Data Parsing Notes)
- 취소 정책(Cancellation Policy), 편의시설(Amenity), 브레드크럼(Breadcrumb) 등은 원본 JSON에서 깊은 뎁스의 배열(Array) 형태로 존재하므로 누락되지 않도록 매핑 테이블(`LISTING_AMENITY`, `LISTING_CANCELLATION_POLICY` 등)에 안전하게 해체해야 합니다.
- 숙소별 OS 링크(Android, iOS URL)는 별도의 테이블이 아닌 `LISTING` 테이블의 컬럼으로 바로 적재됩니다.
