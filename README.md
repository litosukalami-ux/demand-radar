# 需求雷达（GitHub Actions 版）

每天 9:00（北京时间）自动采集 → 打分 → 生成《需求日报》，跑在 GitHub 上，不依赖你的电脑开机。

## 它每天做什么

1. **热度**：App Store 中国区免费/付费榜（公开接口）+ 微博热搜 + B站排行榜
2. **抱怨**：App Store 常见类目 App 的最新差评（1-2 星）
3. **打分**：证据强度 / 痛点密度 / 付费迁移信号 / 可行动性，各 0-3 分 × 触达系数
4. **产出**：`digest/YYYY-MM-DD.md` 和 `digest/最新.md`，同时提交回仓库

## 部署（5 分钟）

1. 在 GitHub 新建一个仓库（public 或 private 都行）
2. 把本文件夹整个上传上去（网页版：Add file → Upload files，把整个「需求雷达」文件夹拖进去）
3. 仓库 Settings → Secrets and variables → Actions → New repository secret
   - Name: `DEEPSEEK_API_KEY`
   - Value: 你的 DeepSeek API Key（没有的话也能跑，只是日报变成规则版摘要）
4. 打开 Actions 标签，启用 workflow；点一次 `Run workflow` 手动试跑
5. 之后每天 01:00 UTC（= 09:00 北京时间）自动跑

## 看日报

- 直接在 GitHub 仓库里打开 `digest/最新.md`
- 想更好看：Settings → Pages → Branch 选 `main` / `root`，之后可以访问 `https://<你的用户名>.github.io/<仓库名>/digest/最新.md`

## 说明

- **GitHub runner 在海外**：App Store、微博、B站接口通常可用；抖音、豆瓣、小红书这些海外 IP 容易被风控，所以云端版不抓它们（本地 DSH 任务继续抓）。失败会记录在采集文件的 errors 里，不中断。
- 日报内容按「10 条主流 + 3 条小众 + 5 条待验证」生成，每条带热度位置、抱怨原话、付费证据、可做的第一个小交付。
