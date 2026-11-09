import { useEffect, useMemo, useRef, useState } from "react";
import "./glossary.css";

const empty = () => ({ category: "부품", title: "", code: "", aliases: "", scope: "", location: "", photo_caption: "", definition: "", symptoms: "", actions: "", regulations: "" });
const fields = Object.keys(empty());
const payload = value => Object.fromEntries(fields.map(key => [key, value[key] || ""]));
const statusText = status => status === "published" ? "검색 등록됨" : "초안";
const apiBase = import.meta.env.VITE_API_BASE_URL || "";

export function Glossary({ api }) {
  const [items, setItems] = useState([]), [query, setQuery] = useState("");
  const [entry, setEntry] = useState(null), [dirty, setDirty] = useState(false);
  const [queued, setQueued] = useState(null), [photoFile, setPhotoFile] = useState(null), [photoUrl, setPhotoUrl] = useState(""), [localPhotoUrl, setLocalPhotoUrl] = useState("");
  const [refs, setRefs] = useState([]), [tab, setTab] = useState("pdf"), [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
  const fileRef = useRef(null);

  async function refresh(search = query) {
    const result = await api(`/api/glossary?q=${encodeURIComponent(search)}`);
    setItems(result);
  }
  useEffect(() => { refresh("").catch(reason => setError(reason.message)); }, [api]);
  useEffect(() => {
    if (!entry?.id || !entry.has_photo) { setPhotoUrl(""); return undefined; }
    let active = true, url = "";
    const token = localStorage.getItem("daalgi_admin_token");
    fetch(`${apiBase}/api/glossary/${entry.id}/photo`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(response => { if (!response.ok) throw new Error("사진을 불러오지 못했습니다."); return response.blob(); })
      .then(blob => { url = URL.createObjectURL(blob); if (active) setPhotoUrl(url); else URL.revokeObjectURL(url); })
      .catch(reason => { if (active) setError(reason.message); });
    return () => { active = false; if (url) URL.revokeObjectURL(url); };
  }, [entry?.id, entry?.has_photo]);
  useEffect(() => {
    if (!photoFile) { setLocalPhotoUrl(""); return undefined; }
    const url = URL.createObjectURL(photoFile);
    setLocalPhotoUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [photoFile]);
  useEffect(() => {
    const timer = setTimeout(() => refresh(query).catch(reason => setError(reason.message)), 250);
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    const text = entry?.regulations || "";
    const timer = setTimeout(() => {
      if (!text.trim()) { setRefs([]); return; }
      api(`/api/glossary/regulation-refs?text=${encodeURIComponent(text)}`).then(setRefs).catch(reason => setError(reason.message));
    }, 400);
    return () => clearTimeout(timer);
  }, [api, entry?.regulations]);

  function set(field, value) { setEntry(previous => ({ ...previous, [field]: value })); setDirty(true); setMessage(""); }
  function requestSwitch(target) {
    if (dirty) { setQueued(target); return; }
    void open(target);
  }
  async function open(target) {
    setQueued(null); setError(""); setMessage(""); setPhotoFile(null);
    if (target === "new") { setEntry(empty()); setDirty(false); return; }
    if (!target) { setEntry(null); setDirty(false); return; }
    try {
      const value = await api(`/api/glossary/${target}`);
      setEntry(value); setDirty(false);
    } catch (reason) { setError(reason.message); }
  }
  async function persist() {
    if (!entry) return null;
    const body = payload(entry);
    const result = entry.id
      ? await api(`/api/glossary/${entry.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      : await api("/api/glossary", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    let next = result;
    if (photoFile) {
      const form = new FormData(); form.append("file", photoFile);
      next = await api(`/api/glossary/${result.id}/photo`, { method: "PUT", body: form });
    }
    setEntry(next); setPhotoFile(null); setDirty(false);
    await refresh(); return next;
  }
  async function save(publish = false) {
    setBusy(true); setError(""); setMessage("");
    try {
      const next = await persist();
      if (!publish) { setMessage("초안을 저장했습니다."); return; }
      const result = await api(`/api/glossary/${next.id}/publish`, { method: "POST" });
      setEntry(result.entry); setDirty(false);
      await refresh();
      setMessage(`PDF를 검색에 등록했습니다. 연결 검토에서 초안을 승인해 주세요. ${result.links.map(link => `${link.ref}: ${link.status === "draft" ? "승인 대기" : link.status === "exists" ? "기존 연결" : "미등록"}`).join(" · ")}`);
    } catch (reason) { setError(reason.message); }
    finally { setBusy(false); }
  }
  async function remove() {
    setBusy(true); setError("");
    try { await api(`/api/glossary/${entry.id}`, { method: "DELETE" }); setMessage("항목을 삭제했습니다."); await refresh(); await open(null); }
    catch (reason) { setError(reason.message); }
    finally { setBusy(false); }
  }
  function takePhoto(file) { if (file) { setPhotoFile(file); setEntry(previous => ({ ...previous, has_photo: true })); setDirty(true); } }
  async function removePhoto() {
    if (photoFile) { setPhotoFile(null); setEntry(previous => ({ ...previous, has_photo: false })); setDirty(true); return; }
    if (!entry?.id) return;
    try { const next = await api(`/api/glossary/${entry.id}/photo`, { method: "DELETE" }); setPhotoUrl(""); setEntry(next); setDirty(true); }
    catch (reason) { setError(reason.message); }
  }
  const shownItems = items;
  const image = photoFile ? localPhotoUrl : entry?.has_photo ? photoUrl : "";
  const text = useMemo(() => entry ? [entry.title, entry.code && `코드: ${entry.code}`, entry.aliases && `별칭·검색어: ${entry.aliases}`, entry.scope && `적용 범위: ${entry.scope}`, entry.location && `설치 위치: ${entry.location}`, entry.photo_caption && `사진 설명: ${entry.photo_caption}`, entry.definition, entry.symptoms && `이상 현상: ${entry.symptoms}`, entry.actions && `점검·조치: ${entry.actions}`, entry.regulations && `관련 규정: ${entry.regulations}`].filter(Boolean).join("\n") : "", [entry]);

  return <section className="glossary">
    {error && <p className="glossary-alert" role="alert">{error}</p>}{message && <p className="glossary-message" role="status">{message}</p>}
    {queued && queued !== "delete" && <div className="glossary-unsaved" role="alert"><span>저장하지 않은 변경 사항이 있습니다. 이동할까요?</span><button type="button" onClick={() => setQueued(null)}>계속 편집</button><button type="button" onClick={() => { setDirty(false); void open(queued); }}>저장하지 않고 이동</button></div>}
    <div className="glossary-panes">
      <section className="glossary-pane" aria-label="항목 목록"><header><h2>항목 <small>{shownItems.length}</small></h2><button type="button" onClick={() => requestSwitch("new")}>+ 새 항목</button></header><div className="glossary-list">
        <input type="search" placeholder="표제어·코드·별칭 검색" aria-label="항목 검색" value={query} onChange={event => setQuery(event.target.value)} />
        <ul>{shownItems.map(item => <li key={item.id}><button type="button" aria-pressed={entry?.id === item.id} onClick={() => requestSwitch(item.id)}><PhotoThumb item={item} /><span className="glossary-list-text"><b>{item.title || "제목 없음"}</b><small>{item.code || item.category}<i className={item.status === "published" ? "published" : "draft"}>{statusText(item.status)}</i></small></span></button></li>)}{!shownItems.length && <li className="glossary-empty">일치하는 항목이 없습니다.</li>}</ul>
      </div></section>
      <section className="glossary-pane glossary-editor"><header><h2>항목 정보</h2>{entry && <span className={`glossary-pill ${entry.status === "published" ? "published" : "draft"}`}>{statusText(entry.status)}</span>}</header>
        {!entry ? <p className="glossary-empty editor-empty">왼쪽 목록에서 항목을 고르거나 새 항목을 만드세요.</p> : <>
        <div className="glossary-fields">
          <Field label="분류"><select value={entry.category || "부품"} onChange={e => set("category", e.target.value)}>{["부품", "장비", "용어", "기타"].map(x => <option key={x}>{x}</option>)}</select></Field>
          <Field label="표제어" required hint="검색 결과와 PDF 제목에 쓰입니다."><input maxLength="200" value={entry.title} onChange={e => set("title", e.target.value)} /></Field>
          <Field label="코드"><input maxLength="100" value={entry.code || ""} onChange={e => set("code", e.target.value)} /></Field>
          <Field label="별칭·검색어" wide hint="쉼표로 구분합니다. 현장에서 부르는 이름도 함께 적으면 검색이 잘 됩니다."><input value={entry.aliases || ""} onChange={e => set("aliases", e.target.value)} /></Field>
          <Field label="적용 범위"><input value={entry.scope || ""} onChange={e => set("scope", e.target.value)} /></Field>
          {entry.category !== "용어" && <Field label="설치 위치"><input value={entry.location || ""} onChange={e => set("location", e.target.value)} /></Field>}
          <div className="glossary-photo-field"><span className="glossary-label">사진 <small>(선택)</small></span><div className="glossary-photo-row"><label className="glossary-drop" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); takePhoto(e.dataTransfer.files?.[0]); }}><input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" onChange={e => takePhoto(e.target.files?.[0])} />{image ? <img src={image} alt="선택한 사진 미리보기" /> : <span>사진을 끌어 놓거나 눌러서 고르세요</span>}</label><Field label="사진 설명" hint="사진 속 대상과 보이는 특징을 문장으로 적습니다. 사진은 설명과 함께 검색 근거에 반영됩니다."><textarea value={entry.photo_caption || ""} onChange={e => set("photo_caption", e.target.value)} /></Field></div>{(image || entry.has_photo) && <button type="button" onClick={() => void removePhoto()}>사진 제거</button>}</div>
          <Field label="정의·기능" required wide hint="한 항목의 역할이나 뜻을 완결된 문장으로 설명합니다."><textarea value={entry.definition || ""} onChange={e => set("definition", e.target.value)} /></Field>
          {entry.category !== "용어" && <Field label="이상 현상" wide><textarea value={entry.symptoms || ""} onChange={e => set("symptoms", e.target.value)} /></Field>}
          <Field label="점검·조치" wide hint="주어와 동사가 있는 완결된 문장으로 씁니다."><textarea value={entry.actions || ""} onChange={e => set("actions", e.target.value)} /></Field>
          <Field label="관련 규정" wide hint="예: 운전취급규정 제328조. 여러 조문은 쉼표로 구분합니다."><input value={entry.regulations || ""} onChange={e => set("regulations", e.target.value)} /></Field>
          {entry.category === "용어" && <details className="glossary-extra wide"><summary>추가 항목</summary><Field label="설치 위치"><input value={entry.location || ""} onChange={e => set("location", e.target.value)} /></Field><Field label="이상 현상"><textarea value={entry.symptoms || ""} onChange={e => set("symptoms", e.target.value)} /></Field></details>}
          <div className="glossary-field wide"><span className="glossary-label">자동 생성될 링크</span><div className="glossary-links">{!entry.regulations?.trim() ? <span>관련 규정을 적으면 조문 연결 초안이 만들어집니다. 연결 검토에서 승인해야 검색에 쓰입니다.</span> : !refs.length ? <span>규정 조문을 확인하고 있습니다…</span> : refs.map(ref => <div key={ref.ref}><b>{ref.ref}</b>{ref.found ? <span>→ VISUAL_HELP → {ref.filename} {ref.article || ""} <i className="glossary-pill draft">승인 대기</i></span> : <span className="glossary-warning">'{ref.ref}'을(를) 등록된 규정에서 찾지 못했습니다. 규정명과 조문 번호를 확인하세요.</span>}</div>)}</div></div>
        </div><footer className="glossary-actions"><button type="button" className="glossary-delete" disabled={!entry.id || busy} onClick={() => setQueued("delete")}>삭제</button><span />{queued === "delete" && <><span>이 항목을 삭제할까요?</span><button type="button" onClick={() => setQueued(null)}>취소</button><button type="button" onClick={() => { setQueued(null); void remove(); }}>삭제 확인</button></>}<button type="button" disabled={busy} onClick={() => void save(false)}>초안 저장</button><button type="button" className="glossary-primary" disabled={busy} onClick={() => void save(true)}>PDF 생성 후 검색에 등록</button></footer>
        </>}
      </section>
      <section className="glossary-pane glossary-preview"><header><h2>미리보기</h2><div className="glossary-tabs" role="tablist" aria-label="미리보기 종류">{[["pdf", "PDF"], ["text", "검색 텍스트"], ["chat", "채팅 근거"]].map(([key, label]) => <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)}>{label}</button>)}</div></header>
        <div className="glossary-preview-body">{!entry ? <p className="glossary-empty">항목을 선택하면 미리보기가 표시됩니다.</p> : tab === "pdf" ? <><article className="glossary-sheet"><h3>도해 사전 · {entry.title || "표제어"}</h3><table><tbody>{[["분류", entry.category], ["코드", entry.code], ["별칭·검색어", entry.aliases], ["적용 범위", entry.scope], ["설치 위치", entry.location], ["사진 설명", entry.photo_caption], ["정의·기능", entry.definition], ["이상 현상", entry.symptoms], ["점검·조치", entry.actions], ["관련 규정", entry.regulations]].filter(([, value]) => value).map(([label, value]) => <tr key={label}><td>{label}</td><td>{value}</td></tr>)}{image && <tr><td>사진</td><td className="glossary-sheet-photo"><img src={image} alt="" /></td></tr>}</tbody></table><small>도해 사전 · 검색 단위 1페이지</small></article><p className="glossary-note">한 항목이 PDF 한 페이지가 되어 검색 단위 하나로 인덱싱됩니다.</p></> : tab === "text" ? <><p className="glossary-meta"><b>파일</b> 도해 사전 - {entry.title || "제목 없음"}.pdf<br /><b>단위</b> 페이지 1 · fragment 1개 · 임베딩 1건</p><pre className="glossary-indexed">{text}</pre></> : <><p className="glossary-note">질문 예: “{entry.title || "이 항목"}의 기능과 점검 방법은?”</p><article className="glossary-card">{image && <img src={image} alt="" />}<div><small>도해 사전 - {entry.title || "제목 없음"}.pdf · 페이지 1</small><b>{entry.title || "표제어"}{entry.code && ` (${entry.code})`}</b><p>{entry.actions || entry.definition || "정의·기능을 입력하면 근거 카드에 표시됩니다."}</p></div></article><p className="glossary-note">이 근거는 PDF 1쪽을 가리킵니다. 초안 연결은 연결 검토에서 승인한 뒤 검색에 사용됩니다.</p></>}</div>
      </section>
    </div>
  </section>;
}

function Field({ label, required, hint, wide, children }) {
  return <label className={`glossary-field${wide ? " wide" : ""}`}><span className={`glossary-label${required ? " required" : ""}`}>{label}{required && " *"}</span>{children}{hint && <small>{hint}</small>}</label>;
}

function PhotoThumb({ item }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    if (!item.has_photo) { setUrl(""); return undefined; }
    let active = true, objectUrl = "";
    const token = localStorage.getItem("daalgi_admin_token");
    fetch(`${apiBase}/api/glossary/${item.id}/photo`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(response => response.ok ? response.blob() : Promise.reject(new Error("")))
      .then(blob => { objectUrl = URL.createObjectURL(blob); if (active) setUrl(objectUrl); else URL.revokeObjectURL(objectUrl); })
      .catch(() => {});
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [item.id, item.has_photo]);
  return <span className="glossary-thumb">{url && <img src={url} alt="" />}</span>;
}
