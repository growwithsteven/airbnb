---
theme: default
background: https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=1600&q=80
class: text-center
highlighter: shiki
lineNumbers: true
drawings:
  persist: false
transition: slide-left
title: Slidev 핵심 가이드
---

# 🚀 Slidev 빠른 시작 가이드
마크다운으로 만드는 모던 인터랙티브 프레젠테이션

<div class="pt-12">
  <span @click="$slidev.nav.next" class="px-3 py-1 rounded cursor-pointer" hover="bg-white bg-opacity-10">
    Space 또는 오른쪽 방향키(→)를 눌러 넘겨보세요 <carbon:arrow-right class="inline"/>
  </span>
</div>

---
layout: default
---

# 1. Slidev 기본 원리

슬라이드 제작은 딱 세 가지만 알면 끝납니다.

- **구분선 (`---`)**: 페이지를 나눌 때 `---` 세 개만 넣으면 새 슬라이드가 됩니다.
- **표준 마크다운**: 제목(`#`), 본문, 리스트(`-`), 볼드(`**`), 표 등 일반 마크다운 문법 100% 지원
- **실시간 반영 (Hot Reload)**: `slides.md`를 저장하면 브라우저가 새로고침 없이 즉시 바뀝니다.

```markdown
# 1페이지 제목
내용 작성...

---

# 2페이지 제목
다음 페이지 내용...
```

---
layout: default
---

# 2. 발표 중 필수 단축키 (지금 눌러보세요!)

키보드 자판 하나로 파워포인트보다 강력한 도구를 켭니다.

| 단축키 | 기능 | 직접 체험해보기 |
| :---: | :--- | :--- |
| **`Space` / `→`** | 다음 슬라이드 / 다음 애니메이션 | 다음 장으로 이동 |
| **`o`** | **Overview 맵 뷰** | 전체 슬라이드를 바둑판으로 보고 원하는 장으로 순간이동 |
| **`p`** | **발표자 전용 모드** | 경과 시간, 다음 장 미리보기, 발표자 노트 표시 |
| **`d`** | **펜 드로잉 모드** | 슬라이드 위에 형광펜/마커로 자유롭게 필기 |

<!--
이 내용은 발표자 노트(Presenter Note)입니다!
슬라이드 화면에는 보이지 않으며, 키보드 'p'를 눌렀을 때만 오른쪽 화면에 나타납니다.
-->

---
layout: two-cols
---

# 3. 2열 레이아웃 (`layout: two-cols`)

좌우로 내용을 분할할 때 `::left::`와 `::right::`를 사용합니다.

::left::
### 👈 왼쪽 컬럼
- 핵심 통계 요약
- 모델 설명력 ($R^2 = 0.42$)
- 표본 크기: $N = 1,250$

::right::
### 👉 오른쪽 컬럼
- 비즈니스 권고사항
- 가격 인하 전략보다는 청결도/응답률 개선 우선
- 슈퍼호스트 배지 획득 유도

---
layout: default
---

# 4. 개발자/분석가를 위한 코드 하이라이트

SAS, Python, SQL 등 코드 블록의 특정 줄만 강조할 수 있습니다.

```sas {2-3|5-7|all}
/* 에어비앤비 평점 분석 회귀 모델 */
PROC REG DATA=airbnb_clean;
    MODEL rating_overall = host_is_superhost 
                          price_night 
                          rating_cleanliness 
                          rating_location 
                          rating_reviewsCount;
RUN;
QUIT;
```

<div class="mt-4 text-sm opacity-70">
하단 방향키를 누르면 줄 단위로 단계별 하이라이트가 이동합니다.
</div>

---
layout: default
---

# 5. 클릭할 때마다 하나씩 등장 (`v-click`)

`v-click` 디렉티브를 붙이면 발표 클릭 시 순서대로 뜹니다.

<v-clicks>

- 1️⃣ **첫 번째 메시지**: 결측치 정제 완료
- 2️⃣ **두 번째 메시지**: 다중공선성(VIF) 검정 통과
- 3️⃣ **세 번째 메시지**: 통계적 유의성 확보 ($p < 0.001$)

</v-clicks>

<div v-click class="mt-6 p-4 rounded bg-blue-500 bg-opacity-20 text-blue-200">
🎉 중요한 결론이나 콜아웃 박스도 이렇게 클릭 시점에 맞춰 띄울 수 있습니다!
</div>

---
layout: center
class: text-center
---

# 6. PDF 및 PPTX 내보내기

발표가 끝나고 파일로 제출하거나 공유해야 할 때:

```bash
# PDF 문서로 내보내기
slidev export slides.md --format pdf

# PPTX(파워포인트)로 내보내기
slidev export slides.md --format pptx
```

<div class="mt-8 text-lg text-emerald-400 font-semibold">
이제 터미널에서 <code>slidev slides.md --open</code> 을 쳐보세요!
</div>
