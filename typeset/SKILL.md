---
name: hwpx-book
description: 부크크(Bookk) 책 조판 파이프라인 — B5 교재는 승인된 본책 hwpx를 템플릿으로 Markdown을 hwpx로 변환하고, A5(국판) 단행본은 부크크 워드서식으로 Markdown을 docx로 변환한다. 기존 hwpx에서 목차(부/장/절)·스타일 구조 추출과 출력 검증 포함. hwpx/한글 문서를 읽거나 만들거나, 교재·단행본 원고를 출간 포맷으로 조판하거나, 목차를 뽑아야 할 때 반드시 이 스킬을 사용할 것. "hwpx", "한글 파일", "부크크", "B5 교재", "A5", "국판", "조판", "목차 추출", "원고를 책 포맷으로" 같은 말이 나오면 직접 ZIP을 풀거나 새 변환 코드를 짜지 말고 이 스킬의 스크립트를 쓴다. 논문(학술지)은 inca-paper, 슬라이드·교안은 workshop-deck을 쓸 것 — 이 스킬은 교재(B5)·단행본(A5)·워크북 전용. 원고 문체 윤문은 ai-tone-remover로. [분류: 조판·출판 / 교재B5·단행본A5·워크북 / 윤문: 단행본=L포함·교재=L제외]
---

# hwpx-book: 부크크 책 조판 파이프라인 (B5 hwpx / A5 docx)

## ⛔ 집필 금지 표현 (이수미 전 산출물 공통 — 어기면 AI 흔적)

**책 원고만이 아니라 슬라이드(pptx)·발표자 노트 등 이수미의 모든 산출물에 적용한다.** 원고·캡션·그림 라벨 어디에도 쓰지 말 것. 발견하면 평이한 표현으로 대치하고, 빌드/조판 전 grep으로 0개 확인한다. 조사 끝소리 바뀌면 같이 맞춘다(기둥이→요소가, 관문으로→검사로). 슬라이드 제작 시 workshop-deck 스킬에도 같은 규칙과 빌드후 grep 검증이 명시돼 있다.

| 금지 | 대치 |
|---|---|
| **관통(하다)** | 전체에서 쓰다 / 거듭 다루다 |
| **쥐다 / 쥐고 있다**(손에 쥐는 은유) | 맡다 / 직접 정하다 / 책임지다 |
| **척추**(이 책의 척추 등) | 중심 |
| **(네) 기둥** | (네) 요소 |
| **관문** | 검사 / 기준 / 단계 / 점검 |
| **받친다 / 떠받친다**(지탱 은유) | 지킨다 / 책임진다 / 담당한다 |
| **꿰다 / 꿰어 / 한 줄로 꿰는** | 잇다 / 이어 / 하나로 잇는 |
| **흐른다**(문장 서술 "~로 흐른다") | 이어진다 / 순서를 따른다 |
| **출발점** | 시작점 |
| **뿌리**(원인 은유) | 원인 |
| **여정** | 과정 / 흐름 / 길 |

추가로 **따옴표(' " “ ” ‘ ’)·인라인 백틱 금지**, AI 억양(띄어쓴 엠대시 ` — `, "A가 아니라 B다" 남발, "~것이다" 남발) 금지, 상투 비유(손에 넣다·길잡이·두 마리 토끼·발판·디딤돌·마중물·밑거름·첫걸음을 떼다·비로소·마침내·나침반·첫 단추) 금지.

또 **AI 프레젠테이션·마케팅 상투 표현 금지**(슬라이드·노트 특히): "이 한 문장이(이 한 줄이·한마디가) ~을 만든다 / 만든 차이", "오늘 우리가(우리는)~ / 우리가 함께~", "~의 비밀", 시간대 과잉 강조("오늘 오전~" 반복) 등 과장·호명·티저 카피. → 무엇이 구체적으로 달라졌는지 담백하게 서술하고, 청중 호명·티저·시간대 강조는 뺀다. (2026-06 AX 워크숍에서 지적)

또 **이모지·이모지형 딩벳 전면 금지**(산출물 본문 = 슬라이드·노트·Notion·책 모두): 컬러 이모지(🛠 ✅ 🎯 📘 🙋 등)와 이모지 변형 글리프(✓ ☑ ▶ ☆ ● ➤ 등) 모두 제거. 강조는 색·굵기·머리말·번호로 대신한다. 화살표 →(U+2192)는 흐름도 연결용으로만 허용. (2026-06 AX 지적)

또 **자기 지칭 금지**: 이 책에서/이 책의/책 전체 같은 표현 대신 부·장 번호로 구체적으로 지칭한다(이 책의 후반부→2부와 3부, 이 책에서 다루는 위치→위치). 그리고 **표 머리행은 최단 명사**로 쓴다(적용 분야→분야, 하는 일 정도만 허용 — 구·절 형태 금지). (2026-07 AI영상분석 시안에서 지적)

⚠️ **마크다운 원고(ch*.md)와 조판 hwpx 둘 다** 고쳐야 한다 — hwpx만 고치면 md에서 재빌드할 때 되살아난다(2026-06 VIBE에서 발생).

**자동 점검**: `python scripts/clean_ai_traces.py <파일.hwpx|md>`(dry-run)가 ① 고유 은유어(자동치환) ②
흔한 AI 티 표현(오늘 우리가·산출물·결과물·시사하는 바·결론적으로·이러한 맥락에서·~의 비밀 등 — 맥락 의존이라
**보고만**, 사람이 윤문)을 함께 짚어 준다. 탐지 목록은 imnotai(github.com/sumilee-pcu/imnotai)에서 책 맥락에
맞는 것만 추렸고, 새 표현이 보이면 스크립트의 `REPORT_RE`에 (라벨, 정규식) 한 줄로 추가한다.

## 판형별 경로 선택

| 판형 | 용도 | 포맷 | 스크립트 |
|---|---|---|---|
| **B5(46배판)** 188×257 | 교재(코드 실습서) | md → **hwpx** (승인 본책 템플릿) | `md2hwpx.py` |
| **A5(국판)** 154×216 | 단행본(논문작성법 류) | md → **docx** (부크크 워드서식) | `md2docx_a5.py` |

## B5 교재: hwpx 파이프라인

게임인공지능첫걸음(B5, 부크크 승인) 집필에서 확립한 파이프라인. 핵심 원리:
**hwpx를 처음부터 만들지 않는다.** 승인된 본책 hwpx를 템플릿으로 복제하고
`Contents/section0.xml`(본문)만 교체한다. 페이지 설정(B5)·글꼴·스타일은 전부
템플릿의 `header.xml`과 첫 문단의 `secPr`에 들어 있으므로 건드리지 않으면 보존된다.

## 스크립트 (scripts/)

| 스크립트 | 역할 |
|---|---|
| `hwpx_outline.py` | hwpx에서 목차(부/장/절)·글자모양 일람 추출 |
| `hwpx_text.py` | hwpx 본문을 평문 텍스트로 추출(읽기·교정·금지표현 grep용) |
| `md2hwpx.py` | [B5] Markdown 원고 → 본책 스타일 hwpx 변환 |
| `validate_hwpx.py` | [B5] 출력 hwpx 무결성 검증 |
| `md2docx_a5.py` | [A5] Markdown 원고 → 부크크 국판 docx 변환 |
| `figlib.py` | 교재 삽화(개념 다이어그램) 공용 스타일·프리미티브 라이브러리 |
| `hwpx_insert_figs.py` | hwpx 본문에 PNG를 앵커 텍스트 기준 일괄 삽입 |
| `hwpx_code_boxes.py` | 코드박스 정규화: md2hwpx의 1열 코드'표'를 테두리 '문단'(border+connect=1)으로 변환 → 코드가 좌측바에 밀착·본문폭 규칙적 |
| `hwpx_pdf_export.py` | 한글 COM으로 hwpx→PDF 렌더(실제 페이지번호 추출·육안검증. Quit 안 함=사용자 문서 보호) |
| `strip_linesegs.py` | section 전역 linesegarray 제거(외부 편집 후 한글 변조차단 해제, 함정 3) |
| `gen_cover.py` | 파라메트릭 앞표지 생성(네이비+골드 시리즈 디자인, spec JSON→300DPI 인쇄용) |
| `gen_openers.py` | 부·장 간지 + 반표지/속표지 전량 생성(spec JSON, 팔레트·문안만 책별 교체) |
| `design_studio.py` | 표지·간지 GUI(로컬 웹앱, 의존성 제로) — 폼 편집→실제 엔진 미리보기→300DPI 출력 |

### 0. 본문 읽기/검수 — `hwpx_text.py`

hwpx는 ZIP이므로 직접 풀지 말고 이 스크립트로 평문을 뽑는다. 본문 통독·교정,
그리고 위 **집필 금지 표현을 grep으로 0개 확인**할 때 쓴다.

```
python scripts/hwpx_text.py <책.hwpx>                       # 평문을 stdout으로 (auto: 미리보기→없으면 본문 XML)
python scripts/hwpx_text.py <책.hwpx> --source sections     # 본문 section*.xml에서 전체 추출(전수 검수용)
python scripts/hwpx_text.py <책.hwpx> --out extracted.txt   # 파일로 저장 후 grep
```

`--source` 기본값 `auto`는 `Preview/PrvText.txt`(한글이 저장한 미리보기, 빠르지만
앞부분 위주)를 먼저 보고, 비면 `Contents/section*.xml` 본문을 파싱한다. **전체를
빠짐없이** 검수/grep하려면 `--source sections`를 명시할 것(미리보기는 일부만 담길 수 있다).

### 1. 목차/구조 추출

```
python scripts/hwpx_outline.py <책.hwpx> --analyze        # 1단계: 문단별 charPr 사용 분석 (제목 id 찾기)
python scripts/hwpx_outline.py <책.hwpx> --map "67:1,70:2,13:2,19:3" --out outline.md
python scripts/hwpx_outline.py <책.hwpx> --styles         # charPr id별 크기/굵기 일람
```

처음 보는 hwpx는 반드시 `--analyze`부터: 각 charPr id의 크기·굵기·사용 횟수·샘플
텍스트가 나오므로 부/장/절 제목 id를 바로 식별할 수 있다. 그 다음 `--map "id:레벨,..."`
(1=#, 2=##, 3=###)으로 추출. 출력의 `(?cid=NN)`은 맵에 없는 굵은 대형 글자 — 제목
후보다. 목차 페이지 항목(탭 leader 포함 텍스트)은 본문 제목과 별도 id이므로 무시한다.

**검증된 맵 — 게임인공지능첫걸음_B5_최종버전.hwpx**: `--map "67:1,70:2,13:2,19:3"`
(부=67, 장=70(예외 1건 13), 절=19. 6부/13장/장당 9~10절 구조 확인 완료)

### 2. Markdown → hwpx

```
# 기본: 동봉 본책 템플릿(assets/B5_book_template.hwpx) + 검증된 charmap 자동 적용
python scripts/md2hwpx.py --out <초안.hwpx> 장01.md 장02.md ...

# 다른 템플릿을 쓸 때 (id가 다르므로 charmap 함께 지정)
python scripts/md2hwpx.py --template <승인본책.hwpx> --out <초안.hwpx> \
       --charmap "h1:70,h2:19,h3:7,bold:7,body:11,quote:9" 장01.md 장02.md ...
```

`--charmap` 키: h1(#)/h2(##)/h3(###)/bold(####·굵게·표머리)/body/quote(>).
생략하면 `_wbtmpl/book` 워크북 템플릿 기본값(33/23/50/7/12/9). **템플릿마다 id가
다르므로** 새 템플릿이면 `--analyze`로 확인 후 지정한다. lineseg 높이는 템플릿
header.xml에서 자동으로 읽는다.

`--textwidth <HWPUNIT>`: 표·코드박스 폭의 기준이 되는 본문 폭. 기본 36000(승인 본책
B5). **템플릿마다 다르므로** 본문 문단 lineseg의 horzsize 값으로 확인해 지정한다
(예: LLM애플리케이션입문 계열 32670). 표 칼럼 폭은 셀 내용 길이에 비례해 자동
배분된다(한글 1.0·라틴 0.55 가중, 최소폭 보장 — 행이 한 줄에 깔끔히 들어오도록.
2026-07 AI영상분석 시안에서 추가).

**검증된 charmap — 최종본책 템플릿**: `h1:70,h2:19,h3:7,bold:7,body:11,quote:9`
(end-to-end 변환·검증·역추출 확인 완료. h3와 bold가 id 7을 공유하므로 ###와 표
머리행이 같은 모양 — 소절을 따로 구분하려면 header.xml에 글자모양 추가 필요, 함정 4 참고)

- 템플릿은 `.hwpx` 파일 또는 미리 풀어둔 폴더(예: `인공지능교재집필\_wbtmpl\book`) 둘 다 가능.
- md 파일 하나가 한 장(章). 각 파일은 자동으로 새 쪽에서 시작.
- 기본으로 템플릿 BinData(이미지)를 제거하고 manifest를 정리한다. 이미지가 필요하면
  `--keep-bindata` — 단, md의 이미지 문법은 변환되지 않으므로 그림은 한글에서 수동 배치.

지원하는 md 문법: `#`~`####` 제목, 본문, `- ` 불릿, `1. ` 번호, `> ` 인용,
`**굵게**`, `` `코드` ``(굵게 처리), 표(`|`), 코드펜스(1열 박스 표), `- [ ]` 체크박스, `---`(여백).
이 밖의 문법(이미지, 각주, 중첩 리스트 등)은 본문 텍스트로 떨어지므로 원고에서 피한다.

### 3. 검증 (변환 후 반드시)

```
python scripts/validate_hwpx.py <출안.hwpx>
```

마지막 줄 `VALID HWPX` 확인. 최종 확인은 사용자가 한글 뷰어로 직접 연다(글꼴
임베딩·줄바꿈은 스크립트로 검증 불가).

### 4. 코드박스 정규화 — `hwpx_code_boxes.py` (코드 있는 책)

md2hwpx는 코드펜스를 **1열 표**로 조판한다. 표는 셀 패딩 때문에 코드가 좌측 액센트바에서
떨어지고 폭·정렬이 불규칙해 보인다(블록체인 책의 깔끔한 코드박스와 다름). 코드에 스타일
(Consolas charPr + 좌측바 borderFill)을 입힌 **뒤**, 이 스크립트로 1열 코드표를 **테두리 문단**
(border + `connect="1"`)으로 바꾸면 코드가 좌측바에 밀착하고 박스가 본문폭에 규칙적으로 맞는다.

```
python scripts/hwpx_code_boxes.py <책.hwpx> [out.hwpx]   # id는 파일에서 실측(재저장·재번호돼도 동작)
```

- 코드 charPr·좌측바 borderFill·신규 paraPr id를 파일에서 자동 감지하므로, 한글이 재저장해
  id가 뒤섞인 파일에도 그대로 동작한다(2026-07 ROS2 1·7장에서 확립).
- 전제: 1열 코드표에 **이미** 코드 스타일이 입혀져 있어야 한다(그 표의 borderFill을 문단이 물려받음).
  스타일 미적용 상태면 책별 restyle(Consolas charPr + 좌측바 borderFill 주입)을 먼저 돌린다.
- 실행 후 `validate_hwpx.py` → 한글로 직접 확인. linesegarray는 스크립트가 자동 제거(변조차단 방지).

## 그림(삽화): figlib + hwpx_insert_figs

md2hwpx는 이미지를 넣지 않는다(텍스트·표·코드만). 그래서 **그림은 ① figlib로 생성 → ② 변환 후 hwpx_insert_figs로 삽입**(또는 한글 수동 배치)한다.

### 1. 삽화 생성 — `figlib.py` (import 라이브러리)
matplotlib 기반 개념 다이어그램(흐름도·비교·와이어프레임)용 공용 스타일·프리미티브.
**개별 그림은 책별 데이터**이므로 각 책 폴더의 생성 스크립트에서 import해서 그린다.

```python
import sys; sys.path.append(r"C:\Users\user\.claude\skills\hwpx-book\scripts")
from figlib import *
set_outdir("figs")
fig, ax = canvas(8.6, 3.4, ylim=6.0)
gtitle(ax, 8, 5.6, "그림 1-3  LLM 응답 생성 흐름")
hflow(ax, [("입력","사용자 프롬프트",BLUE_L,BLUE),
           ("토큰화","문장 분할",PURPLE_L,PURPLE),
           ("응답","문장 완성",GOLD_L,GOLD)], y=3.0, w=3.3, h=2.0, gap=0.9)
save(fig, "fig1_3_tokenflow.png")     # 300DPI·흰배경, figs/에 저장
```

- 프리미티브: `box·T·arrow·gtitle`, 합성: `stepbox·panel·hflow·list_panel`. 좌표계는 가로 16 단위.
- 통일 타이포(`F_TITLE 15`/`F_HEAD 13`/`F_BODY 11.5`/`F_SUB 10.5`)·팔레트(BLUE/PURPLE/GOLD/GREEN/RED + `_L` 연색 + `HEAD_*`).
- 한글 폰트는 malgun→Apple→Nanum→Noto 순 자동 탐색. **설치 확인**: `python figlib.py --demo` → `figs/_figlib_demo.png`.

### 2. 그림 삽입 — `hwpx_insert_figs.py`
앵커 텍스트가 든 문단 **뒤**에 그림을 삽입. 앵커 문단의 `paraPrIDRef`를 상속하므로 템플릿(A5/B5) 무관.

```
# 플랜(TSV, # 주석·빈줄 무시). 2열(png⇥앵커, 섹션 자동탐색) 또는 3열(png⇥섹션N⇥앵커)
#   fig1_3_tokenflow.png<TAB>이 과정을 반복해 응답을 완성한다.
python hwpx_insert_figs.py --hwpx 초안.hwpx --plan figplan.tsv --figdir figs --dry-run   # 앵커 점검
python hwpx_insert_figs.py --hwpx 초안.hwpx --plan figplan.tsv --figdir figs              # 실제 삽입
```

- 폭: `--width`(이미지 표시폭, 기본 32000) · `--bodywidth`(lineseg 가로폭=본문폭, **B5 36000 / A5 29196**, 기본=width).
- 앵커가 **유일**해야 삽입(2열은 전체 섹션에서, 3열은 지정 섹션에서). 중복/미발견은 ERROR로 보고하고 건너뜀.
- `<hwpx>.bak` 자동 백업(`--no-backup`으로 생략), opf:item에 `isEmbeded="1"` 자동, mimetype STORED 유지.
- 삽입 후 **반드시** `validate_hwpx.py`로 검증하고 한글로 직접 열어 확인.

## 목차(TOC): 페이지번호 + 점 리더 (기존 hwpx 직접 편집)

출고본이 굳은 뒤(md와 발산·hwpx가 canonical) 목차 페이지번호를 실제 레이아웃에 맞추고, 부크크 하우스 스타일대로 **우측정렬 탭 + 점 리더**를 넣는 정본 작업. 2026-07 블록체인 책에서 확립. **md 재빌드 금지, section0.xml 직접 치환만**(그림·스타일 리라이트 보존).

### A. 실제 페이지번호 뽑기
1. `python scripts/hwpx_pdf_export.py <책.hwpx> <책>.pdf` — 한글이 렌더한 진짜 페이지.
2. PyMuPDF(`fitz`)로 페이지 텍스트를 뽑아, 장 표지 `제N장`·절 머리 `N.M.`·후부(용어집·참고문헌·부록 A/B/C)가 **처음 나타나는 물리 페이지**를 찾는다.
3. **오프셋**: 인쇄 쪽번호 = PDF 물리쪽 + N. 앞부속(표지·판권·머리말·목차) 페이지 수만큼 차이 난다. **각주에 찍힌 숫자를 실측**해 오프셋 확정(블록체인=+10, 책마다 다름). 히스토그램으로 최빈값 검증.

### B. 목차 줄에 번호 채우기 — 재생성 말고 **제자리 치환**
- ⚠️ 한글이 재저장한 hwpx는 **charPr id가 재배치**돼 있다(옛 목차 빌더의 부63·장42·절22 → 재저장본은 부29·장24·절16·후부25 식). **문단을 재생성하는 스크립트는 StopIteration로 깨진다.** 반드시 `--analyze`나 파싱으로 현행 목차 줄의 charPr을 먼저 확인.
- 안전한 방법: 목차 영역(`CONTENT`~`지은이` 문단 사이)에서 각 줄의 **마지막 `<hp:t>` 안 끝 숫자만** 정규식으로 바꾼다. 순서 기반 매핑(목차 줄과 추출 리스트 둘 다 책 순서) — 제목 텍스트 매칭보다 견고. 장/절/후부 개수(예 13/69/5)로 소비 검증.
- 제목에도 숫자가 있으니(`ERC-20`·`제6장`) 반드시 `(.*\S)\s\s+(\d{1,3})$`처럼 **끝의 2칸+숫자**만 잡는다.

### C. 점 리더 + 우측정렬 (자매편과 통일)
- 자매편(LLM책 06)은 목차 줄이 `<hp:t> 제목<hp:tab leader="7" type="2"/>페이지</hp:t>` — 탭이 **hp:t 안에** 인라인으로 들어가고, `paraPr`의 `tabPr`(예 `<hh:tabItem pos="58000" type="RIGHT" leader="CIRCLE"/>`)이 우측정렬 점선을 만든다.
- **핵심**: 두 책의 목차 paraPr·tabPr이 동일하면(같은 템플릿 계열이면 대개 동일) **탭만 끼우면** 끝. 공백 2칸을 `<hp:tab leader="7" type="2"/>`로 치환. `hwpx_outline.py`/파싱으로 두 책 `paraPr`·해당 `tabPr`이 같은지 먼저 대조.
- 편집한 목차 문단은 **linesegarray를 지워** 한글이 탭 폭·줄배치를 재계산하게 한다.

### D. 넘치는 장 제목 — 축약 우선, 안 되면 장평
- 제목이 길면 점선이 안 그려지거나 두 줄로 넘친다. **측정 규칙(블록체인 실측)**: 점선은 `title_right ≤ ~400pt`(=번호와의 gap ≥ ~185pt)에서 렌더, gap 128pt는 0개. PDF 스팬 bbox로 장별 `title_right`를 재 어느 줄이 넘치는지 특정.
- **1순위: 제목 축약**(TOC와 본문 장 표지 **양쪽** 치환, 산문 언급과 안 겹치는 패턴으로 — 예 `솔리디티 프로그래밍 (1)`→`솔리디티 (1)`). 사용자에게 문안 확정 받는다(정체성).
- **2순위: 장평(글자 가로폭 %)** — 축약해도 넘칠 때. 해당 줄 charPr을 복제해 `<hh:ratio hangul="84" latin="84" …/>`로 낮춘 새 charPr(id=max+1, itemCnt+1) 만들고 **그 목차 줄의 run만** repoint. **본문 장 표지는 정폭 유지**(공간 넉넉 → 안 건드림). 84%면 gap 199 확보돼 점선 복구(블록체인 제7장).

### E. 마무리 (필수 순서)
1. `header.xml`을 건드렸으면(장평 charPr 추가 등) **한글이 변조차단**한다 → `python scripts/strip_linesegs.py <책.hwpx>`로 section 전역 linesegarray 0개. (함정 3)
2. `validate_hwpx.py` → `VALID HWPX`.
3. `hwpx_pdf_export.py`로 재렌더 후 **전수 검증**: ①총 페이지 수 불변 ②목차 숫자 == 본문 실제 위치(장/절/후부 전부) ③넘쳤던 장 줄에 점선 렌더(gap의 검은 픽셀 카운트). 페이지가 밀렸으면 오프셋/번호 재적용.
- 단계마다 `*.before_*.hwpx` 백업. COM export는 **사용자가 다른 한글 문서를 열어두면 Quit 금지**(스크립트 기본값이 FileClose — 지킴).

## 표지·간지 디자인 자산: gen_cover + gen_openers (spec JSON 기반)

이수미 시리즈의 표지(네이비 `#0A3345`+골드 `#B99E5A`)와 내지 간지 디자인을 코드로 고정한 생성기. **AI 이미지 생성 금지** — 3:4 비율 고정·도련 미반영·저해상도 문제가 반복된다. 생성기는 판형·도련·300DPI를 처음부터 만족한다(블록체인 2026-07 검증).

### 앞표지 — `gen_cover.py`
```
# spec 복제 후 book 필드(제목줄·부제·키워드·저자·쪽수)만 수정
python scripts/gen_cover.py <cover_spec.json> <출력접두어>
# → <접두어>_front_300dpi.png (도련 3mm 포함, B5=2220x3106px) + _preview.png(적색선=재단선)
```
- 레이아웃 규칙이 spec에 다 있다: 좌측 골드 바, 타이틀 줄별 폭맞춤(이진탐색), 골드 박스 부제, 골드 도트 키워드 스트립, 저자명.
- 폰트: Helvetica Condensed Black(제목)·GmarketSansTTFBold(한글)·BookkGothic_Bold(저자) — 사용자 폰트 폴더에서 자동 탐색.
- **책등·날개는 업체 의뢰**: 쪽수·판형만 전달(부크크 표지 레이아웃 hwp가 책등 폭 산출). 뒷표지가 필요하면 같은 엔진에 텍스트 블록 추가.

### 부·장 간지 + 반표지/속표지 — `gen_openers.py`
```
python scripts/gen_openers.py <opener_spec.json> [출력폴더]
# → partN_opener.png, chNN_opener.png, title_front.png, title_inner.png (300DPI, 4.537x7.28in)
```
- spec 템플릿: `assets/opener_spec.template.json`(블록체인 실물 값 — 부·장 간지는 실물과 **픽셀 일치** 검증됨).
- 계보: 09영상분석(NAVY) → 블록체인(진초록) → 팔레트만 바꿔 재사용. 새 책 = palette 7색 + 문안(parts/chapters intro 줄배열=수동 개행이 조판 의도).
- 장 간지: 어두운 배경+장번호 워터마크(110pt α0.55)+우측정렬 제목+골드 괘선. 부 간지: 크림 배경+PART 넘버 88pt.
- **주입은 별도**: 간지 PNG는 `hwpx_insert_figs.py` 또는 책별 inject 스크립트로 hwpx에 넣는다(전면 이미지 문단 치환 + pageHiding 보존 — 블록체인 `_조판/openers/inject_*.py` 참조).

### GUI — `design_studio.py` (표지+간지 통합 스튜디오)
```
python scripts/design_studio.py [포트=8765]   # 브라우저 자동 오픈, Ctrl+C 종료
```
- 로컬 웹앱(stdlib http.server — Flask 등 설치 불필요). 탭 2개: 표지 / 간지·표제지.
- 미리보기 = **실제 gen_cover/gen_openers 엔진**을 110DPI로 호출 → 화면과 인쇄본이 어긋날 수 없음. 간지 미리보기는 표본(부1·장 처음/끝·표제지)만, 출력 시 전량 생성.
- [300DPI 출력] = 출력 폴더에 인쇄용 PNG + 사용한 spec JSON 동시 저장(재현 가능). [스펙 저장/불러오기]로 책별 프로필 관리.
- matplotlib 스레드 문제는 RENDER_LOCK으로 직렬화. 미리보기 해상도는 `PREVIEW_DPI` 상수.

## 스타일 매핑 (템플릿 2종 — id가 서로 다름에 주의)

| md | 용도 | 워크북 템플릿(_wbtmpl/book) | 최종본책(최종버전.hwpx) |
|---|---|---|---|
| `#` | 장 제목 | 33 (1500 bold) | 70 (1400 bold) / 부 제목은 67 (1600 bold) |
| `##` | 절 제목 | 23 (1100 bold) | 19 (1100 bold) |
| `###` | 소절 | 50 (1100 bold) | 7 (1000 bold, bold와 공유) |
| `####`, `**..**` | 굵은 라벨/표 머리 | 7 (1000 bold) | 7 (1000 bold) |
| 본문 | 본문/불릿/표 셀 | 12 (1000) | 11 (1000) |
| `>` | 인용/캡션 | 9 (900) | 9 (900) |

최종본책의 장 구성 라벨: 29(1000 bold)="이 장에서 다루는 내용"/"학습 목표",
15(1000 bold)="정리"/"핵심 용어", 9(900)=그림 캡션("그림 N-N. ...").
paraPr(워크북 기준): 16=본문, 1=표 래퍼, 22=표 셀. borderFill 4=표 테두리. 본문 폭 36000 HWPUNIT.

## A5(국판) 단행본: docx 파이프라인

AI활용논문작성법 v3 출간에서 검증된 경로. hwpx가 아니라 **python-docx로 부크크
워드서식을 채우는** 방식이다 (A5 단행본은 부크크에 워드 입고).

```
python scripts/md2docx_a5.py --out <원고.docx> 장01.md 장02.md ...   # 한 문서로 연결
python scripts/md2docx_a5.py --out-dir <폴더> 장01.md 장02.md ...    # 장별 파일
```

- 템플릿 기본값: 스킬 동봉본 `assets/A5_bookk_template.docx` (부크크 공식 빈 A5 워드서식 — 자동 인식되므로 어느 컴퓨터에서든 그대로 동작). 다른 서식은 `--template`.
- 페이지: 15.4×21.6cm, 여백 좌우 2.3/상 2.8/하 3.3/제본 0.5cm. 푸터 가운데 쪽번호 자동.
- 글꼴: 본문 KoPubWorld바탕체 9.4pt(행간 1.45), 제목 KoPubWorld돋움체, 코드 Consolas 7.4pt — **KoPubWorld 글꼴이 설치돼 있어야** 한글 부분이 의도대로 렌더링된다.
- 제목 규칙: `#`=19pt / `##`이 "제"로 시작(`제N장 ...`)하면 17pt 가운데 정렬 장 표제 / 일반 `##`=13.2pt 남색 / `###`=11.2pt / `####`=10.2pt.
- B5 hwpx 변환기보다 md 지원 폭이 넓다: 이미지(`![](path)` — 본문 폭 맞춤 삽입), 중첩 리스트, 인용 블록 음영, 표 머리행 음영.
- 의존성: `pip install markdown beautifulsoup4 lxml python-docx`
- 원본: `U:\2026\02_논문POD집필\build_bookk_a5_chapters.py`

## 함정 (어기면 한글에서 안 열리거나 깨짐)

1. **mimetype은 ZIP의 첫 항목 + 무압축(STORED)** — md2hwpx.py가 처리하지만, 수동 패키징 시 잊기 쉽다.
2. **section0.xml 첫 문단은 보존** — `secPr`(B5 페이지 설정)이 여기 있다. 교체 범위는 첫 `</hp:p>` 이후부터.
3. **`<hp:linesegarray>`는 직접 만들지 말 것** — 이것은 한글이 저장할 때 기록하는 줄 배치 캐시다. 생성기가 한 줄짜리로 기록하면 여러 줄 문단이 전부 같은 위치에 겹쳐 렌더링된다(잘라내기→붙여넣기 하면 정상화되는 증상이 이것). 빼고 저장하면 한글이 열 때 스스로 계산한다. md2hwpx.py는 기본으로 기록하지 않는다(`--legacy-lineseg`로만 활성화).
   - **⚠️ 기존 한글 hwpx를 파이썬으로 외부 편집할 때(매번 겪는 함정)**: 한글이 만든 원본에는 모든 문단에 linesegarray가 박혀 있다. section을 외부에서 수정하면 한글이 **"문서가 손상되었거나 변조되었을 가능성… [문서 보안 설정]을 [낮음]으로"** 경고로 **하드 차단**(확인 눌러도 로드 안 됨). **해결 = 보안 설정 건드리지 말고, `Contents/section*.xml`에서 `<hp:linesegarray>…</hp:linesegarray>` 및 `<hp:linesegarray/>`를 전부 제거 후 재패킹**(mimetype STORED 우선). 그러면 한글이 열 때 레이아웃 재계산하며 경고 없이 정상 오픈. **일부만(새로 넣은 문단만) 지우면 안 되고 section 전역에서 0개로 만들어야** 한다. 헛다리(다 무효): ZIP 지문 일치·악성코드차단 체크해제(도구→환경설정→기타)·보안 리본 "문서 보안 설정" 버튼·환경설정 파일/기타 탭. 검증은 반드시 한글 GUI로 직접 열어 확인(validate_hwpx 통과해도 변조차단은 못 잡음). (2026-06 부산 새일센터 강의지도안 hwpx 편집에서 재확인.)
4. **header.xml에 글자모양/문단모양 추가 시 id는 연속 인덱스** — 기존 max id 다음 번호를 써야 한다 (예: charPr 0~65 존재 → 66부터). itemCnt도 함께 갱신.
5. **BinData를 지우면 content.hpf의 `<opf:item id="imageN">`도 함께 제거** — 매니페스트 불일치는 열기 오류. **이미지 추가 시 opf:item에 `isEmbeded="1"` 필수** — 빠지면 한글이 외부 링크로 보고 "그림 경로" 프롬프트 + 빈칸 렌더(validate는 통과). 기존 항목 형식: `<opf:item id="imageN" href="BinData/imageN.png" media-type="image/png" isEmbeded="1"/>`. (이 책은 header.xml에 binDataList 없이 content.hpf만으로 이미지 등록함.)
6. XML 특수문자는 반드시 escape (`&`, `<`, `>`).
7. **새 구역(sectionN.xml) 신설은 한글이 렌더 안 함 — 기존 구역에 병합할 것.** content.hpf(manifest+spine) + `META-INF/container.rdf`(hasPart+SectionFile)에 다 등록하고 validate_hwpx를 통과해도, 한글 GUI는 **net-new 구역을 로드하지 않는다**(구역 수에 안 잡히고 비표시. 클린 재오픈·RDF 추가로도 안 됨). 부록·용어집 등은 독립 구역 대신 **이미 정상 렌더되는 인접 구역에 병합**(예: 용어집을 참고문헌 section19에 합쳐 `[secPr+용어집 제목+본문] + [쪽나눔 참고문헌 제목] + [기존 본문]`)하거나, 기존 장 끝에 `pageBreak="1"` 문단으로 붙인다. (2026-06 생성형AI첫걸음 용어집 107개 추가에서 확인.)
8. **f-string 안에 `\"` 백슬래시 금지(Py3.11)** — 검증 출력에서 `count('...="33"')`을 f-string에 직접 넣으면 SyntaxError. 변수로 빼서 넣을 것.
9. **대괄호(`[`)가 든 hwpx 경로를 PowerShell로 validate 호출 시** `--%`는 뒤 `;`·체이닝까지 먹어 경로가 깨진다. `python -c "import sys; sys.argv=['v', r'<경로>']; exec(open(r'<validate.py>',encoding='utf-8').read())"`로 리터럴 주입이 안전.

## 관련 자산

> 두 파이프라인 모두 동봉 자산(`assets/`)만으로 어느 컴퓨터에서든 동작한다.
> B5 본책 템플릿은 책 원고 전체가 들어 있으므로 **리포는 반드시 private 유지**.
> 아래 `U:\` 경로는 메인 Windows PC 기준 원본 위치다.

- [B5] 동봉 템플릿: `assets/B5_book_template.hwpx` (= 승인 본책 최종버전, 검증 charmap `h1:70,h2:19,h3:7,bold:7,body:11,quote:9`)
- [B5] 워크북 템플릿(풀린 상태, 로컬 전용): `U:\2026\전자책출간관련\인공지능교재집필\_wbtmpl\book`
- [B5] 승인 본책: `게임인공지능첫걸음_B5_이수미_최종버전.hwpx` (온톨로지LLM_차기작자료 폴더)
- [A5] 부크크 워드서식: `U:\2026\02_논문POD집필\부크크서식\[워드서식]A5(국판)_부크크서식(기본).docx`
- [A5] 출간 입고본 예시: `U:\2026\02_논문POD집필\부크크_A5_입력본_v1\`
- 원본 스크립트(이 스킬의 출처): `인공지능교재집필\집필용\게임ai집필\워크북\_md2hwpx.py`, `_validate.py`, `_mksian_hwpx.py`(스타일 추가 예제), `인공지능교재집필\_inspecthdr.py`(header 분석), `02_논문POD집필\build_bookk_a5_chapters.py`(A5 원본)
