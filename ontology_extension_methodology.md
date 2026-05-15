# 微电子本体扩展方法论

> 基于 WDZYZCL-ontology 一次实际扩展过程（16类→45类）沉淀的实操手册。
> 目标：当需要从核心本体（PMDco）衍生领域扩展时，有一套可复用的流程和检查清单。

---

## 一、总体流程

```
需求分析 → 父类确认 → 关系设计 → ID规划 → 批量实现 → 全面验证
```

---

## 二、需求分析：找缺口

不要凭感觉列清单。**从本体描述出发**：

1. 看 extension 的 `dcterms:description`，提取承诺覆盖的领域
2. 对比当前已有的类，看哪些领域完全空白
3. 按优先级排序（描述承诺但缺失的 > 已有类的自然延伸 > 锦上添花）

**实例**（本次扩展）：
- 描述承诺：*wide bandgap semiconductors, oxide semiconductors, thin-film materials, heterostructures, microelectronics processes, and semiconductor devices*
- 已有：材料和工艺部分覆盖
- 缺失高优先级：**器件（完全空白）**、**异质结构（完全空白）**
- 缺失中优先级：更多材料（SiC, GaAs等）、更多性质（击穿电压等）

---

## 三、父类选择：必须看定义，不能只看标签

**核心原则：子类是父类的一种**

### 3.1 操作流程

1. 在核心本体中找到候选父类的完整定义块
2. 看 `rdfs:label`（知道它是什么）
3. 看 `skos:definition`（确认它的**内涵**能覆盖子类）
4. 看 `rdfs:subClassOf`（了解它在BFO/PMD层级中的位置）
5. 判断："这个新实体是候选父类的一种吗？"

### 3.2 常见陷阱：device ≠ 半导体器件

```
PMD_0000602 (device) = 制造/检测设备（模具、轧机、焊机、色谱仪）
PMD_0020152 (component) = 在技术系统中承担功能的对象聚合体
BFO_0000030 (object) = 最大自连接的、具有内在统一性的物质实体
```

**半导体器件（HEMT, TFT, LED, MOSFET）是电子元器件**，不是制造设备。
→ 正确父类：`PMD_0020152` 或 `BFO_0000030`
→ 错误父类：`PMD_0000602`

### 3.3 常用父类映射（参考表）

| 新类类型 | 父类 | 定义 |
|---|---|---|
| 化合物半导体材料 | `PMD_0010101` | semiconductor composed of two or more pure elements |
| 元素半导体材料 | `PMD_0010100` | semiconductor showing semiconductive behavior as a pure element |
| 工程材料 | `PMD_0000002` | material that is output of a manufacturing process |
| 晶体结构 | `PMD_0000591` | intensive quality embodying the periodic geometric arrangement of a crystal |
| 带隙 | `PMD_0090002` | energy range between valence and conduction band where no states exist |
| 电学性质 | `PMD_0000621` | material property under influence of electric field |
| 光学性质 | `PMD_0000877` | material property describing interaction with light |
| 一般材料属性 | `PMD_0000005` | material property (disposition) |
| 半导体器件 | 新建 `semiconductor device` → `BFO_0000030` | 不要挂在 PMD_0000602 下 |
| 气相涂覆工艺 | `PMD_0000569` | coating from gaseous/vapour state |
| 离子化涂覆工艺 | `PMD_0000571` | coating from ionized state |
| 一般制造工艺 | `PMD_0000833` | manufacturing process |

### 3.4 当没有合适父类时

- 跳到 BFO 顶层类（如 `BFO_0000030` object）
- 或为这一族新建一个中间类（如 `semiconductor device`）

---

## 四、关系设计：必须理解 domain/range

> OWL 中每条关系都有 domain（主体类型）和 range（客体类型）约束。
> 选对关系 = 理解 BFO 的基本分类。

### 4.1 四条核心关系

| 关系 | 中文名 | Domain → Range | 用途 | ❌ 不要用于 |
|---|---|---|---|---|
| `RO_0000086` | has quality | 独立持续者 → 质量 | 物质→晶体结构、带隙 | 物质→物质 |
| `RO_0000091` | has disposition | 独立持续者 → 倾向性 | 物质→迁移率、热导率 | 物质→物质 |
| `RO_0002353` | output of | 物质/过程 → 过程 | 材料/器件→它的制造工艺 | 反过来用 |
| `BFO_0000051` | has part | 独立持续者 → 独立持续者 | 器件→构成它的材料 | 特性→物质 |

### 4.2 最容易踩的坑：RO_0000053（has characteristic）

```
❌ HEMT → RO_0000053 → GaN
   RO_0000053 的 range = BFO_0000020（特性/倾向/功能）
   GaN 是物质实体（独立持续者），不是特性
   类型错误！

✅ HEMT → BFO_0000051 → GaN
   BFO_0000051 的 range = 独立持续者
   器件以材料为部分，类型正确
```

### 4.3 如何验证关系正确性

在核心本体中搜索关系定义块：

```text
# 找到 <owl:ObjectProperty rdf:about=".../RO_0000091">
# 看它的 rdfs:domain 和 rdfs:range
```

---

## 五、ID 规划策略

WDZ 的 ID 是 7 位数字，建议按模块分配号段：

| 号段 | 模块 | 本次使用 |
|---|---|---|
| `WDZ_01001xx` | 化合物/元素半导体材料 | GaN, AlN, IGZO, SiC, GaAs... |
| `WDZ_01002xx` | 一般工程材料 | SiO2 |
| `WDZ_02000xx` | 晶体结构 | wurtzite, amorphous, diamond cubic... |
| `WDZ_02100xx` | 带隙类型 | wide, ultra-wide, direct, indirect |
| `WDZ_02200xx` | 电学性质 | mobility, breakdown voltage, saturation velocity |
| `WDZ_02300xx` | 光学性质 | optical transparency |
| `WDZ_02400xx` | 耦合/跨领域性质 | piezoelectric |
| `WDZ_03000xx` | 制造工艺 | epitaxy, MOCVD, ALD, RIE, RTA... |
| `WDZ_04000xx` | 器件 + 异质结构 | semiconductor device, HEMT, TFT, heterostructure... |

---

## 六、实现流程（以一次扩展为例）

### 6.1 准备工作

```python
# 读取核心本体和扩展本体
# 提取所有已有类的 ID 和父类引用
# 确认 max ID 号段
```

### 6.2 批量添加

- 同类实体放到同一 section 注释下
- 每个类写四要素：`rdfs:label`(en/zh)、`skos:definition`(en/zh)、`rdfs:subClassOf`
- 可选要素：`skos:altLabel`、`skos:example`
- 新增引用已有 WDZ 类时，确保该 WDZ 类已定义

### 6.3 验证清单

```text
[ ] XML 标签平衡（owl:Class open == close）
[ ] 所有类有 en/zh label 和 definition
[ ] 所有类有 rdfs:subClassOf
[ ] 引用的所有 PMD 类在核心本体中存在
[ ] 引用的所有 WDZ 类在扩展本体中已定义
[ ] 没有重复的 ID（每个类出现恰好一次）
[ ] 关系 domain/range 类型正确（特别是 RO_0000053 不要用于物质→物质）
[ ] 没有遗留的 PMD_0000602（device）作为器件父类
[ ] </rdf:RDF> 在文件末尾
```

---

## 七、持久化规范

所有方法论沉淀写入 **AGENTS.md**（位于项目根目录）：

- **新增类检查流程**：确定父类 → 查定义 → 判断语义对齐 → 不一致则更换
- **器件类约束**：标注哪些父类不可用
- **关系使用表**：标注哪些关系不允许什么用法
- **父类映射表**：快速参考

AI 每次在项目目录下工作时自动读取 CLAUDE.md，规则会被强制执行。

---

## 八、常见错误速查

| 症状 | 根因 | 修复 |
|---|---|---|
| 器件类与模具在同一层级 | 父类选错了 PMD_0000602 | 改用 BFO_0000030 或新建 semiconductor device 中间类 |
| 引用"具有特性"将材料挂器件下 | RO_0000053 range 是特性不是物质 | 改用 BFO_0000051 (has part) |
| 父类定义不覆盖子类 | 凭标签选父类没看定义 | 按 3.1 流程重选 |
| ID 重复 | 批量插入未检查 | 用 grep 搜索 rdf:about 确认 |
| 引用未定义类 | 跨模块引用顺序错误 | 确保引用的 WDZ 类在文件更前面定义 |
