스타 승자예측 관리툴 v3.2

추가 기능
- 앱 실행 시 version.json으로 최신 버전 자동 확인
- 새 버전 발견 시 자동으로 캐시 우회 주소로 재접속
- 앱 포커스 복귀/홈화면 재진입 시 자동 확인
- 60초마다 자동 업데이트 확인
- 수동 '업데이트 확인' 버튼
- Service Worker가 오래된 캐시를 삭제하고 네트워크 우선 사용
- localStorage의 참가자/대회/예측 기록은 삭제하지 않음

GitHub에 올릴 파일
1. index.html
2. manifest.webmanifest
3. version.json
4. sw.js

중요
- v3.1 → v3.2 첫 전환 때는 기존 v3.1 코드에 자동업데이트 기능이 없기 때문에,
  GitHub에 v3.2를 올린 뒤 최초 1회는 Safari/홈화면 앱을 완전히 닫고 다시 열거나 새로고침해야 할 수 있음.
- v3.2 이후 업데이트부터는 version.json의 버전 숫자만 올리면 자동 감지 가능.
