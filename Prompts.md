# General

- 发布新版本

```
github项目：huangwb8/bensz-auto-contribution
version=1.1.2
git-commit skill保存变更; 最后一个commit要新增 tag 为 v{version}，并且该commit信息要提到更新版本； git-publish-release skill 发布为一个release到github仓库。然后，再发布到pypi上。
```

# 日常

---

基于 docs/plans/2026-05-26-bac-architecture-design.md 设计bac系统。 使用 awesome-code skill 辅助规划、优化。 不要破坏其它已经存在的功能。要保证最终成品能正常、稳定、高效地工作，让成品趋于完美。

---

本项目，我希望开发一个系统，它作为ai的一个tool，可以用来创建区分人类/ai在某个具体项目里的贡献的特殊文件，它的文件名后缀是 .bac (全称是 bensz auto contribution) 。 它应该不能被随便篡改，而只能忠实地记录ai和人类的贡献。 请使用 Init Project 为本项目进行初始化。