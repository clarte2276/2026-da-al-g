import { useEffect, useRef, useState } from "react";
import { FileExplorer } from "./file-explorer";
import { PageThumbnail, SelectionViewer } from "./selection-viewer";
import { LinkGraph } from "./link-graph";
import { ChatPreview } from "./chat-preview";
const write = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const textRanges = selection => selection?.ranges || (selection?.exact ? [selection] : []);
const selectionLabel = selection => selection?.kind === "text"
  ? textRanges(selection).map(range => range.exact).join(" … ")
  : selection ? `${selection.pages.join(", ")} 페이지·슬라이드` : "선택하지 않음";

function SelectionSummary({ content, selection, resource, onSelect, label }) {
  return <section className="chosen-selection">
    <h3>{label} · {content?.filename || "문서 미선택"}</h3>
    {!selection ? <p>연결할 구절이나 페이지를 지정하세요.</p> : <>
      {selection.kind === "text" ? textRanges(selection).map((range, index) => <details key={range.start}>
        <summary>{range.exact.slice(0, 100)}{range.exact.length > 100 ? "…" : ""}</summary>
        <blockquote>{range.exact}</blockquote>
        <button aria-label={`${index + 1}번째 구절 해제`} onClick={() => {
          const rest = textRanges(selection).filter(other => other.start !== range.start);
          onSelect(rest.length ? { ...selection, ranges: rest } : null);
        }}>해제</button></details>) : <div className="selected-pages">
        {selection.pages.map(number => <div key={number}>
          <PageThumbnail resource={resource} number={number} />
          <span>{number} {content.filename.toLowerCase().endsWith(".pptx") ? "슬라이드" : "페이지"}</span>
          <button aria-label={`${number} 선택 해제`} onClick={() => {
            const pages = selection.pages.filter(n => n !== number);
            onSelect(pages.length ? { ...selection, pages } : null);
          }}>해제</button>
        </div>)}
      </div>}
      <button onClick={() => onSelect(null)}>선택 초기화</button>
    </>}
  </section>;
}

function ReviewCards({ links, busy, onReopen, onDecide }) {
  return links.map(link => <article className="review-link" key={link.id}>
    <strong>{link.source_filename} ↔ {link.target_filename}</strong><span className={`status status-${link.status}`}>{({ draft: "승인 대기", approved: "승인됨", rejected: "반려됨" })[link.status]}</span>
    <div className="selection-pair">{[link.source_selection, link.target_selection].map((selection, index) =>
      <details key={index}><summary>{selectionLabel(selection).slice(0, 110)}</summary><blockquote>{selectionLabel(selection)}</blockquote></details>)}</div>
    {link.note && <p>{link.note}</p>}<div className="pane-toolbar">
      <button disabled={busy} onClick={() => onReopen(link)}>선택 확인·수정</button>
      <button disabled={busy || link.status === "approved"} onClick={() => onDecide(link.id, "approve")}>승인</button>
      <button disabled={busy || link.status === "rejected"} onClick={() => onDecide(link.id, "reject")}>반려</button></div>
  </article>);
}

export function LinkGenerator({ tab, onTab: setTab, api, apiBase, token, user, onUnauthorized }) {
  const [roots, setRoots] = useState([]), [rootId, setRootId] = useState("");
  const [query, setQuery] = useState(""), [files, setFiles] = useState([]);
  const [source, setSource] = useState(null), [target, setTarget] = useState(null);
  const [sourceSelection, setSourceSelection] = useState(null), [targetSelection, setTargetSelection] = useState(null);
  const [sourceResource, setSourceResource] = useState(null), [targetResource, setTargetResource] = useState(null);
  const [note, setNote] = useState(""), [editing, setEditing] = useState(null);
  const [relation, setRelation] = useState("RELATED");
  const [links, setLinks] = useState([]), [filter, setFilter] = useState("approved");
  const [reviewMode, setReviewMode] = useState("graph"), [graphSelection, setGraphSelection] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(""), [error, setError] = useState("");
  const openRequests = useRef({ source: 0, target: 0 });
  const [explorerOpen, setExplorerOpen] = useState(true);

  async function task(action) {
    setBusy(true); setError("");
    try { await action(); } catch (reason) {
      if (reason.status === 401) { onUnauthorized(); return; }
      setError(reason.message);
    }
    finally { setBusy(false); }
  }
  useEffect(() => {
    let gone = false;
    if (!user) return () => { gone = true; };
    api("/api/local/roots").then(items => {
      if (!gone) { setRoots(items); setRootId(items[0]?.id || ""); }
    }).catch(reason => {
      if (gone) return;
      if (reason.status === 401) onUnauthorized();
      else setError(reason.message);
    });
    return () => { gone = true; };
  }, [user]);
  useEffect(() => {
    let gone = false;
    if (user && rootId) api(`/api/local/files?${new URLSearchParams({ root_id: rootId, query })}`)
      .then(items => { if (!gone) setFiles(items); }).catch(reason => {
        if (gone) return;
        if (reason.status === 401) onUnauthorized();
        else setError(reason.message);
      });
    return () => { gone = true; };
  }, [user, rootId, query]);
  async function refresh() {
    setLinks(await api("/api/links"));
  }
  useEffect(() => { if (tab === "review") task(refresh); }, [tab]);

  async function loadContent(documentId, versionId) {
    return api(`/api/documents/${documentId}/content?${new URLSearchParams({ version_id: versionId })}`);
  }
  function openFile(file, side) {
    const request = ++openRequests.current[side];
    task(async () => {
      const opened = await api("/api/local/open", write("POST", { root_id: file.root_id, relative_path: file.relative_path }));
      const content = await loadContent(opened.document.id, opened.version.id);
      if (request !== openRequests.current[side]) return;
      if (side === "source") { setSource(content); setSourceSelection(null); }
      else { setTarget(content); setTargetSelection(null); }
      if ((side === "source" && target) || (side === "target" && source)) setExplorerOpen(false);
      setMessage(`${file.filename} 문서를 열었습니다.`);
    });
  }
  function save() {
    task(async () => {
      const link = await api(editing ? `/api/links/${editing}` : "/api/links", write(editing ? "PUT" : "POST", {
        source_selection: sourceSelection, target_selection: targetSelection, note: note || null, relation_type: relation,
      }));
      setEditing(null); setNote(""); setRelation("RELATED"); setSourceSelection(null); setTargetSelection(null);
      setMessage("연결 1건을 저장했습니다. 바로 검색에 반영됩니다.");
      await refresh();
    });
  }
  async function loadLink(link) {
      const [left, right] = await Promise.all([
        loadContent(link.source_document_id, link.source_version_id),
        loadContent(link.target_document_id, link.target_version_id),
      ]);
      setSource(left); setTarget(right); setSourceSelection(link.source_selection); setTargetSelection(link.target_selection);
      setNote(link.note || ""); setRelation(link.relation_type); setEditing(link.id); setTab("edit"); setExplorerOpen(false);
      setMessage("저장된 선택을 열었습니다. 수정해 저장하면 바로 검색에 반영됩니다.");
  }
  function reopen(link) {
    task(() => loadLink(link));
  }
  function decide(id, decision) {
    task(async () => {
      await api(`/api/links/${id}/${decision}`, write("POST", {}));
      await refresh(); setMessage(decision === "approve" ? "연결을 승인했습니다." : "연결을 반려했습니다.");
    });
  }
  function openEvidence(item) {
    task(async () => {
      if (item.link_id) { await loadLink(await api(`/api/links/${item.link_id}`)); return; }
      const documentId = item.document_id || item.fragment?.document_id;
      const versionId = item.version_id || item.fragment?.version_id || item.selection?.version_id;
      if (!documentId || !versionId) throw new Error("원문 정보를 찾을 수 없습니다.");
      const version = await api(`/api/documents/${documentId}/content?${new URLSearchParams({ version_id: versionId })}`);
      setSource(version); setSourceSelection(item.selection || null); setTab("edit");
    });
  }

  const filteredLinks = links.filter(link => !filter || link.status === filter);
  const selectedLinks = graphSelection ? filteredLinks.filter(link => graphSelection.ids.includes(link.id)) : [];

  return <section className="link-generator-module" aria-label="RAG 링크 관리">
    <p className="busy-line" role="status">{busy ? "처리 중…" : ""}</p>
    {(error || message) && <div className={`notice ${error ? "error" : "success"}`} role={error ? "alert" : "status"}>{error || message}</div>}
    <div hidden={tab !== "edit"}>
      <details className="explorer-section" open={explorerOpen} onToggle={event => setExplorerOpen(event.currentTarget.open)}>
        <summary>문서 탐색 <span>왼쪽이나 오른쪽 창에 열 문서를 고릅니다</span></summary>
        <div className="pane-toolbar"><select aria-label="문서 폴더" value={rootId} onChange={event => setRootId(event.target.value)}>
          {roots.map(root => <option value={root.id} key={root.id}>{root.label}</option>)}</select>
          <input aria-label="파일명·폴더명 검색" placeholder="파일명·폴더명 검색" value={query} onChange={event => setQuery(event.target.value)} /></div>
        {!roots.length && <p>설정된 문서 폴더가 없습니다.</p>}
        <FileExplorer files={files.filter(file => String(file.relative_path || "").replaceAll("\\", "/").startsWith("data_raw/"))} rootId={rootId} query={query} onOpen={openFile} />
      </details>
      <div className="reading-panes">
        <SelectionViewer content={source} selection={sourceSelection} onSelect={setSourceSelection} apiBase={apiBase} authToken={token} onResource={setSourceResource} />
        <SelectionViewer content={target} selection={targetSelection} onSelect={setTargetSelection} apiBase={apiBase} authToken={token} onResource={setTargetResource} />
      </div>
      <section className="connection-bar">
        <div className="selection-pair">
          <SelectionSummary label="왼쪽" content={source} selection={sourceSelection} resource={sourceResource} onSelect={setSourceSelection} />
          <SelectionSummary label="오른쪽" content={target} selection={targetSelection} resource={targetResource} onSelect={setTargetSelection} />
        </div>
        <label>메모 <textarea value={note} onChange={event => setNote(event.target.value)} maxLength={5000} placeholder="이 연결의 의미 (선택)" /></label>
        <div className="pane-toolbar"><button className="primary-button" disabled={busy || !sourceSelection || !targetSelection} onClick={save}>
          {editing ? "수정 저장" : "연결 저장"}</button>
          <span>저장하면 바로 검색에 반영됩니다.</span></div>
      </section>
    </div>
    {tab === "review" && <section className="edges-section">
      <div className="review-toolbar">
        <select aria-label="연결 상태" value={filter} onChange={event => { setFilter(event.target.value); setGraphSelection(null); }}>
          <option value="approved">승인됨</option><option value="draft">승인 대기</option><option value="rejected">반려됨</option><option value="">전체</option></select>
        <div className="review-mode" role="group" aria-label="연결 검토 보기">
          <button aria-pressed={reviewMode === "graph"} onClick={() => setReviewMode("graph")}>그래프</button>
          <button aria-pressed={reviewMode === "list"} onClick={() => setReviewMode("list")}>목록</button>
        </div>
      </div>
      {reviewMode === "graph" ? <div className="review-graph-layout">
        <div className="review-graph-canvas"><LinkGraph links={filteredLinks} onSelect={setGraphSelection} /></div>
        <aside className="review-graph-detail" aria-label="선택한 연결">
          {graphSelection ? <>
            <div className="review-detail-heading"><h3>{graphSelection.label}</h3><button aria-label="선택 닫기" onClick={() => setGraphSelection(null)}>닫기</button></div>
            {selectedLinks.length ? <ReviewCards links={selectedLinks} busy={busy} onReopen={reopen} onDecide={decide} /> : <p className="empty-state">해당 상태의 연결이 없습니다.</p>}
          </> : <p className="empty-state">그래프의 문서나 연결을 선택하면 목록이 표시됩니다.</p>}
        </aside>
      </div> : filteredLinks.length ? <ReviewCards links={filteredLinks} busy={busy} onReopen={reopen} onDecide={decide} /> : <p className="empty-state">해당 상태의 연결이 없습니다.</p>}
    </section>}
    {tab === "search" && <section className="rag-section"><ChatPreview apiBase={apiBase} token={token} onUnauthorized={onUnauthorized} onOpenSource={openEvidence} /></section>}
  </section>;
}
