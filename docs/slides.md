---
theme: default
colorSchema: light
highlighter: shiki
lineNumbers: false
drawings:
  persist: false
transition: none
title: 별들의 값어치
aspectRatio: 16/9
canvasWidth: 980
---

<style>
h1 {
  font-size: 1.6rem !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
  margin-bottom: 0.8rem !important;
  font-weight: 700 !important;
  color: #111827 !important;
}

.slidev-page-1 h1 {
  font-size: 3.8rem !important;
  line-height: 1.1 !important;
}
</style>

# 별들의 값어치
### 에어비앤비 평점은 가격과 어떤 관계를 가질까?

<!--
에어비앤비 예약 시 게스트가 가장 중요하게 보는 요소는 평점입니다.
가격 예측 모델을 구축하는 과정에서 8개 평점 관련 변수는 모두 후보에서 제외했습니다.
오늘 발표에서는 이 표본과 모형에서 평점 지표의 단순 설명력이 제한적이었던 근거를 말씀드리겠습니다.
-->

---
layout: default
---

# 에어비앤비 실제 평가 체계

<div class="grid grid-cols-2 gap-10 mt-6 items-start">

<div>
  <img src="/airbnb_guest_favorite_ratings.png" class="rounded w-full max-h-[300px] object-contain" />
</div>

<div class="space-y-5">
  <div>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">상단 총괄 지표 (2개)</div>
    <div class="grid grid-cols-2 gap-3">
      <div class="bg-gray-50 p-2.5 rounded">
        <div class="text-xs text-gray-400">대표 별점</div>
        <div class="text-sm font-semibold text-gray-800">종합 평점 (게스트 만족도)</div>
      </div>
      <div class="bg-gray-50 p-2.5 rounded">
        <div class="text-xs text-gray-400">누적 신뢰도</div>
        <div class="text-sm font-semibold text-gray-800">리뷰 수 (후기 건수)</div>
      </div>
    </div>
  </div>

  <div>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">하단 6대 세부 평가 항목 (5점 만점)</div>
    <div class="grid grid-cols-3 gap-2 text-xs text-gray-700">
      <div class="bg-gray-50 py-2 px-2 rounded text-center font-medium">청결도</div>
      <div class="bg-gray-50 py-2 px-2 rounded text-center font-medium">정확도</div>
      <div class="bg-gray-50 py-2 px-2 rounded text-center font-medium">체크인</div>
      <div class="bg-gray-50 py-2 px-2 rounded text-center font-medium">의사소통</div>
      <div class="bg-gray-50 py-2 px-2 rounded text-center font-medium">위치</div>
      <div class="bg-gray-50 py-2 px-2 rounded text-center font-medium">가격 대비 가치</div>
    </div>
  </div>

</div>

</div>

<!--
에어비앤비는 종합 별점 외에 6가지 세부 항목을 평가받습니다.
다음 장부터 각 평점 지표와 1박 가격의 단순 선형 관계를 확인합니다.
-->

---
layout: default
---

# 선형 연관성 근거가 약한 지표: 체크인 및 의사소통

<div class="grid grid-cols-2 gap-12 mt-6 items-start">

<div class="space-y-2">
  <div class="text-2xl font-bold text-gray-900 tracking-tight">체크인 만족도</div>
  <img src="/rating_regression_checking.png" class="w-full h-[215px] object-contain" />
  <div class="flex items-baseline gap-3">
    <span class="text-xs text-gray-400">P-value</span>
    <span class="text-3xl font-light font-mono text-gray-900">0.6592</span>
    <span class="text-xs text-gray-500">R² 0.02%</span>
  </div>
</div>

<div class="space-y-2">
  <div class="text-2xl font-bold text-gray-900 tracking-tight">의사소통 만족도</div>
  <img src="/rating_regression_communication.png" class="w-full h-[215px] object-contain" />
  <div class="flex items-baseline gap-3">
    <span class="text-xs text-gray-400">P-value</span>
    <span class="text-3xl font-light font-mono text-gray-900">0.4763</span>
    <span class="text-xs text-gray-500">R² 0.04%</span>
  </div>
</div>

</div>

<!--
체크인과 의사소통의 단순회귀 P값은 각각 0.6592와 0.4763입니다.
이 표본에서 선형 연관성의 통계적 근거가 충분하지 않았고, 설명력도 각각 0.02%, 0.04%에 그쳤습니다.
이 P값은 8개 평점을 탐색적으로 비교한 단순회귀의 결과입니다.
이 결과는 관계가 없음을 증명하는 것이 아니라, 이 두 변수를 가격 예측 후보로 유지할 근거가 약하다는 뜻입니다.
-->

---
layout: default
---

# 설명력 낮음: 1.08% 이하의 지표들

<div class="grid grid-cols-2 gap-x-12 gap-y-6 mt-5 items-start">

<div class="space-y-1">
  <div class="text-xl font-bold text-gray-900 tracking-tight">정보 정확도</div>
  <img src="/rating_regression_accuracy.png" class="w-full h-[170px] object-contain" />
  <div class="flex items-baseline gap-2"><span class="text-2xl font-light font-mono text-gray-900">0.53%</span><span class="text-xs text-gray-400">R² · P 0.0124</span></div>
</div>

<div class="space-y-1">
  <div class="text-xl font-bold text-gray-900 tracking-tight">위치 만족도</div>
  <img src="/rating_regression_location.png" class="w-full h-[170px] object-contain" />
  <div class="flex items-baseline gap-2"><span class="text-2xl font-light font-mono text-gray-900">1.08%</span><span class="text-xs text-gray-400">R² · P 0.0004</span></div>
</div>

<div class="space-y-1">
  <div class="text-xl font-bold text-gray-900 tracking-tight">종합 평점</div>
  <img src="/rating_regression_guest_satisfaction.png" class="w-full h-[170px] object-contain" />
  <div class="flex items-baseline gap-2"><span class="text-2xl font-light font-mono text-gray-900">0.87%</span><span class="text-xs text-gray-400">R² · P 0.0014</span></div>
</div>

<div class="space-y-1">
  <div class="text-xl font-bold text-gray-900 tracking-tight">누적 리뷰 수</div>
  <img src="/rating_regression_reviews_count.png" class="w-full h-[170px] object-contain" />
  <div class="flex items-baseline gap-2"><span class="text-2xl font-light font-mono text-gray-900">0.04%</span><span class="text-xs text-gray-400">R² · P 0.4729</span></div>
</div>

</div>

<!--
이 네 지표의 단순회귀 설명력은 0.04%에서 1.08% 범위입니다.
통계적으로 유의한 계수가 있더라도, 이 단일 평점으로 설명되는 로그 가격 변동은 작았습니다.
각 P값은 탐색적 단순회귀의 결과로, 변수의 인과적 우열을 뜻하지 않습니다.
따라서 이 결과는 물리적 입지나 설비 특성과 비교할 가격 예측 후보로서의 우선순위가 낮다는 근거입니다.
-->

---
layout: default
---

# 가격 대비 가치: 예측 입력으로 부적합한 평점

<div class="grid grid-cols-3 gap-10 items-start mt-6">

<div class="col-span-2">
  <img src="/rating_regression_value.png" class="w-full h-[290px] object-contain" />
  <div class="text-xs text-gray-400 mt-1 text-center">전체 단순회귀선 (β = −0.51)</div>
</div>

<div class="space-y-3">
  <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">회귀계수</div>
  <div class="text-5xl font-light font-mono text-gray-900">-0.5131</div>
  <div class="pt-3 text-xs text-gray-400">
    P값 0.0004 | 설명력 1.04%
  </div>
</div>

</div>

<!--
가격 대비 가치 평점은 통계적으로 유의한 음의 계수(-0.5131, P=0.0004)를 보입니다.
그러나 이 연관성만으로 가격이 평점을 낮춘다는 인과 방향을 확정할 수는 없습니다.
가격과 개념적으로 얽혀 있고 역인과 위험이 있으므로, 가격 예측의 입력 변수에서는 제외합니다.
-->

---
layout: default
---

# 청결도의 단순회귀 설명력: 추가 검토 대상

<div class="grid grid-cols-2 gap-10 mt-6 items-start">

<div>
  <img src="/cleanliness_scatter_step1.png" class="rounded w-full max-h-[300px] object-contain" />
  <div class="text-xs text-gray-400 mt-2 text-center">전체 단순회귀선 (β = +0.98)</div>
</div>

<div class="space-y-6">
  <div>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">단순회귀 설명력</div>
    <div class="text-5xl font-light font-mono text-gray-900 mb-1">3.85%</div>
    <div class="text-xs text-gray-400">8개 평점 중 가장 큰 단순 설명력 (P &lt; 0.001)</div>
  </div>

  <div class="space-y-3 text-xs pt-4">
    <div>
      <div class="font-bold text-gray-900 mb-0.5">양의 단순회귀선</div>
    </div>
    <div>
      <div class="font-bold text-gray-900 mb-0.5">숙소 타입 통제 확인</div>
    </div>
  </div>
</div>

</div>

<!--
청결도는 8개 평점 중 가장 큰 단순 설명력(3.85%)과 양의 계수(0.9751)를 보였습니다.
다만 3.85%는 여전히 제한적인 설명력이며, 이 관계는 숙소 타입 같은 특성의 차이를 반영했을 수 있습니다.
다음 슬라이드에서 같은 첫 번째 크롤링 표본에 숙소 타입을 함께 넣어 확인합니다.
-->

---
layout: default
---

# 숙소 타입을 함께 고려한 청결도 연관성

<div class="grid grid-cols-2 gap-10 mt-6 items-start">

<div>
  <img src="/cleanliness_scatter_step2.png" class="rounded w-full max-h-[300px] object-contain" />
  <div class="text-xs text-gray-400 mt-2 text-center">방 타입별 통제 회귀선 (단독 숙소 · 개인실 · 공유 숙소)</div>
</div>

<div class="space-y-5">
  <div>
    <div class="text-xs text-gray-400 mb-1">1. 청결도 회귀계수 변화</div>
    <div class="flex items-baseline space-x-2">
      <span class="font-mono text-gray-400 text-lg">0.9751</span>
      <span class="text-gray-300">→</span>
      <span class="font-mono font-bold text-gray-900 text-3xl">0.1888</span>
      <span class="text-xs text-gray-500 font-medium">(80.6% 감소, P=0.0964)</span>
    </div>
  </div>

  <div class="pt-3">
    <div class="text-xs text-gray-400 mb-1">2. 모델 설명력 (R²) 변화</div>
    <div class="flex items-baseline space-x-2">
      <span class="font-mono text-gray-400 text-lg">3.85%</span>
      <span class="text-gray-300">→</span>
      <span class="font-mono font-bold text-gray-900 text-3xl">42.46%</span>
      <span class="text-xs text-gray-500 font-medium">(숙소 타입 포함 모형)</span>
    </div>
  </div>

  <div class="pt-3">
    <div class="text-xs text-gray-400 mb-1">3. 다중공선성 진단 (VIF)</div>
    <div class="flex items-baseline space-x-2">
      <span class="font-mono font-bold text-gray-900 text-3xl">1.07</span>
      <span class="text-xs text-gray-500 font-medium">(청결도 기준 VIF)</span>
    </div>
  </div>
</div>

</div>

<!--
같은 첫 번째 크롤링 표본에서 숙소 타입을 함께 넣으면 청결도 계수는 0.9751에서 0.1888로 작아지고, P값은 0.0964가 됩니다.
이것은 숙소 타입을 조건으로 했을 때 청결도와 가격의 선형 연관성에 대한 근거가 약해진 결과입니다.
모형 R²는 42.46%이지만, 이 증가를 숙소 타입의 인과 효과로 해석하지 않습니다. VIF 1.07은 큰 선형 공선성이 없다는 진단입니다.
-->

---
layout: default
---

# 종합 결론: 평점 변수 후보 제외 및 모델링 방향

<div class="grid grid-cols-2 gap-12 mt-8 items-start">

<div class="space-y-3">
  <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">8개 평점 지표 탈락 종합 (MECE)</div>
  <div class="text-xs text-gray-400">공통 배경: 평점 분포의 상단 집중 (천장 효과)</div>
  <table class="w-full text-xs text-left">
    <tbody>
      <tr>
        <td class="py-2.5 text-gray-400 w-28">연관성 근거 약함</td>
        <td class="py-2.5 text-gray-800">체크인, 의사소통 <span class="text-gray-400">(P &gt; 0.05)</span></td>
      </tr>
      <tr>
        <td class="py-2.5 text-gray-400">설명력 낮음</td>
        <td class="py-2.5 text-gray-800">정확도, 위치, 종합평점, 리뷰수 <span class="text-gray-400">(R² ≤ 1.08%)</span></td>
      </tr>
      <tr>
        <td class="py-2.5 text-gray-400">내생성 위험</td>
        <td class="py-2.5 text-gray-800">가격 대비 가치 <span class="text-gray-400">(가격과 개념적 중첩)</span></td>
      </tr>
      <tr>
        <td class="py-2.5 text-gray-400">조건부 연관성 약화</td>
        <td class="py-2.5 text-gray-800">청결도 <span class="text-gray-400">(숙소 타입 통제 뒤 P=0.0964)</span></td>
      </tr>
    </tbody>
  </table>
</div>

<div class="space-y-4 pl-10">
  <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">최종 모델링 방향</div>
  <div class="space-y-4 pt-1 text-sm">
    <div class="font-bold text-gray-900">평점 변수 후보 제외</div>
    <div class="font-bold text-gray-900">물리적 설비 스펙 중심</div>
    <div class="font-bold text-gray-900">공간 좌표·입지 클러스터링</div>
  </div>
</div>

</div>

<!--
첫 번째 크롤링의 유효 숙소 1,179건에서, 8개 평점 변수는 단순모형의 가격 설명력이 0.02%에서 3.85%에 머물렀습니다.
가격 대비 가치 평점은 내생성 위험이 있고, 청결도는 숙소 타입을 함께 고려하면 조건부 연관성의 근거가 약해졌습니다.
따라서 이 가격 예측 모델에서는 평점 변수를 후보에서 제외하고, 물리적 설비와 공간·입지 특성을 중심으로 다음 모형을 구성합니다.
-->
