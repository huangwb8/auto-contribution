# PyPI 发布流程

本项目使用 `pyproject.toml`、setuptools 和 GitHub Actions 发布 Python 包。默认采用 PyPI Trusted Publishing，不在仓库中保存 PyPI API token。

## 前置条件

- 包版本号以 `pyproject.toml` 为唯一来源。
- GitHub Release tag 必须使用 `vX.Y.Z`，并与 `pyproject.toml` 一致，例如 `v1.1.2`。
- 需要在 PyPI 为本项目配置 Trusted Publishing：
  - Owner：`huangwb8`
  - Repository：`bensz-auto-contribution`
  - Workflow：`publish-pypi.yml`
  - Environment：`pypi`

## 本地检查

创建 release 前先运行：

```bash
python -m pip install --upgrade build twine pytest
python -m pytest -q
rm -rf dist
python -m build
python -m twine check dist/*
python -m pip install --force-reinstall dist/bensz_auto_contribution-*.whl
bac --help
```

## 发布步骤

1. 按 SemVer 更新 `pyproject.toml` 版本号。
2. 将 `CHANGELOG.md` 中对应的 `[Unreleased]` 条目移动到发布版本下。
3. 运行上方本地检查。
4. 提交 release 相关改动。
5. 创建并推送匹配 tag：

```bash
git tag vX.Y.Z
git push origin main --tags
```

6. 基于该 tag 创建 GitHub Release。
7. 发布 GitHub Release 后，`.github/workflows/publish-pypi.yml` 会构建包、检查元数据、上传构建产物并发布到 PyPI。

## 手动触发

工作流也支持 `workflow_dispatch` 手动触发。仅在 `pypi` environment 已启用审批保护时使用，因为它会把当前 `pyproject.toml` 版本发布到 PyPI。

## 失败处理

- 如果 tag 与 `pyproject.toml` 不一致，工作流会在发布前停止。
- 如果 `twine check` 失败，应先修复包元数据再重试。
- 如果 PyPI 因版本已存在而拒绝上传，需要递增版本号并创建新 release。PyPI 文件一经发布不可覆盖。
