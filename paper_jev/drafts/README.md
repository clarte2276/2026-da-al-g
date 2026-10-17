# DOCX 초안 작성

빌더는 KIISE 심사 양식에 초안을 넣고, Markdown 파일과 같은 폴더에 DOCX를 만든다. Python 환경에 `python-docx`가 없다면 아래처럼 실행한다.

```bash
uv run --with python-docx python paper_jev/drafts/build_docx.py paper_jev/drafts/roundN_draft.md
```

빌더는 `paper_jev/references/forms/kiise_review_form.docx`를 템플릿으로 사용한다. 초안은 UTF-8로 저장한다. 현재 지원하는 Markdown 형태는 다음과 같다.

- `# 제목`은 한글 제목, 다음의 `*English title*`은 영문 제목이다.
- `## 요약` 다음 내용을 초록으로 넣고, `## 1. ...`부터 본문으로 넣는다. 요약은 본문보다 앞에 있어야 한다.
- `##`와 `###`는 본문 제목과 하위 제목이다.
- 파이프 표는 일반 Markdown 표처럼 쓴다. 구분선 행은 제외되고 첫 행은 굵게 표시된다. 4열 표는 열 폭을 한 단 너비에 맞춘다.
- `![대체 텍스트](figures/fig1.png)`는 초안 파일 기준 상대 경로의 그림을 넣는다. 별도의 `그림 1. ...` 문단은 가운데 정렬된다. `표 1. ...` 문단은 왼쪽 정렬된다.
- 문단 안의 `**굵게**`, `*기울임*`을 지원한다. 줄 끝 두 칸 또는 `<br>`은 강제 줄바꿈이다.
- 참고문헌은 `[1] 저자, ...` 형식으로 한 항목씩 쓴다.

일반 Markdown 링크 렌더링, 목록, 코드 블록, 중첩 표는 지원하지 않는다. 이미지가 없거나 제목·요약·첫 본문 제목이 빠지면 빌드가 실패한다.
