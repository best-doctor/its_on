from types import SimpleNamespace

import pytest

from its_on.cache import switch_list_cache_key_builder


@pytest.fixture()
def make_view():
    def _with_params(validated_data: dict) -> SimpleNamespace:
        return SimpleNamespace(request={'validated_data': validated_data})

    return _with_params


@pytest.mark.parametrize('validated_data,expected_key', [
    ({'group': 'group1'}, 'switch_list__group1__None__None__None'),
    (
        {'group': 'group1', 'version': 4, 'is_active': True},
        'switch_list__group1__4__True__None',
    ),
    (
        {'group': 'group1', 'environment': 'staging'},
        'switch_list__group1__None__None__staging',
    ),
])
def test__switch_list_cache_key_builder__key_format(make_view, validated_data, expected_key):
    """
    Arrange: view с разными провалидированными параметрами запроса
    Act: строим ключ кэша
    Assert: ключ содержит group, version, is_active и environment
    """
    key = switch_list_cache_key_builder(method=lambda: None, view=make_view(validated_data))

    assert key == expected_key


def test__switch_list_cache_key_builder__different_environments_have_different_keys(make_view):
    """
    Arrange: два запроса одной группы для разных окружений
    Act: строим ключи кэша
    Assert: ключи различаются, ответы окружений не перепутаются
    """
    staging_key = switch_list_cache_key_builder(
        method=lambda: None, view=make_view({'group': 'group1', 'environment': 'staging'}),
    )
    production_key = switch_list_cache_key_builder(
        method=lambda: None, view=make_view({'group': 'group1', 'environment': 'production'}),
    )

    assert staging_key != production_key
