# WDZYZCL 本体开发规范

## 新增类的检查流程

每次在 `WDZYZCL-v1-extension.owl` 中新增类之前，必须：

1. **确定父类**：为新增实体选择合适的 PMDco 核心类或已有 WDZ 类作为父类
2. **检查父类定义**：在 `WDZYZCL-v1.owl` 中找到父类的完整定义（包括 `rdfs:label` 和 `skos:definition`）
3. **判断适合性**：确认父类的定义能覆盖子类的语义——"子类是父类的一种"
4. **不一致则更换父类**：如果发现语义不对齐，换更合适的父类或直接跳到 BFO 层

## 器件类注意事项

- 半导体器件（HEMT, TFT, LED, MOSFET 等）是 **电子元器件**，应挂在 `PMD_0020152`（component）或 `BFO_0000030`（object）下
- **不要**挂在 `PMD_0000602`（device）下——那是制造/检测设备（模具、轧机、焊机、色谱仪）
- 已创建的中间类 `WDZ_0400000`（semiconductor device）→ `BFO_0000030`，所有器件子类挂在此处

## 现有父类映射（参考）

| 新类类型 | 使用父类 | 说明 |
|---|---|---|
| 化合物半导体材料 | `PMD_0010101` (compound semiconductor) | GaN, AlN, IGZO, SiC, GaAs 等 |
| 元素半导体材料 | `PMD_0010100` (elemental semiconductor) | Si, diamond |
| 一般工程材料 | `PMD_0000002` (engineered material) | SiO₂, heterostructure |
| 晶体结构 | `PMD_0000591` (crystal structure) | |
| 带隙类型 | `PMD_0090002` (band gap) | |
| 电学性质 | `PMD_0000621` (electrical property) | |
| 光学性质 | `PMD_0000877` (optical property) | |
| 一般材料属性 | `PMD_0000005` (material property) | 压电等跨领域属性 |
| 气相涂覆工艺 | `PMD_0000569` (coating from gaseous state) | 外延, ALD |
| 离子化涂覆工艺 | `PMD_0000571` (coating from ionized state) | 溅射 |
| 一般制造工艺 | `PMD_0000833` (manufacturing process) | 热氧化, RIE, RTA, 离子注入, 光刻 |

## 关系使用规范

在 `owl:Restriction` 中使用关系时：

| 关系 | 用途 | 不允许的用法 |
|---|---|---|
| `RO_0000086` (has quality) | 物质→质量（晶体结构、带隙等） | — |
| `RO_0000091` (has disposition) | 物质→属性/倾向性（迁移率、热导率等） | — |
| `RO_0002353` (output of) | 材料/器件→制造它的工艺 | — |
| `BFO_0000051` (has part) | 器件→组成它的材料 | ❌ 不要用 `RO_0000053` (has characteristic) 替代——它的 range 是 BFO_0000020（特性/倾向），不是物质实体 |
