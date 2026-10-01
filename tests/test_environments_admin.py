import re
from typing import Callable, List, Tuple

import pytest
from sqlalchemy import func, select

from its_on.models import environments, switch_environments, switch_history, switches

SWITCH_FORM = [('is_active', '1'), ('groups', 'group1, group2'), ('ttl', '5'), ('comment', 'new')]
STAGING_ID, PRODUCTION_ID, QA_ID = 1, 2, 3


@pytest.fixture()
def get_environment_states(db_conn_acquirer) -> Callable:
    async def _with_params(switch_id: int) -> List[Tuple[int, bool]]:
        query = (
            switch_environments.select()
            .where(switch_environments.c.switch_id == switch_id)
            .order_by(switch_environments.c.environment_id)
        )
        async with db_conn_acquirer() as conn:
            result = await conn.execute(query)
            return [(row.environment_id, row.is_active) for row in await result.fetchall()]

    return _with_params


@pytest.fixture()
def get_environment_history(db_conn_acquirer) -> Callable:
    async def _with_params(switch_id: int) -> List[Tuple[str, str]]:
        query = switch_history.select().where(
            switch_history.c.switch_id == switch_id,
            switch_history.c.environment.isnot(None),
        )
        async with db_conn_acquirer() as conn:
            result = await conn.execute(query)
            return sorted((row.environment, row.new_value) for row in await result.fetchall())

    return _with_params


@pytest.fixture()
def count_environments(db_conn_acquirer) -> Callable:
    async def _with_params(name: str) -> int:
        async with db_conn_acquirer() as conn:
            return await conn.scalar(
                select([func.count()]).select_from(environments).where(environments.c.name == name),
            )

    return _with_params


def get_flash_message(content: str) -> str:
    match = re.search(r'well well-sm (?:success|error)">(.*?)</div>', content, re.S)
    return match.group(1) if match else ''


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__environment_list_view__without_login__redirects_to_login(client, login_path):
    """
    Arrange: неавторизованный клиент
    Act: открываем список окружений
    Assert: нас перекинуло на страницу логина
    """
    response = await client.get('/zbs/environments')

    assert response.status == 200
    assert response.url.path == login_path


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__environment_list_view__shows_environments_with_usage_count(client):
    """
    Arrange: три окружения, staging и production привязаны к двум флагам, qa - ни к одному
    Act: открываем список окружений суперюзером
    Assert: отображаются все имена и количество флагов
    """
    response = await client.get('/zbs/environments')

    content = await response.text()
    assert response.status == 200
    assert re.findall(r'<td>(\w+)</td>\s*<td>(\d+) flags</td>', content) == [
        ('production', '2'), ('qa', '0'), ('staging', '2'),
    ]


@pytest.mark.usefixtures('setup_tables_and_data', 'user_login')
@pytest.mark.parametrize('method,path', [
    ('get', '/zbs/environments'),
    ('get', '/zbs/environments/add'),
    ('post', '/zbs/environments/add'),
    ('post', f'/zbs/environments/{STAGING_ID}/delete'),
], ids=['list', 'add_form', 'add_submit', 'delete'])
async def test__environment_admin_views__not_superuser__forbidden(
    client, count_environments, method, path,
):
    """
    Arrange: авторизованный пользователь без прав суперюзера
    Act: обращаемся ко всем страницам справочника окружений
    Assert: получаем 403, окружение staging на месте
    """
    response = await getattr(client, method)(path, data={'name': 'forbidden-env'})

    assert response.status == 403
    assert await count_environments('staging') == 1
    assert await count_environments('forbidden-env') == 0


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
@pytest.mark.parametrize('name', ['new-env', 'qa-1', 'prod'])
async def test__environment_add_view__valid_slug__creates_environment(
    client, count_environments, name,
):
    """
    Arrange: суперюзер и корректное slug-имя окружения
    Act: отправляем форму добавления
    Assert: редирект на список, окружение создано
    """
    response = await client.post(
        '/zbs/environments/add', data={'name': name}, allow_redirects=False,
    )

    assert response.status == 302
    assert response.headers['Location'] == '/zbs/environments'
    assert await count_environments(name) == 1


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
@pytest.mark.parametrize('name', [
    'Bad_Name', 'two words', 'Prod', 'стейдж', '-env', 'env-', 'a--b', '',
], ids=['underscore', 'space', 'uppercase', 'cyrillic', 'leading_hyphen', 'trailing_hyphen',
        'double_hyphen', 'empty'])
async def test__environment_add_view__invalid_name__shows_error_and_does_not_create(
    client, count_environments, name,
):
    """
    Arrange: суперюзер и имя, не являющееся slug
    Act: отправляем форму добавления
    Assert: показана ошибка валидации, окружение не создано
    """
    response = await client.post('/zbs/environments/add', data={'name': name})

    content = await response.text()
    assert response.status == 200
    assert 'well-sm error' in content
    assert await count_environments(name) == 0


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__environment_add_view__duplicate_name__shows_error(client, count_environments):
    """
    Arrange: окружение staging уже существует
    Act: пытаемся добавить окружение с тем же именем
    Assert: показана ошибка, дубль не создан
    """
    response = await client.post('/zbs/environments/add', data={'name': 'staging'})

    assert response.status == 200
    assert 'well-sm error' in await response.text()
    assert await count_environments('staging') == 1


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__environment_delete_view__removes_environment_and_cascades(
    client, count_environments, get_environment_states,
):
    """
    Arrange: staging привязан к switch1 и switch3, production - к switch1 и switch4
    Act: удаляем окружение staging
    Assert: staging исчез, его привязки удалены каскадом, привязки production остались
    """
    response = await client.post(
        f'/zbs/environments/{STAGING_ID}/delete', allow_redirects=False,
    )

    assert response.status == 302
    assert await count_environments('staging') == 0
    assert await get_environment_states(1) == [(PRODUCTION_ID, False)]
    assert await get_environment_states(3) == []
    assert await get_environment_states(4) == [(PRODUCTION_ID, True)]


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__shows_environments_block(client):
    """
    Arrange: у switch1 staging включен и активен, production включен и выключен
    Act: открываем страницу флага
    Assert: в блоке перечислены все окружения справочника, включая непривязанное qa
    """
    response = await client.get('/zbs/switches/1')

    content = await response.text()
    assert response.status == 200
    for name in ('staging', 'production', 'qa'):
        assert f'<td>{name}</td>' in content
    assert f'name="environment_ids" value="{QA_ID}"' in content
    assert re.search(rf'value="{STAGING_ID}"\s+checked="checked"', content)
    assert not re.search(rf'value="{QA_ID}"\s+checked="checked"', content)


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__post_syncs_environments_without_touching_switch_fields(
    client, db_conn_acquirer, get_environment_states,
):
    """
    Arrange: у switch1 привязаны staging (вкл.) и production (выкл.)
    Act: сохраняем форму: staging активен, production снят, qa добавлен без активности
    Assert: привязки синхронизированы, скалярные поля обновились, форма не упала на лишних полях
    """
    data = SWITCH_FORM + [
        ('environment_ids', str(STAGING_ID)),
        ('environment_ids', str(QA_ID)),
        (f'environment_active_{STAGING_ID}', '1'),
    ]

    response = await client.post('/zbs/switches/1', data=data)

    assert response.status == 200
    assert get_flash_message(await response.text()) == 'Updated'
    assert await get_environment_states(1) == [(STAGING_ID, True), (QA_ID, False)]
    async with db_conn_acquirer() as conn:
        result = await conn.execute(switches.select().where(switches.c.id == 1))
        switch = await result.first()
    assert switch.comment == 'new'
    assert switch.ttl == 5


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__post_toggles_environment_activity(
    client, get_environment_states,
):
    """
    Arrange: у switch1 staging активен, production неактивен
    Act: сохраняем форму, поменяв активность местами
    Assert: is_active окружений поменялись
    """
    data = SWITCH_FORM + [
        ('environment_ids', str(STAGING_ID)),
        ('environment_ids', str(PRODUCTION_ID)),
        (f'environment_active_{PRODUCTION_ID}', '1'),
    ]

    await client.post('/zbs/switches/1', data=data)

    assert await get_environment_states(1) == [(STAGING_ID, False), (PRODUCTION_ID, True)]


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__post_without_environments__removes_all_overrides(
    client, get_environment_states,
):
    """
    Arrange: у switch1 есть привязки к двум окружениям
    Act: сохраняем форму без полей окружений
    Assert: все привязки удалены, флаг снова глобальный
    """
    response = await client.post('/zbs/switches/1', data=SWITCH_FORM)

    assert get_flash_message(await response.text()) == 'Updated'
    assert await get_environment_states(1) == []


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__post_unknown_environment__ignored(
    client, get_environment_states,
):
    """
    Arrange: окружения с id 999 нет в справочнике
    Act: сохраняем форму с этим id и валидным production
    Assert: несуществующее окружение проигнорировано, production сохранен
    """
    data = SWITCH_FORM + [('environment_ids', '999'), ('environment_ids', str(PRODUCTION_ID))]

    response = await client.post('/zbs/switches/1', data=data)

    assert get_flash_message(await response.text()) == 'Updated'
    assert await get_environment_states(1) == [(PRODUCTION_ID, False)]


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__post_invalid_environment_id__shows_error_and_keeps_state(
    client, get_environment_states,
):
    """
    Arrange: у switch1 привязаны staging и production
    Act: сохраняем форму с нечисловым id окружения
    Assert: показана ошибка, привязки не изменились
    """
    data = SWITCH_FORM + [('environment_ids', 'abc')]

    response = await client.post('/zbs/switches/1', data=data)

    assert get_flash_message(await response.text()) == 'Invalid environment id.'
    assert await get_environment_states(1) == [(STAGING_ID, True), (PRODUCTION_ID, False)]


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__post_invalid_switch_fields__keeps_environments(
    client, get_environment_states,
):
    """
    Arrange: у switch1 привязаны staging и production
    Act: сохраняем форму с пустым списком групп и другими окружениями
    Assert: показана ошибка валидации, привязки окружений не изменились
    """
    data = [('is_active', '1'), ('groups', ''), ('ttl', '5'), ('environment_ids', str(QA_ID))]

    response = await client.post('/zbs/switches/1', data=data)

    assert 'At least one group is required.' in await response.text()
    assert await get_environment_states(1) == [(STAGING_ID, True), (PRODUCTION_ID, False)]


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__post_environment_changes__saved_to_history(
    client, get_environment_history,
):
    """
    Arrange: у switch1 staging активен, production неактивен
    Act: выключаем staging, отвязываем production, привязываем qa с активностью
    Assert: в истории по одной записи на каждое окружение с именем и новым значением
    """
    data = SWITCH_FORM + [
        ('environment_ids', str(STAGING_ID)),
        ('environment_ids', str(QA_ID)),
        (f'environment_active_{QA_ID}', '1'),
    ]

    await client.post('/zbs/switches/1', data=data)

    assert await get_environment_history(1) == [
        ('production', 'removed'), ('qa', '1'), ('staging', '0'),
    ]


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__post_unchanged_environments__no_environment_history(
    client, get_environment_history,
):
    """
    Arrange: у switch1 staging активен, production неактивен
    Act: сохраняем форму с теми же состояниями окружений
    Assert: записей истории по окружениям нет
    """
    data = SWITCH_FORM + [
        ('environment_ids', str(STAGING_ID)),
        ('environment_ids', str(PRODUCTION_ID)),
        (f'environment_active_{STAGING_ID}', '1'),
    ]

    await client.post('/zbs/switches/1', data=data)

    assert await get_environment_history(1) == []


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__history_table_shows_environment_name(client):
    """
    Arrange: сохранили форму, отвязав production от switch1
    Act: открываем страницу флага
    Assert: в таблице History есть колонка Environment и запись об удалении production
    """
    await client.post('/zbs/switches/1', data=SWITCH_FORM + [('environment_ids', str(STAGING_ID))])

    response = await client.get('/zbs/switches/1')

    history_block = (await response.text()).split('id="collapseTwo"')[1]
    assert '<th>Environment</th>' in history_block
    assert re.search(r'<td>production</td>\s*<td>\s*removed\s*</td>', history_block)


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
@pytest.mark.parametrize('is_active,expected_history_count', [
    ('1', 0),
    ('0', 1),
], ids=['is_active_unchanged', 'is_active_changed'])
async def test__switch_detail_view__post__writes_flag_history_only_when_is_active_changed(
    client, db_conn_acquirer, is_active, expected_history_count,
):
    """
    Arrange: switch1 активен, окружения в форме не меняются
    Act: сохраняем форму с тем же и с другим значением is_active
    Assert: запись об общем состоянии флага появляется только при изменении is_active
    """
    data = [
        ('is_active', is_active), ('groups', 'group1, group2'), ('ttl', '5'),
        ('environment_ids', str(STAGING_ID)), ('environment_ids', str(PRODUCTION_ID)),
        (f'environment_active_{STAGING_ID}', '1'),
    ]

    await client.post('/zbs/switches/1', data=data)

    async with db_conn_acquirer() as conn:
        result = await conn.execute(
            switch_history.select().where(
                switch_history.c.switch_id == 1, switch_history.c.environment.is_(None),
            ),
        )
        assert len(await result.fetchall()) == expected_history_count


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__environment_change_only__single_history_row(
    client, db_conn_acquirer,
):
    """
    Arrange: у switch1 staging активен, production неактивен
    Act: сохраняем форму, выключив только staging
    Assert: в истории ровно одна запись - про staging
    """
    data = SWITCH_FORM + [
        ('environment_ids', str(STAGING_ID)), ('environment_ids', str(PRODUCTION_ID)),
    ]

    await client.post('/zbs/switches/1', data=data)

    async with db_conn_acquirer() as conn:
        result = await conn.execute(switch_history.select().where(switch_history.c.switch_id == 1))
        rows = await result.fetchall()
    assert [(row.environment, row.new_value) for row in rows] == [('staging', '0')]


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test__switch_detail_view__history_table_labels_flag_level_changes(client):
    """
    Arrange: сохранили форму, выключив весь флаг
    Act: открываем страницу флага
    Assert: запись об общем состоянии подписана Whole flag
    """
    await client.post('/zbs/switches/1', data=[('is_active', '0'), ('groups', 'group1')])

    response = await client.get('/zbs/switches/1')

    history_block = (await response.text()).split('id="collapseTwo"')[1]
    assert '<td>Whole flag</td>' in history_block
