#!/usr/bin/env python3
"""
Demo: 本体驱动的知识抽取
流水线: PaddleOCR 解析 PDF -> DeepSeek 知识抽取 -> Turtle + JSON 输出
论文: Synthesis of c-axis oriented AlN thin films on different substrates: A review
"""

import json
import os
import time
from pathlib import Path

import requests
from openai import OpenAI


# ============================================================
# 配置
# ============================================================
PAPER_PATH = "papers/Synthesis_of_c_axis_oriented_AlN_thin_fi.pdf"
OUTPUT_DIR = "knowledge_extraction"

DEEPSEEK_KEY = "sk-<your-deepseek-key>"
PADDLE_TOKEN = "<your-paddle-token>"


# ============================================================
# Step 1: PaddleOCR-VL 文档解析
# ============================================================
def parse_pdf(file_path: str) -> str:
    JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
    headers = {"Authorization": f"bearer {PADDLE_TOKEN}"}
    MODEL = "PaddleOCR-VL-1.5"
    optional = {
        "useDocOrientationClassify": False,
        "useDocUnwarping": False,
        "useChartRecognition": False,
    }

    print(f"[PaddleOCR] 提交解析任务: {file_path}")
    abs_path = str(Path(file_path).resolve())
    data = {"model": MODEL, "optionalPayload": json.dumps(optional)}
    with open(abs_path, "rb") as f:
        resp = requests.post(JOB_URL, headers=headers, data=data, files={"file": f})

    if resp.status_code != 200:
        raise RuntimeError(f"PaddleOCR 提交失败: {resp.status_code} {resp.text}")
    job_id = resp.json()["data"]["jobId"]
    print(f"[PaddleOCR] job id: {job_id}")

    # 轮询
    while True:
        poll = requests.get(f"{JOB_URL}/{job_id}", headers=headers).json()
        state = poll["data"]["state"]
        if state == "done":
            prog = poll["data"]["extractProgress"]
            print(f"[PaddleOCR] 完成, {prog.get('extractedPages', 0)} 页")
            jsonl_url = poll["data"]["resultUrl"]["jsonUrl"]
            break
        elif state == "failed":
            raise RuntimeError(f"解析失败: {poll['data'].get('errorMsg', 'unknown')}")
        else:
            print(f"[PaddleOCR] {state}...")
            time.sleep(5)

    # 下载结果
    md_pages = []
    for line in requests.get(jsonl_url).text.strip().split("\n"):
        if not line.strip():
            continue
        for res in json.loads(line)["result"].get("layoutParsingResults", []):
            md_text = res.get("markdown", {}).get("text", "")
            if md_text:
                md_pages.append(md_text)

    full_md = "\n\n---\n\n".join(md_pages)
    print(f"[PaddleOCR] 共 {len(md_pages)} 页, {len(full_md)} 字符")
    return full_md


# ============================================================
# Step 2: 本体 Schema
# ============================================================
SCHEMA = """
## 允许实体类型 -- 只从 PMDco 核心本体

### 材料
- PMD_0010100  elemental semiconductor    元素半导体 (Si, diamond)
- PMD_0010101  compound semiconductor     化合物半导体 (GaN, AlN, ZnO, SiC, GaAs)
- PMD_0000002  engineered material         工程材料 (SiO2, Al2O3, sapphire)

### 晶体结构 & 带隙
- PMD_0000591  crystal structure           晶体结构
- PMD_0090002  band gap                    带隙

### 性质
- PMD_0000005  material property           材料属性 (thermal conductivity, piezoelectric)
- PMD_0000621  electrical property         电学性质 (resistivity, mobility)
- PMD_0000877  optical property            光学性质

### 工艺
- PMD_0000569  coating from gaseous state  气相涂覆 (CVD, MOCVD, MBE)
- PMD_0000571  coating from ionized state  离子化涂覆 (sputtering)
- PMD_0000833  manufacturing process       一般制造工艺

### 器件
- PMD_0020152  component                   组件 (SAW device, LED)
- BFO_0000030  object                      BFO 物质实体

## 允许的关系
- RO_0000086  has quality        物质 -> 质量
- RO_0000091  has disposition    物质 -> 倾向性/属性
- RO_0002353  output of          物质/器件 -> 制造工艺
- BFO_0000051 has part           器件 -> 组成部分
"""

PROMPT_TEMPLATE = """你是材料科学知识抽取助手。从论文中抽取实体和关系，映射到本体类，输出 JSON。

{SCHEMA}

输出格式: {{"entities": [...], "relations": [...]}}

entity: {{"id":"e1","name":"","name_zh":"","type_iri":"","type_name":"","properties":{{}},"evidence":""}}
relation: {{"subject":"e1","predicate_iri":"RO_0000086","predicate_name":"","object":"e2","evidence":""}}

约束:
- type_iri 只允许使用 PMD_ 或 BFO_ 前缀，优先选 PMD_
- 数值必须带单位
- 只输出 JSON, 不要多余文本
- 映射不了的标 type_iri="UNKNOWN"

{paper_text}"""


# ============================================================
# Step 3: DeepSeek 抽取
# ============================================================
def extract(md_text: str) -> str:
    client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
    prompt = PROMPT_TEMPLATE.format(SCHEMA=SCHEMA, paper_text=md_text)
    print(f"\n[DeepSeek] 发送请求, 输入 {len(prompt)} 字符...")
    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=8192,
    )
    print(f"[DeepSeek] tokens: {resp.usage.total_tokens}")
    return resp.choices[0].message.content


# ============================================================
# Step 4: JSON -> Turtle
# ============================================================
def to_owl(json_str: str) -> str:
    cleaned = json_str.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(cleaned.split("\n")[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    data = json.loads(cleaned)

    prefix = """@prefix pmd: <https://w3id.org/pmd/co/> .
@prefix ro:  <http://purl.obolibrary.org/obo/RO_> .
@prefix bfo: <http://purl.obolibrary.org/obo/BFO_> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:<http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos:<http://www.w3.org/2004/02/skos/core#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .

"""

    lines = [prefix]
    lines.append("# Paper: Synthesis of c-axis oriented AlN thin films\n")

    # 跳过：使用 OWL 格式输出而非 Turtle（Protégé 兼容性更好）

    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: 解析
    print("=" * 60)
    print("  Step 1: PaddleOCR-VL 文档解析")
    print("=" * 60)
    md = parse_pdf(PAPER_PATH)

    md_path = os.path.join(OUTPUT_DIR, "paper_parsed.md")
    with open(md_path, "w") as f:
        f.write(md)
    print(f"  -> 保存解析结果 {md_path}")

    if len(md) > 16000:
        print(f"  [截取] {len(md)} 字符 -> 16000 字符")
        md = md[:16000]

    # Step 2 + 3: 抽取
    print("\n" + "=" * 60)
    print("  Step 2: DeepSeek 知识抽取")
    print("=" * 60)
    raw = extract(md)

    # Step 4: 解析 JSON + 输出
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.split("\n")[1:])
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        parsed = json.loads(cleaned)

        print(f"\n实体数: {len(parsed.get('entities', []))}")
        print(f"关系数: {len(parsed.get('relations', []))}")

        json_path = os.path.join(OUTPUT_DIR, "extracted_knowledge.json")
        with open(json_path, "w") as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)
        print(f"  -> {json_path}")

        owl_path = os.path.join(OUTPUT_DIR, "extracted_knowledge.ttl")
        owl = to_owl(cleaned)
        with open(owl_path, "w") as f:
            f.write(ttl)
        print(f"  -> {owl_path}")

        # 终端展示
        print("\n--- JSON 预览 ---")
        print(json.dumps(parsed, indent=2, ensure_ascii=False)[:2000])

    except json.JSONDecodeError:
        raw_path = os.path.join(OUTPUT_DIR, "extracted_knowledge_raw.txt")
        with open(raw_path, "w") as f:
            f.write(raw)
        print(f"  JSON 解析失败, 原始输出 -> {raw_path}")
        print(raw[:2000])

    print(f"\n输出目录: {OUTPUT_DIR}/")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"  {f:45s} {size:>8,} bytes")


if __name__ == "__main__":
    main()
