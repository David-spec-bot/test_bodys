# Virtual Try-On — Body Builder MVP

参数化伪3D人体建模应用：输入身高/三围 + 照片，生成可在浏览器中旋转查看的 3D 人体模型。

---

## 功能概览

- **参数驱动建模**：输入身高、胸围、腰围、臀围，自动生成比例匹配的人体网格（`.glb`）
- **照片肤色采样**：上传正面/侧面照片，MediaPipe 自动检测人脸并采样肤色，应用到模型上
- **3D 浏览器查看器**：基于 react-three-fiber，支持鼠标旋转、缩放、平移
- **优雅降级**：没有照片时使用默认肤色；MediaPipe 未安装时自动跳过人脸检测

---

## 项目结构

```
test_bodys/
├── backend/                        Python 后端
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                 FastAPI 入口，CORS 配置
│   │   ├── config.py               路径常量、文件类型限制
│   │   ├── api/
│   │   │   └── routes.py           API 路由（generate / mesh / face）
│   │   ├── models/
│   │   │   ├── schemas.py          Pydantic 请求/响应模型
│   │   │   └── parametric_body.py  人体网格生成器（lofted rings）
│   │   └── services/
│   │       ├── measurement_mapper.py  三围 → 身体比例换算
│   │       ├── face_extractor.py      人脸检测 + 肤色采样
│   │       └── body_generator.py      端到端流水线
│   └── tests/
│       └── test_body.py            pytest 烟雾测试
│
└── frontend/                       React 前端
    ├── package.json
    ├── vite.config.js              代理 /api → localhost:8000
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx                 状态管理、提交逻辑
        ├── api.js                  fetch /api/generate
        ├── styles.css              暗色主题
        └── components/
            ├── ParameterPanel.jsx  参数表单 + 照片上传
            ├── PhotoUpload.jsx     文件选择控件
            └── ModelViewer.jsx     Three.js Canvas + OrbitControls
```

---

## 快速开始

### 环境要求

| 工具 | 版本 |
|------|------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

后端启动后访问 http://localhost:8000/health 确认运行正常。

### 2. 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

打开浏览器访问 **http://localhost:5173**

---

## API 文档

### POST `/api/generate`

生成人体 3D 模型。使用 `multipart/form-data` 格式提交。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `height_cm` | float | ✅ | 身高（80–230 cm）|
| `bust_cm` | float | ✅ | 胸围（周长，cm）|
| `waist_cm` | float | ✅ | 腰围（周长，cm）|
| `hips_cm` | float | ✅ | 臀围（周长，cm）|
| `gender` | string | | `female` / `male` / `neutral`（默认 neutral）|
| `skin_tone` | string | | 皮肤色十六进制，如 `#d8a98a`（留空则从照片采样）|
| `photo_front` | file | | 正面照，jpeg/png/webp，≤10MB |
| `photo_side` | file | | 侧面照（可选）|

**响应示例：**

```json
{
  "job_id": "63ffe8a5faae",
  "mesh_url": "/api/jobs/63ffe8a5faae/mesh",
  "face_url": "/api/jobs/63ffe8a5faae/face",
  "stats": {
    "vertices": 1646,
    "faces": 3264,
    "skin_rgb": [216, 169, 138],
    "proportions_m": {
      "height": 1.68,
      "torso_h": 0.538,
      "leg_h": 0.857,
      "shoulder_w": 0.336
    }
  }
}
```

### GET `/api/jobs/{job_id}/mesh`

返回生成的 `.glb` 文件（`model/gltf-binary`）。

### GET `/api/jobs/{job_id}/face`

返回裁剪后的人脸 PNG 图片。

---

## 运行测试

```bash
cd backend
python -m pytest tests/ -v
```

当前测试覆盖：
- 生成网格的高度误差 < 5%
- 三围越大 → 网格横向宽度越大

---

## 技术说明

### 人体网格生成原理

使用 **lofted rings** 方法构建参数化人体：

```
臀部环（hips_radius）
    ↓ 平滑过渡
腰部环（waist_radius）
    ↓ 平滑过渡
胸部环（bust_radius）
    ↓ 平滑过渡
肩部环（shoulder_width/2）
```

躯干前后方向略扁（depth_factor=0.72），四肢为锥形圆柱，头部为轻微压扁的 icosphere。

### 后续升级路径

- [ ] **接入 SMPL-X**：将 `parametric_body.py` 替换为 `smplx` 库调用，三围通过回归器映射到 10 个形状系数（β）。需在 [smpl-x.is.tue.mpg.de](https://smpl-x.is.tue.mpg.de/) 注册并下载权重（非商用免费）。
- [ ] **SHAPY 姿态估计**：从照片直接回归 β 参数，比纯三围映射更准确。
- [ ] **UV 人脸贴图**：将人脸照片投影到头部网格的 UV 坐标上（当前只做了顶点肤色）。
- [ ] **3D 服装**：叠加预制的 3D 服装网格，接入布料模拟实现自然垂感。

---

## 注意事项

- 当前人体模型为简化几何体，用于验证流水线，非解剖学精准模型
- MediaPipe 肤色采样对强烈侧光或低亮度照片效果较差，建议在均匀光照下拍照
- 生成的 `.glb` 文件存储在 `backend/storage/{job_id}/`，不随代码提交（已加入 `.gitignore`）
- SMPL-X 及 SHAPY 模型权重需单独下载，不包含在本仓库中
