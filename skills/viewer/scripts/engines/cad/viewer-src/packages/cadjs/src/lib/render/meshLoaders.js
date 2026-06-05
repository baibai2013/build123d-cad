import {
  renderFormatFromPath,
  RENDER_FORMAT
} from "../fileFormats.js";
import {
  loadRender3Mf,
  loadRenderGlb,
  loadRenderStl,
  peekRender3Mf,
  peekRenderGlb,
  peekRenderStl
} from "../renderAssetClient.js";

function meshBaseUrl() {
  return typeof window !== "undefined" ? window.location.href : "";
}

function isMeshFormat(format) {
  return format === RENDER_FORMAT.STL || format === RENDER_FORMAT.THREE_MF || format === RENDER_FORMAT.GLB;
}

// 资源 URL 形如 `/__cad/asset?file=/abs/path/part.glb` 时,扩展名在 query 而非 path 里,
// renderFormatFromPath 取 pathname 会丢掉它 → 误判为 fallback。这里在 path 检测失败时,
// 回看 `file` query 参数的扩展名,避免把 GLB 当 STL 解析(否则 STL 解析器读到垃圾三角形数,
// 抛 "Invalid typed array length")。URDF/机器人网格的 mesh 引用都是这种 URL 形式。
function meshFormatConsideringFileQuery(url) {
  const baseUrl = meshBaseUrl();
  const fromPath = renderFormatFromPath(url, { baseUrl });
  if (isMeshFormat(fromPath)) {
    return fromPath;
  }
  try {
    const fileParam = new URL(url, baseUrl || "http://localhost/").searchParams.get("file");
    if (fileParam) {
      return renderFormatFromPath(fileParam, { baseUrl });
    }
  } catch {
    /* 非法 URL:忽略,沿用 path 检测结果 */
  }
  return fromPath;
}

export function meshFormatFromUrl(url) {
  const format = meshFormatConsideringFileQuery(url);
  return isMeshFormat(format) ? format : RENDER_FORMAT.GLB;
}

function normalizeMeshFallback(fallback) {
  return isMeshFormat(fallback) ? fallback : RENDER_FORMAT.GLB;
}

export function resolveMeshFormatFromUrl(url, { fallback = RENDER_FORMAT.GLB } = {}) {
  const format = meshFormatConsideringFileQuery(url);
  return isMeshFormat(format) ? format : normalizeMeshFallback(fallback);
}

export function peekRenderMeshByUrl(url, options = {}) {
  const format = resolveMeshFormatFromUrl(url, options);
  if (format === RENDER_FORMAT.STL) {
    return peekRenderStl(url);
  }
  if (format === RENDER_FORMAT.THREE_MF) {
    return peekRender3Mf(url);
  }
  return peekRenderGlb(url);
}

export async function loadRenderMeshByUrl(url, options = {}) {
  const format = resolveMeshFormatFromUrl(url, options);
  if (format === RENDER_FORMAT.STL) {
    return loadRenderStl(url, options);
  }
  if (format === RENDER_FORMAT.THREE_MF) {
    return loadRender3Mf(url, options);
  }
  return loadRenderGlb(url, options);  // options 透传 unitScale(URDF 传 1)
}
