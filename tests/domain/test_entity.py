from project_sentinel.domain.common import Entity


def test_entity_has_id():
    entity = Entity()
    assert entity.id is not None


def test_entity_touch():
    entity = Entity()

    before = entity.audit.updated_at

    entity.touch()

    assert entity.audit.updated_at >= before
