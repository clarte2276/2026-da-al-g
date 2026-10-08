import { useCallback, useEffect, useRef, useState } from "react";
import { Locale } from "@svar-ui/react-core";
import { en as filemanagerEn } from "@svar-ui/filemanager-locales";
import { Filemanager, Willow } from "@svar-ui/react-filemanager";
import "@svar-ui/react-filemanager/all.css";
import "./explorer.css";

const SUPPORTED = new Set([".docx", ".hwp", ".hwpx", ".pptx", ".pdf"]);
const ROOT_PANELS = [{ path: "/" }];
const koWords = {
  ...filemanagerEn,
  filemanager: {
    ...filemanagerEn.filemanager,
    "My files": "문서",
    "Add New": "새로 만들기",
    Ok: "확인",
    Cancel: "취소",
    "Delete files": "파일 삭제",
    Files: "파일",
    Folder: "폴더",
    "Back to parent folder": "상위 폴더",
    Information: "정보",
    Found: "검색 결과",
    "Are you sure you want to delete these items:": "다음 항목을 삭제하시겠습니까?",
    "Enter file name": "파일 이름 입력",
    "Enter folder name": "폴더 이름 입력",
    Result: "결과",
    Search: "검색",
    "Search results in": "검색 위치",
    "Add new file": "새 파일",
    "Add new folder": "새 폴더",
    "Upload file": "파일 업로드",
    Size: "크기",
    Name: "이름",
    Type: "유형",
    Date: "수정한 날짜",
    Rename: "이름 바꾸기",
    Cut: "잘라내기",
    Delete: "삭제",
    Copy: "복사",
    Paste: "붙여넣기",
    Download: "다운로드",
    Count: "항목 수",
    folder: "폴더",
    folders: "폴더",
    file: "파일",
    files: "파일",
    "Multiple files": "여러 항목",
    multiple: "여러 항목",
    Preview: "미리 보기",
    of: "/",
    used: "사용 중",
    "Select file or folder to view details": "세부 정보를 보려면 파일이나 폴더를 선택하세요.",
    "Looks like nothing is here": "이 폴더는 비어 있습니다.",
    "Unknown file": "알 수 없는 파일",
    "A miniature file preview": "파일 미리 보기",
  },
  core: { ok: "확인", cancel: "취소", select: "선택", "No data": "데이터 없음" },
};

const json = (method, body) => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
const join = (folder, name) => [folder, name].filter(Boolean).join("/");
const parent = path => path.split("/").slice(0, -1).join("/");
const nameOf = path => path.split("/").at(-1) || "";
const localPath = id => id === "/" ? "" : id.replace(/^\//, "");
const svarPath = path => path ? `/${path}` : "/";
const query = (rootId, path) => new URLSearchParams({ root_id: rootId, path }).toString();
const formatSize = bytes => {
  if (!Number.isFinite(bytes)) return "—";
  if (bytes < 1024) return `${bytes}바이트`;
  const units = ["KB", "MB", "GB", "TB"];
  let size = bytes;
  let unit = -1;
  do { size /= 1024; unit += 1; } while (size >= 1024 && unit < units.length - 1);
  return `${new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 1 }).format(size)} ${units[unit]}`;
};
const dateText = date => {
  const value = new Date(date);
  if (!date || Number.isNaN(value.getTime())) return "—";
  const pad = part => String(part).padStart(2, "0");
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())} ${value.toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit", hour12: true })}`;
};

function getDocument(documents, path) {
  const name = nameOf(path);
  const folder = parent(path);
  return documents.find(doc => doc.filename === name && (doc.folder || "") === folder);
}

function toFilemanagerData(entries, documents) {
  return entries.map(entry => {
    const document = entry.type === "file" ? getDocument(documents, entry.path) : null;
    return {
      id: svarPath(entry.path),
      type: entry.type,
      ...(entry.type === "file" ? { size: entry.size_bytes } : {}),
      date: entry.modified_at ? new Date(entry.modified_at) : undefined,
      lazy: entry.type === "folder",
      ragStatus: document?.status || "미등록",
      ragDocumentId: document?.id,
      fragmentCount: document?.fragment_count || 0,
    };
  });
}

function entryIcon(file, size = "small") {
  const extent = size === "big" ? 64 : 32;
  if (file.type === "folder") {
    return `data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="${extent}" height="${extent}" viewBox="0 0 64 64"><path fill="#e6aa00" d="M5 15a5 5 0 0 1 5-5h18l7 7h19a5 5 0 0 1 5 5v4H5z"/><path fill="#ffca28" d="M5 23h50a4 4 0 0 1 4 5l-4 24a5 5 0 0 1-5 4H10a5 5 0 0 1-5-5z"/></svg>`)}`;
  }
  const ext = (file.ext || nameOf(file.id).split(".").at(-1) || "").toLowerCase();
  const color = ext === "pdf" ? "#d83b36" : ext === "pptx" ? "#d96c28" : ["hwp", "hwpx"].includes(ext) ? "#16875b" : "#2475c5";
  const label = ({ pdf: "PDF", pptx: "P", docx: "W", hwp: "H", hwpx: "H" })[ext] || "DOC";
  const rag = file.ragDocumentId ? `<circle cx="53" cy="53" r="8" fill="${file.ragStatus?.toLowerCase().includes("fail") ? "#d83b36" : "#107c10"}" stroke="white" stroke-width="3"/>` : "";
  return `data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="${extent}" height="${extent}" viewBox="0 0 64 64"><path fill="#fff" stroke="#b8b8b8" stroke-width="2" d="M13 4h25l14 14v40a3 3 0 0 1-3 3H13a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3z"/><path fill="#e6e6e6" d="M38 4v14h14z"/><rect x="7" y="34" width="42" height="17" rx="3" fill="${color}"/><text x="28" y="46" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="700" fill="white">${label}</text>${rag}</svg>`)}`;
}

const glyphs = {
  back: "M14.5 4.5 7 12l7.5 7.5M7.5 12H21",
  forward: "m9.5 4.5 7.5 7.5-7.5 7.5M16.5 12H3",
  up: "M12 19V5m-7 7 7-7 7 7",
  folder: "M3 7h7l2 2h9v10H3z",
  cut: "m6 6 12 12M18 6 6 18M5 5h.01M19 19h.01",
  copy: "M8 8V4h12v12h-4M4 8h12v12H4z",
  paste: "M8 5h8l2 2v13H6V7h2m2-2V3h4v2",
  rename: "M4 20h4l11-11-4-4L4 16zM13.5 6.5l4 4M4 4h6",
  delete: "M4 7h16m-14 0 1 13h10l1-13M9 7V4h6v3m-5 3v6m4-6v6",
  list: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
  cards: "M4 4h7v7H4zM14 4h7v7h-7zM4 14h7v7H4zM14 14h7v7h-7z",
  sort: "M8 5v14m0 0-4-4m4 4 4-4M16 5h4m-4 4h3m-3 4h2m-2 4h1",
  details: "M4 5h16v14H4zM8 9h8M8 13h8M8 17h4",
};

function Icon({ name }) {
  return <svg aria-hidden="true" viewBox="0 0 24 24" className="explorer-icon" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d={glyphs[name]} /></svg>;
}

function fetchEntries(api, rootId, path) {
  return api(`/api/local/entries?${query(rootId, path)}`);
}

export function DocumentManager({ api }) {
  const [roots, setRoots] = useState([]);
  const [rootId, setRootId] = useState("");
  const [initialData, setInitialData] = useState(null);
  const [dataRootId, setDataRootId] = useState("");
  const [documents, setDocuments] = useState([]);
  const [currentPath, setCurrentPath] = useState("");
  const [currentItems, setCurrentItems] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [view, setView] = useState("table");
  const [sortKey, setSortKey] = useState("name");
  const [sortOrder, setSortOrder] = useState("asc");
  const [, setHistoryVersion] = useState(0);
  const [clipboard, setClipboard] = useState({ mode: "", ids: [] });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const fmRef = useRef(null);
  const hostRef = useRef(null);
  const uploadRef = useRef(null);
  const rootIdRef = useRef(rootId);
  const docsRef = useRef(documents);
  const selectedRef = useRef([]);
  const clipboardRef = useRef(clipboard);
  const busyRef = useRef(false);
  const historyRef = useRef({ paths: ["/"], index: 0, going: null });
  rootIdRef.current = rootId;
  docsRef.current = documents;
  selectedRef.current = selectedIds;
  clipboardRef.current = clipboard;

  useEffect(() => {
    let active = true;
    api("/api/local/roots").then(items => {
      if (!active) return;
      setRoots(items);
      if (items.length) setRootId(items[0].id);
    }).catch(reason => { if (active) setError(reason.message); });
    return () => { active = false; };
  }, [api]);

  useEffect(() => {
    if (!rootId) return undefined;
    let active = true;
    setInitialData(null);
    setDataRootId("");
    setCurrentPath("");
    setCurrentItems([]);
    setSelectedIds([]);
    historyRef.current = { paths: ["/"], index: 0, going: null };
    Promise.all([fetchEntries(api, rootId, ""), api("/api/documents")]).then(([entries, nextDocuments]) => {
      if (!active) return;
      docsRef.current = nextDocuments;
      setDocuments(nextDocuments);
      setInitialData(toFilemanagerData(entries, nextDocuments));
      setDataRootId(rootId);
    }).catch(reason => { if (active) setError(reason.message); });
    return () => { active = false; };
  }, [api, rootId]);

  async function refreshDocuments() {
    const next = await api("/api/documents");
    docsRef.current = next;
    setDocuments(next);
  }

  async function refreshPath(path) {
    const id = rootIdRef.current;
    if (!id || !fmRef.current) return;
    const entries = await fetchEntries(api, id, path);
    await fmRef.current.exec("provide-data", { id: svarPath(path), data: toFilemanagerData(entries, docsRef.current) });
    updateFromApi();
  }

  async function run(action, success, refreshPaths = [], refreshRag = false) {
    if (busyRef.current) return false;
    busyRef.current = true;
    setBusy(true);
    setError("");
    setMessage("");
    let failure;
    try { await action(); }
    catch (reason) { failure = reason; }
    if (refreshRag) {
      try { await refreshDocuments(); }
      catch (reason) { failure ||= reason; }
    }
    try { await Promise.all([...new Set(refreshPaths)].map(refreshPath)); }
    catch (reason) { failure ||= reason; }
    if (failure) setError(failure.message || "요청을 처리하지 못했습니다.");
    else setMessage(success);
    busyRef.current = false;
    setBusy(false);
    return !failure;
  }

  function updateFromApi(apiInstance = fmRef.current) {
    if (!apiInstance) return;
    const state = apiInstance.getState();
    const panel = state.panels[state.activePanel] || state.panels[0];
    if (!panel) return;
    const ids = (panel.selected || []).filter(id => !id.startsWith("/wx-filemanager-"));
    selectedRef.current = ids;
    setSelectedIds(ids);
    setCurrentPath(localPath(panel.path));
    setCurrentItems((panel._files || []).filter(item => !item.id.startsWith("/wx-filemanager-")));
  }

  function pathChanged(id) {
    setCurrentPath(localPath(id));
    const history = historyRef.current;
    if (history.going === id) history.going = null;
    else if (history.paths[history.index] !== id) {
      history.paths = [...history.paths.slice(0, history.index + 1), id];
      history.index = history.paths.length - 1;
    }
    setHistoryVersion(value => value + 1);
    setTimeout(() => updateFromApi(), 0);
  }

  function goTo(id) {
    historyRef.current.going = id;
    fmRef.current?.exec("set-path", { id }).then(() => {
      if (historyRef.current.going === id) historyRef.current.going = null;
    });
  }

  function back() {
    const history = historyRef.current;
    if (history.index === 0) return;
    history.index -= 1;
    setHistoryVersion(value => value + 1);
    goTo(history.paths[history.index]);
  }

  function forward() {
    const history = historyRef.current;
    if (history.index >= history.paths.length - 1) return;
    history.index += 1;
    setHistoryVersion(value => value + 1);
    goTo(history.paths[history.index]);
  }

  function createFolderAt(path, suppliedName) {
    const rawName = suppliedName ?? window.prompt("새 폴더 이름");
    const name = rawName?.trim();
    if (!name) return;
    if ([".", ".."].includes(name) || /[/\\]/.test(name)) {
      setError("폴더 이름에 경로 구분자를 사용할 수 없습니다.");
      return;
    }
    return run(
      () => api("/api/local/folders", json("POST", { root_id: rootIdRef.current, relative_path: join(path, name) })),
      "폴더를 만들었습니다.",
      [path],
    );
  }

  function renameItem(id) {
    const path = localPath(id);
    const oldName = nameOf(path);
    const name = window.prompt("새 이름", oldName)?.trim();
    if (!name || [".", ".."].includes(name) || /[/\\]/.test(name)) return;
    const item = fmRef.current?.getFile(id);
    if (item?.type === "file" && name.slice(name.lastIndexOf(".")).toLowerCase() !== oldName.slice(oldName.lastIndexOf(".")).toLowerCase()) {
      setError("파일 형식은 변경할 수 없습니다.");
      return;
    }
    const destination = join(parent(path), name);
    return run(() => api("/api/local/move", json("POST", {
      root_id: rootIdRef.current,
      source_path: path,
      destination_path: destination,
    })), "이름을 변경했습니다.", [parent(path)], true);
  }

  function cutItems(ids) {
    if (!ids.length) return;
    const next = { mode: "move", ids: [...ids] };
    clipboardRef.current = next;
    setClipboard(next);
  }

  function copyToClipboard(ids) {
    if (!ids.length) return;
    const next = { mode: "copy", ids: [...ids] };
    clipboardRef.current = next;
    setClipboard(next);
  }

  async function moveItems(ids, target) {
    if (!ids.length) return false;
    const sources = ids.map(id => ({ id, path: localPath(id), item: fmRef.current?.getFile(id) })).filter(source => source.path && source.item);
    const refreshPaths = [target, ...sources.map(source => parent(source.path))];
    return run(async () => {
      const failures = [];
      for (const source of sources) {
        if (source.item.type === "folder" && (target === source.path || target.startsWith(`${source.path}/`))) {
          failures.push(`${nameOf(source.path)} 폴더 안으로 이동할 수 없습니다.`);
          continue;
        }
        const destination = join(target, nameOf(source.path));
        if (destination === source.path) continue;
        try {
          await api("/api/local/move", json("POST", {
            root_id: rootIdRef.current,
            source_path: source.path,
            destination_path: destination,
          }));
        } catch (reason) { failures.push(`${nameOf(source.path)}: ${reason.message}`); }
      }
      if (failures.length) throw new Error(failures.join(" · "));
    }, "항목을 이동했습니다.", refreshPaths, true);
  }

  function nextCopyName(name, folder, taken) {
    const dot = folder ? -1 : name.lastIndexOf(".");
    const stem = dot > 0 ? name.slice(0, dot) : name;
    const suffix = dot > 0 ? name.slice(dot) : "";
    let index = 1;
    let candidate;
    do {
      candidate = `${stem} - 복사본${index > 1 ? ` (${index})` : ""}${suffix}`;
      index += 1;
    } while (taken.has(candidate.toLocaleLowerCase()));
    taken.add(candidate.toLocaleLowerCase());
    return candidate;
  }

  async function copyItems(ids, target) {
    if (!ids.length) return false;
    const sources = ids.map(id => ({ id, path: localPath(id), item: fmRef.current?.getFile(id) })).filter(source => source.path && source.item);
    const refreshPaths = [target];
    return run(async () => {
      const entries = await fetchEntries(api, rootIdRef.current, target);
      const taken = new Set(entries.map(entry => entry.name.toLocaleLowerCase()));
      const failures = [];
      for (const source of sources) {
        if (source.item.type === "folder" && (target === source.path || target.startsWith(`${source.path}/`))) {
          failures.push(`${nameOf(source.path)} 폴더 안으로 복사할 수 없습니다.`);
          continue;
        }
        let copied = false;
        for (let attempt = 0; attempt < 100 && !copied; attempt += 1) {
          const name = nextCopyName(nameOf(source.path), source.item.type === "folder", taken);
          const destination = join(target, name);
          try {
            await api("/api/local/copy", json("POST", {
              root_id: rootIdRef.current,
              source_path: source.path,
              destination_path: destination,
            }));
            copied = true;
          } catch (reason) {
            if (reason.status !== 409) { failures.push(`${nameOf(source.path)}: ${reason.message}`); break; }
          }
        }
        if (!copied && !failures.some(failure => failure.startsWith(`${nameOf(source.path)}:`))) failures.push(`${nameOf(source.path)}: 복사본 이름을 만들 수 없습니다.`);
      }
      if (failures.length) throw new Error(failures.join(" · "));
    }, "항목을 복사했습니다.", refreshPaths);
  }

  async function pasteInto(target = currentPath) {
    const pending = clipboardRef.current;
    if (!pending.ids.length) return;
    const succeeded = pending.mode === "move"
      ? await moveItems(pending.ids, target)
      : await copyItems(pending.ids, target);
    if (succeeded && pending.mode === "move") {
      const empty = { mode: "", ids: [] };
      clipboardRef.current = empty;
      setClipboard(empty);
    }
  }

  function deleteItems(ids) {
    const valid = ids.filter(id => fmRef.current?.getFile(id));
    if (!valid.length || !window.confirm(`선택한 ${valid.length}개 항목을 영구 삭제할까요?\n폴더와 그 안의 문서도 함께 삭제됩니다. 삭제한 원본의 RAG 내용과 링크는 유지됩니다.`)) return;
    const paths = valid.map(localPath);
    return run(async () => {
      const failures = [];
      for (const path of paths) {
        const item = fmRef.current?.getFile(svarPath(path));
        const folder = item?.type === "folder";
        try {
          await api(folder ? "/api/local/folders" : "/api/local/files", {
            ...json("DELETE", { root_id: rootIdRef.current, relative_path: path, ...(folder ? { recursive: true } : {}) }),
          });
        } catch (reason) { failures.push(`${nameOf(path)}: ${reason.message}`); }
      }
      if (failures.length) throw new Error(failures.join(" · "));
    }, "선택한 항목을 영구 삭제했습니다.", paths.map(parent));
  }

  function uploadFiles(files, path = currentPath) {
    const selectedFiles = [...files].filter(file => SUPPORTED.has(`.${file.name.split(".").at(-1).toLowerCase()}`));
    if (!selectedFiles.length) {
      setError("지원하는 문서 파일(.docx, .hwp, .hwpx, .pptx, .pdf)을 선택하세요.");
      return;
    }
    return run(async () => {
      const failures = [];
      for (const file of selectedFiles) {
        const body = new FormData();
        body.set("file", file);
        body.set("root_id", rootIdRef.current);
        body.set("folder_path", path);
        try { await api("/api/documents/upload", { method: "POST", body }); }
        catch (reason) { failures.push(`${file.name}: ${reason.message}`); }
      }
      if (failures.length) throw new Error(failures.join(" · "));
    }, "문서를 업로드했습니다.", [path], true);
  }

  async function registerRag(path) {
    return run(() => api("/api/local/open", json("POST", { root_id: rootIdRef.current, relative_path: path })), "RAG에 등록했습니다.", [parent(path)], true);
  }

  async function reprocess(document) {
    if (!document) return;
    return run(() => api(`/api/documents/${document.id}/ingest`, { method: "POST" }), "문서를 다시 처리했습니다.", [currentPath], true);
  }

  async function openOriginal(document) {
    if (!document) {
      setError("원문을 열려면 먼저 RAG에 등록하세요.");
      return;
    }
    const tab = window.open("about:blank", "_blank");
    if (!tab) {
      setError("새 탭을 열 수 없습니다. 팝업 차단을 확인하세요.");
      return;
    }
    tab.opener = null;
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || ""}/api/documents/${document.id}/pdf`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("daalgi_admin_token") || ""}` },
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `원문을 열지 못했습니다 (${response.status})`);
      }
      const url = URL.createObjectURL(await response.blob());
      tab.location.href = url;
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (reason) {
      tab.close();
      setError(reason.message);
    }
  }

  function openItem(id) {
    const item = fmRef.current?.getFile(id);
    if (!item) return;
    if (item.type === "folder") {
      goTo(id);
      return;
    }
    void openOriginal(getDocument(docsRef.current, localPath(id)));
  }

  function selectedFor(item) {
    const selected = selectedRef.current;
    if (!item) return selected;
    return selected.includes(item.id) ? selected : [item.id];
  }

  function contextTarget(item, mode) {
    return mode === "folder" && item?.type === "folder" ? localPath(item.id) : currentPath;
  }

  const menuOptions = useCallback((mode, item) => {
    const make = (id, text, icon, handler, hotkey) => ({ id, text, icon: `wxi ${icon}`, handler, hotkey });
    const ids = selectedFor(item);
    if (mode === "add") return [
      { id: "add-folder", text: "새 폴더", icon: "wxi wxi-folder-plus" },
      { id: "upload", text: "파일 업로드", icon: "wxi wxi-upload", comp: "upload" },
    ];
    if (mode === "body") return [
      make("paste", "붙여넣기", "content-paste", () => void pasteInto(currentPath), "Ctrl+V"),
      make("add-folder", "새 폴더", "folder-plus", () => void createFolderAt(currentPath)),
      make("upload", "파일 업로드", "upload", () => uploadRef.current?.click()),
    ];
    const items = [];
    if (mode === "file" || mode === "folder") items.push(make("open", "열기", "open-in-new", () => item && openItem(item.id), "Enter"));
    items.push(
      make("cut", "잘라내기", "content-cut", () => cutItems(ids), "Ctrl+X"),
      make("copy", "복사", "content-copy", () => copyToClipboard(ids), "Ctrl+C"),
      make("paste", "붙여넣기", "content-paste", () => void pasteInto(contextTarget(item, mode)), "Ctrl+V"),
    );
    if (mode !== "multiselect") items.push(
      make("rename", "이름 바꾸기", "edit", () => item && renameItem(item.id), "F2"),
      make("delete", "삭제", "close", () => deleteItems(ids), "Delete"),
    );
    else items.push(make("delete", "삭제", "close", () => deleteItems(ids), "Delete"));
    if (mode === "file" && item) {
      const document = getDocument(docsRef.current, localPath(item.id));
      items.push(make("rag-register", "RAG 등록", "database-plus", () => void registerRag(localPath(item.id))));
      if (document) items.push(make("rag-process", "다시 처리", "refresh", () => void reprocess(document)));
    }
    if (mode === "file" || mode === "folder") items.push(make("add-folder", "새 폴더", "folder-plus", () => void createFolderAt(contextTarget(item, mode))));
    items.push(make("properties", "속성", "information", () => item && fmRef.current?.exec("select-file", { id: item.id })));
    return items;
  }, [currentPath, documents, selectedIds]);

  const init = useCallback(apiInstance => {
    fmRef.current = apiInstance;
    apiInstance.on("request-data", ({ id }) => {
      const path = localPath(id);
      return fetchEntries(api, rootIdRef.current, path)
        .then(entries => apiInstance.exec("provide-data", { id, data: toFilemanagerData(entries, docsRef.current) }))
        .then(() => updateFromApi(apiInstance))
        .catch(reason => setError(reason.message));
    });
    apiInstance.on("set-path", ({ id }) => pathChanged(id));
    apiInstance.on("select-file", () => setTimeout(() => updateFromApi(apiInstance), 0));
    apiInstance.on("filter-files", () => setTimeout(() => updateFromApi(apiInstance), 0));
    apiInstance.on("set-mode", ({ mode }) => setView(mode));
    setTimeout(() => updateFromApi(apiInstance), 0);
    apiInstance.intercept("create-file", ({ file, parent: parentId }) => {
      const path = localPath(parentId);
      if (file?.file instanceof File) void uploadFiles([file.file], path);
      else if (file?.type === "folder") void createFolderAt(path, file.name);
      else setError("새 파일은 업로드 기능으로 추가하세요.");
      return false;
    });
    apiInstance.intercept("rename-file", ({ id }) => { void renameItem(id); return false; });
    apiInstance.intercept("move-files", ({ ids, target }) => { void moveItems(ids, localPath(target)); return false; });
    apiInstance.intercept("copy-files", ({ ids, target }) => { void copyItems(ids, localPath(target)); return false; });
    apiInstance.intercept("delete-files", ({ ids }) => { void deleteItems(ids); return false; });
    apiInstance.intercept("open-file", ({ id }) => { openItem(id); return false; });
  }, [api]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !initialData) return undefined;
    // ponytail: SVAR 2.6 exposes no drag-to-folder action, so this uses its item classes until the package offers a public DnD hook.
    const markDraggable = () => host.querySelectorAll(".wx-cards .wx-item[data-id], .wx-folder[data-id], .wx-list .wx-row[data-id]").forEach(node => {
      const id = node.getAttribute("data-id");
      if (id && fmRef.current?.getFile(id)?.type) node.setAttribute("draggable", "true");
    });
    const markTreeToggles = () => host.querySelectorAll(".wx-tree .wx-folder[data-id]").forEach(node => {
      const id = node.getAttribute("data-id")?.replace(/^:/, "");
      const item = id && fmRef.current?.getFile(id);
      const toggle = node.querySelector(".wx-toggle-placeholder");
      if (!toggle) return;
      if (item?.lazy) {
        toggle.classList.add("explorer-tree-toggle");
        toggle.setAttribute("role", "button");
        toggle.setAttribute("tabindex", "0");
        toggle.setAttribute("aria-expanded", String(Boolean(item.open)));
        toggle.setAttribute("aria-label", `${item.name} 하위 폴더 ${item.open ? "접기" : "펼치기"}`);
      } else {
        toggle.classList.remove("explorer-tree-toggle");
        toggle.removeAttribute("role");
        toggle.removeAttribute("tabindex");
        toggle.removeAttribute("aria-expanded");
        toggle.removeAttribute("aria-label");
      }
    });
    // ponytail: SVAR 2.6 has no date-cell formatter prop; remove this when it exposes one.
    const formatDates = () => host.querySelectorAll(".wx-list .wx-row[data-id]").forEach(row => {
      const id = row.getAttribute("data-id")?.replace(/^:/, "");
      const date = id && fmRef.current?.getFile(id)?.date;
      const cell = row.querySelector('[data-col-id=":date"]');
      const formatted = dateText(date);
      if (date && cell && cell.textContent !== formatted) cell.textContent = formatted;
    });
    const syncView = () => {
      markDraggable();
      markTreeToggles();
      formatDates();
    };
    // ponytail: SVAR 2.6 has no lazy-tree expansion hook; remove this when it adds one.
    const toggleLazyFolder = event => {
      if (!(event.target instanceof Element)) return;
      const toggle = event.target.closest(".explorer-tree-toggle");
      if (!toggle || (event.type === "keydown" && !["Enter", " "].includes(event.key))) return;
      const id = toggle.closest(".wx-folder[data-id]")?.getAttribute("data-id")?.replace(/^:/, "");
      const item = id && fmRef.current?.getFile(id);
      if (!item?.lazy) return;
      event.preventDefault();
      event.stopPropagation();
      const mode = !item.open;
      toggle.setAttribute("aria-expanded", String(mode));
      toggle.setAttribute("aria-label", `${item.name} 하위 폴더 ${mode ? "접기" : "펼치기"}`);
      void fmRef.current.exec("open-tree-folder", { id, mode });
      if (mode) void fmRef.current.exec("request-data", { id }).then(() => {
        const folder = fmRef.current?.getFile(id);
        if (!folder?.data?.some(child => child.type === "folder")) return fmRef.current.exec("open-tree-folder", { id, mode: false });
      }).then(syncView);
    };
    host.addEventListener("click", toggleLazyFolder, true);
    host.addEventListener("keydown", toggleLazyFolder, true);
    syncView();
    const observer = new MutationObserver(syncView);
    observer.observe(host, { childList: true, subtree: true, characterData: true });
    return () => {
      observer.disconnect();
      host.removeEventListener("click", toggleLazyFolder, true);
      host.removeEventListener("keydown", toggleLazyFolder, true);
    };
  }, [initialData, view]);

  async function dropMove(event) {
    const ids = event.dataTransfer.getData("application/x-daalgi-entries").split("\n").filter(Boolean);
    const targetNode = event.target instanceof Element ? event.target.closest("[data-id]") : null;
    const targetId = targetNode?.getAttribute("data-id");
    const target = targetId === "body" ? currentPath : fmRef.current?.getFile(targetId)?.type === "folder" ? localPath(targetId) : null;
    if (ids.length && target !== null) {
      event.preventDefault();
      await moveItems(ids, target);
    }
  }

  function onDragStart(event) {
    const node = event.target instanceof Element ? event.target.closest("[data-id]") : null;
    const id = node?.getAttribute("data-id");
    if (!id || !fmRef.current?.getFile(id)) return;
    const ids = selectedRef.current.includes(id) ? selectedRef.current : [id];
    event.dataTransfer.setData("application/x-daalgi-entries", ids.join("\n"));
    event.dataTransfer.effectAllowed = "move";
  }

  function onDragOver(event) {
    if (![...event.dataTransfer.types].includes("application/x-daalgi-entries")) return;
    const node = event.target instanceof Element ? event.target.closest("[data-id]") : null;
    const id = node?.getAttribute("data-id");
    if (id === "body" || fmRef.current?.getFile(id)?.type === "folder") {
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
    }
  }

  function handleKeyDown(event) {
    const target = event.target;
    if (target instanceof Element && target.closest("input, textarea, select, [contenteditable='true']")) return;
    const key = event.key.toLowerCase();
    const command = event.ctrlKey || event.metaKey;
    if (event.altKey && key === "arrowleft") { event.preventDefault(); event.stopPropagation(); back(); return; }
    if (event.altKey && key === "arrowright") { event.preventDefault(); event.stopPropagation(); forward(); return; }
    if (event.altKey && key === "arrowup") { event.preventDefault(); event.stopPropagation(); if (currentPath) goTo(svarPath(parent(currentPath))); return; }
    if (key === "backspace") { event.preventDefault(); event.stopPropagation(); if (currentPath) back(); return; }
    if (key === "f2" && selectedRef.current.length === 1) { event.preventDefault(); event.stopPropagation(); renameItem(selectedRef.current[0]); return; }
    if (key === "delete" && selectedRef.current.length) { event.preventDefault(); event.stopPropagation(); deleteItems(selectedRef.current); return; }
    if (command && key === "x") { event.preventDefault(); event.stopPropagation(); cutItems(selectedRef.current); return; }
    if (command && key === "c") { event.preventDefault(); event.stopPropagation(); copyToClipboard(selectedRef.current); return; }
    if (command && key === "v") { event.preventDefault(); event.stopPropagation(); void pasteInto(); }
  }

  function changeSort(key) {
    const order = sortKey === key ? (sortOrder === "asc" ? "desc" : "asc") : "asc";
    setSortKey(key);
    setSortOrder(order);
    fmRef.current?.exec("sort-files", { key, order, path: svarPath(currentPath) });
  }

  const selectedItems = selectedIds.map(id => fmRef.current?.getFile(id)).filter(Boolean);
  const selectedItem = selectedItems.length === 1 ? selectedItems[0] : null;
  const selectedPath = selectedItem ? localPath(selectedItem.id) : "";
  const selectedDocument = selectedPath && selectedItem?.type === "file" ? getDocument(documents, selectedPath) : null;
  const realItems = currentItems.filter(item => item.type === "file" || item.type === "folder");
  const selectedSize = selectedItems.reduce((total, item) => total + (item.type === "file" ? item.size || 0 : 0), 0);
  const root = roots.find(item => item.id === rootId);
  const history = historyRef.current;

  return <section className="management-panel document-manager explorer-page" onKeyDown={handleKeyDown}>
    <div className="explorer-heading"><h2>문서</h2>{root && roots.length === 1 && <span>{root.label}</span>}</div>
    {error && <p className="notice error" role="alert">{error}</p>}
    {message && <p className="notice success" role="status">{message}</p>}
    {!roots.length ? <p className="explorer-empty">관리할 문서 폴더가 서버에 설정되어 있지 않습니다.</p> : !initialData || dataRootId !== rootId ? <p className="explorer-empty">문서 폴더를 불러오는 중입니다.</p> : <>
      <div className="explorer-commandbar" role="toolbar" aria-label="파일 탐색기 명령">
        <div className="explorer-nav-buttons">
          <button type="button" title="뒤로" aria-label="뒤로" disabled={history.index === 0} onClick={back}><Icon name="back" /></button>
          <button type="button" title="앞으로" aria-label="앞으로" disabled={history.index >= history.paths.length - 1} onClick={forward}><Icon name="forward" /></button>
          <button type="button" title="위로" aria-label="위로" disabled={!currentPath} onClick={() => goTo(svarPath(parent(currentPath)))}><Icon name="up" /></button>
        </div>
        {roots.length > 1 && <label className="explorer-root"><span className="sr-only">문서 저장소</span><select value={rootId} disabled={busy} onChange={event => setRootId(event.target.value)}>{roots.map(item => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>}
        <div className="explorer-command-separator" />
        <button type="button" onClick={() => void createFolderAt(currentPath)} disabled={busy}><Icon name="folder" /><span>새 폴더</span></button>
        <button type="button" onClick={() => cutItems(selectedIds)} disabled={!selectedIds.length || busy}><Icon name="cut" /><span>잘라내기</span></button>
        <button type="button" onClick={() => copyToClipboard(selectedIds)} disabled={!selectedIds.length || busy}><Icon name="copy" /><span>복사</span></button>
        <button type="button" onClick={() => void pasteInto()} disabled={!clipboard.ids.length || busy}><Icon name="paste" /><span>붙여넣기</span></button>
        <button type="button" onClick={() => selectedIds.length === 1 && renameItem(selectedIds[0])} disabled={selectedIds.length !== 1 || busy}><Icon name="rename" /><span>이름 바꾸기</span></button>
        <button type="button" onClick={() => deleteItems(selectedIds)} disabled={!selectedIds.length || busy}><Icon name="delete" /><span>삭제</span></button>
        <label className="explorer-sort"><Icon name="sort" /><span>정렬</span><select aria-label="정렬" value={sortKey} onChange={event => changeSort(event.target.value)}><option value="name">이름</option><option value="date">수정한 날짜</option><option value="size">크기</option></select></label>
        <div className="explorer-view-toggle" aria-label="보기">
          <button type="button" aria-pressed={view === "table"} title="자세히" onClick={() => fmRef.current?.exec("set-mode", { mode: "table" })}><Icon name="list" /><span>자세히</span></button>
          <button type="button" aria-pressed={view === "cards"} title="큰 아이콘" onClick={() => fmRef.current?.exec("set-mode", { mode: "cards" })}><Icon name="cards" /><span>큰 아이콘</span></button>
        </div>
        <button type="button" className="explorer-upload" onClick={() => uploadRef.current?.click()} disabled={busy}>업로드</button>
        <input ref={uploadRef} className="sr-only" type="file" accept=".docx,.hwp,.hwpx,.pptx,.pdf" multiple onChange={event => {
          if (event.target.files?.length) void uploadFiles(event.target.files);
          event.target.value = "";
        }} />
      </div>
      <div className="explorer-workspace" ref={hostRef} onDragStart={onDragStart} onDragOver={onDragOver} onDrop={event => void dropMove(event)}>
        <div className="explorer-filemanager">
          <Locale words={koWords}>
            <Willow>
              <Filemanager key={rootId} ref={fmRef} init={init} data={initialData} mode={view} panels={ROOT_PANELS} activePanel={0} preview={false} menuOptions={menuOptions} icons={entryIcon} />
            </Willow>
          </Locale>
        </div>
        <aside className="explorer-details" aria-label="세부 정보">
          <header><Icon name="details" /><h3>세부 정보</h3></header>
          {!selectedItems.length ? <p className="explorer-detail-empty">항목을 선택하면 세부 정보가 표시됩니다.</p> : selectedItem ? <>
            <div className="explorer-detail-title"><img src={entryIcon(selectedItem, "big")} alt="" /><div><strong>{selectedItem.name}</strong><span>{selectedItem.type === "folder" ? "폴더" : "파일"}</span></div></div>
            <dl>
              <dt>유형</dt><dd>{selectedItem.type === "folder" ? "폴더" : ({ pdf: "PDF 문서", docx: "Word 문서 (DOCX)", hwp: "한글 문서 (HWP)", hwpx: "한글 문서 (HWPX)", pptx: "PowerPoint 문서" })[selectedItem.ext] || "문서"}</dd>
              <dt>크기</dt><dd>{selectedItem.type === "folder" ? "—" : formatSize(selectedItem.size)}</dd>
              <dt>수정한 날짜</dt><dd>{dateText(selectedItem.date)}</dd>
              <dt>경로</dt><dd className="explorer-detail-path">{root?.label}{selectedPath ? `/${selectedPath}` : ""}</dd>
              {selectedItem.type === "file" && <><dt>RAG 상태</dt><dd>{selectedDocument?.status || "미등록"}</dd><dt>조각 수</dt><dd>{selectedDocument?.fragment_count ?? 0}</dd></>}
            </dl>
            {selectedItem.type === "file" && <div className="explorer-detail-actions">
              {!selectedDocument ? <button type="button" onClick={() => void registerRag(selectedPath)} disabled={busy}>RAG 등록</button> : <>
                <button type="button" onClick={() => void reprocess(selectedDocument)} disabled={busy}>다시 처리</button>
                <button type="button" onClick={() => void openOriginal(selectedDocument)} disabled={busy}>원문 보기</button>
              </>}
            </div>}
          </> : <p className="explorer-detail-empty">{selectedItems.length}개 항목을 선택했습니다.</p>}
        </aside>
      </div>
      <footer className="explorer-statusbar">
        <span>항목 {realItems.length}개</span>
        {selectedItems.length > 0 && <span>{selectedItems.length}개 항목 선택함{selectedItems.some(item => item.type === "file") && ` · ${formatSize(selectedSize)}`}</span>}
      </footer>
    </>}
  </section>;
}
