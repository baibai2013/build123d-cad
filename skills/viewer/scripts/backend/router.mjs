// router.mjs — 纯函数,后缀 → 引擎 路由
// 规格见 share/build123d-cad改造/03-viewer多引擎子技能.md §4 / §4.1
//
// 22 条目权威路由表。任何加/删/改一行,必须同步:
//   ① 03 §4.1 表(单一权威源)
//   ② shared/CHANGELOG.md(跨技能影响登记)
//   ③ tests/test_routing.py(单测覆盖)
//
// 扩支持新格式 = 在 ENGINE_ROUTES 加一行 + 在 engines/<name>/ 放静态文件,不改 server.mjs。
// 本模块零依赖,可直接 node 跑或 import 单测。

export const ENGINE_ROUTES = [
  // ===== cad engine(P0/P1:3D + 2D + URDF 家族 + 工艺 + 图片)=====
  { ext: ['.step', '.stp'],                         engine: 'cad' },  // P0 OCC native
  { ext: ['.brep'],                                 engine: 'cad' },  // P0 OCCT 边界表示
  { ext: ['.iges', '.igs'],                         engine: 'cad' },  // P1
  { ext: ['.stl'],                                  engine: 'cad' },  // P0
  { ext: ['.glb', '.gltf'],                         engine: 'cad' },  // P0 GLTFLoader
  { ext: ['.obj'],                                  engine: 'cad' },  // P1 OBJLoader
  { ext: ['.3mf'],                                  engine: 'cad' },  // P0 3MFLoader
  { ext: ['.fcstd'],                                engine: 'cad' },  // P3 FreeCAD CLI 转 STEP
  { ext: ['.urdf', '.srdf'],                        engine: 'cad' },  // P0 urdf-loader-three
  { ext: ['.sdf'],                                  engine: 'cad' },  // P1 sdf2urdf 桥接
  { ext: ['.gcode', '.nc'],                         engine: 'cad' },  // P0 toolpath ribbon
  { ext: ['.dxf'],                                  engine: 'cad' },  // P0 dxf-parser + Canvas
  { ext: ['.png', '.jpg', '.jpeg', '.webp'],        engine: 'cad' },  // P0 raw image inline (?mode=image)

  // ===== pcb engine(P3 占位)=====
  { ext: ['.kicad_pcb'],                            engine: 'pcb' },  // P3 tracespace + kicad-cli gltf 桥接
  { ext: ['.gbr', '.ger', '.drl', '.gtl', '.gbl'],  engine: 'pcb' },  // P3 tracespace 纯 web Gerber

  // ===== sch engine(P3 占位)=====
  { ext: ['.kicad_sch', '.sch'],                    engine: 'sch' },  // P3 KiCanvas
  { ext: ['.svg'],                                  engine: 'sch' },  // P3 inline + 缩放(原理图导出场景)

  // ===== sim engine(仿真回放:frame scrubber + canvas 曲线 + checks 徽章)=====
  // '.results.json' 必须排在 '.json' ambiguous 之前(endsWith 顺序匹配,同 '.circuit.json')。
  { ext: ['.results.json'],                         engine: 'sim' },  // simulation 时序回放仪表盘
  { ext: ['.csv'],                                  engine: 'sim' },  // 时序 CSV 表格
  { ext: ['.mp4', '.webm'],                         engine: 'sim' },  // HTML5 video 录屏

  // ===== tscircuit engine(M2:RunFrame 直引,PCB/原理图/3D + BOM/总价面板)=====
  // 必须排在 '.json' 之前:routeByExtension 按 endsWith 顺序匹配,
  // <board>.circuit.json 先命中 tscircuit,不落到 .json 的 'ambiguous'。
  { ext: ['.circuit.json'],                         engine: 'tscircuit' },  // M2 单文件 RunFrame bundle

  // .json 后缀冲突(urdf 轨迹回放 ↔ 通用配置):router 不 sniff,
  // routeByExtension 返 'ambiguous',要求调用方 ?engine=sim 显式透传,否则 server 回 409。
  { ext: ['.json'],                                 engine: 'ambiguous' },
];

export const SUPPORTED_ENGINES = ['cad', 'pcb', 'sch', 'sim', 'tscircuit'];

// 把所有后缀拍平,给 server.mjs 的文件代理白名单用(去掉 'ambiguous' 哨兵也没事,白名单只查后缀)
export const SUPPORTED_EXTENSIONS = (() => {
  const set = new Set();
  for (const { ext } of ENGINE_ROUTES) ext.forEach(e => set.add(e));
  // urdf/srdf 配套配置文件(.json 已在 ENGINE_ROUTES 里)
  set.add('.yaml'); set.add('.yml');
  return Array.from(set).sort();
})();

/**
 * 后缀 → engine 名。
 * @returns {'cad'|'pcb'|'sch'|'sim'|'ambiguous'|null}
 *   - 已支持后缀返回引擎名;
 *   - '.json' 返回 'ambiguous'(server 据此回 409 + 提示需 ?engine= 透传);
 *   - 未知后缀返回 null(server 据此回 400 + 列全部支持后缀)。
 */
export function routeByExtension(filePath) {
  if (filePath == null) return null;
  const lower = String(filePath).toLowerCase();
  for (const { ext, engine } of ENGINE_ROUTES) {
    if (ext.some(e => lower.endsWith(e))) return engine;
  }
  return null;
}

export function listSupportedExtensions() {
  return ENGINE_ROUTES.flatMap(r => r.ext);
}
