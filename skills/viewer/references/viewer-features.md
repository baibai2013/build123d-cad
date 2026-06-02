# cad-viewer 功能复刻清单

> cad SPA 的功能由 cad-viewer 原作者实现并打包在 dist 里。本文档登记我们消费的关键功能,
> 升级 dist 时回头核对这些功能是否还在。

## 已具备(P0 ready,继承自 cad-viewer)

- STEP / STL / GLB / 3MF 加载
- URDF / SRDF / SDF 解析 + 关节滑块(joint sliders)
- G-code 轨迹可视化(toolpath ribbon,按速度 / 层着色)
- DXF 2D 平面查看
- 截面(section view)
- 测量(distance / angle)
- 摄像机视角 deep-link(URL hash)
- 暗色 / 亮色主题(localStorage 持久化)

## URL hash 协议(由 cad SPA 自管,不在 server)

```
#frame=base_link&joint=hip:0.5&joint=knee:-0.3&camera=...
```

cad-viewer 原作者维护;升级时如果 hash 协议变,需要在 04(urdf)+ 05(gcode)同步。

## 不复刻

- ❌ 服务端 SSR(用不到,父 server 静态 serve 就够)
- ❌ 多文件 workspace 浏览(我们用 `?dir=&file=` 单文件)
- ❌ cad-viewer 的鉴权 / 多用户(单机单租户)
