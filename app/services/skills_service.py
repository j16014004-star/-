"""岗位推荐共用的规则技能处理"""

SKILL_KEYWORDS = (
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
    "FastAPI", "Flask", "Django", "Spring", "Spring Boot", "Vue", "React", "Angular",
    "MySQL", "Redis", "MongoDB", "PostgreSQL", "Elasticsearch", "Docker", "Kubernetes",
    "Git", "Linux", "Nginx", "Node.js", "SQLAlchemy", "Pydantic", "JWT", "OAuth",
    "RESTful", "WebSocket", "Celery", "RabbitMQ", "Kafka", "TensorFlow", "PyTorch",
    "pandas", "NumPy", "AWS", "Azure", "GCP", "Excel",
    "厨师", "面点师", "西餐厨师", "中餐厨师", "服务员", "收银员", "店员", "营业员",
    "销售", "客服", "前台", "文员", "行政", "人事", "司机", "仓管", "保安", "保洁",
    "普工", "技工", "电工", "焊工", "叉车", "会计", "出纳", "财务", "运营", "设计",
    "剪辑", "摄影", "主播", "教师", "助教", "护士", "美容师", "美发师",
)

ALIASES = {
    "js": "JavaScript",
    "vue.js": "Vue",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "postgres": "PostgreSQL",
}


def normalize_skills(skills: list[str], max_items: int = 20) -> list[str]:
    """规范化、去重并限制技能数量。"""
    result: list[str] = []
    seen: set[str] = set()
    for value in skills:
        if not isinstance(value, str):
            continue
        raw = value.strip()
        if not raw:
            continue
        normalized = ALIASES.get(raw.lower(), raw)
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            result.append(normalized)
        if len(result) >= max_items:
            break
    return result


def extract_skills_from_text(text: str, max_items: int = 20) -> list[str]:
    """从简历或岗位文本中按受控词典提取技能。"""
    text_lower = text.lower()
    found = [skill for skill in SKILL_KEYWORDS if skill.lower() in text_lower]
    return normalize_skills(found, max_items)


def get_resume_skills(structured_data: dict | None, extracted_text: str | None) -> list[str]:
    """优先使用结构化技能，缺失时回退全文提取。"""
    structured = (structured_data or {}).get("skills", [])
    skills = normalize_skills(structured if isinstance(structured, list) else [])
    return skills or extract_skills_from_text(extracted_text or "")


def score_skills(resume_skills: list[str], job_skills: list[str]) -> tuple[int, list[str], list[str]]:
    """计算规则匹配分、命中技能和展示原因。"""
    resume_map = {skill.lower(): skill for skill in normalize_skills(resume_skills)}
    matched = [skill for skill in normalize_skills(job_skills) if skill.lower() in resume_map]
    matched = normalize_skills(matched)
    score = int(len(matched) * 100 / len(resume_map)) if resume_map else 0
    reasons = [f"技能匹配度 {score}%"] + [f"匹配: {skill}" for skill in matched[:5]]
    return score, matched, reasons
