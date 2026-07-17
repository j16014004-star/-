"""岗位推荐的搜索意图归一化与可解释规则评分。"""
from __future__ import annotations

import re
from typing import Any

from app.ai.knowledge import KnowledgeChunk
from app.crawlers.job_58_playwright import Job58PlaywrightCrawler
from app.services.skills_service import normalize_skills


ROLE_PROFILES = (
    {
        "markers": ("python", "fastapi", "django", "flask"),
        "role": "Python后端开发工程师",
        "queries": ("Python后端开发", "Python开发工程师", "后端开发工程师"),
        "title_terms": ("python", "后端", "服务端", "程序员"),
    },
    {
        "markers": ("java", "spring"),
        "role": "Java开发工程师",
        "queries": ("Java开发工程师", "Java后端开发", "后端开发工程师"),
        "title_terms": ("java", "后端", "服务端", "程序员"),
    },
    {
        "markers": ("vue", "react", "javascript", "typescript", "前端"),
        "role": "Web前端开发工程师",
        "queries": ("Web前端开发", "前端开发工程师", "Vue前端开发"),
        "title_terms": ("前端", "web", "vue", "react"),
    },
    {
        "markers": (
            "秘书学", "秘书", "文秘", "行政助理", "办公室文员",
            "综合文员", "经理助理", "公文写作", "会议纪要", "档案管理",
        ),
        "role": "秘书/行政助理",
        "queries": ("秘书", "行政助理", "文秘", "办公室文员"),
        "title_terms": (
            "秘书", "文秘", "行政助理", "办公室文员", "综合文员",
            "经理助理", "总经理助理", "董事长助理",
        ),
    },
    {
        "markers": ("数据分析", "pandas", "excel", "数据处理"),
        "role": "数据分析师",
        "queries": ("数据分析师", "数据分析专员", "数据运营"),
        "title_terms": ("数据分析", "数据运营", "数据专员", "数据处理"),
    },
    {
        "markers": ("厨师", "面点师", "西餐", "中餐"),
        "role": "厨师",
        "queries": ("厨师", "中餐厨师", "餐饮厨师"),
        "title_terms": ("厨师", "炒锅", "后厨", "面点"),
    },
)

GENERIC_ROLE_WORDS = {
    "工程师", "开发", "专员", "助理", "人员", "岗位", "职位", "高级", "初级", "中级",
    "办公室", "综合",
}


def clean_text(value: str | None, max_length: int = 100) -> str | None:
    if not value:
        return None
    cleaned = " ".join(str(value).split()).strip()
    return cleaned[:max_length] or None


def normalize_city(value: str | None) -> str | None:
    cleaned = clean_text(value, 50)
    if not cleaned:
        return None
    city = re.sub(r"(市|城区)$", "", cleaned)
    return city if city in Job58PlaywrightCrawler.CITY_CODES else None


def infer_target_city(structured_data: dict | None, extracted_text: str | None) -> str:
    data = structured_data or {}
    basic = data.get("basic_info") if isinstance(data.get("basic_info"), dict) else {}
    candidates = [
        data.get("target_city"), data.get("city"), basic.get("location"), basic.get("city"),
    ]
    text = extracted_text or ""
    for pattern in (
        r"(?:期望城市|目标城市|工作城市|现居)[：:]\s*([\u4e00-\u9fff]{2,5})",
        r"(?:所在地|居住地)[：:]\s*([\u4e00-\u9fff]{2,5})",
    ):
        match = re.search(pattern, text)
        if match:
            candidates.append(match.group(1))
    for value in candidates:
        city = normalize_city(value)
        if city:
            return city
    return "北京"


def _profile_for_text(*values: str) -> dict[str, Any] | None:
    combined = " ".join(values).lower()
    for profile in ROLE_PROFILES:
        if any(marker in combined for marker in profile["markers"]):
            return profile
    return None


def infer_target_role(
    structured_data: dict | None,
    extracted_text: str | None,
    skills: list[str],
) -> str:
    """从明确的简历求职意向优先推断岗位，技能只作为最后回退。"""
    data = structured_data or {}
    basic = data.get("basic_info") if isinstance(data.get("basic_info"), dict) else {}
    for key in (
        "target_role", "desired_position", "expected_position", "job_intention", "career_objective",
    ):
        candidate = clean_text(data.get(key) or basic.get(key))
        if candidate:
            return candidate

    text = extracted_text or ""
    for pattern in (
        r"(?:目标岗位|期望岗位|求职意向|应聘岗位)[：:]\s*([^\n，,；;]{2,30})",
        r"(?:岗位方向|职业方向)[：:]\s*([^\n，,；;]{2,30})",
    ):
        match = re.search(pattern, text)
        if match:
            candidate = clean_text(match.group(1))
            if candidate:
                return candidate

    profile = _profile_for_text(*skills, text[:2000])
    if profile:
        return profile["role"]
    return f"{skills[0]}相关岗位" if skills else "通用岗位"


def build_search_keywords(target_role: str, skills: list[str], max_items: int = 4) -> list[str]:
    """把目标岗位转换为招聘网站常用搜索词，禁止直接拿长技能短语搜索。"""
    target = clean_text(target_role) or ""
    profile = _profile_for_text(target) or _profile_for_text(*skills)
    candidates: list[str] = [target]
    if profile:
        candidates.extend(profile["queries"])

    # 未命中预设职业时仍以用户目标岗位为核心，只补一个短职业词。
    if not profile:
        short_role = re.sub(r"(高级|中级|初级|资深|实习)", "", target).strip()
        candidates.append(short_role)

    result: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        value = clean_text(value, 40) or ""
        key = value.lower().replace(" ", "")
        if not value or key in seen or value == "通用岗位":
            continue
        seen.add(key)
        result.append(value)
        if len(result) >= max_items:
            break
    return result


def expand_search_keywords_from_knowledge(
    target_role: str,
    existing: list[str],
    chunks: list[KnowledgeChunk],
    max_items: int = 5,
) -> list[str]:
    """Add only aliases from the KB line that explicitly names the selected role."""
    result = list(existing)
    seen = {item.lower().replace(" ", "") for item in result}
    role_key = (clean_text(target_role) or "").lower().replace(" ", "")
    for chunk in chunks:
        for line in chunk.content.splitlines():
            compact_line = line.lower().replace(" ", "")
            if role_key and role_key not in compact_line:
                continue
            parts = re.split(r"[：:]", line, maxsplit=1)
            if len(parts) != 2:
                continue
            for alias in re.split(r"[、，,；;。]", parts[1]):
                candidate = clean_text(alias, 40) or ""
                key = candidate.lower().replace(" ", "")
                if len(candidate) < 2 or key in seen:
                    continue
                seen.add(key)
                result.append(candidate)
                if len(result) >= max_items:
                    return result
    return result[:max_items]


def role_title_terms(target_role: str, skills: list[str]) -> list[str]:
    profile = _profile_for_text(target_role) or _profile_for_text(*skills)
    if profile:
        return list(profile["title_terms"])
    terms = re.findall(r"[A-Za-z][A-Za-z0-9.+#-]*|[\u4e00-\u9fff]{2,6}", target_role.lower())
    return [term for term in terms if term not in GENERIC_ROLE_WORDS]


def score_job_match(
    *,
    target_role: str,
    target_city: str,
    resume_skills: list[str],
    job_title: str,
    job_city: str | None,
    job_skills: list[str],
    job_description: str | None,
    knowledge_context: str | None = None,
) -> tuple[int, list[str], list[str], bool]:
    """先做岗位方向门控，再按岗位方向、技能、城市和数据完整度评分。"""
    title_lower = (job_title or "").lower()
    searchable = f"{job_title} {job_description or ''} {' '.join(job_skills or [])}".lower()
    terms = role_title_terms(target_role, resume_skills)
    title_hits = [term for term in terms if term.lower() in title_lower]
    direction_relevant = bool(title_hits)

    normalized_resume = normalize_skills(resume_skills)
    matched_skills = [skill for skill in normalized_resume if skill.lower() in searchable]
    matched_skills = normalize_skills(matched_skills)

    # 岗位标题必须命中目标方向。仅技能偶然出现在福利/描述中不能进入推荐列表。
    if not direction_relevant:
        return 0, matched_skills, ["岗位方向与目标岗位不一致"], False

    exact_role = (clean_text(target_role) or "").lower().replace(" ", "")
    compact_title = title_lower.replace(" ", "")
    if exact_role and (exact_role in compact_title or compact_title in exact_role):
        direction_score = 45
    else:
        direction_score = min(45, 25 + 10 * len(set(title_hits)))

    skill_score = (
        round(len(matched_skills) * 35 / len(normalized_resume))
        if normalized_resume else 0
    )
    city_score = 15 if normalize_city(job_city) == normalize_city(target_city) else 0
    completeness_score = 5 if job_description or job_skills else 0
    knowledge_score = 0
    if knowledge_context and any(
        term.lower() in knowledge_context.lower() for term in title_hits
    ):
        knowledge_score = 5
    score = min(
        100,
        direction_score + skill_score + city_score + completeness_score + knowledge_score,
    )

    reasons = [f"岗位方向匹配：{', '.join(title_hits[:3])}"]
    if matched_skills:
        reasons.append(f"技能匹配：{', '.join(matched_skills[:5])}")
    if city_score:
        reasons.append(f"工作城市匹配：{target_city}")
    if knowledge_score:
        reasons.append("岗位方向符合推荐知识库规范")
    return score, matched_skills, reasons, True
