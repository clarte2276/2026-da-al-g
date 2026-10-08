import { useEffect, useRef, useState } from "react";
import "./chat-preview.css";

function Robot() {
  return <span className="chat-preview-avatar" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3v3M8 6h8a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3Z"/><path d="M9 12h.01M15 12h.01M9 16h6"/>
  </svg></span>;
}

function MessageText({ text }) {
  return <div className="chat-preview-message-text">{text.split("\n").map((line, index) => line.startsWith('"') && line.endsWith('"') && line.length > 1
    ? <div className="chat-preview-quote" key={index}>{line}</div>
    : <div className="chat-preview-text-line" key={index}>{line.split("**").map((part, i) => i % 2 ? <strong key={i}>{part}</strong> : part)}</div>)}</div>;
}

function EvidenceCard({ item, onOpen }) {
  const related = (item.hop || 0) > 0;
  const chapter = [item.location || item.fragment?.title || "제목 없음", item.via_relation].filter(Boolean).join(" · ");
  const sourceText = item.text ?? item.fragment?.text ?? "";
  const excerpt = sourceText.replace(/\s+/g, " ").trim();
  return <article className={`chat-preview-evidence ${related ? "is-related" : "is-direct"}`}>
    <div className="chat-preview-evidence-kind"><span aria-hidden="true">{related ? "↗" : "▤"}</span>{related ? "관련 조항" : "근거"}</div>
    <strong className="chat-preview-evidence-file">{item.filename || "알 수 없음"}</strong>
    <span className="chat-preview-evidence-chapter">{chapter}</span>
    {excerpt && <p className="chat-preview-evidence-excerpt">{excerpt}</p>}
    <button onClick={() => onOpen(item)}>원문 보기</button>
  </article>;
}

function TypingIndicator({ text }) {
  return <div className="chat-preview-typing"><Robot /><div><span className="chat-preview-spinner" />{text || "답변을 준비하고 있습니다"}…</div></div>;
}

export function ChatPreview({ apiBase, token, onUnauthorized, onOpenSource }) {
  const [messages, setMessages] = useState([]), [input, setInput] = useState("");
  const [busy, setBusy] = useState(false), [status, setStatus] = useState(""), [failure, setFailure] = useState("");
  const transcriptRef = useRef(null);

  useEffect(() => {
    const transcript = transcriptRef.current;
    if (transcript) transcript.scrollTop = transcript.scrollHeight;
  }, [messages, status, failure]);

  async function send(event) {
    event.preventDefault();
    const message = input.trim();
    if (!message || busy) return;
    const history = messages.slice(-12).map(({ role, content }) => ({ role, content }));
    const assistantIndex = messages.length + 1;
    setMessages(current => [...current, { role: "user", content: message }]);
    setInput(""); setBusy(true); setStatus("답변 생성 중"); setFailure("");
    let answer = "", finished = false, buffer = "";
    const updateAssistant = update => setMessages(current => {
      const next = [...current];
      next[assistantIndex] = { ...(next[assistantIndex] || { role: "assistant", content: "", evidence: [] }), ...update };
      return next;
    });
    const consume = line => {
      if (!line.trim()) return;
      const record = JSON.parse(line);
      if (record.type === "status") setStatus(record.text || "답변 생성 중");
      if (record.type === "delta") { answer += record.text || ""; updateAssistant({ content: answer }); }
      if (record.type === "done") {
        finished = true; answer = record.answer ?? answer;
        updateAssistant({ content: answer, evidence: Array.isArray(record.evidence) ? record.evidence : [], mode: record.mode || "rag" });
        setStatus("");
      }
    };
    try {
      const response = await fetch(`${apiBase.replace(/\/$/, "")}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ message, history }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        if (response.status === 401) onUnauthorized();
        throw new Error(typeof body.detail === "string" ? body.detail : `요청 실패 (${response.status})`);
      }
      if (!response.body) throw new Error("응답 스트림을 읽을 수 없습니다.");
      const reader = response.body.getReader(), decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const lines = buffer.split(/\r?\n/); buffer = lines.pop() || "";
        lines.forEach(consume);
        if (done) { if (buffer.trim()) consume(buffer); break; }
        if (finished) { await reader.cancel(); break; }
      }
      if (!finished) throw new Error("답변이 중간에 끊겼습니다.");
    } catch (reason) {
      setFailure(reason.message || "답변을 불러오지 못했습니다.");
    } finally { setBusy(false); setStatus(""); }
  }

  return <div className="chat-preview-phone" aria-label="사용자 앱 채팅 화면 미리보기">
    <div className="chat-preview-notch" aria-hidden="true" />
    <div className="chat-preview-screen">
      <div className="chat-preview-device-status"><span>9:41</span><span aria-hidden="true">● ▰ ▴</span></div>
      <header className="chat-preview-header"><span aria-hidden="true">‹</span><strong>규정 검색</strong><span aria-hidden="true">•••</span></header>
      <div className="chat-preview-messages" ref={transcriptRef} aria-live="polite">
        {!messages.length && <p className="chat-preview-welcome">규정이나 업무 절차를 질문해 주세요.</p>}
        {messages.map((message, index) => message.role === "user"
          ? <div className="chat-preview-user-row" key={index}><div className="chat-preview-user-bubble">{message.content}</div></div>
          : <div className="chat-preview-ai-row" key={index}>
            <Robot /><div className="chat-preview-ai-body">
              <div className="chat-preview-ai-bubble"><MessageText text={message.content} /></div>
              {message.evidence?.length === 1 && <div className="chat-preview-evidence-list"><EvidenceCard item={message.evidence[0]} onOpen={onOpenSource} /></div>}
              {message.evidence?.length > 1 && <div className="chat-preview-evidence-list">
                <p className="chat-preview-evidence-caption">근거 {message.evidence.length}건 · 옆으로 넘겨 보기</p>
                <div className="chat-preview-evidence-scroll">{message.evidence.map((item, i) => <EvidenceCard key={item.link_id || item.fragment?.id || i} item={item} onOpen={onOpenSource} />)}</div>
              </div>}
              <details className="chat-preview-debug"><summary>디버그</summary><pre>{JSON.stringify({ mode: message.mode, evidence: message.evidence || [] }, null, 2)}</pre></details>
            </div>
          </div>)}
        {busy && <TypingIndicator text={status} />}
        {failure && <p className="chat-preview-error" role="alert">{failure}</p>}
      </div>
      <div className="chat-preview-disclaimer">AI 답변은 참고용입니다. 공식 규정집이 우선합니다.</div>
      <form className="chat-preview-compose" onSubmit={send}>
        <input aria-label="메시지 입력" value={input} onChange={event => setInput(event.target.value)} placeholder="메시지 입력…" />
        <button aria-label="보내기" disabled={busy || !input.trim()}><span aria-hidden="true">↑</span></button>
      </form>
    </div>
  </div>;
}
