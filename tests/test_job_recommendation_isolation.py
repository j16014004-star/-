import asyncio
from types import SimpleNamespace

from app.routers.jobs import job_to_dict
from app.services.job_service import get_recommendations


class Result:
    def __init__(self, *, one=None, scalar_value=None, rows=None):
        self.one = one
        self.scalar_value = scalar_value
        self.rows = rows or []

    def scalar_one_or_none(self):
        return self.one

    def scalar(self):
        return self.scalar_value

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return self.responses.pop(0)


def test_new_user_without_recommendation_task_gets_empty_page():
    db = FakeSession([Result(one=None)])

    payload = asyncio.run(get_recommendations(db, user_id=90210))

    assert payload == {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 10,
    }


def test_recommendation_query_is_scoped_to_current_user_and_latest_task():
    task = SimpleNamespace(id="task-user-7", status="success")
    db = FakeSession([
        Result(one=task),
        Result(scalar_value=0),
        Result(rows=[]),
    ])

    payload = asyncio.run(get_recommendations(db, user_id=7, source="58"))

    assert payload["total"] == 0
    assert len(db.statements) == 3
    task_params = db.statements[0].compile().params
    count_params = db.statements[1].compile().params
    page_params = db.statements[2].compile().params
    assert 7 in task_params.values()
    assert "task-user-7" in count_params.values()
    assert 7 in count_params.values()
    assert "task-user-7" in page_params.values()
    assert 7 in page_params.values()


def test_job_serializer_uses_user_specific_match_values():
    job = SimpleNamespace(
        id=11,
        company="Example",
        company_logo=None,
        title="Python Backend Engineer",
        salary_min=10000,
        salary_max=15000,
        city="Xi'an",
        experience_required="1-3 years",
        education_required="Bachelor",
        skills=["Python"],
        description=None,
        match_score=12,
        match_reasons=["global value"],
        source="58",
        source_name="58.com",
        source_url="https://xa.58.com/example",
        is_active=True,
        crawl_time=None,
        created_at=None,
    )
    recommendation = SimpleNamespace(
        match_score=88,
        match_reasons=["current user match"],
    )

    payload = job_to_dict(job, recommendation=recommendation)

    assert payload["match_score"] == 88
    assert payload["match_reasons"] == ["current user match"]
