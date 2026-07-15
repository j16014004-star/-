"""
纯规则简历结构化解析器

从清洗后的简历纯文本中提取结构化信息（基础信息、教育、工作、项目、技能）。
不依赖 AI、外部服务或数据库；纯函数，无副作用。
"""
import re
from typing import Any

# ── 模块级预编译正则 ──────────────────────────────────────────

# 邮箱
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# 中国手机号（兼容 1xx 开头 11 位）
RE_PHONE = re.compile(r"1[3-9]\d{9}")

# URL
RE_URL = re.compile(r"https?://[^\s,，、；;)]+")

# 日期区间：2021.09-2025.06 / 2021/09-2025/06 / 2021年9月-2025年6月
RE_DATE_RANGE = re.compile(
    r"(\d{4})[.年/](\d{1,2})[.月]?\s*(?:-|—|–|～|~|至)\s*"
    r"(?:(\d{4})[.年/])?(\d{1,2})[.月]?(?:至今|当前|现在|present)?"
)
# 单起始日期
RE_DATE_START = re.compile(r"(\d{4})[.年/](\d{1,2})[.月]?")

# 学历关键词
DEGREES = {"本科", "硕士", "博士", "大专", "高中", "中专", "研究生",
           "学士", "Master", "Bachelor", "PhD", "Ph.D", "MBA", "EMBA"}

# 章节标题（按出现优先级，非贪婪匹配）
SECTION_HEADERS: list[tuple[str, str]] = [
    ("basic_info",   "基本信息|个人信息|个人资料|基本资料|联系方式|contact"),
    ("education",    "教育背景|教育经历|学历|education"),
    ("work",         "工作经历|工作经验|实习经历|work experience|working experience"),
    ("projects",     "项目经历|项目经验|project experience"),
    ("skills",       "专业技能|技能|技术栈|个人技能|核心技能|skill"),
]

# 常见分隔符切分用
RE_SPLIT = re.compile(r"[、，,、/|·•\s]{1,3}")


def parse_resume(cleaned_text: str) -> dict[str, Any]:
    """
    解析简历结构化信息。

    Args:
        cleaned_text: 经 clean_text() 处理后的纯文本。

    Returns:
        固定结构的 dict，包含 parser_version、basic_info、education、
        work_experience、projects、skills、warnings。
    """
    result: dict[str, Any] = {
        "parser_version": "rules-v1",
        "basic_info": {"name": None, "phone": [], "email": [],
                       "location": None, "links": []},
        "education": [],
        "work_experience": [],
        "projects": [],
        "skills": [],
        "warnings": [],
    }

    text = cleaned_text.strip()
    if not text:
        result["warnings"].append("empty_cleaned_text")
        return result

    # 限制输入长度，防止极端大文本拖慢
    MAX_CHARS = 100_000
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        result["warnings"].append("text_truncated_for_parser")

    lines = text.splitlines()

    # ── 第一遍：全局确定性提取 ──
    emails = list({m.group(0).strip().lower()
                   for m in RE_EMAIL.finditer(text)})
    phones = list({m.group(0).strip()
                   for m in RE_PHONE.finditer(text)})
    urls = list(dict.fromkeys(m.group(0).strip()
                              for m in RE_URL.finditer(text)))

    result["basic_info"]["email"] = emails
    result["basic_info"]["phone"] = phones
    result["basic_info"]["links"] = [_classify_link(u) for u in urls]

    # ── 第二遍：章节定位 ──
    sections = _detect_sections(lines)
    if not sections:
        result["warnings"].append("section_not_detected")

    # ── 基本信息（姓名、所在地）─ 优先从 basic_info 区取，否则从开头取 ──
    basic_lines = sections.get("basic_info")
    if basic_lines:
        result["basic_info"]["name"] = _extract_name(basic_lines)
        result["basic_info"]["location"] = _extract_location(basic_lines)
    else:
        # 从简历前 20 行推测姓名
        result["basic_info"]["name"] = _extract_name(lines[:20])

    # ── 教育经历 ──
    edu_lines = sections.get("education", [])
    result["education"] = _parse_education(edu_lines)

    # ── 工作经历 ──
    work_lines = sections.get("work", [])
    result["work_experience"] = _parse_work_experience(work_lines)

    # ── 项目经历 ──
    proj_lines = sections.get("projects", [])
    result["projects"] = _parse_projects(proj_lines)

    # ── 技能 ──
    skill_lines = sections.get("skills", [])
    result["skills"] = _parse_skills(skill_lines, text)

    return result


# ── 内部函数 ──────────────────────────────────────────────────


def _classify_link(url: str) -> dict[str, str]:
    """将 URL 归类为 github / linkedin / 其他"""
    lower = url.lower()
    if "github" in lower:
        t = "github"
    elif "linkedin" in lower:
        t = "linkedin"
    else:
        t = "other"
    return {"type": t, "url": url}


def _detect_sections(lines: list[str]) -> dict[str, list[str]]:
    """识别章节标题并返回各章节的行列表（不含标题行）。"""
    sections: dict[str, list[str]] = {}
    current_section: str | None = None
    current_lines: list[str] = []

    # 构建复合正则：一行匹配任一标题
    all_patterns = "|".join(p for _, p in SECTION_HEADERS)
    header_re = re.compile(all_patterns, re.IGNORECASE)

    # 标题行映射
    header_to_key: dict[str, str] = {}
    for key, pat in SECTION_HEADERS:
        for variant in pat.split("|"):
            header_to_key[variant.lower()] = key

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_section:
                current_lines.append("")
            continue

        m = header_re.match(stripped)
        if m:
            # 保存上一个章节
            if current_section and current_lines:
                sections[current_section] = current_lines
            # 开始新章节
            matched_text = m.group(0).lower()
            current_section = header_to_key.get(matched_text, "basic_info")
            current_lines = []
        else:
            if current_section:
                current_lines.append(stripped)
            # 尚未进入任何章节的内容忽略（通常是姓名行等基本信息区域）

    if current_section and current_lines:
        sections[current_section] = current_lines

    return sections


def _extract_name(lines: list[str]) -> str | None:
    """保守提取姓名（仅返回高置信度结果）。"""
    for line in lines[:20]:
        s = line.strip()
        if not s or len(s) > 10:
            continue
        # 不能含有数字、邮箱、电话、URL、标点
        if re.search(r"\d", s):
            continue
        if re.search(r"[@.://]", s):
            continue
        # 中文名 2-4 字 或 英文名 2-3 词
        cn = re.match(r"^[一-鿿]{2,4}$", s)
        en = re.match(r"^[a-zA-Z]+(?: [a-zA-Z]+){1,2}$", s)
        if cn or en:
            return s
    return None


def _extract_location(lines: list[str]) -> str | None:
    """提取所在地/现居城市。"""
    for line in lines:
        s = line.strip()
        # 匹配"现居/所在地/居住地/城市：xxx"
        m = re.search(r"(?:现居|所在地|居住地|地址|城市)[：:]\s*(.+)", s)
        if m:
            loc = m.group(1).strip()
            if 2 <= len(loc) <= 20:
                return loc
        # 纯城市名（2-3字），单独一行且不含其他内容
        if re.match(r"^[一-鿿]{2,3}(?:市|区)?$", s) and len(s) <= 4:
            # 避免把学校名/专业/学历误认为城市
            if not any(kw in s for kw in ["大学", "学院", "公司", "集团", "有限",
                                           "本科", "硕士", "博士", "专业", "课程"]):
                return s
    return None


def _parse_date_range(text: str) -> tuple[str | None, str | None]:
    """从文本中提取日期区间，返回 (start, end)，均为 YYYY-MM 格式。"""
    m = RE_DATE_RANGE.search(text)
    if m:
        y1, m1, y2, m2 = m.group(1), m.group(2), m.group(3), m.group(4)
        start = f"{y1}-{int(m1):02d}"
        if y2:
            end = f"{y2}-{int(m2):02d}"
        else:
            end = None  # 至今
        return start, end

    # 尝试单日期
    m2 = RE_DATE_START.search(text)
    if m2:
        return f"{m2.group(1)}-{int(m2.group(2)):02d}", None
    return None, None


def _parse_education(lines: list[str]) -> list[dict[str, Any]]:
    """解析教育经历。"""
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_desc: list[str] = []

    def flush_entry():
        nonlocal current, pending_desc
        if current is None:
            return
        desc = " ".join(pending_desc).strip()
        if desc and desc != current.get("raw_text", ""):
            desc = desc.replace(current.get("raw_text", ""), "", 1).strip()
        if desc:
            current["description"] = desc
        if current.get("school") or current.get("raw_text"):
            entries.append(current)
        current = None
        pending_desc = []

    for line in lines:
        s = line.strip()
        if not s:
            flush_entry()
            continue

        # 检查是否包含日期 → 新条目
        start, end = _parse_date_range(s)
        if start:
            flush_entry()
            current = {
                "raw_text": s,
                "start_date": start,
                "end_date": end,
                "school": None,
                "major": None,
                "degree": None,
                "description": None,
            }
            # 从当前行提取学校/专业/学历
            _fill_edu_fields(current, s)
            pending_desc = []
        elif current:
            # 尝试从行中提取缺失字段
            _fill_edu_fields(current, s)
            pending_desc.append(s)

    flush_entry()
    return entries


def _fill_edu_fields(entry: dict[str, Any], text: str):
    """从文本行中补充教育字段（学校、专业、学历）。"""
    # 学历
    for deg in DEGREES:
        if deg in text and entry["degree"] is None:
            entry["degree"] = deg
            break

    lines_in_text = text.splitlines()
    for line in lines_in_text:
        s = line.strip()
        # 学校：含"大学""学院""学校"且不只有学历词
        if re.search(r"大学|学院|学校", s) and entry["school"] is None:
            # 尝试提取完整学校名
            m = re.search(r"([一-鿿 ]{4,30}(?:大学|学院|学校))", s)
            if m:
                entry["school"] = m.group(1).strip()
        # 专业
        if "专业" in s or "主修" in s:
            m = re.search(r"(?:专业|主修)[：:：]?\s*(.{2,30})", s)
            if m and entry["major"] is None:
                major = m.group(1).strip()
                if not re.match(r"^课程", major):  # 排除"课程："
                    entry["major"] = major
        # 行中可能包含专业名（| 分隔）
        if entry["major"] is None and "|" in s:
            parts = s.split("|")
            for part in parts:
                p = part.strip()
                if 2 <= len(p) <= 30 and not any(kw in p for kw in ["大学", "学院", "本科", "硕士", "博士"]):
                    if re.search(r"[一-鿿]", p):
                        entry["major"] = p
        # 如果行是单纯的专业名（不含学校/学历等词）
        if entry["major"] is None and 2 <= len(s) <= 30:
            if not any(kw in s for kw in ["大学", "学院", "本科", "硕士", "博士"]):
                if re.match(r"^[一-鿿／/、\\s]+$", s):
                    # 仅当行是学历后续行且像专业名
                    pass  # 通过 description 传递


def _parse_work_experience(lines: list[str]) -> list[dict[str, Any]]:
    """解析工作经历。"""
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_desc: list[str] = []

    def flush_entry():
        nonlocal current, pending_desc
        if current is None:
            return
        desc = "\n".join(pending_desc).strip()
        if desc:
            current["description"] = desc
        if current.get("company") or current.get("raw_text"):
            entries.append(current)
        current = None
        pending_desc = []

    for line in lines:
        s = line.strip()
        if not s:
            flush_entry()
            continue

        start, end = _parse_date_range(s)
        if start:
            flush_entry()
            current = {
                "raw_text": s,
                "start_date": start,
                "end_date": end,
                "company": None,
                "title": None,
                "description": None,
            }
            # 从当前行提取公司/职位
            _fill_work_fields(current, s)
        elif current:
            _fill_work_fields(current, s)
            # 如果是职责描述条目（以 • - 或数字开头），保留
            pending_desc.append(s)

    flush_entry()
    return entries


def _fill_work_fields(entry: dict[str, Any], text: str):
    """从文本行中补充工作字段（公司、职位）。"""
    # 常见职位关键词
    titles = ["工程师", "专员", "经理", "主管", "总监", "实习生",
              "开发", "设计", "运营", "产品", "分析师", "顾问",
              "助理", "负责人", "主任", "专家", "架构师"]
    # 公司后缀
    company_suffixes = ["有限公司", "责任公司", "集团", "股份", "合伙",
                        "事务所", "工作室", "厂", "公司"]

    # 清理行中日期前缀后提取公司名
    clean_line = re.sub(r"^\d{4}[./年]\d{1,2}[.月]?\s*(?:-|—|–|～|~|至)\s*(?:\d{4}[./年])?\d{1,2}[.月]?\s*", "", text).strip()

    for suf in company_suffixes:
        if suf in clean_line and entry["company"] is None:
            m = re.search(r"([一-鿿A-Za-z0-9 ]{2,50}" + re.escape(suf) + ")", clean_line)
            if m:
                entry["company"] = m.group(1).strip()

    # 职位
    for t in titles:
        if t in text and entry["title"] is None:
            # 取包含该职位的短片段
            m = re.search(r"([一-鿿A-Za-z/ ]{1,20}" + re.escape(t) + ")", text)
            if m:
                entry["title"] = m.group(1).strip()


def _parse_projects(lines: list[str]) -> list[dict[str, Any]]:
    """解析项目经历。"""
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_desc: list[str] = []

    def flush_entry():
        nonlocal current, pending_desc
        if current is None:
            return
        desc = "\n".join(pending_desc).strip()
        if desc:
            current["description"] = desc
        if current.get("name") or current.get("raw_text"):
            entries.append(current)
        current = None
        pending_desc = []

    for line in lines:
        s = line.strip()
        if not s:
            continue
        start, end = _parse_date_range(s)

        # 仅根据日期拆分项目条目
        is_new = bool(start)

        if is_new:
            # 如果 current 非空，先保存
            if current:
                # 检查是否真正是新项目还是上一条的描述
                pass
            flush_entry()
            current = {
                "raw_text": s,
                "name": None,
                "role": None,
                "start_date": start,
                "end_date": end,
                "description": None,
                "technologies": [],
            }
            _fill_project_fields(current, s)
            pending_desc = []
        elif current:
            _fill_project_fields(current, s)
            pending_desc.append(s)

    # 最后一条
    if current:
        desc = "\n".join(pending_desc).strip()
        if desc:
            current["description"] = desc
        if current.get("name") or current.get("raw_text"):
            entries.append(current)

    # 如果没有按日期切分出条目，则整个段落作为一个项目
    if not entries and lines:
        text_block = "\n".join(lines).strip()
        if text_block:
            first_line = lines[0].strip() if lines else ""
            entries.append({
                "raw_text": text_block[:500],
                "name": first_line if len(first_line) >= 4 else None,
                "role": None,
                "start_date": None,
                "end_date": None,
                "description": text_block,
                "technologies": [],
            })
            # 从全文重新提取技术栈
            _fill_project_fields(entries[-1], text_block)

    return entries


def _fill_project_fields(entry: dict[str, Any], text: str):
    """从文本行中补充项目字段（名称、技术栈）。"""
    # 如果 name 为空，取文本首行作为项目名
    if entry["name"] is None:
        first_line = text.split('\n', 1)[0].strip()
        # 清理行尾的技术栈部分（| 后内容）
        name_part = first_line.split("|")[0].strip()
        if len(name_part) >= 4:
            entry["name"] = name_part

    # 提取技术栈：包含常见技术关键词的行
    tech_keywords = [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
        "FastAPI", "Flask", "Django", "Spring", "Vue", "React", "Angular",
        "MySQL", "Redis", "MongoDB", "PostgreSQL", "SQLite", "Elasticsearch",
        "Docker", "Kubernetes", "Git", "Linux", "Nginx",
        "HTML", "CSS", "Node.js", "Express", "jQuery",
        "SQLAlchemy", "Alembic", "Pydantic", "JWT", "OAuth",
        "RESTful", "API", "WebSocket", "Celery", "RabbitMQ",
        "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy",
        "AWS", "Azure", "GCP", "阿里云", "腾讯云",
        "Vue.js", "Element Plus", "Tailwind", "Bootstrap",
    ]
    found = [kw for kw in tech_keywords if kw.lower() in text.lower()
             and kw not in entry["technologies"]]
    entry["technologies"].extend(found)

    # 项目名：如果当前行不含技术关键词且不是空行，可能是项目名
    # 保留在 raw_text 和 description 中


def _parse_skills(lines: list[str], full_text: str) -> list[str]:
    """解析技能列表。"""
    all_skills: list[str] = []

    # 从 skill 章节行中提取
    for line in lines:
        s = line.strip()
        if not s or len(s) > 500:
            continue
        # 按常见分隔符切分
        parts = RE_SPLIT.split(s)
        for p in parts:
            p = p.strip()
            # 过滤：太短、纯数字、纯标点、含冒号的标签、明显不是技能
            if len(p) < 2:
                continue
            if re.match(r"^[\d\W]+$", p):
                continue
            if ":" in p or "：" in p:
                continue
            if any(ex in p for ex in ["经历", "经验", "项目", "教育", "语言能力"]):
                continue
            if p not in all_skills:
                all_skills.append(p)

    # 如果章节不明显，从全文提取常见技术名词
    if not all_skills:
        tech_patterns = [
            r"Python|Java|JavaScript|TypeScript|Go|Rust|C\+\+|C#",
            r"FastAPI|Flask|Django|Spring|Vue|React|Angular",
            r"MySQL|Redis|MongoDB|PostgreSQL|Elasticsearch",
            r"Docker|Kubernetes|Git|Linux|Nginx",
            r"SQLAlchemy|Alembic|Pydantic|JWT|OAuth",
            r"厨师|面点师|西餐厨师|中餐厨师|服务员|收银员|店员|营业员",
            r"销售|客服|前台|文员|行政|人事|司机|仓管|保安|保洁",
            r"普工|技工|电工|焊工|叉车|会计|出纳|财务|运营|设计",
            r"剪辑|摄影|主播|教师|助教|护士|美容师|美发师",
        ]
        seen: set[str] = set()
        for pat in tech_patterns:
            for m in re.finditer(pat, full_text, re.IGNORECASE):
                skill = m.group(0)
                if skill.lower() not in seen:
                    seen.add(skill.lower())
                    all_skills.append(skill)

    # 去重保序
    return list(dict.fromkeys(all_skills))


def normalize_structured_data_for_frontend(data: dict[str, Any] | None) -> dict[str, Any]:
    """Return parser output with frontend-compatible resume detail aliases."""
    source = data if isinstance(data, dict) else {}
    normalized: dict[str, Any] = dict(source)
    basic = source.get("basic_info") if isinstance(source.get("basic_info"), dict) else {}

    name = _first_text(source.get("name"), source.get("full_name"), basic.get("name"))
    phone = _first_text(source.get("phone"), source.get("phone_number"), source.get("mobile"), basic.get("phone"))
    email = _first_text(source.get("email"), basic.get("email"))
    city = _first_text(
        source.get("city"),
        source.get("current_city"),
        source.get("expected_city"),
        source.get("location"),
        basic.get("location"),
    )

    education_list = [_normalize_education_item(item) for item in _first_list(
        source.get("education_list"),
        source.get("educationList"),
        source.get("educations"),
        source.get("education_background"),
        source.get("education"),
    )]
    work_list = [_normalize_work_item(item) for item in _first_list(
        source.get("work_list"),
        source.get("workList"),
        source.get("work_experiences"),
        source.get("experiences"),
        source.get("work_experience"),
    )]
    skills = [str(item).strip() for item in _first_list(
        source.get("skills"),
        source.get("skill_tags"),
        source.get("skillTags"),
    ) if str(item).strip()]

    normalized.update({
        "name": name,
        "full_name": name,
        "phone": phone,
        "phone_number": phone,
        "mobile": phone,
        "email": email,
        "city": city,
        "current_city": city,
        "expected_city": city,
        "location": city,
        "education": _highest_degree(education_list) or source.get("education"),
        "highest_education": _highest_degree(education_list) or source.get("highest_education"),
        "degree": _highest_degree(education_list) or source.get("degree"),
        "experience": _estimate_experience(work_list) or source.get("experience"),
        "work_experience": _estimate_experience(work_list) or source.get("work_experience"),
        "years_of_experience": _estimate_experience(work_list) or source.get("years_of_experience"),
        "education_list": education_list,
        "educationList": education_list,
        "educations": education_list,
        "education_background": education_list,
        "work_list": work_list,
        "workList": work_list,
        "work_experiences": work_list,
        "experiences": work_list,
        "skills": skills,
        "skill_tags": skills,
        "skillTags": skills,
    })
    return normalized


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, list):
            for item in value:
                text = str(item).strip()
                if text:
                    return text
        elif value is not None:
            text = str(value).strip()
            if text:
                return text
    return ""


def _first_list(*values: Any) -> list[Any]:
    for value in values:
        if isinstance(value, list):
            return value
    return []


def _normalize_education_item(item: Any) -> dict[str, Any]:
    raw = item if isinstance(item, dict) else {"raw_text": str(item)}
    period = _period_text(raw.get("period") or raw.get("time") or raw.get("date_range") or raw.get("duration"), raw)
    return {
        **raw,
        "school": _first_text(raw.get("school"), raw.get("university"), raw.get("college"), raw.get("name")),
        "university": _first_text(raw.get("school"), raw.get("university"), raw.get("college"), raw.get("name")),
        "college": _first_text(raw.get("school"), raw.get("university"), raw.get("college"), raw.get("name")),
        "major": _first_text(raw.get("major"), raw.get("profession"), raw.get("field")),
        "profession": _first_text(raw.get("major"), raw.get("profession"), raw.get("field")),
        "field": _first_text(raw.get("major"), raw.get("profession"), raw.get("field")),
        "degree": _first_text(raw.get("degree"), raw.get("education"), raw.get("level")),
        "education": _first_text(raw.get("degree"), raw.get("education"), raw.get("level")),
        "level": _first_text(raw.get("degree"), raw.get("education"), raw.get("level")),
        "period": period,
        "time": period,
        "date_range": period,
        "duration": period,
    }


def _normalize_work_item(item: Any) -> dict[str, Any]:
    raw = item if isinstance(item, dict) else {"raw_text": str(item)}
    period = _period_text(raw.get("period") or raw.get("time") or raw.get("date_range") or raw.get("duration"), raw)
    description = raw.get("description") or raw.get("responsibilities") or raw.get("duties") or ""
    if isinstance(description, list):
        description = "\n".join(str(part).strip() for part in description if str(part).strip())
    position = _first_text(raw.get("position"), raw.get("job_title"), raw.get("title"), raw.get("role"))
    company = _first_text(raw.get("company"), raw.get("company_name"), raw.get("name"))
    return {
        **raw,
        "company": company,
        "company_name": company,
        "position": position,
        "job_title": position,
        "title": position,
        "role": position,
        "period": period,
        "time": period,
        "date_range": period,
        "duration": period,
        "description": str(description).strip(),
        "responsibilities": description,
        "duties": description,
    }


def _period_text(value: Any, raw: dict[str, Any]) -> str:
    text = _first_text(value)
    if text:
        return text
    start = _first_text(raw.get("start_date"))
    end = _first_text(raw.get("end_date")) or "至今"
    if start:
        return f"{start.replace('-', '.')} - {end.replace('-', '.')}"
    return ""


def _highest_degree(education_list: list[dict[str, Any]]) -> str:
    rank = {"博士": 6, "硕士": 5, "研究生": 4, "本科": 3, "学士": 3, "大专": 2, "中专": 1, "高中": 1}
    best = ""
    best_rank = -1
    for item in education_list:
        degree = str(item.get("degree") or "").strip()
        current_rank = max((score for key, score in rank.items() if key in degree), default=0)
        if degree and current_rank >= best_rank:
            best = degree
            best_rank = current_rank
    return best


def _estimate_experience(work_list: list[dict[str, Any]]) -> str:
    total_months = 0
    for item in work_list:
        start = _date_to_month(item.get("start_date"))
        end = _date_to_month(item.get("end_date")) or _date_to_month(item.get("start_date"))
        if start and end and end >= start:
            total_months += end - start + 1
    if total_months <= 0:
        return ""
    years, months = divmod(total_months, 12)
    if years and months:
        return f"约{years}年{months}个月"
    if years:
        return f"约{years}年"
    return f"约{months}个月"


def _date_to_month(value: Any) -> int | None:
    text = _first_text(value)
    match = re.search(r"(\d{4})[-./年](\d{1,2})", text)
    if not match:
        return None
    return int(match.group(1)) * 12 + int(match.group(2))
