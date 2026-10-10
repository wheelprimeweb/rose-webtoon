# ROSE · 임신혜 웹툰

이미지 폴더를 올리면 회차 등록, 표시용 이미지 변환, 이전화·다음화 연결, 사이트 배포가 자동으로 진행됩니다.

사이트: https://wheelprimeweb.github.io/rose-webtoon/index.html

## 다음 회차 올리기 — Windows

처음 한 번만 [GitHub Desktop 공식 설치 파일](https://desktop.github.com/download/)을 설치하고 GitHub 계정으로 로그인합니다. 비밀번호나 인증 코드를 다른 사람에게 보내지 마세요.

1. GitHub Desktop에서 **File → Clone repository → URL**을 선택합니다.
2. `https://github.com/wheelprimeweb/rose-webtoon`을 넣습니다. 저장 위치는 찾기 쉬운 폴더를 선택하고 **Clone**을 누릅니다. 이 작업은 처음 한 번입니다.
3. **Repository → Show in Explorer**를 누르면 웹툰 폴더가 열립니다.

이후 새 회차를 올릴 때는 아래만 반복합니다.

1. GitHub Desktop에서 **Fetch origin**을 누릅니다. **Pull origin**이 나타나면 눌러 최신 상태로 맞춥니다.
2. 탐색기에서 `episodes` 안에 `03` 같은 새 회차 폴더를 만듭니다. 4화는 `04`, 100화는 `100`입니다.
3. 해당 회차의 완성된 사진을 **한꺼번에** 넣습니다. 지원 파일은 PNG/JPG/JPEG/WebP입니다. 폴더 안에 또 폴더를 만들지 마세요.
4. GitHub Desktop 왼쪽 아래 **Summary**에 `3화 추가`를 입력하고 **Commit to main → Push origin**을 누릅니다.
5. [업로드·배포 상태](https://github.com/wheelprimeweb/rose-webtoon/actions)를 엽니다. **ROSE 자동 최적화 및 배포**에 초록색 체크가 생기면 사이트에 반영된 것입니다. 노란색은 작업 중, 빨간색은 실패입니다.

**사진만 복사하고 Push origin을 누르지 않으면 온라인에 올라가지 않습니다.** 한 회차를 여러 번 나누어 Push하면 아직 덜 올린 회차가 공개될 수 있으므로 한꺼번에 올려주세요.

파일 이름은 `001.png`, `002.png`, `010.jpg`처럼 사용하세요. 005가 없어도 004 다음 006이 정상으로 이어집니다. `1.png`와 `001.jpg`처럼 같은 번호를 두 번 쓰면 오류로 중단합니다. PNG가 들어 있는 ZIP 자체를 올리면 안 됩니다. 먼저 압축을 풀어주세요.

HTML은 새로 만들거나 수정할 필요가 없습니다. `episode-03.html` 주소와 메인 목록, 이전화·다음화는 자동 생성됩니다. 마지막 회차는 ‘다음화 준비 중’으로 표시됩니다.

## 로딩과 화질

- 원본은 `episodes`에 그대로 남고 기존 원본 주소도 유지됩니다.
- 원래 해상도 WebP는 **무손실**입니다. 원본을 읽어서 만든 픽셀과 변환된 픽셀이 모두 일치하는지 검사합니다. 얼굴·말풍선·효과음·색상·여백을 AI로 바꾸지 않습니다.
- 휴대폰은 640/960px 축소본 또는 원래 크기 중 화면 크기·화면 배율에 맞는 것을 브라우저가 선택합니다. 축소본도 종횡비를 유지하고 무손실 형식으로 저장합니다. 확대 감상에서는 원래 크기보다 세부가 적을 수 있습니다.
- 첫 컷은 우선 다운로드하고 아래 컷들은 브라우저가 스크롤 위치에 맞춰 불러옵니다. 처음부터 64컷 전체를 내려받지 않습니다.
- 화면을 누르거나 오른쪽 아래 **메뉴**를 누르면 이동 메뉴가 표시됩니다. 끝까지 읽으면 아래에도 이전화·목록·다음화가 있습니다.
- 이미지 오류가 나면 자동으로 원래 크기 WebP, 원본 순서로 재시도하고 계속 실패하면 **이 컷 다시 불러오기** 버튼을 표시합니다.
- 사이트가 컷 사이에 추가하는 간격은 0px입니다. 업로드한 그림 자체의 위아래 여백만 사용합니다. 원본 이미지 안쪽의 색상이나 여백은 수정하지 않습니다.
- 방문 중 GitHub API를 호출하지 않습니다. 회차 목록은 빌드할 때 완성됩니다.

## 상태·용량 확인

[Actions](https://github.com/wheelprimeweb/rose-webtoon/actions)에서 해당 실행을 열면 컷 수, 원본/변환 후 용량, 재사용 이미지 수가 표시됩니다. 사이트의 `build-report.md`와 `episodes.json`에도 관리 정보가 있습니다. 보고서는 합산 파일 용량이며 실제 체감 시간은 통신 상태와 기기에 따라 달라집니다.

같은 내용의 그림이 여러 파일에 들어 있으면 경고를 표시하지만 자동으로 삭제하지 않습니다. 의도된 반복 컷일 수 있기 때문입니다. 빠진 번호는 허용되므로 ‘실수로 안 올린 그림’까지 자동으로 알아낼 수는 없습니다. 최종 컷 수를 꼭 확인하세요.

처음 빌드는 기존 모든 컷을 변환하므로 수 분 이상 걸릴 수 있습니다. 다음부터는 바뀌지 않은 이미지의 변환 결과를 재사용합니다. GitHub 캐시가 만료되면 다시 변환하지만 원본은 변하지 않습니다.

## 오류가 났을 때

Actions에서 빨간 실행 → 빨간 단계 이름을 누르면 원인이 표시됩니다. 파일 이름 중복, 빈 회차 폴더, 읽을 수 없는 이미지, 기존 원본 변경, 과도하게 큰 이미지가 있으면 배포를 중단합니다. **빌드가 실패하면 마지막 정상 공개 사이트가 유지됩니다.** 잘못된 파일을 고치고 다시 Commit/Push하면 됩니다.

기존 1·2화는 파일 이름/순서/내용을 검사하는 보호 목록이 있습니다. 실수로 원본을 바꾸거나 지우면 배포하지 않습니다. 기존 컷을 정말 수정할 때는 백업을 먼저 만들고 보호 목록을 함께 검토해야 합니다.

## 복구

- 새 회차에 문제가 있으면 GitHub Desktop의 **History**에서 방금 올린 커밋을 오른쪽 클릭하고 **Revert changes in commit**을 선택한 뒤 **Push origin**을 누릅니다. 해당 변경을 취소하는 새 기록이 남고 자동 재배포됩니다. 기존 기록을 강제로 지우지 마세요.
- 자동화 도입 자체를 되돌릴 때는 도입 커밋을 되돌린 뒤 저장소 **Settings → Pages → Source**를 **Deploy from a branch**, `main` / `(root)`로 되돌립니다. 도입 전 HTML·그림은 최초 백업에도 보존되어 있습니다.
- 전체 저장소 백업 `ROSE_작업전_원본백업.bundle`은 별도 전달 파일입니다. 원본 이미지와 Git 기록을 포함합니다. 복원 예: `git clone ROSE_작업전_원본백업.bundle ROSE_복원본`.

## 최초 배포 설정 / 유지보수 참고

저장소 **Settings → Pages → Build and deployment → Source**는 **GitHub Actions**여야 합니다. 워크플로는 main 업로드 시 검사·최적화·정적 사이트 생성 후 Pages에 배포합니다. 별도 유료 API 키는 없습니다.

생성된 공개 파일은 `_site`에 있습니다. 저장소 루트의 기존 HTML은 도입 전 복구용으로 보존하며, Actions 배포에서는 사용하지 않습니다. 브라우저에서 루트 원본 HTML만 열면 최적화 전 버전이므로 공개 사이트 주소로 확인하세요.

개발 검증: `pip install -r requirements.txt`, `python -m unittest discover -s tests -v`, `python scripts/build.py`, `python scripts/check_site.py`. 테스트 3화·100화는 임시 폴더 안에서만 만들며 공개 사이트에는 올리지 않습니다.

회차 번호는 100화 이상도 지원합니다. 다만 [GitHub Pages는 공개 사이트 전체 용량을 1GB로 제한](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)합니다. 회차 수와 별개로 큰 이미지가 누적되면 이미지 전용 저장소를 분리해야 합니다. 한도 근처에서는 오류로 안내하고 기존 사이트를 유지합니다. 100화 분량의 대용량 그림까지 현재 Pages 한도 안에 무조건 담을 수 있다는 뜻은 아닙니다.

출처: [GitHub Desktop 사용 안내](https://docs.github.com/en/desktop/overview/creating-your-first-repository-using-github-desktop), [GitHub Pages 자동 배포 안내](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
