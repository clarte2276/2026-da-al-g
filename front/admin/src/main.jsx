import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { LinkGenerator } from "./link-generator";
import { Management } from "./management";
import { DocumentManager } from "./document-manager";
import "./admin.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const TOKEN_KEY = "daalgi_admin_token";
let authToken = "";

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.ok && response.headers.get("content-type")?.includes("spreadsheetml")) return response.blob();
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(typeof body.detail === "string" ? body.detail : `요청 실패 (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return body;
}

function AdminLogin({ onLogin, busy, error }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  return <main className="auth-shell"><section className="auth-card">
    <p className="brand"><span className="line-badge" aria-hidden="true">6</span>6호선 길라잡이</p>
    <h1>관리자 로그인</h1>
    <p className="subtitle">회원, 규정 문서, 근무표, RAG 연결을 관리합니다.</p>
    {error && <div className="notice error" role="alert">{error}</div>}
    <form onSubmit={event => { event.preventDefault(); onLogin(username.trim(), password); }}>
      <label>아이디<input autoFocus value={username} onChange={event => setUsername(event.target.value)} /></label>
      <label>비밀번호<input type="password" value={password} onChange={event => setPassword(event.target.value)} /></label>
      <button className="primary-button" disabled={busy || !username.trim() || !password}>{busy ? "로그인 중…" : "로그인"}</button>
    </form>
  </section></main>;
}

const lines = [
  ["사용자 앱", [
    ["users", "회원", "앱을 쓰는 승무원 계정을 발급하고 관리합니다."],
    ["documents", "문서", "규정 문서를 올리고 폴더를 정리한 뒤 RAG에 등록합니다."],
    ["duty", "근무표", "월별 교번 근무표 엑셀을 올려 앱에 반영합니다."],
    ["feedback", "고객문의/피드백", "고객문의와 답변 피드백을 확인하고 답변합니다."],
  ]],
  ["RAG 링크", [
    ["edit", "문서 연결", "두 문서를 나란히 열고 구절이나 페이지를 서로 연결합니다."],
    ["review", "연결 검토", "저장된 연결을 확인하고, 잘못된 연결은 반려해 검색에서 뺍니다."],
    ["search", "검색 검증", "질문을 넣어 답변과 근거가 제대로 나오는지 확인합니다."],
  ]],
];
const ragStops = new Set(["edit", "review", "search"]);

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [sessionReady, setSessionReady] = useState(() => !token);
  const [user, setUser] = useState(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");
  const [section, setSection] = useState("users");

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    authToken = "";
    setToken("");
    setUser(null);
    setSessionReady(true);
  }

  async function logout() {
    try { if (token) await api("/api/auth/logout", { method: "POST" }); }
    catch (_) { /* Local session still ends if the server is unavailable. */ }
    finally { clearSession(); }
  }

  async function login(username, password) {
    setAuthBusy(true); setAuthError("");
    try {
      const body = await api("/api/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }),
      });
      if (body.user?.role !== "admin") throw new Error("관리자 계정으로 로그인해 주세요.");
      localStorage.setItem(TOKEN_KEY, body.access_token);
      authToken = body.access_token;
      setUser(body.user);
      setToken(body.access_token);
      setSessionReady(true);
    } catch (reason) { setAuthError(reason.message); }
    finally { setAuthBusy(false); }
  }

  useEffect(() => {
    authToken = token;
    if (!token) { setUser(null); setSessionReady(true); return; }
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

  if (!sessionReady) return <main className="auth-shell"><p className="subtitle">관리자 세션을 확인하는 중입니다…</p></main>;
  if (!user) return <AdminLogin onLogin={login} busy={authBusy} error={authError} />;

  const [, [, title, description]] = lines.flatMap(([, stops]) => stops.map(stop => [stop[0], stop]))
    .find(([value]) => value === section);

  return <div className="admin-app">
    <aside className="route-map">
      <p className="brand"><span className="line-badge" aria-hidden="true">6</span>6호선 길라잡이</p>
      <nav aria-label="관리 메뉴">{lines.map(([name, stops]) => <section key={name}>
        <h2>{name}</h2>
        <ol>{stops.map(([value, label]) => <li key={value}>
          <button aria-current={section === value ? "page" : undefined} onClick={() => setSection(value)}>{label}</button>
        </li>)}</ol>
      </section>)}</nav>
      <div className="account"><span>{user.display_name}</span><button onClick={logout}>로그아웃</button></div>
    </aside>
    <main className="workspace">
      <header className="page-header"><h1>{title}</h1><p>{description}</p></header>
      {ragStops.has(section)
        ? <LinkGenerator tab={section} onTab={setSection} api={api} apiBase={API_BASE} token={token} user={user} onUnauthorized={clearSession} />
        : section === "documents" ? <DocumentManager api={api} /> : <Management section={section} api={api} />}
    </main>
  </div>;
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
