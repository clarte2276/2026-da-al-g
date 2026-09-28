import { useEffect, useState } from "react";

const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const when = value => value ? new Date(value).toLocaleString("ko-KR") : "";

export function Management({ section, api }) {
  const [rows, setRows] = useState([]);
  const [users, setUsers] = useState([]);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [file, setFile] = useState(null);

  const paths = {
    users: "/api/admin/users", duty: "/api/admin/duty",
    feedback: "/api/admin/feedback", conversations: "/api/admin/users",
    bookmarks: "/api/admin/users",
  };

  async function refresh() {
    const items = await api(paths[section]);
    if (section === "conversations" || section === "bookmarks") setUsers(items);
    else setRows(items);
  }

  useEffect(() => {
    setRows([]); setDetail([]); setError("");
    refresh().catch(e => setError(e.message));
  }, [section]);

  useEffect(() => {
    if (!selected || !["conversations", "bookmarks"].includes(section)) return;
    api(`/api/admin/users/${selected}/${section}`).then(setDetail).catch(e => setError(e.message));
  }, [selected, section]);

  async function run(action, success = "저장했습니다.") {
    setBusy(true); setError(""); setMessage("");
    try { await action(); setMessage(success); await refresh(); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  async function updateUser(user, field, value) {
    await run(() => api(`/api/admin/users/${user.id}`, json("PATCH", { [field]: value })));
  }

  function createUser(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    run(async () => {
      await api("/api/admin/users", json("POST", Object.fromEntries(form)));
      event.target.reset();
    });
  }

  async function removePersonal(item) {
    if (!confirm("이 항목을 삭제하시겠습니까? 사용자 기기에서도 동기화 후 사라집니다.")) return;
    await run(async () => {
      await api(`/api/admin/users/${selected}/${section}/${encodeURIComponent(item.id)}`, { method: "DELETE" });
      setDetail(await api(`/api/admin/users/${selected}/${section}`));
    }, "삭제했습니다.");
  }

  return <section className="management-panel">
    {error && <p className="notice error" role="alert">{error}</p>}
    {message && <p className="notice success" role="status">{message}</p>}
    {section === "users" && <>
      <h2>회원 관리</h2>
      <form className="management-form" onSubmit={createUser}>
        <label>아이디<input name="username" minLength="3" maxLength="64" required /></label>
        <label>이름<input name="display_name" maxLength="100" required /></label>
        <label>초기 비밀번호<input name="password" type="password" minLength="8" required /></label>
        <button className="primary-button" disabled={busy}>회원 발급</button>
      </form>
      <div className="management-list">{rows.map(user => <article key={user.id}>
        <div><strong>{user.display_name}</strong> <small>{user.username}</small> <span>{user.is_active ? "활성" : "비활성"}</span></div>
        <div className="pane-toolbar">
          <button disabled={busy} onClick={() => { const name = prompt("새 표시명", user.display_name); if (name?.trim()) updateUser(user, "display_name", name.trim()); }}>이름 변경</button>
          <button disabled={busy} onClick={() => { const password = prompt("새 비밀번호 (8자 이상)"); if (password) updateUser(user, "password", password); }}>비밀번호 재설정</button>
          <button disabled={busy} onClick={() => updateUser(user, "is_active", !user.is_active)}>{user.is_active ? "비활성화" : "활성화"}</button>
        </div>
      </article>)}</div>
    </>}
    {section === "duty" && <>
      <h2>월별 근무표</h2>
      <p className="helper-text">교번기관사 근무계획 시트가 있는 기존 엑셀 양식을 사용합니다. 선택한 월의 날짜와 기관사 행을 검사합니다.</p>
      <form className="management-form" onSubmit={event => { event.preventDefault(); const body = new FormData(); body.append("file", file); run(() => api(`/api/admin/duty/${month}`, { method: "POST", body }), "근무표를 반영했습니다."); }}>
        <label>적용 월<input type="month" value={month} onChange={event => setMonth(event.target.value)} required /></label>
        <label>엑셀 파일<input type="file" accept=".xlsx" onChange={event => setFile(event.target.files[0])} required /></label>
        <button className="primary-button" disabled={busy || !file}>업로드·교체</button>
      </form>
      <div className="management-list">{rows.map(row => <article key={row.month}>
        <strong>{row.month}</strong> <span>{row.driver_count}명</span> <small>{row.source_filename} · {when(row.updated_at)}</small>
      </article>)}</div>
    </>}
    {section === "feedback" && <>
      <h2>채팅 피드백</h2>
      <div className="management-list">{rows.map(row => <article key={row.id}>
        <div><strong>{row.rating === "up" ? "도움이 됨" : "개선 필요"}</strong> <small>{row.user_id} · {when(row.created_at)}</small></div>
        <p><b>질문</b> {row.question}</p><p><b>답변</b> {row.answer}</p>
        {row.reason && <p><b>사유</b> {row.reason}</p>}
        {!!row.evidence?.length && <details><summary>근거 {row.evidence.length}개</summary><pre>{JSON.stringify(row.evidence, null, 2)}</pre></details>}
      </article>)}</div>
    </>}
    {["conversations", "bookmarks"].includes(section) && <>
      <h2>{section === "conversations" ? "대화 기록" : "북마크"}</h2>
      <label className="management-select">회원 선택<select value={selected} onChange={event => setSelected(event.target.value)}>
        <option value="">선택하세요</option>{users.map(user => <option key={user.id} value={user.id}>{user.display_name} ({user.username})</option>)}
      </select></label>
      <div className="management-list">{detail.map(item => <article key={item.id}>
        <div><strong>{item.title || `${item.regulation} · ${item.chapter}`}</strong> <small>{when(item.createdAt)}</small></div>
        {item.messages && <details><summary>대화 {item.messages.length}개 보기</summary>{item.messages.map((msg, i) => <p key={i}><b>{msg.isUser ? "사용자" : "AI"}</b> {msg.text}</p>)}</details>}
        {item.excerpt && <p>{item.excerpt}</p>}
        <button disabled={busy} onClick={() => removePersonal(item)}>삭제</button>
      </article>)}</div>
    </>}
  </section>;
}
