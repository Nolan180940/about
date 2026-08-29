# about

个人主页（about 页面），由 GitHub Profile README 自动生成。

## 工作原理

```
Nolan180940/Nolan180940 仓库
└── README.zh.md          ← 唯一内容源（在这里编辑内容）
        │
        ▼
scripts/build.py          ← 拉取 README → 渲染成 index.html
        │
        ▼
index.html                ← 本仓库的静态页面（自动生成，勿手改）
```

## 本地构建

```bash
# 从 GitHub 拉取最新 README 并生成 index.html
python scripts/build.py

# 使用本地 README.zh.md（调试用）
python scripts/build.py --local
```

## 自动同步

`.github/workflows/build.yml` 会在以下时机自动重建 `index.html`：

| 触发方式 | 说明 |
|---|---|
| push 到 main（scripts/ 或 README.zh.md 变更） | 本仓库内改动 |
| 手动触发（workflow_dispatch） | GitHub Actions 页面点 Run workflow |
| repository_dispatch（rebuild-about） | 由 profile 仓库 push README 触发 |
| 每日定时（UTC 02:00） | 兜底同步 |

### 启用「改 README 自动同步」

1. 在 `Nolan180940/Nolan180940` 仓库 Settings → Secrets and variables → Actions 添加：
   - `ABOUT_REPO_TOKEN`：一个有 `repo` 权限的 PAT（Personal Access Token）
2. 把 `.github/workflows/trigger-from-profile.yml` 复制到 `Nolan180940/Nolan180940` 仓库的 `.github/workflows/` 目录

之后每次 push `README.zh.md`，about 页面会在几分钟内自动更新。

## 文件结构

```
├── index.html                    ← 构建产物（自动生成）
├── README.zh.md                  ← 本地副本（调试用，可选）
├── scripts/
│   └── build.py                  ← 构建脚本（Markdown → HTML）
└── .github/workflows/
    ├── build.yml                 ← about 仓库自动构建
    └── trigger-from-profile.yml  ← 复制到 profile 仓库的触发文件
```
