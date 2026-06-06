import React from "react"
import { createRoot } from "react-dom/client"
import { CircuitJsonPreview } from "@tscircuit/runframe/preview"

const q = new URLSearchParams(location.search)
const DIR = q.get("dir") || ""
const FILE = q.get("file")
const filesUrl = (f) => `/files/${encodeURIComponent(f)}?dir=${encodeURIComponent(DIR)}`

function useJson(file) {
  const [data, setData] = React.useState(null)
  const [err, setErr] = React.useState(null)
  React.useEffect(() => {
    if (!file) return
    fetch(filesUrl(file))
      .then(r => r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status)))
      .then(setData).catch(e => setErr(String(e)))
  }, [file])
  return [data, err]
}

function bomToCsv(bom) {
  const head = ["Designator", "Value", "Footprint", "LCSC", "Qty", "UnitPrice", "LineTotal"]
  const rows = bom.items.map(i => [i.ref, i.value, i.footprint, i.lcsc, i.qty,
    i.unit_price ?? "", i.line_total ?? ""])
  return [head, ...rows].map(r => r.join(",")).join("\n")
}

function BomPanel({ bom }) {
  if (!bom) return (
    <div style={{ padding: 12, font: "13px system-ui", color: "#666" }}>
      无 <code>.bom.json</code> sidecar。<br />运行 <code>pcb/scripts/bom_price.py</code> 生成报价。
    </div>
  )
  const download = () => {
    const url = URL.createObjectURL(new Blob([bomToCsv(bom)], { type: "text/csv" }))
    const a = document.createElement("a"); a.href = url
    a.download = (FILE || "board").replace(/\.(circuit\.)?json$/, "") + "-bom.csv"
    a.click(); URL.revokeObjectURL(url)
  }
  const priced = bom.priced_via === "jlcpcb-mcp"
  return (
    <div style={{ font: "13px system-ui", height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "10px 12px", borderBottom: "1px solid #eee", display: "flex",
        alignItems: "center", justifyContent: "space-between" }}>
        <b>BOM · 嘉立创报价</b>
        <button onClick={download} style={{ font: "12px system-ui", cursor: "pointer" }}>下载 CSV</button>
      </div>
      <div style={{ overflow: "auto", flex: 1 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead><tr style={{ textAlign: "left", color: "#888" }}>
            <th style={{ padding: 6 }}>位号</th><th>值</th><th>LCSC</th><th>库存</th><th style={{ textAlign: "right" }}>单价</th>
          </tr></thead>
          <tbody>{bom.items.map((i, k) => (
            <tr key={k} style={{ borderTop: "1px solid #f0f0f0" }}>
              <td style={{ padding: 6 }}>{i.ref}</td><td>{String(i.value)}</td>
              <td><code>{i.lcsc || "—"}</code></td>
              <td style={{ color: i.available ? "#1a7" : "#c33" }}>{i.available === undefined ? "—" : (i.available ? "有" : "缺")}</td>
              <td style={{ textAlign: "right" }}>{i.unit_price != null ? "$" + i.unit_price : "—"}</td>
            </tr>))}</tbody>
        </table>
      </div>
      <div style={{ padding: "10px 12px", borderTop: "2px solid #eee", background: "#fafafa" }}>
        <div>板数 ×{bom.board_qty}</div>
        <div style={{ fontSize: 16, marginTop: 4 }}>
          物料总价:<b>{priced ? `$${bom.material_total} ${bom.currency}` : "未定价"}</b>
        </div>
        <div style={{ color: "#999", fontSize: 11, marginTop: 2 }}>
          {priced ? "经 jlcpcb-mcp 免 key 物料报价" : `priced_via=${bom.priced_via}`};板费另计(需 key)
        </div>
      </div>
    </div>
  )
}

function App() {
  const [open, setOpen] = React.useState(true)
  const [cj, cjErr] = useJson(FILE)
  const bomFile = FILE ? FILE.replace(/\.(circuit\.)?json$/, "") + ".bom.json" : null
  const [bom] = useJson(bomFile)

  if (!FILE) return <pre style={{ color: "crimson", padding: 16 }}>缺 ?file= 参数</pre>
  if (cjErr) return <pre style={{ color: "crimson", padding: 16 }}>{cjErr}</pre>
  if (!cj) return <div style={{ padding: 16, font: "14px system-ui" }}>Loading circuit.json…</div>

  return (
    <div style={{ height: "100%", display: "flex" }}>
      <div style={{ flex: 1, minWidth: 0, position: "relative" }}>
        <CircuitJsonPreview circuitJson={cj} />
        <button onClick={() => setOpen(o => !o)} title="BOM/总价"
          style={{ position: "absolute", top: 8, left: 8, zIndex: 10, font: "12px system-ui", cursor: "pointer" }}>
          {open ? "隐藏 BOM" : "显示 BOM"}
        </button>
      </div>
      {open && <div style={{ width: 340, borderLeft: "1px solid #ddd", background: "#fff" }}>
        <BomPanel bom={bom} />
      </div>}
    </div>
  )
}
createRoot(document.getElementById("root")).render(<App />)
