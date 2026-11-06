# AI分工与科研产出：研究设计

Nov 5, 2026 · @Evie Hou

## 研究问题

本研究问：文本中类似AI的信号从写作扩展到想法时，后续论文数量和引用是否出现不同变化。代码作为2025年后的扩展维度。

这里研究的是AI介入哪些环节，不直接测人在互动时的认知投入。因此结论不写成“代劳”或“讨论”。

**预期发现：**

- **假设一，quick adopter：** 控制起始条件后，早期用AI写作的人，也会更早用AI写代码和处理想法。这里检验的是跨维度的采用倾向，不主张写作导致了后续采用。
- **假设二，分工与产出：** 相对只把AI用于写作的作者，写作和想法都出现AI信号的作者，后续论文数量和引用变化不同。这里不预设数量和引用同方向变化。代码在2025年后作为扩展分析，三个维度齐备不是主分析条件。

## 研究框架

&#91;embedded content: 研究框架 · 三个时间窗口与四项分析\]

每一行是一项分析，每一列说明它如何使用该时期的数据。主分析用文字和想法信号，比较论文数量和引用；AI研究者另作单独分析。

## 测量

文字和想法从2023年起进入主分析；代码主要从2025年起进入扩展分析。想法信号最需要先验证。

| 维度 | 主要测量 | 补充信号 | 能说明什么 | 不能说明什么 |
| --- | --- | --- | --- | --- |
| 文字 | arXiv第一版全文逐篇AI文字分数 | 披露声明用于校验 | 文字可能由AI生成或修改 | AI是否参与研究本身 |
| 代码 | 2025年后的配置文件和commit署名 | 2024年信号较弱，只作描述 | 用过AI写代码 | 没有痕迹不代表没用 |
| 想法 | IdeaLens分数 | AI生成想法对照、ChatGPT前已有想法 | 论文内容接近AI常见思路 | 想法一定来自AI |

代码信号优先检查`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、`.claude/`、`.cursor/`、`.cursorrules`和`.github/copilot-instructions.md`。这些文件首次出现的时间可作为最晚采用时间，加入文件的提交者可用于个人归属。

代码维度只在能连到仓库的作者中定义。没有公开仓库时记为缺失，不记为“未使用”。

## 假设一：quick adopter

核心检验是：在相同起始概率下，早期写作者是否更快出现代码和想法信号。

1. **估计起始概率：** 只用2023年前的信息，预测作者成为早期AI写作者的概率。变量包括领域、学术年龄、发文水平和趋势、合作规模和基线代码活动。
2. **分层或匹配：** 比较概率相近的早期写作者和其他作者。
3. **比较采用速度：** 使用离散时间风险模型，因变量是首次出现代码信号或想法信号。
4. **按机会建模：** 以论文或仓库为机会单位，或固定每位作者的文档数，避免发文多的人更容易被检测到。
5. **分开测量：** 用不同论文测写作和想法，降低同一文本造成的信号污染。

结果只解释为条件相关。若仍有差异，说明存在已观测变量无法解释的跨维度采用倾向。

## 假设二：DiD设计

主设计是作者×半年面板的DiD，比较不同AI分工类型相对2018–2022年基线的变化。匹配只作为稳健性检验；若只有匹配后才满足平行趋势，再把匹配纳入主设计。

```latex
Y_{it}=\alpha_i+\lambda_{f(i),a(i,t),t}+\sum_k \beta_k\left(\text{Type}_{ik}\times\text{Post}_t\right)+\varepsilon_{it}
```

- **结果：** 数量用每半年正式发表论文数的固定效应泊松模型（PPML），同时报告分数计数和第一或末位作者计数；2023–2024年已有arXiv第一版的论文不计入结果，不论分数高低，并另做计入这些论文的稳健性检验；arXiv第一版提交量作为领先指标；引用主指标为每位作者每年的领域标准化引用总和，保留0；各队列都按带日期的施引文献统计到次年9月30日，预印本和正式版记录去重后合并引用；高被引论文数为次要指标，篇均引用只作描述；另做论文层面的同作者比较。
- **固定效应：** 作者固定效应，加上领域×学术年龄×时间固定效应。
- **分工类型：** 用2023年前的arXiv第一版按学科组校准阈值，先判断每篇论文，再按2023–2024年的被判比例定义作者类型。每人最多抽3篇arXiv第一版；因判定结果和实际篇数有机械关系，模型控制篇数×时期和暴露期arXiv论文数×时期，并单独看3篇作者。主要比较“只用于写作 vs. 都未出现”和“写作和想法都用 vs. 只用于写作”；“只用于想法”仅作探索。主阈值和替代阈值都要报告，连续分数和分箱图作稳健性检验。
- **平行趋势：** 用事件研究展示2018–2022年的动态系数。
- **稳健性：** 若改用错峰采用设定，使用Callaway-Sant'Anna或Sun-Abraham，并对平行趋势做敏感性分析。

**代码扩展：** 2025年后加入代码信号，先比较采用先后及其与文字、想法信号的关系。代码与2026年产出的关系只作初步证据，2027年数据更完整后再做正式检验。

**新入行者补充分析：** 比较2023–2024年和2019–2020年入行者在相同学术年龄的产出，并在新入行者内部比较使用类型。这部分没有前期趋势，只作描述。

**样本规则：** 结果样本为OpenAlex中的正式发表论文，包括期刊和会议论文，不含书籍，也计入作者没发到arXiv的论文。学科覆盖以arXiv为限，不限计算机，结论也限于2023–2024年发过arXiv的作者。沿用Kusumegi等人的门槛，作者需要在2018–2021年至少有4篇论文，并在2023–2024年至少有1篇可匹配、可测的arXiv第一版论文；2022年保留为前趋势检验期。主分析在作者层面排除2023年前的AI研究者，并单独分析。不按2025–2026年是否发表筛选；从作者首次发表后开始，没有发文的半年记为0，首次发表前不补0。

**作者规则：** 沿用[Kusumegi等人](https://gwern.net/doc/science/2025-kusumegi.pdf)的做法，主分析包括论文的所有作者，产出按作者参与的全部论文计算。稳健性检验包括：只把第一或末位作者算作使用者；产出只算第一或末位作者论文；产出按1/团队人数分摊；只看小团队学科；有贡献声明时只看主要写作者。

**时间解释：** 想法信号没有明确的开始时间，因此主分析不设个人采用日期。结论比较不同类型相对基线的变化，不写成“开始使用AI后的效应”。假设一只比较半年或一年尺度上的最晚可见时间。

**设计对照：** 文字信号用滚动滞后暴露或年度队列做稳健性检验，并在同一样本复现按月首次检测。只控制被检测概率不能解决问题，因为当月发文数本身就是结果。

**论文层面的价值分析：** 对2023–2024年的arXiv第一版论文，比较同一作者内部想法信号高和低的论文在固定时间窗内的领域标准化引用。作者可能把AI用于不同类型的项目，因此只解释为条件相关。

**入选和arXiv偏差：** 2023–2024年发arXiv的条件无法避免，用AI的人也可能更愿意发arXiv。我们报告入选率差异，做逆概率加权或界限分析，比较有无arXiv论文作者的基线趋势，并单独看2023年前已发arXiv的作者和arXiv覆盖率较高的作者。产出和引用计算作者的全部正式发表论文，不只算arXiv论文。

结论写法：在平行趋势假设下，不同分工类型的产出变化不同。设计本身不足以直接写成“AI分工导致了产出增长”。

## 主要风险

最需要优先处理的是检测机会差异、时间窗口重叠和个人层面的同时变化。

| 风险 | 为什么有问题 | 处理 |
| --- | --- | --- |
| 发文多更易被检出 | 会同时制造AI使用和高产出 | 用平均值或比例；固定每人文档数；按机会建模 |
| 暴露期和结果期重叠 | 同一篇论文既是原因也是结果 | 用2023–2024年定义类型，用2025–2026上半年看结果；暴露期已有arXiv第一版的论文不计入主结果 |
| 均值回归 | 要求暴露期多发文会选中短期高产者 | 不把暴露期算作DiD前期；比较2018–2022年与之后 |
| 个人同时发生变化 | 换导师、进入大团队、冲刺毕业会同时影响AI使用和产出 | 平行趋势检验；机构和合作变化检验；结论不写成确定因果 |
| 模型更新影响检测 | 新模型可能降低检出率，看起来像行为变化 | 跨年份校准；比较多个检测器；用已知模型生成文本测试 |
| 想法检测与论文质量相关 | 含糊、缺来源的文本可能被判为AI，同时也影响接收和引用 | 按领域校准；控制文本具体程度；先做效度研究 |
| 有代码样本的选择 | 样本偏向计算机领域、活跃作者和开源作者 | 报告覆盖率；结论限定在公开代码样本 |
| arXiv样本有选择 | 样本偏向arXiv活跃领域，社科和人文覆盖少；用AI也可能影响是否发arXiv | 按学科报告漏斗；比较基线趋势；结论限定样本；覆盖不足时用备选方案 |
| arXiv与OpenAlex匹配错误 | 漏匹配或重复计数会影响样本、产出和引用 | 优先用arXiv ID和DOI；抽样核查；报告匹配率；按论文家族去重 |
| arXiv政策变化 | 2025年10月后的审核和投稿规则可能压低提交量 | 主要影响领先指标；排除综述和立场论文；并用截至2025年10月前的窗口检验 |

## 文献调研

我没有找到把文字、代码和想法三个信号连到同一批科研人员后续产出的研究。这是基于本轮检索的判断，不是系统综述。现有文献分别解决了其中一段。

| 主题 | 文献 | 做法与发现 | 对本研究的用处 | 局限 | 阅读范围 |
| --- | --- | --- | --- | --- | --- |
| AI写作与产出 | [Kusumegi et al., Science 2025](https://arxiv.org/abs/2601.13187) | 用摘要文本识别LLM使用，按首次检测月做堆叠DiD，以从未检测到的作者为对照 | 科学学基准 | 依赖首次检测时点 | 正文和补充材料前100,000字符 |
| 时点批评 | [PNAS 2026](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13486544/) | 指出按首次检测定义采用时间，会产生虚假的产出增长 | 决定了本研究不用首次检测 | 全文未能打开 | 检索摘要 |
| 作者层DiD | [Filimonovic et al.](https://arxiv.org/html/2510.02408v1) | 社科作者面板，关键词识别，1:3匹配加个人和年份固定效应；发文效应2023年15%、2024年36%，前趋势通过 | 最接近假设二的设计 | 只有写作信号；使用者分类和结果都用2023–2024年 | 前100,000字符 |
| AI方法与科学 | [Hao et al., Nature 2026](https://arxiv.org/abs/2412.07727v4) | 个人发文和引用更多，但集体研究主题收缩 | 说明需要看数量以外的结果 | 测AI作为方法，不是使用分工 | 摘要和片段 |
| 分章节文字 | [Holzwarth et al.](https://arxiv.org/pdf/2608.10715) | PMC论文按章节估计LLM比例，2025年底全文89%；Discussion片段68%，Methods片段32% | 证明写作信号接近饱和，早晚差异更关键 | 语料层估计，不能逐篇判断 | 全文 |
| 代码分类器 | [Daniotti et al., Science 2026](https://arxiv.org/pdf/2506.08945) | 用分类器识别AI写的Python函数，再连到开发者产出 | 可用于描述2024年前后的代码使用 | 只覆盖Python，且不是科研样本 | 片段 |
| 代码代理痕迹 | [Khosravani & Mockus](https://arxiv.org/pdf/2606.24429) | 组合账号、commit、作者名和配置文件；配置文件精度92%，63.6%的Claude配置项目有commit痕迹 | 可直接复用检测规则 | 配置文件不等于实际使用；Copilot等工具几乎不留commit痕迹 | 全文 |
| 项目层DiD | [He et al., MSR 2026](https://arxiv.org/abs/2511.04427) | 用Cursor配置文件定义采用，匹配后做DiD；速度短暂上升，代码复杂度持续上升 | 说明配置文件可用于DiD，也提示要测质量 | 分析单位是项目，不是研究者 | 摘要 |
| 想法来源 | [IdeaLens](https://arxiv.org/pdf/2610.06778) | 用提纲测想法来源；人按AI提纲写的故事检出68%，新模型检出率降到51–79% | 提供想法信号 | 没有论文真值；发布约一个月 | 前100,000字符 |
| 论文—仓库—作者连接 | [Brown et al.](https://arxiv.org/pdf/2510.16242) | rs-graph-v1有138,596对论文和仓库；作者匹配模型F1为0.89–0.94；第一作者写代码比例69.8% | 可作为样本和作者连接的起点 | 2024年10–11月采集，缺少后续更新 | 前100,000字符 |
| 采用者差异 | [Humlum & Vestergaard](https://docs.iza.org/dp16992.pdf)、[Bick et al.](https://equitablegrowth.org/working-papers/what-work-does-generative-ai-do/) | 相似工作的人采用差异仍然很大 | 支持研究采用者异质性 | 来自工作场景的调查 | 片段 |

**对设计的三点启发：**

1. Filimonovic等人的结果说明，作者层DiD可行，但他们的分类和结果处在同一时期。本设计用分开的暴露期和结果期处理这个问题。
2. Brown等人报告预印本仓库的提交持续时间中位数只有53天，也提到存在“code dump”。这支持代码信号必须检查仓库历史，并把缺失与未使用分开。
3. 第一作者写代码的比例明显高于中间作者和末位作者。代码扩展应优先检查第一作者。

## 数据调研

主设计用arXiv第一版全文测文字和想法信号，用OpenAlex确定作者、入样门槛和正式发表结果，包括数量、节奏和引用。主测量不混用全文来源。最大的缺口是arXiv的学科覆盖、arXiv与OpenAlex的匹配、论文—仓库连接，以及把作者可靠地连到GitHub账号。

### 科学学常用数据源

[Web of Science和Scopus长期是科学学的基础数据](https://arxiv.org/pdf/2404.17663)，近年研究越来越多使用OpenAlex及基于它的SciSciNet。本项目以OpenAlex建主面板，用ORCID子样本和DBLP校验作者记录；若有权限，再用商业库做稳健性检验。

| 数据源 | 获取方式 | 优势 | 主要限制 | 本项目用途 |
| --- | --- | --- | --- | --- |
| Web of Science | 机构订阅 | 长期使用，记录和局限已被充分研究 | [覆盖偏向特定学科和地区](https://arxiv.org/pdf/2404.17663) | 若有权限，做稳健性检验 |
| Scopus | 机构订阅 | 长期使用；[Filimonovic等人的作者面板](https://arxiv.org/html/2510.02408v1)也用它 | 覆盖同样受限；原始数据通常不能公开 | 若有权限，核对作者和发文记录 |
| [OpenAlex](https://help.openalex.org/data/how-its-built/) | CC0开放，含整库下载 | 覆盖广；[实证上可与Scopus比较](https://arxiv.org/pdf/2404.17663)；[Hao等人用它并以Web of Science佐证](https://arxiv.org/html/2412.07727v4) | 个别记录有误，但已被广泛使用；[没有代码字段，可下载全文约5000万篇](https://help.openalex.org/data/works/attributes/) | 主发文和引用数据 |
| [SciSciNet](https://northwestern-cssi.github.io/sciscinet) | 开放下载；v2约2.5亿篇 | 专为科学学整理；v2基于OpenAlex，并含预计算指标 | 继承OpenAlex的错误；快照更新较慢 | 可直接取现成指标 |
| [DBLP](https://arxiv.org/abs/1806.10540v2) | CC0开放，提供数据转储 | 计算机领域专门维护；作者消歧精度和召回约0.90或更高 | 只覆盖计算机及相关领域；同名作者仍是弱点；该评估发表于2018年 | 计算机样本的作者校验 |
| Semantic Scholar | 开放API和数据集 | 覆盖广；已被用于[作者和代码身份连接实验](https://arxiv.org/pdf/2607.06183) | 大量作者缺少机构或外部ID，只靠姓名很容易误连 | 补充和交叉核对 |

### 本项目的数据拼接

| 用途 | 来源 | 覆盖与获取 | 主要限制 | 我的判断 |
| --- | --- | --- | --- | --- |
| 论文全文和LaTeX | [arXiv S3](https://info.arxiv.org/help/bulk_data_s3.html)、[OAI-PMH](https://info.arxiv.org/help/bulk_data.html) | 提供PDF和源文件；约每月更新；2025年4月全库约9.2 TB；下载者付费 | 多数论文不能二次分发；要确认S3是否含第一版，并估算所需月份的费用 | 文字和想法信号的主文本；也提取代码链接 |
| 论文—仓库连接 | [rs-graph-v1](https://arxiv.org/pdf/2510.16242) | 138,596对一对一连接，主要来自Papers with Code | 2024年10–11月采集；个人数据需申请 | 2023–2024年起点 |
| 论文—仓库连接 | [Papers with Code归档](https://www.coursera.org/articles/papers-with-code) | 公开静态归档 | 2025年7月后不更新；偏机器学习 | 补2024–2025年上半年 |
| 论文—仓库连接 | 从arXiv全文和LaTeX提取GitHub链接 | 可以自行覆盖所有目标年份 | 要区分官方仓库和被引用仓库 | 必须补做，尤其是2025下半年 |
| 作者和产出 | [OpenAlex](https://help.openalex.org/data/how-its-built/) | 作品、作者、机构、引用；CC0；持续更新 | [作者合并有错误](https://groups.google.com/g/openalex-community/c/35CB8okSaig)，近期索引也可能滞后 | 作者、入样门槛和发表结果的主数据；需要稳健性检验 |
| 作者到GitHub | [Brown et al.模型](https://arxiv.org/pdf/2510.16242) | 公开模型；非JOSS样本F1为0.89，Papers with Code子集精度1.00、召回0.81 | 短名字和组织账号容易出错 | 优先复用 |
| 代码历史 | GitHub API | 每个仓库的提交和文件历史 | 大规模采集有速率限制，已删除仓库不可得；限制未在本轮核实 | 适合样本明确后补采 |
| 全量代码基础设施 | [World of Code](https://arxiv.org/pdf/2607.06183) | V2604含58.7亿次提交；身份映射精度0.88、召回0.70 | 完整访问需申请服务器账号；临近快照截止日的提交可能不全 | 若需要作者全部仓库，值得申请 |
| 代码检测规则 | [Khosravani & Mockus](https://arxiv.org/pdf/2606.24429) | 配置文件和commit规则，论文说明发表后在Zenodo发布复现包 | 规则随工具变化；复现包当前状态未核实 | 直接参考 |
| 文字和想法检测 | [idealens](https://pypi.org/project/idealens/) | IdeaLens和ProseLens；80GB GPU可运行 | 提纲抽取有成本；代码和结果为非商业许可 | 可用，但要先做效度检验 |
| 校验 | [ICLR和EMNLP披露声明](https://arxiv.org/pdf/2608.23271) | 13,867条声明，含任务标签流程 | 只覆盖计算机顶会，也有模板化声明 | 用于校验，不作主变量 |

**建议的数据连接路径：**

1. 用2026年10月OpenAlex公开快照生成2012–2026年子集（2012–2017年只用于伪时间线），建立作者面板，并按arXiv ID、DOI和题名匹配arXiv论文；结果按多学科正式发表论文计算，文字和想法信号来自arXiv第一版。
2. 用arXiv全文、rs-graph-v1、Papers with Code和arXiv LaTeX链接得到2024–2025年的论文—仓库连接。
3. 代码扩展：用Brown等人的模型把作者连到GitHub账号，只保留高置信连接。
4. 从GitHub或World of Code提取个人的提交和配置文件历史。
5. 主分析在有arXiv第一版的作者中运行全文文字和想法检测；摘要文字信号用于比较该样本和更大样本的差异。
6. 用披露声明和ChatGPT前论文检验测量。

**发表时滞需要单独处理：** 暴露时间统一用arXiv第一版日期，不要求论文之后正式发表。正式结果按发表日期计算，arXiv提交量按第一版日期计算，用来缓解发表时滞。我们按学科报告第一版到发表的时滞，检查各组发表渠道是否变化，并用会议子样本做稳健性检验。

## 可行性与资源评估

项目可行，但应分阶段投入：作者面板和文字信号把握较大，想法信号决定论文核心能否成立。默认用Adroit本地GPU做提纲抽取，Athena和子集存储预算上限为$100。arXiv全文费用单独估算和审批。若提纲抽取用外部服务，验证和主分析情景约为$470和$2,700，不含arXiv传输和算力；真实处理量和费用要等漏斗结果。

### 各环节可行性

| 环节 | 判断 | 依据 | 最大风险 | 建议通过标准（初定） |
| --- | --- | --- | --- | --- |
| OpenAlex作者面板 | 高 | 公开快照可免费获取；已有大量研究使用 | 作者合并错误；近期索引不全 | 与ORCID或DBLP子样本核对后结果方向不变 |
| 摘要文字信号 | 高 | 已有研究使用摘要；[ProseLens无需LLM调用](https://pypi.org/project/idealens/) | 摘要短；新模型可能漏检 | 2023年前论文误报率稳定，并按年份比较检出率 |
| 想法信号 | 中低 | [有Academic Writing格式，但没有论文想法来源真值](https://arxiv.org/pdf/2610.06778) | 可能测到论文具体程度，而不是想法来源 | 2023年前误报率可校准；不随领域或英语背景明显变化 |
| arXiv全文覆盖 | 中 | [S3提供PDF和源文件](https://info.arxiv.org/help/bulk_data_s3.html)；各学科覆盖待统计 | 结论限于发arXiv的作者；社科和人文覆盖少 | 排除AI研究者后仍有多个学科样本足够；报告匹配率；比较有无arXiv作者的基线差异 |
| 论文—仓库连接 | 中 | 2024–2025年有[143,210篇计算机作品提到github.com](https://api.openalex.org/works?filter=publication_year:2024-2025,primary_topic.field.id:17,fulltext.search:github.com&per-page=1&select=id) | 提到仓库不等于论文自己的仓库 | 人工抽样后精度至少0.90 |
| 作者到GitHub | 中 | [Brown等人的模型在非JOSS样本F1为0.89](https://arxiv.org/pdf/2510.16242) | 短名字、组织账号、同名作者 | 目标样本人工检查精度至少0.90 |
| 代码扩展 | 中低 | [代理痕迹主要在2025年后出现](https://arxiv.org/pdf/2606.24429) | 结果期短；没有痕迹不代表未使用 | 只报告初步结果 |
| DiD | 中 | 2018–2022年可做前趋势检验 | 换单位或进入大团队等同时变化 | 前趋势系数接近0，且敏感性分析不改变结论 |

### 所需资源

| 资源 | 用途 | 需求 | 判断 |
| --- | --- | --- | --- |
| 存储 | OpenAlex元数据 | [2026年9月版压缩约750 GB，其中works约615 GB；解压后数TB](https://developers.openalex.org/download/overview) | 现有数据只到2025年3月；不全量下载，用Athena或流式筛选生成子集，再下载到集群 |
| 存储 | 10万篇PDF | 按[全文库250 TB/5000–6000万篇](https://help.openalex.org/access/fulltext/)估算，约400–500 GB | 可行；[Adroit共享scratch约24 TB](https://researchcomputing.princeton.edu/adroit)，要先查个人配额 |
| GPU | IdeaLens打分 | [80 GB GPU，权重59 GiB，加载时约60 GiB内存](https://pypi.org/project/idealens/) | 现有A100可用；吞吐量要实测 |
| 网络 | 提纲抽取和GitHub采集 | 需要联网运行 | 计算节点离线，这些任务要放在可联网节点 |
| 经费 | 提纲抽取 | [约$0.018/篇](https://arxiv.org/pdf/2610.06778) | 若用外部模型，是最大开销；也可在Adroit用开放模型，但要重新校准和验证 |
| 经费 | 全文 | [OpenAlex $0.01/文件](https://help.openalex.org/access/fulltext/)，[每天有$1免费额度](https://help.openalex.org/access/pricing/)；[arXiv S3由下载者付费](https://info.arxiv.org/help/bulk_data_s3.html) | 主设计用arXiv，运行前比较S3和逐篇获取第一版的费用并审批；OpenAlex按篇下载只用于验证或备选 |
| 接口 | GitHub | [认证用户5,000次请求/小时](https://docs.github.com/en/enterprise-cloud@latest/rest/overview/rate-limits-for-the-rest-api) | 优先用不含文件内容的partial clone；API作补充，具体可行性待试跑 |
| 人工 | 仓库、账号和论文抽检 | 约40–80小时（估算） | 可由研究者和一名助研完成 |
| 合规 | 全文发送给外部模型 | arXiv和开放获取论文许可不同；工具代码为CC BY-NC-SA | 正式运行前确认普林斯顿和数据许可要求 |

### 经费情景

下表的论文数只是预算假设，不是符合条件的论文数。实际处理量约等于目标作者数乘以每人抽取的论文数。以下估算假设提纲抽取用Gemini 3.7 Flash批处理，打分用Adroit。校准按每组拟合和留出各2,500篇计算，这样在1%误报率下才能满足工具[预期至少25篇低于阈值](https://pypi.org/project/idealens/)的要求。

| 情景 | 目标论文 | 校准论文 | 提纲抽取 | 全文（OpenAlex备选） | 备选方案合计（约） |
| --- | --- | --- | --- | --- | --- |
| 验证 | 6,000（约2,000位作者） | 20,000（4组） | $468 | $260 | $728 |
| 主分析 | 100,000 | 50,000（10组） | $2,700 | $1,500 | $4,200 |
| 扩大样本 | 500,000 | 100,000（20组） | $10,800 | $6,000 | $16,800 |

主设计用arXiv第一版，不付OpenAlex按篇费用，但arXiv传输和算力费用待第0阶段估算；表中全文列和合计只适用于OpenAlex备选方案。若不用Adroit，改用Tinker打分，每1,000篇约增加[$0.50](https://pypi.org/project/idealens/)。GitHub和人工标注未计入。

### 分阶段路线

&#91;embedded content: 分阶段路线 · 四个阶段与验证门槛\]

全程约14–20周（一名研究者配合编程代理的估算），阶段1的结果决定是否进入主要开销。

## 待决定事项和下一步

下一步应先统计样本量，因为连接后样本可能大幅缩小，也决定IdeaLens是否值得运行。

**先做样本漏斗：**

- [ ] 统计arXiv与OpenAlex的匹配率、第一版到发表的时滞，以及2023–2026年目标论文的摘要和官方仓库覆盖
- [ ] 统计作者能高置信连到GitHub账号的比例（代码扩展）
- [ ] 统计这些作者在2018–2021年至少有4篇论文的比例
- [ ] 比较暴露期至少有1、2、3篇可测arXiv第一版时的作者数量，并按学科查看排除AI研究者后的样本
- [ ] 检查文字、代码和想法信号是否能区分不同作者

**第一阶段验证：**

- [ ] 用整体前移6年的伪时间线（2012–2015入样，2017–2018伪暴露，2019–2020伪结果）模拟“AI无效应”，比较固定窗口、首次检测和滚动设计是否产生虚假差异
- [ ] 在同一伪时间线上，用2017–2018年分数最高的十分位作者看2019–2020年产出，检验分数本身是否预示增长，并报告含与不含2020上半年的结果；安慰剂不得读取2021年及以后的结果
- [ ] 把2023年前的人写论文用AI润色，检查想法分是否随之上升
- [ ] 查看文字和想法信号的2×2分布，以及两者的粗略先后顺序

**需要决定：**

- [ ] 主样本在arXiv覆盖范围内保持多学科，不限计算机；需决定校准和异质性分析按哪一级学科分组
- [ ] 主分析已定为所有作者，第一和末位作者作稳健性检验；确认“至少4篇”在正式发表论文中是否过严
- [ ] 正式发表已定为期刊和会议论文；确定如何从OpenAlex准确识别会议论文，以及如何处理发表时滞
- [ ] 2027年数据更完整后，是否把代码扩展升级为正式检验

**进入第一阶段前还要定：**

- [ ] 2023–2024年“发arXiv”无法避免：主样本用尽量低的门槛，报告入选率差异，并做逆概率加权或界限分析
- [ ] 阈值已定为主规格；确定论文判定的误报率、作者层面的比例标准和替代阈值范围
- [ ] 主分析已定为arXiv第一版全文；确定LaTeX和PDF的解析规则、长文档的切分方式，以及摘要结果如何作稳健性检验
- [ ] 主分析已定为在作者层面排除2023年前的AI研究者，并单独分析；确定AI研究者的判定规则
- [ ] 主结果已定为论文数量和引用，价值暂只看引用；预先指定引用时间窗、主比较、标准误聚类方式和多重检验处理，并完成功效分析

**若arXiv覆盖不足：** 排除AI研究者后若样本集中在一两个学科，就停下来商量。默认备选是主测量统一用OpenAlex全文，并按学科和职业阶段随机抽作者。预算只影响抽样人数，不影响论文选择规则，也不用多个全文来源拼补。

## Sources

**已打开（全文或主要部分）：** [Filimonovic et al.](https://arxiv.org/html/2510.02408v1)、[Holzwarth et al.](https://arxiv.org/pdf/2608.10715)、[Khosravani & Mockus](https://arxiv.org/pdf/2606.24429)、[IdeaLens](https://arxiv.org/pdf/2610.06778)、[Brown et al.](https://arxiv.org/pdf/2510.16242)、[World of Code身份映射](https://arxiv.org/pdf/2607.06183)、[AI披露声明研究](https://arxiv.org/pdf/2608.23271)、[idealens](https://pypi.org/project/idealens/)、[arXiv bulk data](https://info.arxiv.org/help/bulk_data.html)、[arXiv S3](https://info.arxiv.org/help/bulk_data_s3.html)、[OpenAlex构建说明](https://help.openalex.org/data/how-its-built/)。

**数据源比较新增：** [Alperin et al.](https://arxiv.org/pdf/2404.17663)（已打开；部分作者为OpenAlex团队成员）、[Culbert et al.](https://arxiv.org/pdf/2401.16359v1)（片段）、[SciSciNet文档](https://northwestern-cssi.github.io/sciscinet)（片段）、[Kim 2018关于DBLP](https://arxiv.org/abs/1806.10540v2)（摘要）、[arXiv OAI-PMH说明](https://info.arxiv.org/help/oa/index.html)（已打开）。

**资源评估新增：** [IdeaLens论文](https://arxiv.org/pdf/2610.06778)（前100,000字符）、[idealens 0.1.7](https://pypi.org/project/idealens/)、[OpenAlex字段说明](https://help.openalex.org/data/works/attributes/)和[定价](https://help.openalex.org/access/pricing/)（已打开）；[OpenAlex全文说明](https://help.openalex.org/access/fulltext/)、[下载说明](https://developers.openalex.org/download/overview)、[Adroit](https://researchcomputing.princeton.edu/adroit)、[GitHub接口限额](https://docs.github.com/en/enterprise-cloud@latest/rest/overview/rate-limits-for-the-rest-api)（片段）。

**只读摘要或检索片段：** [Kusumegi et al.](https://arxiv.org/abs/2601.13187)、[PNAS时点批评](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13486544/)、[Hao et al.](https://arxiv.org/abs/2412.07727v4)、[Daniotti et al.](https://arxiv.org/pdf/2506.08945)、[He et al.](https://arxiv.org/abs/2511.04427)、[Humlum & Vestergaard](https://docs.iza.org/dp16992.pdf)、[Bick et al.](https://equitablegrowth.org/working-papers/what-work-does-generative-ai-do/)、[Papers with Code归档说明](https://www.coursera.org/articles/papers-with-code)、[OpenAlex社区讨论](https://groups.google.com/g/openalex-community/c/35CB8okSaig)。

**未核实：** rs-graph-v1的Dataverse页面不允许自动访问，相关信息来自Brown等人的论文。GitHub API速率限制和Khosravani & Mockus复现包的当前状态也未在本轮核实。

**首次检测批评补充：** [Renault et al.](https://arxiv.org/pdf/2605.17979)（片段）。Kusumegi等人的[正文和补充材料](https://gwern.net/doc/science/2025-kusumegi.pdf)已打开前100,000字符。

**arXiv主设计补充：** [arXiv S3批量数据](https://info.arxiv.org/help/bulk_data_s3.html)（已打开）、[arXiv审核政策](https://blog.arxiv.org/category/moderation)（分类页摘要）、[2026年政策变化汇总](https://casrai.org/news/arxiv-2026-endorsement-english-ai-policy-changes)（已打开）。S3是否含第一版、各学科覆盖和匹配率尚未核实。
