import { useEffect, useState } from "react";

const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const join = (folder, name) => [folder, name].filter(Boolean).join("/");
const parent = path => path.split("/").slice(0, -1).join("/");

export function DocumentManager({ api }) {
  const [roots, setRoots] = useState([]);
  const [rootId, setRootId] = useState("");
  const [current, setCurrent] = useState("");
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [targets, setTargets] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function refresh(id = rootId) {
    if (!id) return;
    const query = encodeURIComponent(id);
    const [nextFolders, nextFiles, nextDocuments] = await Promise.all([
      api(`/api/local/folders?root_id=${query}`),
      api(`/api/local/files?root_id=${query}&limit=20000`),
      api("/api/documents"),
    ]);
    setFolders(nextFolders); setFiles(nextFiles); setDocuments(nextDocuments);
  }

  useEffect(() => {
    api("/api/local/roots").then(items => {
      setRoots(items);
      if (items.length) setRootId(items[0].id);
    }).catch(reason => setError(reason.message));
  }, []);

  useEffect(() => {
    setCurrent(""); setTargets({});
    refresh(rootId).catch(reason => setError(reason.message));
  }, [rootId]);

  async function run(action, success) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); await refresh(); setMessage(success); return true; }
    catch (reason) { setError(reason.message); }
    finally { setBusy(false); }
  }

  function createFolder() {
    const name = prompt("새 폴더 이름");
    if (!name) return;
    if ([".", ".."].includes(name) || /[/\\]/.test(name)) { setError("폴더 이름에 경로 구분자를 사용할 수 없습니다."); return; }
    run(() => api("/api/local/folders", json("POST", { root_id: rootId, relative_path: join(current, name.trim()) })), "폴더를 만들었습니다.");
  }

  function move(path, isFolder) {
    const destinationFolder = targets[path] ?? parent(path);
    const destination = join(destinationFolder, path.split("/").at(-1));
    if (destination === path) return;
    if (isFolder && (destinationFolder === path || destinationFolder.startsWith(`${path}/`))) {
      setError("폴더를 자기 안으로 이동할 수 없습니다."); return;
    }
    run(() => api("/api/local/move", json("POST", {
      root_id: rootId, source_path: path, destination_path: destination,
    })), "이동했습니다.");
  }

  function rename(path) {
    const name = prompt("새 이름", path.split("/").at(-1));
    if (!name || [".", ".."].includes(name) || /[/\\]/.test(name)) return;
    run(() => api("/api/local/move", json("POST", {
      root_id: rootId, source_path: path, destination_path: join(parent(path), name.trim()),
    })), "이름을 변경했습니다.");
  }

  const children = folders.filter(path => parent(path) === current);
  const visibleFiles = files.filter(file => parent(file.relative_path) === current);
  const folderOptions = ["", ...folders];
  const targetPicker = path => <select aria-label={`${path} 이동할 폴더`} value={targets[path] ?? parent(path)}
    onChange={event => setTargets(previous => ({ ...previous, [path]: event.target.value }))}>
    {folderOptions.map(folder => <option key={folder} value={folder}>{folder || "문서 루트"}</option>)}
  </select>;

  return <section className="management-panel document-manager">
    <h2>문서 관리</h2>
    {error && <p className="notice error" role="alert">{error}</p>}
    {message && <p className="notice success" role="status">{message}</p>}
    {!roots.length ? <p>관리할 문서 폴더가 서버에 설정되어 있지 않습니다.</p> : <>
      <div className="pane-toolbar">
        <label>문서 저장소 <select value={rootId} onChange={event => setRootId(event.target.value)}>
          {roots.map(root => <option key={root.id} value={root.id}>{root.label}</option>)}
        </select></label>
        <button type="button" disabled={busy} onClick={createFolder}>새 폴더</button>
      </div>
      <form className="management-form" onSubmit={event => {
        event.preventDefault();
        const form = event.currentTarget;
        const body = new FormData(form);
        body.set("root_id", rootId); body.set("folder_path", current);
        run(() => api("/api/documents/upload", { method: "POST", body }), "문서를 업로드했습니다.").then(ok => { if (ok) form.reset(); });
      }}>
        <label>현재 폴더에 업로드 <input name="file" type="file" accept=".docx,.hwp,.hwpx,.pptx,.pdf" required /></label>
        <button className="primary-button" disabled={busy}>업로드</button>
      </form>
      <div className="explorer-breadcrumbs document-breadcrumbs">
        <button type="button" onClick={() => setCurrent("")}>문서 루트</button>
        {current.split("/").filter(Boolean).map((part, index, parts) => <span key={index}> / <button type="button"
          onClick={() => setCurrent(parts.slice(0, index + 1).join("/"))}>{part}</button></span>)}
      </div>
      <div className="management-list">
        {current && <button className="folder-row" onClick={() => setCurrent(parent(current))}>↩ 상위 폴더</button>}
        {children.map(path => <article className="document-entry" key={path}>
          <button className="document-entry-name" onClick={() => setCurrent(path)}>📁 {path.split("/").at(-1)}</button>
          <div className="pane-toolbar">{targetPicker(path)}
            <button disabled={busy} onClick={() => move(path, true)}>이동</button>
            <button disabled={busy} onClick={() => rename(path)}>이름 변경</button>
            <button disabled={busy} onClick={() => {
              if (confirm(`빈 폴더 “${path}”를 삭제할까요?`)) run(() => api("/api/local/folders", json("DELETE", { root_id: rootId, relative_path: path })), "폴더를 삭제했습니다.");
            }}>삭제</button>
          </div>
        </article>)}
        {visibleFiles.map(file => {
          const document = documents.find(item => item.folder === current && item.filename === file.filename);
          return <article className="document-entry" key={file.id}>
            <div className="document-entry-name">📄 {file.filename} <small>{document?.status || "미등록"}</small></div>
            <div className="pane-toolbar">{targetPicker(file.relative_path)}
              <button disabled={busy} onClick={() => move(file.relative_path, false)}>이동</button>
              <button disabled={busy} onClick={() => rename(file.relative_path)}>이름 변경</button>
              <button disabled={busy} onClick={() => run(() => api("/api/local/open", json("POST", {
                root_id: rootId, relative_path: file.relative_path,
              })), "문서를 등록했습니다.")}>RAG 등록</button>
              {document && <button disabled={busy} onClick={() => run(() => api(`/api/documents/${document.id}/ingest`, { method: "POST" }), "다시 처리했습니다.")}>다시 처리</button>}
              <button disabled={busy} onClick={() => {
                if (confirm(`“${file.filename}” 원본 파일을 삭제할까요? 이미 등록된 RAG 내용과 링크는 유지됩니다.`))
                  run(() => api("/api/local/files", json("DELETE", { root_id: rootId, relative_path: file.relative_path })), "원본 파일을 삭제했습니다.");
              }}>파일 삭제</button>
            </div>
          </article>;
        })}
        {!children.length && !visibleFiles.length && <p>이 폴더는 비어 있습니다.</p>}
      </div>
    </>}
  </section>;
}
