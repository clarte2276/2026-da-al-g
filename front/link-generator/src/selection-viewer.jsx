import { useEffect, useRef, useState } from "react";
import { PptxViewer, RECOMMENDED_ZIP_LIMITS } from "@aiden0z/pptx-renderer";
import * as pdfjs from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

function TextPane({ content, selection, onSelect }) {
  const root = useRef(null);
  const [pending, setPending] = useState(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const searchEnd = useRef(0);
  const text = content.text;
  const ranges = selection?.ranges || (selection?.exact ? [selection] : []);

  function capture() {
    const native = window.getSelection();
    if (!native?.rangeCount || native.isCollapsed) return;
    const range = native.getRangeAt(0);
    if (!root.current.contains(range.commonAncestorContainer)) return;
    const prefix = range.cloneRange();
    prefix.selectNodeContents(root.current);
    prefix.setEnd(range.startContainer, range.startOffset);
    const start = prefix.toString().length;
    const exact = range.toString();
    if (exact.trim() && text.slice(start, start + exact.length) === exact) {
      setPending({ start, end: start + exact.length, exact });
    }
  }

  function keyboardSelect(event) {
    const native = window.getSelection();
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "a") {
      event.preventDefault();
      const range = document.createRange(); range.selectNodeContents(root.current);
      native.removeAllRanges(); native.addRange(range);
      return;
    }
    const directions = { ArrowLeft: "backward", ArrowUp: "backward", Home: "backward",
      ArrowRight: "forward", ArrowDown: "forward", End: "forward" };
    const direction = directions[event.key];
    if (!direction || (!event.shiftKey && !((event.ctrlKey || event.metaKey) && ["Home", "End"].includes(event.key)))) return;
    if (!native?.modify) return;
    event.preventDefault();
    if (!native.rangeCount || !root.current.contains(native.anchorNode)) {
      const range = document.createRange(); range.selectNodeContents(root.current); range.collapse(true);
      native.removeAllRanges(); native.addRange(range);
    }
    if ((event.ctrlKey || event.metaKey) && ["Home", "End"].includes(event.key)) {
      const range = document.createRange(); range.selectNodeContents(root.current);
      range.collapse(event.key === "Home");
      if (event.shiftKey) native.extend(range.startContainer, range.startOffset);
      else { native.removeAllRanges(); native.addRange(range); }
      return;
    }
    const boundary = ["Home", "End"].includes(event.key);
    const granularity = boundary ? (event.ctrlKey || event.metaKey ? "documentboundary" : "lineboundary")
      : ["ArrowUp", "ArrowDown"].includes(event.key) ? "line"
        : event.ctrlKey || event.metaKey ? "word" : "character";
    native.modify(event.shiftKey ? "extend" : "move", direction, granularity);
    if (!root.current.contains(native.focusNode)) {
      const range = document.createRange(); range.selectNodeContents(root.current);
      range.collapse(direction === "backward"); native.extend(range.startContainer, range.startOffset);
    }
  }

  function find(event) {
    event.preventDefault();
    if (!query) return;
    let start = text.indexOf(query, searchEnd.current);
    if (start < 0) start = text.indexOf(query);
    if (start < 0) { setMessage("찾는 문장이 없습니다."); return; }
    searchEnd.current = start + query.length;
    const walker = document.createTreeWalker(root.current, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    let position = 0;
    let began = false;
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const end = position + node.textContent.length;
      if (!began && start < end) {
        range.setStart(node, start - position); began = true;
      }
      if (began && searchEnd.current <= end) {
        range.setEnd(node, searchEnd.current - position); break;
      }
      position = end;
    }
    const native = window.getSelection();
    native.removeAllRanges(); native.addRange(range);
    root.current.focus({ preventScroll: true });
    const rect = range.getBoundingClientRect();
    root.current.scrollTop += rect.top - root.current.getBoundingClientRect().top - 80;
    capture(); setMessage("찾은 구절을 선택했습니다. 구절 추가를 누르거나 범위를 조정하세요.");
  }

  return <>
    <form className="pane-toolbar" onSubmit={find}>
      <input aria-label="본문 찾기" placeholder="본문에서 찾기" value={query}
        onChange={(event) => { setQuery(event.target.value); searchEnd.current = 0; }} />
      <button>다음 찾기</button>
      <button type="button" disabled={!pending} onClick={() => {
        const kept = ranges.filter(range => range.end <= pending.start || range.start >= pending.end);
        if (kept.length !== ranges.length) setMessage("겹치는 기존 구절을 새 선택으로 바꿨습니다.");
        onSelect({ kind: "text", version_id: content.version_id,
          ranges: [...kept, pending].sort((a, b) => a.start - b.start) });
        setPending(null); window.getSelection()?.removeAllRanges();
      }}>구절 추가</button>
    </form>
    <p className="pane-hint" role="status">{message || "문장을 드래그하거나 Shift와 방향키로 선택한 뒤 구절 추가를 누르세요. 여러 구절을 더할 수 있습니다."}</p>
    <pre ref={root} tabIndex={0} aria-label={`${content.filename} 본문`}
      className="continuous-text" onMouseUp={capture} onKeyDown={keyboardSelect} onKeyUp={capture}>
      {ranges.length ? ranges.flatMap((range, index) => [
        text.slice(index ? ranges[index - 1].end : 0, range.start),
        <mark key={index}>{text.slice(range.start, range.end)}</mark>,
      ]).concat(text.slice(ranges[ranges.length - 1].end)) : text}
    </pre>
    {!text && <p role="status">추출된 텍스트가 없습니다. 원본을 확인해 주세요.</p>}
  </>;
}

export function PageThumbnail({ resource, number, width = 100 }) {
  const root = useRef(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const node = root.current;
    let gone = false, handle, task;
    const observer = new IntersectionObserver(async ([entry]) => {
      if (!entry.isIntersecting || !resource) return;
      observer.disconnect();
      try {
        if (resource.pptx) {
          handle = resource.pptx.renderThumbnailToContainer(number - 1, node, { width });
          await handle?.ready;
        } else {
          const page = await resource.pdf.getPage(number);
          if (gone) return;
          const viewport = page.getViewport({ scale: width / page.getViewport({ scale: 1 }).width });
          const canvas = document.createElement("canvas");
          canvas.width = viewport.width; canvas.height = viewport.height;
          node.replaceChildren(canvas);
          task = page.render({ canvasContext: canvas.getContext("2d"), viewport });
          await task.promise;
        }
      } catch (reason) {
        if (!gone && reason.name !== "RenderingCancelledException") setError("미리보기 없음");
      }
    });
    observer.observe(node);
    return () => { gone = true; observer.disconnect(); task?.cancel(); handle?.dispose(); node.replaceChildren(); };
  }, [resource, number, width]);
  return <div className="page-thumbnail" aria-hidden="true"><div ref={root} />{error}</div>;
}

function PagesPane({ content, selection, onSelect, apiBase, authToken, onResource }) {
  const stage = useRef(null);
  const [resource, setResource] = useState(null);
  const [page, setPage] = useState(selection?.pages[0] || 1);
  const [error, setError] = useState("");
  const selected = selection?.pages || [];
  const slide = content.filename.toLowerCase().endsWith(".pptx");
  const label = slide ? "슬라이드" : "페이지";
  useEffect(() => {
    let gone = false, viewer, loadingTask;
    const abort = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${apiBase}/api/documents/${content.document_id}/source?version_id=${content.version_id}`, {
          signal: abort.signal,
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        });
        if (!response.ok) throw new Error((await response.json()).detail || "원본을 열 수 없습니다.");
        const data = await response.arrayBuffer();
        if (gone) return;
        let loaded;
        if (slide) {
          viewer = new PptxViewer(stage.current, { fitMode: "contain", lazySlides: true,
            lazyMedia: true, zipLimits: RECOMMENDED_ZIP_LIMITS });
          await viewer.open(data, { renderMode: "slide", signal: abort.signal, lazySlides: true, lazyMedia: true });
          loaded = { pptx: viewer };
        } else {
          loadingTask = pdfjs.getDocument({ data });
          loaded = { pdf: await loadingTask.promise };
        }
        if (gone) return;
        const count = loaded.pptx?.slideCount ?? loaded.pdf.numPages;
        if (count !== content.pages.length) throw new Error("원본과 저장된 페이지 수가 다릅니다.");
        setResource(loaded); onResource?.(loaded);
      } catch (reason) { if (!gone) setError(reason.message); }
    }
    load();
    return () => { gone = true; abort.abort(); onResource?.(null); viewer?.destroy(); void loadingTask?.destroy(); };
  }, [content.version_id, apiBase, authToken]);

  useEffect(() => {
    if (!resource) return;
    let gone = false, task;
    async function render() {
      try {
        if (resource.pptx) { await resource.pptx.goToSlide(page - 1); return; }
        const pdfPage = await resource.pdf.getPage(page);
        if (gone) return;
        const width = Math.max(250, stage.current.clientWidth - 24);
        const viewport = pdfPage.getViewport({ scale: width / pdfPage.getViewport({ scale: 1 }).width });
        const canvas = document.createElement("canvas");
        canvas.width = viewport.width; canvas.height = viewport.height;
        stage.current.replaceChildren(canvas);
        task = pdfPage.render({ canvasContext: canvas.getContext("2d"), viewport });
        await task.promise;
      } catch (reason) {
        if (!gone && reason.name !== "RenderingCancelledException") setError(reason.message);
      }
    }
    render();
    return () => { gone = true; task?.cancel(); };
  }, [resource, page]);

  function toggle(number) {
    const pages = selected.includes(number) ? selected.filter(n => n !== number) : [...selected, number].sort((a, b) => a - b);
    onSelect(pages.length ? { kind: "pages", version_id: content.version_id, pages } : null);
  }
  function navigate(number) { setPage(Math.max(1, Math.min(content.pages.length, number || 1))); }
  return <>
    <div className="pane-toolbar">
      <button disabled={page <= 1} onClick={() => navigate(page - 1)}>이전</button>
      <label>{label} <input aria-label={`${label} 번호`} type="number" min={1} max={content.pages.length}
        value={page} onChange={(event) => navigate(Number(event.target.value))} /></label>
      <span>/ {content.pages.length}</span>
      <button disabled={page >= content.pages.length} onClick={() => navigate(page + 1)}>다음</button>
      <button disabled={!resource || !!error} aria-pressed={selected.includes(page)} onClick={() => toggle(page)}>
        {selected.includes(page) ? "선택 해제" : `이 ${label} 선택`}</button>
    </div>
    {error && <p className="notice error" role="alert">{error}</p>}
    {!resource && !error && <p role="status">원본을 불러오는 중입니다…</p>}
    <div className="page-layout">
      <div className="thumbnail-list" aria-label={`${label} 목록`}>
        {content.pages.map(({ number }) => <div className="thumbnail-item" key={number} data-current={page === number}>
          <button aria-label={`${number} ${label} 보기`} onClick={() => navigate(number)}>
            <PageThumbnail resource={resource} number={number} />{number}
          </button>
          <label><input type="checkbox" disabled={!resource || !!error} checked={selected.includes(number)}
            onChange={() => toggle(number)} aria-label={`${number} ${label} 선택`} />선택</label>
        </div>)}
      </div>
      <div ref={stage} className="page-stage" aria-label={`${page} ${label} 원본`} />
    </div>
  </>;
}

async function openProtectedSource(url, authToken) {
  const popup = window.open("about:blank", "_blank");
  try {
    const response = await fetch(url, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    });
    if (!response.ok) throw new Error("원본을 열 수 없습니다.");
    const objectUrl = URL.createObjectURL(await response.blob());
    if (popup) popup.location.href = objectUrl;
    else window.open(objectUrl, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
  } catch (error) {
    popup?.close();
    throw error;
  }
}

export function SelectionViewer({ content, selection, onSelect, apiBase, authToken, onResource }) {
  if (!content) return <div className="viewer-empty">문서 탐색에서 이쪽에 열 문서를 선택하세요.</div>;
  return <section className="selection-viewer">
    <h2>{content.filename}</h2>
    <span className="version-label">문서 버전 {content.version_number}</span>{" · "}
    <button type="button" onClick={() => openProtectedSource(
      `${apiBase}/api/documents/${content.document_id}/source?version_id=${content.version_id}`,
      authToken,
    ).catch(error => window.alert(error.message))}>원본 확인</button>
    {content.kind === "text" ? <TextPane key={content.version_id} {...{ content, selection, onSelect }} />
      : <PagesPane key={content.version_id} {...{ content, selection, onSelect, apiBase, authToken, onResource }} />}
  </section>;
}
