import { useEffect, useMemo, useRef, useState } from "react";
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation } from "d3-force";
import "./link-graph.css";

const statusColor = { approved: "#4b8b68", draft: "#b7922f", rejected: "#b8564b" };

function graphData(links) {
  const nodes = new Map(), pairs = new Map();
  for (const link of links) {
    const source = link.source_document_id, target = link.target_document_id;
    if (!source || !target) continue;
    nodes.set(source, { id: source, label: link.source_filename || "문서" });
    nodes.set(target, { id: target, label: link.target_filename || "문서" });
    const [left, right] = [source, target].sort();
    const key = `${left}:${right}`;
    if (!pairs.has(key)) pairs.set(key, { id: key, source: left, target: right, links: [], statuses: {} });
    const pair = pairs.get(key);
    pair.links.push(link);
    pair.statuses[link.status] = (pair.statuses[link.status] || 0) + 1;
  }
  return {
    nodes: [...nodes.values()],
    edges: [...pairs.values()].map(edge => ({
      ...edge,
      status: Object.entries(edge.statuses).sort((a, b) => b[1] - a[1])[0]?.[0] || "draft",
    })),
  };
}

export function LinkGraph({ links, onSelect }) {
  const svgRef = useRef(null), simulationRef = useRef(null), pointerRef = useRef(null), movedRef = useRef(false);
  const [positions, setPositions] = useState({});
  const [view, setView] = useState({ x: 0, y: 0, scale: 1 });
  const { nodes, edges } = useMemo(() => graphData(links), [links]);

  useEffect(() => {
    if (!nodes.length) { setPositions({}); return undefined; }
    const simulationNodes = nodes.map(node => ({ ...node, r: 16 }));
    const simulationEdges = edges.filter(edge => edge.source !== edge.target)
      .map(edge => ({ source: edge.source, target: edge.target }));
    const simulation = forceSimulation(simulationNodes)
      .force("link", forceLink(simulationEdges).id(node => node.id).distance(150).strength(0.7))
      .force("charge", forceManyBody().strength(-520))
      .force("center", forceCenter(500, 290))
      .force("collide", forceCollide(node => node.r + 42));
    simulationRef.current = { simulation, nodes: simulationNodes };
    simulation.on("tick", () => setPositions(Object.fromEntries(simulationNodes.map(node => [node.id, { x: node.x, y: node.y }]))));
    return () => {
      simulation.stop();
      if (simulationRef.current?.simulation === simulation) simulationRef.current = null;
    };
  }, [nodes, edges]);

  function point(event) {
    const rect = svgRef.current.getBoundingClientRect();
    const scale = Math.min(rect.width / 1000, rect.height / 600);
    const offsetX = (rect.width - 1000 * scale) / 2, offsetY = (rect.height - 600 * scale) / 2;
    return { x: (event.clientX - rect.left - offsetX) / scale, y: (event.clientY - rect.top - offsetY) / scale };
  }
  function pointerDown(event) {
    if (event.target !== svgRef.current) return;
    const p = point(event);
    pointerRef.current = { type: "pan", x: p.x, y: p.y, viewX: view.x, viewY: view.y };
    svgRef.current.setPointerCapture(event.pointerId);
  }
  function nodePointerDown(event, nodeId) {
    event.stopPropagation();
    const node = simulationRef.current?.nodes.find(item => item.id === nodeId);
    if (!node) return;
    const p = point(event), x = (p.x - view.x) / view.scale, y = (p.y - view.y) / view.scale;
    pointerRef.current = { type: "node", id: nodeId, x: p.x, y: p.y, offsetX: node.x - x, offsetY: node.y - y };
    movedRef.current = false;
    node.fx = node.x; node.fy = node.y;
    simulationRef.current.simulation.alphaTarget(0.25).restart();
    svgRef.current.setPointerCapture(event.pointerId);
  }
  function pointerMove(event) {
    const pointer = pointerRef.current;
    if (!pointer) return;
    const p = point(event);
    if (Math.hypot(p.x - pointer.x, p.y - pointer.y) > 3) movedRef.current = true;
    if (pointer.type === "pan") {
      setView(current => ({ ...current, x: pointer.viewX + p.x - pointer.x, y: pointer.viewY + p.y - pointer.y }));
    } else {
      const node = simulationRef.current?.nodes.find(item => item.id === pointer.id);
      if (node) { node.fx = (p.x - view.x) / view.scale + pointer.offsetX; node.fy = (p.y - view.y) / view.scale + pointer.offsetY; }
    }
  }
  function pointerUp() {
    const pointer = pointerRef.current;
    if (pointer?.type === "node") {
      const node = simulationRef.current?.nodes.find(item => item.id === pointer.id);
      if (node) { node.fx = null; node.fy = null; }
      simulationRef.current?.simulation.alphaTarget(0);
    }
    pointerRef.current = null;
  }
  function zoom(event) {
    event.preventDefault();
    const p = point(event);
    setView(current => {
      const scale = Math.max(0.45, Math.min(2.6, current.scale * Math.exp(-event.deltaY * 0.001)));
      return { scale, x: p.x - (p.x - current.x) * scale / current.scale, y: p.y - (p.y - current.y) * scale / current.scale };
    });
  }

  const position = id => positions[id] || { x: 500, y: 290 };
  function choose(edge) {
    onSelect({ label: `${nodes.find(node => node.id === edge.source)?.label || "문서"} ↔ ${nodes.find(node => node.id === edge.target)?.label || "문서"}`, ids: edge.links.map(link => link.id) });
  }

  return <div className="link-graph">
    <div className="link-graph-hint">휠로 확대·축소 · 배경을 끌어 이동 · 문서를 끌어 배치</div>
    {!nodes.length ? <p className="empty-state">표시할 연결이 없습니다.</p> : <svg ref={svgRef} viewBox="0 0 1000 600" role="img" aria-label="문서 연결 그래프"
      onPointerDown={pointerDown} onPointerMove={pointerMove} onPointerUp={pointerUp} onPointerCancel={pointerUp} onWheel={zoom}>
      <g transform={`translate(${view.x} ${view.y}) scale(${view.scale})`}>
        {edges.map(edge => {
          const a = position(edge.source), b = position(edge.target), width = Math.min(2 + edge.links.length * 1.25, 10);
          const self = edge.source === edge.target;
          return <g key={edge.id} className="link-graph-edge" role="button" tabIndex="0" aria-label={`${edge.links.length}건 연결 선택`}
            onPointerDown={event => event.stopPropagation()} onClick={() => choose(edge)}
            onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); choose(edge); } }}>
            <title>{`${edge.links.length}건 · ${edge.status}`}</title>
            {self ? <path d={`M ${a.x} ${a.y - 14} C ${a.x + 90} ${a.y - 110}, ${a.x + 100} ${a.y + 110}, ${a.x} ${a.y + 14}`} stroke={statusColor[edge.status]} strokeWidth={width} fill="none" />
              : <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={statusColor[edge.status]} strokeWidth={width} />}
            <circle cx={(a.x + b.x) / 2} cy={(a.y + b.y) / 2} r="12" fill="transparent" />
          </g>;
        })}
        {nodes.map(node => {
          const p = position(node.id), label = node.label.length > 22 ? `${node.label.slice(0, 21)}…` : node.label;
          const incident = links.filter(link => link.source_document_id === node.id || link.target_document_id === node.id);
          return <g key={node.id} className="link-graph-node" role="button" tabIndex="0" aria-label={`${node.label} 연결 선택`}
            transform={`translate(${p.x} ${p.y})`} onPointerDown={event => nodePointerDown(event, node.id)} onPointerUp={pointerUp}
            onClick={() => { if (!movedRef.current) onSelect({ label: node.label, ids: incident.map(link => link.id) }); }}
            onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect({ label: node.label, ids: incident.map(link => link.id) }); } }}>
            <title>{node.label}</title><circle r="17" />
            <rect x="-69" y="25" width="138" height="24" rx="6" />
            <text y="41">{label}</text>
          </g>;
        })}
      </g>
    </svg>}
    <div className="link-graph-legend" aria-label="연결 상태 범례">
      <span><i className="approved" />승인됨</span><span><i className="draft" />승인 대기</span><span><i className="rejected" />반려됨</span>
      <span className="link-graph-count">선 굵기 = 연결 수</span>
    </div>
  </div>;
}
