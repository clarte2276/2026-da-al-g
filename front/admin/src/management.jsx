import { useEffect, useState } from "react";

const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const when = value => value ? new Date(value).toLocaleString("ko-KR") : "";

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function Management({ section, api }) {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [file, setFile] = useState(null);
  const [routeFile, setRouteFile] = useState(null);
  const [search, setSearch] = useState("");
  const [importFile, setImportFile] = useState(null);
  const [result, setResult] = useState(null);
  const [kind, setKind] = useState("all");
  const [waitingOnly, setWaitingOnly] = useState(false);
  const [replyDrafts, setReplyDrafts] = useState({});

  async function refresh() {
    if (section === "feedback") {
      const query = kind === "all" ? "" : `?kind=${kind}`;
      setRows(await api(`/api/admin/inquiries${query}`));
    } else {
      setRows(await api(section === "users" ? "/api/admin/users" : "/api/admin/duty"));
    }
  }

  useEffect(() => {
    setRows([]); setError("");
    if (section !== "users") setResult(null);
    refresh().catch(e => setError(e.message));
  }, [section, kind]);

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
    const form = event.currentTarget;
    const values = new FormData(form);
    const username = values.get("username").trim();
    const display_name = values.get("display_name").trim();
    if (!/^\d+$/.test(username)) { setError("사번은 숫자만 입력해 주세요."); return; }
    run(async () => {
      const data = await api("/api/admin/users", json("POST", { username, display_name }));
      setResult({ created: [{ ...data.user, initial_password: data.initial_password }], skipped: [] });
      form.reset();
    }, "회원을 등록했습니다. 초기 비밀번호를 저장해 주세요.");
  }

  function importUsers(event) {
    event.preventDefault();
    if (!importFile) return;
    const form = event.currentTarget;
    const body = new FormData();
    body.append("file", importFile);
    run(async () => {
      const data = await api("/api/admin/users/import", { method: "POST", body });
      setResult({ created: data.created, skipped: data.skipped });
      setImportFile(null);
      form.reset();
    }, "엑셀 일괄 등록을 마쳤습니다. 초기 비밀번호를 저장해 주세요.");
  }

  function resetPassword(user) {
    run(async () => {
      const data = await api(`/api/admin/users/${user.id}`, json("PATCH", { reset_password: true }));
      setResult({ created: [{ username: user.username, display_name: user.display_name, initial_password: data.initial_password }], skipped: [] });
    }, "초기 비밀번호를 재설정했습니다. 지금 저장해 주세요.");
  }

  function reply(event, inquiry) {
    event.preventDefault();
    const body = replyDrafts[inquiry.id]?.trim();
    if (!body) return;
    run(async () => {
      await api(`/api/admin/inquiries/${inquiry.id}/replies`, json("POST", { body }));
      setReplyDrafts(drafts => ({ ...drafts, [inquiry.id]: "" }));
    }, "답변을 등록했습니다.");
  }

  const users = rows.filter(user => `${user.username} ${user.display_name}`.toLowerCase().includes(search.trim().toLowerCase()));
  const inquiries = rows.filter(row => !waitingOnly || !row.replies?.some(reply => reply.from_admin));

  return <section className="management-panel">
    {error && <p className="notice error" role="alert">{error}</p>}
    {message && <p className="notice success" role="status">{message}</p>}
    {section === "users" && <>
      <div className="pane-toolbar user-tools">
        <input aria-label="회원 검색" placeholder="사번 또는 이름 검색" value={search} onChange={event => setSearch(event.target.value)} />
        <button disabled={busy} onClick={() => run(async () => saveBlob(await api("/api/admin/users/template.xlsx"), "회원_양식.xlsx"), "회원 등록 양식을 다운로드했습니다.")}>양식 다운로드</button>
      </div>
      <form className="management-form" onSubmit={createUser}>
        <label>사번<input name="username" inputMode="numeric" pattern="[0-9]+" onChange={event => { event.target.value = event.target.value.replace(/\D/g, ""); }} required /></label>
        <label>이름<input name="display_name" maxLength="100" required /></label>
        <button className="primary-button" disabled={busy}>회원 등록</button>
      </form>
      <form className="management-form" onSubmit={importUsers}>
        <label>엑셀 파일<input type="file" accept=".xlsx" onChange={event => setImportFile(event.target.files[0] || null)} required /></label>
        <button className="primary-button" disabled={busy || !importFile}>엑셀 일괄 등록</button>
      </form>
      {result && <section className="credential-results" aria-live="polite">
        <div className="credential-heading"><h2>초기 비밀번호</h2><button onClick={() => setResult(null)}>결과 닫기</button></div>
        <p className="helper-text">초기 비밀번호는 지금만 확인할 수 있습니다. 이 화면을 닫기 전에 저장해 주세요.</p>
        {result.created.length ? <>
          <div className="table-scroll"><table className="management-table credential-table">
            <thead><tr><th>사번</th><th>이름</th><th>초기 비밀번호</th></tr></thead>
            <tbody>{result.created.map(row => <tr key={row.username}><td>{row.username}</td><td>{row.display_name}</td><td><code>{row.initial_password}</code></td></tr>)}</tbody>
          </table></div>
          <button disabled={busy} onClick={() => run(async () => saveBlob(await api("/api/admin/users/credentials.xlsx", json("POST", { rows: result.created })), "회원_초기비밀번호.xlsx"), "초기 비밀번호 엑셀을 다운로드했습니다.")}>엑셀로 저장</button>
        </> : <p className="helper-text">새로 등록된 회원이 없습니다.</p>}
        {!!result.skipped.length && <div className="skipped-list"><h3>건너뛴 행</h3><ul>{result.skipped.map((row, index) => <li key={`${row.username}-${index}`}><strong>{row.username}</strong> {row.reason}</li>)}</ul></div>}
      </section>}
      <div className="table-scroll"><table className="management-table">
        <thead><tr><th>사번</th><th>이름</th><th>상태</th><th>비밀번호 상태</th><th>생성일</th><th>작업</th></tr></thead>
        <tbody>{users.map(user => <tr key={user.id}>
          <td>{user.username}</td>
          <td><input aria-label={`${user.username} 이름`} defaultValue={user.display_name} onBlur={event => {
            const value = event.target.value.trim();
            if (!value) { event.target.value = user.display_name; return; }
            if (value !== user.display_name) updateUser(user, "display_name", value);
          }} onKeyDown={event => {
            if (event.key === "Enter") { event.preventDefault(); event.currentTarget.blur(); }
            if (event.key === "Escape") { event.currentTarget.value = user.display_name; event.currentTarget.blur(); }
          }} /></td>
          <td><button className="status-toggle" aria-pressed={user.is_active} disabled={busy} onClick={() => updateUser(user, "is_active", !user.is_active)}>{user.is_active ? "활성" : "비활성"}</button></td>
          <td>{user.must_change_password ? "초기 비밀번호 변경 대기" : "변경 완료"}</td>
          <td>{when(user.created_at)}</td>
          <td><button disabled={busy} onClick={() => resetPassword(user)}>비밀번호 재설정</button></td>
        </tr>)}</tbody>
      </table></div>
    </>}
    {section === "duty" && <>
      <p className="helper-text">교번기관사 근무계획 시트가 있는 기존 엑셀 양식을 사용합니다. 선택한 월의 날짜와 기관사 행을 검사합니다.</p>
      <form className="management-form" onSubmit={event => { event.preventDefault(); const body = new FormData(); body.append("file", file); run(() => api(`/api/admin/duty/${month}`, { method: "POST", body }), "근무표를 반영했습니다."); }}>
        <label>적용 월<input type="month" value={month} onChange={event => setMonth(event.target.value)} required /></label>
        <label>엑셀 파일<input type="file" accept=".xlsx" onChange={event => setFile(event.target.files[0])} required /></label>
        <button className="primary-button" disabled={busy || !file}>업로드·교체</button>
      </form>
      <p className="helper-text">행로표(수색) 엑셀을 올리면 근무표의 Dia별 출퇴근·운전 시각이 함께 표시됩니다.</p>
      <form className="management-form" onSubmit={event => { event.preventDefault(); const body = new FormData(); body.append("file", routeFile); run(() => api("/api/admin/duty-routes", { method: "POST", body }), "행로표를 반영했습니다."); }}>
        <label>행로표 엑셀<input type="file" accept=".xlsx" onChange={event => setRouteFile(event.target.files[0])} required /></label>
        <button className="primary-button" disabled={busy || !routeFile}>행로표 업로드·교체</button>
      </form>
      <div className="management-list">{rows.map(row => <article key={row.month}><div>
        <strong>{row.month}</strong> <span>{row.driver_count}명</span> <small>{row.source_filename} · {when(row.updated_at)}</small>
      </div></article>)}</div>
    </>}
    {section === "feedback" && <>
      <div className="pane-toolbar inquiry-filters">
        <label>종류<select value={kind} onChange={event => setKind(event.target.value)}><option value="all">전체</option><option value="inquiry">고객문의</option><option value="feedback">답변 피드백</option></select></label>
        <label><input type="checkbox" checked={waitingOnly} onChange={event => setWaitingOnly(event.target.checked)} /> 답변 대기</label>
      </div>
      <div className="inquiry-list">{inquiries.map(inquiry => {
        const hasReply = inquiry.replies?.some(reply => reply.from_admin);
        return <article className={`inquiry-item${hasReply ? "" : " inquiry-unanswered"}`} key={inquiry.id}>
          <header><div><span className="status status-draft">{inquiry.kind === "feedback" ? "답변 피드백" : "고객문의"}</span> <span className={`status status-${hasReply ? "approved" : "rejected"}`}>{hasReply ? "답변 완료" : "답변 대기"}</span></div>
            <small>{inquiry.user?.username} · {inquiry.user?.display_name} · {when(inquiry.created_at)}</small></header>
          <h2>{inquiry.title}</h2>
          {inquiry.body && <p>{inquiry.body}</p>}
          {inquiry.kind === "feedback" && <div className="feedback-context">
            <p><b>평가</b> {inquiry.rating === "up" ? "도움이 됨" : "개선 필요"}</p>
            <p><b>질문</b> {inquiry.question}</p><p><b>답변</b> {inquiry.answer}</p>
            {!!inquiry.evidence?.length && <details><summary>근거 {inquiry.evidence.length}개</summary><pre>{JSON.stringify(inquiry.evidence, null, 2)}</pre></details>}
          </div>}
          {!!inquiry.replies?.length && <div className="reply-thread"><h3>답변 기록</h3>{inquiry.replies.map(item => <p key={item.id}><b>{item.from_admin ? "관리자" : "회원"} · {when(item.created_at)}</b>{item.body}</p>)}</div>}
          <form className="reply-form" onSubmit={event => reply(event, inquiry)}>
            <label htmlFor={`reply-${inquiry.id}`}>답변</label><textarea id={`reply-${inquiry.id}`} value={replyDrafts[inquiry.id] || ""} maxLength="4000" required onChange={event => setReplyDrafts(drafts => ({ ...drafts, [inquiry.id]: event.target.value }))} />
            <button className="primary-button" disabled={busy}>답변 등록</button>
          </form>
        </article>;
      })}</div>
    </>}
  </section>;
}
