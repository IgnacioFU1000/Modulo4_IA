import pytest
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime, timezone


def create_and_manage_room(name, location, capacity, description, equipment_list, created_by_user_id, repository, audit_service, notification_service):
    if not name or len(name.strip()) < 3 or len(name.strip()) > 100:
        raise ValueError("Nombre inválido")
    if not location or len(location.strip()) < 5 or len(location.strip()) > 150:
        raise ValueError("Ubicación inválida")
    if capacity <= 0 or capacity > 500:
        raise ValueError("Capacidad inválida")
    if description and len(description.strip()) > 1000:
        raise ValueError("Descripción demasiado larga")

    if repository.exists_name(name.strip()):
        raise ValueError("El nombre ya existe")

    room_dict = {
        'id': str(uuid4()),
        'name': name.strip(),
        'location': location.strip(),
        'capacity': capacity,
        'description': description.strip() if description else None,
        'equipment': equipment_list if equipment_list else [],
        'is_active': True,
        'created_by': created_by_user_id,
        'created_at': datetime.now(timezone.utc),
    }

    try:
        saved_room = repository.save(room_dict)
    except Exception:
        raise

    try:
        audit_service.log(
            action='ROOM_CREATED',
            entity_id=saved_room['id'],
            actor_id=created_by_user_id,
            details={'name': name, 'capacity': capacity},
        )
    except Exception:
        pass

    try:
        if notification_service:
            notification_service.send_email(
                to='admin@company.com',
                subject=f'Nueva sala creada: {name}',
                body=f'La sala {name} ha sido creada con capacidad {capacity}',
            )
    except Exception:
        pass

    if hasattr(repository, 'cache'):
        try:
            repository.cache.invalidate('all_rooms')
        except Exception:
            pass

    return saved_room


class RoomService:
    def __init__(self, repository, audit_service, notification_service, cache_service):
        self.repository = repository
        self.audit_service = audit_service
        self.notification_service = notification_service
        self.cache_service = cache_service

    def process_room_update(self, room_id, updates, user_id):
        room = self.repository.find_by_id(room_id)
        if not room:
            raise ValueError("Sala no encontrada")

        if 'name' in updates:
            new_name = updates['name']
            if not new_name or len(new_name.strip()) < 3:
                raise ValueError("Nombre inválido")
            if self.repository.exists_name(new_name.strip(), exclude_id=room_id):
                raise ValueError("El nombre ya existe")
            room['name'] = new_name.strip()

        if 'location' in updates:
            new_location = updates['location']
            if not new_location or len(new_location.strip()) < 5:
                raise ValueError("Ubicación inválida")
            room['location'] = new_location.strip()

        if 'capacity' in updates:
            new_capacity = updates['capacity']
            if new_capacity <= 0 or new_capacity > 500:
                raise ValueError("Capacidad inválida")
            room['capacity'] = new_capacity

        if 'description' in updates:
            new_description = updates['description']
            if new_description and len(new_description.strip()) > 1000:
                raise ValueError("Descripción demasiado larga")
            room['description'] = new_description.strip() if new_description else None

        if 'equipment' in updates:
            room['equipment'] = updates['equipment']

        room['updated_at'] = datetime.now(timezone.utc)
        room['updated_by'] = user_id

        updated_room = self.repository.save(room)

        self.audit_service.log(
            action='ROOM_UPDATED',
            entity_id=updated_room['id'],
            actor_id=user_id,
            details=updates,
        )

        try:
            self.notification_service.send_email(
                to='admin@company.com',
                subject=f'Sala actualizada: {updated_room["name"]}',
                body=f'La sala {updated_room["name"]} ha sido actualizada',
            )
        except Exception:
            pass

        try:
            self.cache_service.invalidate('all_rooms')
        except Exception:
            pass

        return updated_room


@pytest.fixture
def mock_repository():
    repository = Mock()
    repository.exists_name.return_value = False
    repository.save.return_value = {
        'id': str(uuid4()),
        'name': 'Sala Madrid',
        'location': 'Edificio A - Planta 2',
        'capacity': 10,
        'description': None,
        'equipment': [],
        'is_active': True,
        'created_by': str(uuid4()),
        'created_at': datetime.now(timezone.utc),
    }
    repository.find_by_id.return_value = {
        'id': str(uuid4()),
        'name': 'Sala Existente',
        'location': 'Edificio A',
        'capacity': 8,
        'description': None,
        'equipment': [],
        'is_active': True,
        'created_by': str(uuid4()),
        'created_at': datetime.now(timezone.utc),
    }
    return repository


@pytest.fixture
def mock_audit_service():
    return Mock()


@pytest.fixture
def mock_notification_service():
    return Mock()


@pytest.fixture
def mock_cache_service():
    return Mock()


class TestCreateAndManageRoom:
    def test_valid_room_creation(self, mock_repository, mock_audit_service, mock_notification_service):
        user_id = uuid4()
        mock_repository.save.return_value = {
            'id': str(uuid4()),
            'name': 'Sala Madrid',
            'location': 'Edificio A - Planta 2',
            'capacity': 10,
            'description': None,
            'equipment': ['Pantalla'],
            'is_active': True,
            'created_by': user_id,
            'created_at': datetime.now(timezone.utc),
        }

        result = create_and_manage_room(
            name='Sala Madrid',
            location='Edificio A - Planta 2',
            capacity=10,
            description=None,
            equipment_list=['Pantalla'],
            created_by_user_id=user_id,
            repository=mock_repository,
            audit_service=mock_audit_service,
            notification_service=mock_notification_service,
        )

        assert result['name'] == 'Sala Madrid'
        assert result['capacity'] == 10
        mock_repository.save.assert_called_once()
        mock_audit_service.log.assert_called_once()

    @pytest.mark.parametrize('name', ['', 'AB', 'A' * 101])
    def test_invalid_name_raises_value_error(self, name, mock_repository, mock_audit_service, mock_notification_service):
        user_id = uuid4()
        with pytest.raises(ValueError, match='Nombre inválido'):
            create_and_manage_room(
                name=name,
                location='Edificio A - Planta 2',
                capacity=10,
                description=None,
                equipment_list=[],
                created_by_user_id=user_id,
                repository=mock_repository,
                audit_service=mock_audit_service,
                notification_service=mock_notification_service,
            )

    @pytest.mark.parametrize('location', ['', 'ABC', 'A' * 151])
    def test_invalid_location_raises_value_error(self, location, mock_repository, mock_audit_service, mock_notification_service):
        user_id = uuid4()
        with pytest.raises(ValueError, match='Ubicación inválida'):
            create_and_manage_room(
                name='Sala Madrid',
                location=location,
                capacity=10,
                description=None,
                equipment_list=[],
                created_by_user_id=user_id,
                repository=mock_repository,
                audit_service=mock_audit_service,
                notification_service=mock_notification_service,
            )

    @pytest.mark.parametrize('capacity', [0, -1, 501])
    def test_invalid_capacity_raises_value_error(self, capacity, mock_repository, mock_audit_service, mock_notification_service):
        user_id = uuid4()
        with pytest.raises(ValueError, match='Capacidad inválida'):
            create_and_manage_room(
                name='Sala Madrid',
                location='Edificio A - Planta 2',
                capacity=capacity,
                description=None,
                equipment_list=[],
                created_by_user_id=user_id,
                repository=mock_repository,
                audit_service=mock_audit_service,
                notification_service=mock_notification_service,
            )

    def test_duplicate_name_raises_value_error(self, mock_repository, mock_audit_service, mock_notification_service):
        user_id = uuid4()
        mock_repository.exists_name.return_value = True

        with pytest.raises(ValueError, match='El nombre ya existe'):
            create_and_manage_room(
                name='Sala Existente',
                location='Edificio A - Planta 2',
                capacity=10,
                description=None,
                equipment_list=[],
                created_by_user_id=user_id,
                repository=mock_repository,
                audit_service=mock_audit_service,
                notification_service=mock_notification_service,
            )

    def test_notification_failure_does_not_break_creation(self, mock_repository, mock_audit_service, mock_notification_service):
        user_id = uuid4()
        mock_repository.exists_name.return_value = False
        mock_repository.save.return_value = {
            'id': str(uuid4()),
            'name': 'Sala Madrid',
            'location': 'Edificio A - Planta 2',
            'capacity': 10,
            'description': None,
            'equipment': [],
            'is_active': True,
            'created_by': user_id,
            'created_at': datetime.now(timezone.utc),
        }
        mock_notification_service.send_email.side_effect = Exception('email fail')

        result = create_and_manage_room(
            name='Sala Madrid',
            location='Edificio A - Planta 2',
            capacity=10,
            description=None,
            equipment_list=[],
            created_by_user_id=user_id,
            repository=mock_repository,
            audit_service=mock_audit_service,
            notification_service=mock_notification_service,
        )

        assert result['name'] == 'Sala Madrid'
        mock_notification_service.send_email.assert_called_once()


class TestRoomServiceUpdate:
    def test_update_room_name(self, mock_repository, mock_audit_service, mock_notification_service, mock_cache_service):
        user_id = uuid4()
        room = {
            'id': str(uuid4()),
            'name': 'Sala Antigua',
            'location': 'Edificio A',
            'capacity': 8,
            'description': None,
            'equipment': [],
            'is_active': True,
            'created_by': str(user_id),
            'created_at': datetime.now(timezone.utc),
        }
        mock_repository.find_by_id.return_value = room
        mock_repository.exists_name.return_value = False
        mock_repository.save.return_value = {**room, 'name': 'Sala Nueva'}

        service = RoomService(
            repository=mock_repository,
            audit_service=mock_audit_service,
            notification_service=mock_notification_service,
            cache_service=mock_cache_service,
        )

        result = service.process_room_update(
            room_id=room['id'],
            updates={'name': 'Sala Nueva'},
            user_id=user_id,
        )

        assert result['name'] == 'Sala Nueva'
        mock_repository.save.assert_called_once()
        mock_audit_service.log.assert_called_once()

    def test_update_room_capacity(self, mock_repository, mock_audit_service, mock_notification_service, mock_cache_service):
        user_id = uuid4()
        room = {
            'id': str(uuid4()),
            'name': 'Sala Antigua',
            'location': 'Edificio A',
            'capacity': 8,
            'description': None,
            'equipment': [],
            'is_active': True,
            'created_by': str(user_id),
            'created_at': datetime.now(timezone.utc),
        }
        mock_repository.find_by_id.return_value = room
        mock_repository.save.return_value = {**room, 'capacity': 12}

        service = RoomService(
            repository=mock_repository,
            audit_service=mock_audit_service,
            notification_service=mock_notification_service,
            cache_service=mock_cache_service,
        )

        result = service.process_room_update(
            room_id=room['id'],
            updates={'capacity': 12},
            user_id=user_id,
        )

        assert result['capacity'] == 12
        mock_repository.save.assert_called_once()

    def test_update_nonexistent_room_raises_error(self, mock_repository, mock_audit_service, mock_notification_service, mock_cache_service):
        user_id = uuid4()
        mock_repository.find_by_id.return_value = None

        service = RoomService(
            repository=mock_repository,
            audit_service=mock_audit_service,
            notification_service=mock_notification_service,
            cache_service=mock_cache_service,
        )

        with pytest.raises(ValueError, match='Sala no encontrada'):
            service.process_room_update(
                room_id='not-found',
                updates={'name': 'Sala Nueva'},
                user_id=user_id,
            )


if __name__ == '__main__':
    pytest.main(['-q'])
