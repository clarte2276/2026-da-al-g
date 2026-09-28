import { useEffect, useMemo, useState } from "react";

function formatBytes(value) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("ko-KR", { dateStyle: "short" }).format(new Date(value));
}

function normalizeRelativePath(value) {
  return String(value || "").replaceAll("\\", "/").replace(/^\/+|\/+$/g, "");
}

function pathParts(value) {
  return normalizeRelativePath(value).split("/").filter(Boolean);
}

function fileDirectory(value) {
  return pathParts(value).slice(0, -1).join("/");
}

export function FileExplorer({ files, onOpen, rootId, query }) {
  const [currentPath, setCurrentPath] = useState("");
  const searching = Boolean(query.trim());

  useEffect(() => {
    setCurrentPath("");
  }, [rootId, query]);

  const { folders, visibleFiles } = useMemo(() => {
    const folderMap = new Map();
    const directFiles = [];
    const prefix = currentPath ? `${currentPath}/` : "";

    files.forEach((file) => {
      const relativePath = normalizeRelativePath(file.relative_path);

      if (searching) {
        directFiles.push(file);
        return;
      }

      if (fileDirectory(relativePath) === currentPath) directFiles.push(file);
      if (!relativePath.startsWith(prefix)) return;

      const rest = relativePath.slice(prefix.length);
      const separator = rest.indexOf("/");
      if (separator === -1) return;

      const name = rest.slice(0, separator);
      const folderPath = `${prefix}${name}`;
      const folder = folderMap.get(folderPath) || { path: folderPath, name, count: 0 };
      folder.count += 1;
      folderMap.set(folderPath, folder);
    });

    const collator = new Intl.Collator("ko");
    return {
      folders: [...folderMap.values()].sort((left, right) => collator.compare(left.name, right.name)),
      visibleFiles: directFiles.sort((left, right) => collator.compare(
        normalizeRelativePath(left.relative_path),
        normalizeRelativePath(right.relative_path),
      )),
    };
  }, [currentPath, files, searching]);

  const breadcrumbs = pathParts(currentPath);
  const navigateTo = (index) => setCurrentPath(breadcrumbs.slice(0, index + 1).join("/"));

  return (
    <>
      <div className="explorer-toolbar">
        <div className="explorer-breadcrumbs">
          <button type="button" onClick={() => setCurrentPath("")}>문서 루트</button>
          {!searching && breadcrumbs.map((part, index) => (
            <span key={`${part}-${index}`}>
              <span aria-hidden="true">/</span>
              <button type="button" onClick={() => navigateTo(index)}>{part}</button>
            </span>
          ))}
          {searching && <span className="search-breadcrumb">검색 결과</span>}
        </div>
        <span className="explorer-stats">
          {searching ? `${visibleFiles.length}개 검색 결과` : `${folders.length}개 폴더 · ${visibleFiles.length}개 파일`}
        </span>
      </div>

      <div className="file-list">
        {!searching && currentPath && (
          <button
            type="button"
            className="folder-row parent-row"
            onClick={() => setCurrentPath(breadcrumbs.slice(0, -1).join("/"))}
          >
            <span className="folder-icon" aria-hidden="true">↩</span>
            <span className="folder-name">상위 폴더</span>
            <span className="folder-meta">뒤로 가기</span>
          </button>
        )}

        {!searching && folders.map((folder) => (
          <button
            type="button"
            className="folder-row"
            key={folder.path}
            onClick={() => setCurrentPath(folder.path)}
          >
            <span className="folder-icon" aria-hidden="true">📁</span>
            <span className="folder-name">{folder.name}</span>
            <span className="folder-meta">문서 {folder.count}개&nbsp;›</span>
          </button>
        ))}

        {visibleFiles.map((file) => (
          <article className="file-row" key={file.id}>
            <div className={`file-type file-type-${file.suffix.slice(1)}`}>{file.suffix.slice(1).toUpperCase()}</div>
            <div className="file-info">
              <strong>{file.filename}</strong>
              <small>{file.relative_path}</small>
              <span>{file.suffix} · {formatBytes(file.size_bytes)} · {formatDate(file.modified_at)}</span>
            </div>
            <div className="file-actions">
              <button type="button" onClick={() => onOpen(file, "source")}>왼쪽</button>
              <button type="button" onClick={() => onOpen(file, "target")}>오른쪽</button>
            </div>
          </article>
        ))}

        {!folders.length && !visibleFiles.length && (
          <div className="explorer-empty">{searching ? "검색된 문서가 없습니다." : "이 폴더에는 문서가 없습니다."}</div>
        )}
      </div>
    </>
  );
}


