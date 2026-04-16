## 项目级规则定位

本文件是全局 `~/.claude/CLAUDE.md` 的项目级补充，不是平行规则系统。

执行顺序：
1. 先服从全局规则
2. 再应用本项目的特定约束
3. 如果项目规则与全局规则冲突，以全局规则为准
4. 项目文件只写这个仓库特有的信息，不重复搬运全局通用原则

本项目内，任务裁决、复杂度分级、验证方法、协作模式、实现流程，默认直接继承全局规则，不在这里重复定义。

## 本项目补充目标

这个仓库的项目级规则只负责两件事：

1. 指定本仓库的默认 skill 路由
2. 记录本仓库反复出现、且不能仅靠全局规则表达清楚的专项约束

如果某条规则可以放进全局文件且对多数项目成立，就不应写在这里。

## Skill routing

当用户请求与可用 skill 匹配时，优先调用 skill，不直接用临时流程替代。

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review

## 项目专项沉淀规则

只有当某个问题满足以下条件时，才应写入本文件：
- 只对本仓库成立
- 反复出现
- 影响判断或执行质量
- 不能仅靠读代码立即得出

### UI / 静态预览专项规则

1. **原生 select 不做重度美化**
   - 不修改会影响系统下拉弹层的样式
   - 禁止为了统一外观去覆盖原生下拉的展开态行为
   - 页面级 select 样式必须局部类隔离，不能写进共享基础主题

2. **共享 CSS 只放安全基础层**
   - `apple-theme.css` 这类共享文件只允许 token、颜色、排版、基础容器
   - 容易串扰的控件样式，必须放页面内局部类

3. **静态预览与 API 预览分开验证**
   - 改服务根目录前，先检查相对路径资源是否还能访问
   - 静态 `http.server` 场景下，必须验证 `manifest.json`、`other_platforms/*`、图片、favicon 都可达
   - 不能因为首页能打开，就默认其他平台正文、图片、上下文还正常

4. **布局压缩单独检查首屏密度**
   - 调整表单控件后，必须检查首屏空间利用率
   - 标签、输入框、按钮高度要一起看，不能只看单个控件是否可用

5. **修复后必须检查同类页面和同类控件**
   - 修共享样式后，必须回归相关页面
   - 修一个下拉框，必须检查所有同类下拉框和展开态

## 项目级文档维护规则

- 不在本文件重复抄写全局的任务分级、协作模式、验证原则、编码流程
- 新增项目前，先判断它是不是全局规则
- 如果是全局规则，更新 `~/.claude/CLAUDE.md` 或 `rules/common/*`
- 如果是项目特例，再写入本文件
- 出现重复规则时，优先删项目级重复项，保持项目文件短、小、专、准
