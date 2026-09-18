import { StrictMode, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { FileExplorer } from "./file-explorer";
import { PageThumbnail, SelectionViewer } from "./selection-viewer";
import "./styles.css";
import "./workspace.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? "" : "http://localhost:8000");
const TOKEN_KEY = "daalgi_admin_token";
let authToken = "";

function setAuthToken(token) {
  authToken = token || "";
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(typeof body.detail === "string" ? body.detail : `요청 실패 (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return body;
}
const write = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const textRanges = selection => selection?.ranges || (selection?.exact ? [selection] : []);
const selectionLabel = selection => selection?.kind === "text"
  ? textRanges(selection).map(range => range.exact).join(" … ")
  : selection ? `${selection.pages.join(", ")} 페이지·슬라이드` : "선택하지 않음";

function AdminLogin({ onLogin, busy, error }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  return <main className="auth-shell">
    <section className="auth-card">
      <p className="eyebrow">Da-Al-G ADMIN</p>
      <h1>문서 연결 관리자</h1>
      <p className="subtitle">문서 연결과 검색 근거를 관리하려면 로그인하세요.</p>
      {error && <div className="notice error" role="alert">{error}</div>}
      <form onSubmit={async event => {
        event.preventDefault();
        await onLogin(username.trim(), password);
      }}>
        <label>아이디<input autoFocus value={username} onChange={event => setUsername(event.target.value)} /></label>
        <label>비밀번호<input type="password" value={password} onChange={event => setPassword(event.target.value)} /></label>
        <button className="primary-button" disabled={busy || !username.trim() || !password}>{busy ? "로그인 중…" : "로그인"}</button>
      </form>
    </section>
  </main>;
}

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

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [sessionReady, setSessionReady] = useState(() => !token);
  const [user, setUser] = useState(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");
  const [tab, setTab] = useState("edit");
  const [roots, setRoots] = useState([]), [rootId, setRootId] = useState("");
  const [query, setQuery] = useState(""), [files, setFiles] = useState([]);
  const [source, setSource] = useState(null), [target, setTarget] = useState(null);
  const [sourceSelection, setSourceSelection] = useState(null), [targetSelection, setTargetSelection] = useState(null);
  const [sourceResource, setSourceResource] = useState(null), [targetResource, setTargetResource] = useState(null);
  const [note, setNote] = useState(""), [editing, setEditing] = useState(null);
  const [relation, setRelation] = useState("RELATED");
  const [links, setLinks] = useState([]), [legacy, setLegacy] = useState([]);
  const [filter, setFilter] = useState("draft"), [question, setQuestion] = useState("");
  const [result, setResult] = useState(null), [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(""), [error, setError] = useState("");
  const openRequests = useRef({ source: 0, target: 0 });
  const [explorerOpen, setExplorerOpen] = useState(true);

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken("");
    setToken("");
    setUser(null);
    setSessionReady(true);
  }

  async function logout() {
    try {
      if (token) await api("/api/auth/logout", { method: "POST" });
    } catch (_) {
      // The local session is cleared even if the server is unavailable.
    } finally {
      clearSession();
    }
  }

  async function login(username, password) {
    setAuthBusy(true); setAuthError("");
    try {
      const body = await api("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (body.user?.role !== "admin") throw new Error("관리자 계정으로 로그인해 주세요.");
      localStorage.setItem(TOKEN_KEY, body.access_token);
      setAuthToken(body.access_token);
      setUser(body.user);
      setToken(body.access_token);
      setSessionReady(true);
    } catch (reason) {
      setAuthError(reason.message);
    } finally {
      setAuthBusy(false);
    }
  }

  useEffect(() => {
    setAuthToken(token);
    if (!token) { setUser(null); setSessionReady(true); return undefined; }
    let gone = false;
    setSessionReady(false);
    api("/api/auth/me").then(me => {
      if (me.role !== "admin") throw new Error("관리자 권한이 없습니다.");
      if (!gone) { setUser(me); setSessionReady(true); }
    }).catch(reason => {
      if (!gone) { setAuthError(reason.message); clearSession(); }
    });
    return () => { gone = true; };
  }, [token]);

  async function task(action) {
    setBusy(true); setError("");
    try { await action(); } catch (reason) {
      if (reason.status === 401) { void logout(); return; }
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
      if (reason.status === 401) void logout();
      else setError(reason.message);
    });
    return () => { gone = true; };
  }, [user]);
  useEffect(() => {
    let gone = false;
    if (user && rootId) api(`/api/local/files?${new URLSearchParams({ root_id: rootId, query })}`)
      .then(items => { if (!gone) setFiles(items); }).catch(reason => {
        if (gone) return;
        if (reason.status === 401) void logout();
        else setError(reason.message);
      });
    return () => { gone = true; };
  }, [user, rootId, query]);
  async function refresh() {
    const [current, previous] = await Promise.all([api("/api/links"), api("/api/edges?limit=1000")]);
    setLinks(current); setLegacy(previous);
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
      setEditing(link.id);
      setMessage("연결 1건을 초안으로 저장했습니다. 연결 검토에서 승인할 수 있습니다.");
      await refresh();
    });
  }
  function newLink() {
    setEditing(null); setNote(""); setRelation("RELATED"); setSourceSelection(null); setTargetSelection(null);
    setMessage("새 연결을 만들 구절이나 페이지를 지정하세요.");
  }
  async function loadLink(link) {
      const [left, right] = await Promise.all([
        loadContent(link.source_document_id, link.source_version_id),
        loadContent(link.target_document_id, link.target_version_id),
      ]);
      setSource(left); setTarget(right); setSourceSelection(link.source_selection); setTargetSelection(link.target_selection);
      setNote(link.note || ""); setRelation(link.relation_type); setEditing(link.id); setTab("edit"); setExplorerOpen(false);
      setMessage("저장된 선택을 열었습니다. 수정하여 저장하면 다시 초안이 됩니다.");
  }
  function reopen(link) {
    task(() => loadLink(link));
  }
  function decide(id, decision, old = false) {
    task(async () => {
      await api(`/api/${old ? "edges" : "links"}/${id}/${decision}`, write("POST", {}));
      await refresh(); setMessage(decision === "approve" ? "연결을 승인했습니다." : "연결을 반려했습니다.");
    });
  }
  function openEvidence(item) {
    task(async () => {
      if (item.link_id) { await loadLink(await api(`/api/links/${item.link_id}`)); return; }
      const version = await api(`/api/documents/${item.document_id}/content?version_id=${item.selection.version_id}`);
      setSource(version); setSourceSelection(item.selection); setTab("edit");
    });
  }

  if (!sessionReady) return <main className="auth-shell"><p>관리자 세션을 확인하는 중입니다…</p></main>;
  if (!user) return <AdminLogin onLogin={login} busy={authBusy} error={authError} />;

  return <main className="app-shell human-workspace">
    <header className="topbar"><div><p className="eyebrow">Da-Al-G</p><h1>문서 연결</h1>
      <p className="subtitle">구절과 페이지를 읽고, 관련 자료를 연결하세요.</p></div>
      <div className="pane-toolbar"><span role="status">{busy ? "처리 중…" : user.display_name}</span><button onClick={logout}>로그아웃</button></div></header>
    <nav className="workspace-tabs" aria-label="작업 화면">
      {[["edit", "문서 연결"], ["review", "연결 검토"], ["search", "검색 검증"]].map(([value, label]) =>
        <button key={value} aria-current={tab === value ? "page" : undefined} onClick={() => setTab(value)}>{label}</button>)}
    </nav>
    {(error || message) && <div className={`notice ${error ? "error" : "success"}`} role={error ? "alert" : "status"}>{error || message}</div>}
    <div hidden={tab !== "edit"}>
      <details className="explorer-section" open={explorerOpen} onToggle={event => setExplorerOpen(event.currentTarget.open)}>
        <summary>문서 탐색 · 왼쪽 또는 오른쪽에 열기</summary>
        <div className="pane-toolbar"><select aria-label="문서 폴더" value={rootId} onChange={event => setRootId(event.target.value)}>
          {roots.map(root => <option value={root.id} key={root.id}>{root.label}</option>)}</select>
          <input aria-label="파일명·폴더명 검색" placeholder="파일명·폴더명 검색" value={query} onChange={event => setQuery(event.target.value)} /></div>
        {!roots.length && <p>설정된 문서 폴더가 없습니다.</p>}
        <FileExplorer files={files} rootId={rootId} query={query} onOpen={openFile} />
      </details>
      <div className="reading-panes">
        <SelectionViewer content={source} selection={sourceSelection} onSelect={setSourceSelection} apiBase={API_BASE} authToken={token} onResource={setSourceResource} />
        <SelectionViewer content={target} selection={targetSelection} onSelect={setTargetSelection} apiBase={API_BASE} authToken={token} onResource={setTargetResource} />
      </div>
      <section className="connection-bar">
        <div className="selection-pair">
          <SelectionSummary label="왼쪽" content={source} selection={sourceSelection} resource={sourceResource} onSelect={setSourceSelection} />
          <SelectionSummary label="오른쪽" content={target} selection={targetSelection} resource={targetResource} onSelect={setTargetSelection} />
        </div>
        <label>메모 <textarea value={note} onChange={event => setNote(event.target.value)} maxLength={5000} placeholder="이 연결의 의미 (선택)" /></label>
        <div className="pane-toolbar"><button className="primary-button" disabled={busy || !sourceSelection || !targetSelection} onClick={save}>
          {editing ? "수정 저장 · 초안" : "연결 저장"}</button><button disabled={busy} onClick={newLink}>새 연결</button>
          <span>연결 하나로 저장되며, 승인 후 검색에 반영됩니다.</span></div>
      </section>
    </div>
    {tab === "review" && <section className="edges-section">
      <h2>연결 검토</h2><select aria-label="연결 상태" value={filter} onChange={event => setFilter(event.target.value)}>
        <option value="draft">승인 대기</option><option value="approved">승인됨</option><option value="rejected">반려됨</option><option value="">전체</option></select>
      {links.filter(link => !filter || link.status === filter).map(link => <article className="review-link" key={link.id}>
        <strong>{link.source_filename} ↔ {link.target_filename}</strong><span>{({ draft: "승인 대기", approved: "승인됨", rejected: "반려됨" })[link.status]}</span>
        <div className="selection-pair">{[link.source_selection, link.target_selection].map((selection, index) =>
          <details key={index}><summary>{selectionLabel(selection).slice(0, 110)}</summary><blockquote>{selectionLabel(selection)}</blockquote></details>)}</div>
        {link.note && <p>{link.note}</p>}<div className="pane-toolbar">
          <button disabled={busy} onClick={() => reopen(link)}>선택 확인·수정</button>
          <button disabled={busy || link.status === "approved"} onClick={() => decide(link.id, "approve")}>승인</button>
          <button disabled={busy || link.status === "rejected"} onClick={() => decide(link.id, "reject")}>반려</button></div>
      </article>)}
      {!links.some(link => !filter || link.status === filter) && <p className="empty-state">해당 상태의 연결이 없습니다.</p>}
      <details><summary>이전 방식 연결 ({legacy.length})</summary>{legacy.map(edge => <article className="review-link" key={edge.id}>
        <p>{edge.source_anchor?.selected_text || "이전 원문 영역"} ↔ {edge.target_anchor?.selected_text || "이전 원문 영역"}</p>
        <span>{edge.status}</span>{edge.note && <p>{edge.note}</p>}
        <button disabled={busy} onClick={() => decide(edge.id, "approve", true)}>승인</button>
        <button disabled={busy} onClick={() => decide(edge.id, "reject", true)}>반려</button>
      </article>)}</details>
    </section>}
    {tab === "search" && <section className="rag-section"><h2>검색 검증</h2>
      <form className="query-form" onSubmit={event => { event.preventDefault(); if (question.trim()) task(async () => {
        setResult(await api("/api/rag/query", write("POST", { question, top_k: 5, max_hops: 2 })));
      }); }}><input aria-label="질문" value={question} onChange={event => setQuestion(event.target.value)} placeholder="문서에 대해 질문하세요." />
        <button disabled={busy || !question.trim()}>검색</button></form>
      {result && <><p className="answer">{result.answer}</p><h3>검색 근거</h3>{result.evidence.map(item => <article className="review-link" key={item.link_id ? `${item.link_id}:${JSON.stringify(item.selection)}` : item.fragment.id}>
        <strong>{item.filename || item.fragment?.title || "문서 근거"}</strong><p>{item.text ?? item.fragment?.text}</p>
        {item.selection && <><p>{item.selection.kind === "pages" ? selectionLabel(item.selection) : "연결된 인용문"}</p>
          <button onClick={() => openEvidence(item)}>연결된 원문 확인</button></>}
      </article>)}</>}
    </section>}
  </main>;
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
