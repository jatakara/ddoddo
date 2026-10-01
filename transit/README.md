# 대중교통 시간 · 길찾기 v2

GitHub Pages에 바로 올릴 수 있는 모바일 우선 단일 페이지 웹앱입니다.

## v2 기능
- 버스정류장 / 지하철역 검색
- 버스: 실시간 도착정보 우선 조회, 미지원 시 첫차·막차·배차간격 자동 대체
- 지하철: 평일/토요일/일요일 자동 구분 + 현재 이후 출발편
- 출발 정류장/역 → 도착 정류장/역 대중교통 길찾기
- 버스 / 지하철 / 도보 구간별 경로 표시
- 예상 소요시간, 요금, 도보거리, 환승 횟수
- 브라우저 현재 위치 → 도착지 길찾기
- 즐겨찾기(LocalStorage)
- PWA용 manifest/service worker 포함
- API 키 없이 UI를 볼 수 있는 데모 모드

## 배포
압축을 풀고 아래 3개 파일을 GitHub Pages 저장소 최상단에 업로드하세요.

- index.html
- manifest.webmanifest
- sw.js

GitHub 저장소 → Settings → Pages → Deploy from a branch → main / root 선택.

## ODsay 설정
1. ODsay LAB에서 애플리케이션 생성
2. Web 플랫폼 생성
3. GitHub Pages 도메인 등록
4. Web API Key 발급
5. 앱의 `API 설정 · 보안`에 Key 입력

Web API Key는 브라우저에서 노출되는 구조이므로 ODsay 관리화면에서 허용 도메인과 사용량 제한을 설정하는 것을 권장합니다.

## 사용 API
- searchStation: 정류장/역 검색
- busStationInfo: 버스정류장 기본 운행정보
- searchSubwaySchedule: 지하철역 전체 시간표
- searchPubTransPathT: 대중교통 경로검색
- realtimeStation: 실시간 버스 도착정보 (지원 지역/계정 조건에 따라 사용 불가할 수 있으며 앱에서 자동 fallback)

## 주의
ODsay 실시간 버스 API는 현재 공개 레퍼런스에서 제외되어 있으며 기존 API 사용자는 계속 사용할 수 있다는 ODsay 관리자 안내가 있습니다.
또한 전국 버스 실시간 도착은 지역별 공공데이터 연계가 필요한 경우가 있습니다.
따라서 실시간 호출 실패 시 앱이 정적 운행정보로 자동 전환합니다.