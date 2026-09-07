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
</style>

# 별들의 값어치
### 에어비앤비 평점은 가격과 어떤 관계를 가질까?

<div class="mt-16 text-sm text-gray-400">
  서울 에어비앤비 표본 1,171건 실증 분석 기반 리뷰 평점 지표 평가
</div>

<!--
에어비앤비 예약 시 게스트가 가장 중요하게 보는 요소는 평점입니다.
하지만 가격 예측 모델을 구축하는 과정에서 8개 평점 관련 변수를 전부 제외하게 되었습니다.
오늘 발표에서는 왜 평점 지표들이 가격 모델에서 모두 탈락할 수밖에 없었는지 데이터와 통계적 근거를 바탕으로 말씀드리겠습니다.
-->

---
layout: default
---

# 에어비앤비 실제 평가 체계와 '천장 효과'

<div class="grid grid-cols-2 gap-10 mt-6 items-start">

<div>
  <img src="/airbnb_guest_favorite_ratings.png" class="rounded w-full max-h-[300px] object-contain" />
  <div class="text-xs text-gray-400 mt-2 text-center">에어비앤비 게스트 선호 평가 UI</div>
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

  <div class="pt-3 border-t border-gray-100">
    <div class="text-xs font-bold text-gray-900 mb-1">데이터 특성: 극단적 천장 효과 (Ceiling Effect)</div>
    <div class="text-xs text-gray-500 leading-relaxed">
      서울 에어비앤비 평점의 90% 이상이 4.7~4.9점에 밀집 (평균 4.85, 편차 0.15)<br>
      게스트 관대화로 분산이 없어 <strong>데이터 구조상 가격 변별력 부재가 이미 예견됨</strong>
    </div>
  </div>
</div>

</div>

<!--
에어비앤비는 종합 별점 외에 6가지 세부 항목을 평가받습니다.
하지만 데이터를 열어보면 가장 먼저 발견되는 현상이 바로 '극단적 천장 효과'입니다.
1박 3만 원 숙소든 50만 원 숙소든 대부분 4.8점 이상의 만점에 가까운 점수를 받고 있어, 평점 자체의 분산이 거의 없습니다.
따라서 회귀분석을 진행하기 전부터 평점이 가격을 설명하기 어려울 것이라는 점이 구조적으로 드러납니다.
-->

---
layout: default
---

# 무의미한 지표: 체크인 및 의사소통

<div class="grid grid-cols-2 gap-16 mt-12 items-start">

<div>
  <div class="text-2xl font-bold text-gray-900 tracking-tight mb-4">체크인 만족도</div>
  <div class="space-y-4">
    <div>
      <div class="text-xs text-gray-400 mb-1">유의확률 (P-value)</div>
      <div class="text-6xl font-light font-mono text-gray-900">0.9372</div>
    </div>
    <div class="pt-4 border-t border-gray-100 text-sm text-gray-500">
      설명력(R²): <span class="font-mono text-gray-800 font-medium">0.00%</span> (기준치 0.05 크게 초과, 유의성 전무)
    </div>
  </div>
</div>

<div class="pl-16 border-l border-gray-100">
  <div class="text-2xl font-bold text-gray-900 tracking-tight mb-4">의사소통 만족도</div>
  <div class="space-y-4">
    <div>
      <div class="text-xs text-gray-400 mb-1">유의확률 (P-value)</div>
      <div class="text-6xl font-light font-mono text-gray-900">0.2477</div>
    </div>
    <div class="pt-4 border-t border-gray-100 text-sm text-gray-500">
      설명력(R²): <span class="font-mono text-gray-800 font-medium">0.11%</span> (유의수준 0.05 미달)
    </div>
  </div>
</div>

</div>

<!--
첫 번째 탈락 그룹은 체크인과 의사소통입니다.
체크인의 P값은 0.94로 가격과 아무런 통계적 관계가 없으며, 의사소통 역시 P값 0.25로 유의수준 5%를 크게 벗어납니다.
1박 3만 원 도미토리나 50만 원 독채나 모두 4.9점대를 유지합니다.
셀프 체크인과 신속한 메시지 응답은 모든 호스트가 동일하게 제공하는 기본 영역이므로, 가격을 더 비싸게 받는 프리미엄 요인이 될 수 없습니다.
-->

---
layout: default
---

# 설명력 결여: 1% 미만의 미미한 지표들

<div class="grid grid-cols-4 gap-8 mt-14 items-start">

<div class="space-y-3">
  <div class="text-xl font-bold text-gray-900 tracking-tight">정보 정확도</div>
  <div class="text-5xl font-light font-mono text-gray-900">0.33%</div>
  <div class="text-xs text-gray-400">설명력 (R²)</div>
  <div class="pt-3 border-t border-gray-100 text-xs text-gray-400">P값 0.0492</div>
</div>

<div class="space-y-3">
  <div class="text-xl font-bold text-gray-900 tracking-tight">위치 만족도</div>
  <div class="text-5xl font-light font-mono text-gray-900">0.89%</div>
  <div class="text-xs text-gray-400">설명력 (R²)</div>
  <div class="pt-3 border-t border-gray-100 text-xs text-gray-400">P값 0.0012</div>
</div>

<div class="space-y-3">
  <div class="text-xl font-bold text-gray-900 tracking-tight">종합 평점</div>
  <div class="text-5xl font-light font-mono text-gray-900">0.56%</div>
  <div class="text-xs text-gray-400">설명력 (R²)</div>
  <div class="pt-3 border-t border-gray-100 text-xs text-gray-400">P값 0.0107</div>
</div>

<div class="space-y-3">
  <div class="text-xl font-bold text-gray-900 tracking-tight">누적 리뷰 수</div>
  <div class="text-5xl font-light font-mono text-gray-900">0.04%</div>
  <div class="text-xs text-gray-400">설명력 (R²)</div>
  <div class="pt-3 border-t border-gray-100 text-xs text-gray-400">P값 0.4788</div>
</div>

</div>

<!--
두 번째 탈락 그룹은 설명력이 1%에도 미치지 못하는 지표들입니다.
에어비앤비의 간판이라 할 수 있는 대표 별점(종합 평점)마저 설명력이 0.56%에 그쳤고, 정보 정확도는 0.33%, 리뷰 수는 0.04%에 불과합니다.
위치 만족도는 P값이 0.001로 유의하나 설명력은 0.89%로 미미합니다. 입지의 가치는 게스트의 주관적 5점 만점이 아니라 실제 강남·홍대 등 물리적 지리 좌표와 역세권 거리로 설명되어야 합니다.
-->

---
layout: default
---

# 가격 대비 가치: 가성비의 역설

<div class="grid grid-cols-3 gap-10 items-start mt-10">

<div class="space-y-3">
  <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">회귀계수</div>
  <div class="text-5xl font-light font-mono text-gray-900">-0.5204</div>
  <div class="text-xs text-gray-500 leading-relaxed">
    가격이 비쌀수록 가성비 평점이 낮아지는 <strong>명확한 음(-)의 상관관계</strong>
  </div>
  <div class="pt-3 border-t border-gray-100 text-xs text-gray-400">
    P값 0.0005 | 설명력 1.03%
  </div>
</div>

<div class="col-span-2 pl-10 border-l border-gray-100 space-y-6">
  <div>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">인과 역전 흐름</div>
    <div class="text-sm text-gray-800 font-medium py-3 px-4 bg-gray-50 rounded">
      숙소 가격 상승 (원인) &nbsp;→&nbsp; 게스트 기대치 상승 &nbsp;→&nbsp; 가성비 평점 감점 (결과)
    </div>
  </div>

  <div class="grid grid-cols-2 gap-6 text-xs leading-relaxed">
    <div>
      <strong class="text-gray-900 block mb-1">기대치 불일치 (Expectation Gap)</strong>
      <p class="text-gray-500">숙소 가격이 비쌀수록 투숙객이 더 엄격한 잣대를 적용하여 가성비 평점을 박하게 부여함</p>
    </div>
    <div>
      <strong class="text-gray-900 block mb-1">개념적 내생성 (Endogeneity)</strong>
      <p class="text-gray-500">가성비 평가 공식의 분모에 이미 가격이 위치하므로, 가격 예측 독립변수로 사용 불가</p>
    </div>
  </div>
</div>

</div>

<!--
가성비 평점은 통계적으로 유의하지만($P=0.0005$), 계수가 -0.52로 뚜렷한 음(-)의 관계를 보입니다.
보시는 도식처럼 숙소 가격이 비싸질수록 게스트의 기대 수준이 높아져 감점을 주기 때문입니다.
즉 가격이 평점을 결정하는 원인이지, 가성비 평점이 가격을 설명하는 독립변수가 될 수 없습니다.
-->

---
layout: default
---

# 청결도의 겉보기 설명력: 전체 단순회귀 착시

<div class="grid grid-cols-2 gap-10 mt-6 items-start">

<div>
  <img src="/cleanliness_scatter_step1.png" class="rounded w-full max-h-[300px] object-contain" />
  <div class="text-xs text-gray-400 mt-2 text-center">전체 단순회귀선 (β = +0.98)</div>
</div>

<div class="space-y-6">
  <div>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">단순회귀 겉보기 설명력</div>
    <div class="text-5xl font-light font-mono text-gray-900 mb-1">3.39%</div>
    <div class="text-xs text-gray-400">8개 평점 지표 중 유일하게 유의미한 설명력 관측 (P &lt; 0.0001)</div>
  </div>

  <div class="space-y-3 text-xs border-t border-gray-100 pt-4">
    <div>
      <div class="font-bold text-gray-900 mb-0.5">가파른 우상향 회귀선</div>
      <div class="text-gray-500">전체 숙소를 합쳐서 보면 청결도가 오를수록 가격이 2배 오르는 착시 발생</div>
    </div>
    <div>
      <div class="font-bold text-gray-900 mb-0.5">핵심 질문</div>
      <div class="text-gray-500">청결도 평점은 정말 가격을 결정하는 유의미한 독립변수인가?</div>
    </div>
  </div>
</div>

</div>

<!--
8개 지표 중 유일하게 설명력(3.39%)을 보인 청결도는 언뜻 방을 깨끗이 하면 가격이 2배 오르는 것처럼 보입니다.
회귀계수가 +0.98에 달하고 P값도 0.0001 미만으로 매우 유의하게 나타납니다.
표면적인 수치만 보면 청결도는 모델에 반드시 넣어야 할 핵심 변수처럼 보입니다.
그러나 다음 슬라이드에서 숙소 타입을 분리해 보면 이 관계의 실체가 드러납니다.
-->

---
layout: default
---

# 실증 확인: 숙소 타입 통제와 유의성 상실

<div class="grid grid-cols-2 gap-10 mt-6 items-start">

<div>
  <img src="/cleanliness_scatter_step2.png" class="rounded w-full max-h-[300px] object-contain" />
  <div class="text-xs text-gray-400 mt-2 text-center">방 타입별 통제 회귀선 (단독 숙소 · 개인실 · 도미토리)</div>
</div>

<div class="space-y-5">
  <div>
    <div class="text-xs text-gray-400 mb-1">1. 청결도 회귀계수 변화</div>
    <div class="flex items-baseline space-x-2">
      <span class="font-mono text-gray-400 text-lg">0.98</span>
      <span class="text-gray-300">→</span>
      <span class="font-mono font-bold text-gray-900 text-3xl">0.19</span>
      <span class="text-xs text-gray-500 font-medium">(80.6% 급감, P=0.096 유의성 상실)</span>
    </div>
  </div>

  <div class="pt-3 border-t border-gray-100">
    <div class="text-xs text-gray-400 mb-1">2. 모델 설명력 (R²) 변화</div>
    <div class="flex items-baseline space-x-2">
      <span class="font-mono text-gray-400 text-lg">3.9%</span>
      <span class="text-gray-300">→</span>
      <span class="font-mono font-bold text-gray-900 text-3xl">42.5%</span>
      <span class="text-xs text-gray-500 font-medium">(숙소 타입이 설명력 지배)</span>
    </div>
  </div>

  <div class="pt-3 border-t border-gray-100">
    <div class="text-xs text-gray-400 mb-1">3. 다중공선성 진단 (VIF)</div>
    <div class="flex items-baseline space-x-2">
      <span class="font-mono font-bold text-gray-900 text-3xl">1.06</span>
      <span class="text-xs text-gray-500 font-medium">(공선성 없음, 본질적 교란 요인 확인)</span>
    </div>
  </div>
</div>

</div>

<!--
보시는 것처럼 숙소 타입(독채, 개인실, 도미토리)을 통제하면, 각 방 타입 내에서 청결도와 가격의 관계는 거의 완전한 수평(기울기 0.19, P=0.096)으로 누워 유의성을 완전히 상실합니다.
반면 모델 설명력은 3.9%에서 42.5%로 폭증합니다.
VIF 지수는 1.06으로 다중공선성이 전혀 아니며, 청결도의 겉보기 설명력은 순전히 '원래 비싼 단독 숙소가 청결 평점도 높았던 것'이 반영된 교란 효과(심슨의 역설)였음을 완벽히 실증합니다.
-->

---
layout: default
---

# 종합 결론: 평점 변수 전면 배제 및 모델링 방향

<div class="grid grid-cols-2 gap-12 mt-8 items-start">

<div class="space-y-3">
  <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">8개 평점 지표 탈락 종합 (MECE)</div>
  <table class="w-full text-xs text-left">
    <tbody>
      <tr class="border-b border-gray-100">
        <td class="py-2.5 text-gray-400 w-28">통계적 무의미</td>
        <td class="py-2.5 text-gray-800">체크인, 의사소통 <span class="text-gray-400">(P &gt; 0.05)</span></td>
      </tr>
      <tr class="border-b border-gray-100">
        <td class="py-2.5 text-gray-400">설명력 결여</td>
        <td class="py-2.5 text-gray-800">정확도, 위치, 종합평점, 리뷰수 <span class="text-gray-400">(R² &lt; 1%)</span></td>
      </tr>
      <tr class="border-b border-gray-100">
        <td class="py-2.5 text-gray-400">역방향 내생성</td>
        <td class="py-2.5 text-gray-800">가격 대비 가치 <span class="text-gray-400">(비쌀수록 감점)</span></td>
      </tr>
      <tr>
        <td class="py-2.5 text-gray-400">교란 요인 혼재</td>
        <td class="py-2.5 text-gray-800">청결도 <span class="text-gray-400">(단독 숙소 효과 흡수)</span></td>
      </tr>
    </tbody>
  </table>
</div>

<div class="space-y-4 pl-10 border-l border-gray-100">
  <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">최종 모델링 방향</div>
  <div class="space-y-4 pt-1 text-sm">
    <div class="font-bold text-gray-900">평점 변수 전면 배제</div>
    <div class="font-bold text-gray-900">물리적 설비 스펙 중심</div>
    <div class="font-bold text-gray-900">공간 좌표·입지 클러스터링</div>
  </div>
</div>

</div>

<!--
8개 평점 지표 중 가격을 설명할 수 있는 유의미한 독립변수는 단 하나도 없었습니다.
천장 효과, 가성비의 역인과, 청결도의 숙소 타입 교란 요인이 입증되었기에 모델에서 평점 변수를 전면 배제하기로 확정했습니다.
최종 가격 예측 모델은 실제 가격을 결정하는 침실 수, 수용 인원, 전용 욕실 등 물리적 설비 스펙과 지리적 좌표 입지 클러스터링을 중심으로 구축됩니다.
결론적으로 평점은 게스트의 선택 기준일 뿐, 공급자의 1박 요금을 결정하는 원인이 아닙니다.
-->
