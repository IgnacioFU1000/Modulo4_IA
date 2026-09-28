# Clean Code: principios, prompts y refactorización

## 1) Principios de Clean Code

### Nombres descriptivos

Los nombres deben expresar intención. Es preferible un nombre ligeramente largo pero claro que un nombre corto y ambiguo.

Ejemplos:

```python
# Malo
x = 10
r = []

def p(d):
    pass

# Bueno
minimum_capacity = 10
filtered_rooms = []

def filter_rooms_by_minimum_capacity(rooms: list[dict], minimum_capacity: int) -> list[dict]:
    return [room for room in rooms if room['capacity'] >= minimum_capacity]
```

### Funciones pequeñas

Una función debe hacer una sola cosa y debe ser fácil de leer en un vistazo.

```python
# Malo

def create_and_manage_room(...):
    validate_data()
    check_duplicates()
    save_to_repository()
    log_audit()
    notify_admin()
    invalidate_cache()

# Bueno

def create_room(...):
    validate_room_data()
    room = build_room()
    saved_room = persist_room(room)
    log_creation(saved_room)
    notify_room_created(saved_room)
    invalidate_cache()
    return saved_room
```

### SRP (Single Responsibility Principle)

Una clase o función debe tener una razón única para cambiar.

```python
class RoomValidator:
    def validate_name(self, name: str) -> None:
        ...

class RoomBuilder:
    def build_room_dict(self, ...) -> dict:
        ...

class RoomAuditService:
    def record_creation(self, ...) -> None:
        ...
```

### DRY (Don't Repeat Yourself)

Evita duplicar lógica; extrae utilidades y validaciones reutilizables.

```python
class StringValidator:
    @staticmethod
    def validate_field_length(value: str, min_length: int, max_length: int, field_name: str) -> None:
        if len(value) < min_length or len(value) > max_length:
            raise ValueError(f"{field_name} debe tener entre {min_length} y {max_length} caracteres")
```

### Type hints

Las anotaciones de tipo mejoran legibilidad y detección de errores.

```python
from typing import Optional


def filter_rooms_by_capacity(rooms: list[dict], minimum_capacity: int) -> list[dict]:
    return [room for room in rooms if room['capacity'] >= minimum_capacity]
```

### Docstrings

Documentar comportamiento, parámetros, retorno y excepciones ayuda a mantener el código.

```python
def calculate_utilization_percentage(booked_hours: float, total_available_hours: float) -> float:
    """
    Calcula el porcentaje de utilización de una sala.

    Args:
        booked_hours: Horas reservadas.
        total_available_hours: Horas totales disponibles.

    Returns:
        Porcentaje de utilización expresado en 0..100.

    Raises:
        ValueError: Si total_available_hours es cero o negativo.
    """
    if total_available_hours <= 0:
        raise ValueError("Las horas totales disponibles deben ser positivas")
    return (booked_hours / total_available_hours) * 100
```

---

## 2) Prompt 1: Renombrar variables y añadir type hints

```text
Actúa como un experto en Clean Code y Python senior.

Tengo este código legacy de gestión de salas de reuniones que necesita mejora:

[pega aquí el código legacy]

Tu tarea es:

1. Renombrar TODAS las variables, funciones y parámetros con nombres descriptivos.
2. Añadir type hints completos.
3. Mantener la funcionalidad idéntica.
4. NO añadir docstrings ni comentarios en esta fase.
5. Proporciona el código refactorizado completo.
6. Añade una tabla de mapeo antigua -> nueva.
7. Explica brevemente por qué cada nombre es mejor.
```

---

## 3) Prompt 2: Extraer métodos y aplicar SRP

```text
Actúa como un arquitecto de software especializado en aplicar el principio Single Responsibility (SRP).

Tengo este código que hace demasiadas cosas en una sola función:

[pega el código legado]

Tu tarea es:

1. Crear clases con una sola responsabilidad:
   - RoomValidator
   - RoomBuilder
   - RoomAuditService
   - RoomNotificationService
   - CacheService
2. Extraer métodos privados en RoomService:
   - _validate_room_data()
   - _persist_room()
   - _record_audit()
   - _notify_creation()
   - _invalidate_cache()
3. Simplificar la función principal: create_room() solo coordina.
4. Para process_room_update(): extraer _validate_field_update() y _apply_field_update().
5. Usa type hints completos, names descriptivos y métodos privados para la coordinación interna.
6. Las operaciones de auditoría, notificación y caché no deben romper la operación principal.
7. NO añadir docstrings en esta fase.

Proporciona:
- Todas las clases nuevas
- La clase RoomService simplificada
- Explicación de cómo cada clase tiene una sola responsabilidad
- Tabla mostrando qué responsabilidad se extrae de dónde
```

---

## 4) Prompt 3: Añadir docstrings y eliminar duplicidades

```text
Actúa como un experto en refactorización de código y Clean Code.

Tengo este código que necesita dos cosas:

[pega el código legado]

Tu tarea es:

1. Eliminar código duplicado usando DRY.
2. Añadir docstrings en formato Google para todas las funciones y clases.
3. Extraer validadores reutilizables y funciones genéricas.
4. Mantener la funcionalidad pero mejorar legibilidad y mantenibilidad.
5. Type hints completos.
6. No duplicar validaciones ni normalizaciones.

Requisitos:
- Crear una función genérica filter_rooms(rooms, predicate)
- Crear funciones específicas para capacidad, ubicación y equipamiento
- Crear StringNormalizer y StringValidator
- Rediseñar RoomValidator para usar validación reutilizable
- Reescribir RoomService sin duplicated logic
- Asegúrate de que todas las funciones tengan docstrings en estilo Google
- Añade ejemplos ejecutables en los docstrings cuando sea posible

Proporciona el código refactorizado completo y una tabla de qué piezas de código fueron eliminadas y por qué.
```

---

## 5) Código de ejemplo para refactorización SRP

El siguiente bloque es el código refactorizado de ejemplo que se puede guardar como referencia y usar para discusión o entrenamiento:

```python
from typing import Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class RoomValidator:
    """Valida los datos de salas."""

    NAME_MIN_LENGTH: int = 3
    NAME_MAX_LENGTH: int = 100
    LOCATION_MIN_LENGTH: int = 5
    LOCATION_MAX_LENGTH: int = 150
    CAPACITY_MIN: int = 1
    CAPACITY_MAX: int = 500
    DESCRIPTION_MAX_LENGTH: int = 1000

    def validate_name(self, name: str) -> None:
        name = name.strip() if name else ""
        if len(name) < self.NAME_MIN_LENGTH or len(name) > self.NAME_MAX_LENGTH:
            raise ValueError(f"El nombre debe tener entre {self.NAME_MIN_LENGTH} y {self.NAME_MAX_LENGTH} caracteres")

    def validate_location(self, location: str) -> None:
        location = location.strip() if location else ""
        if len(location) < self.LOCATION_MIN_LENGTH or len(location) > self.LOCATION_MAX_LENGTH:
            raise ValueError(f"La ubicación debe tener entre {self.LOCATION_MIN_LENGTH} y {self.LOCATION_MAX_LENGTH} caracteres")

    def validate_capacity(self, capacity: int) -> None:
        if capacity < self.CAPACITY_MIN or capacity > self.CAPACITY_MAX:
            raise ValueError(f"La capacidad debe estar entre {self.CAPACITY_MIN} y {self.CAPACITY_MAX}")

    def validate_description(self, description: Optional[str]) -> None:
        if description:
            desc = description.strip() if description else ""
            if len(desc) > self.DESCRIPTION_MAX_LENGTH:
                raise ValueError(f"La descripción no puede exceder {self.DESCRIPTION_MAX_LENGTH} caracteres")

    def validate_all_fields(self, name: str, location: str, capacity: int, description: Optional[str]) -> None:
        self.validate_name(name)
        self.validate_location(location)
        self.validate_capacity(capacity)
        self.validate_description(description)


class RoomBuilder:
    """Construye objetos de sala normalizados."""

    def build_room_dict(
        self,
        name: str,
        location: str,
        capacity: int,
        description: Optional[str],
        equipment: Optional[list[str]],
        created_by_user_id: UUID,
    ) -> dict[str, Any]:
        return {
            'id': str(uuid4()),
            'name': name.strip(),
            'location': location.strip(),
            'capacity': capacity,
            'description': description.strip() if description else None,
            'equipment': equipment if equipment else [],
            'is_active': True,
            'created_by': str(created_by_user_id),
            'created_at': datetime.now(timezone.utc),
        }


class RoomAuditService:
    """Registra eventos de salas en auditoría."""

    def __init__(self, audit_repository: Any) -> None:
        self.audit_repository = audit_repository

    def record_creation(self, room_id: str, actor_id: UUID, room_name: str, capacity: int) -> None:
        self.audit_repository.log(
            action='ROOM_CREATED',
            entity_id=room_id,
            actor_id=str(actor_id),
            details={'name': room_name, 'capacity': capacity},
        )

    def record_update(self, room_id: str, actor_id: UUID, updates: dict[str, Any]) -> None:
        self.audit_repository.log(
            action='ROOM_UPDATED',
            entity_id=room_id,
            actor_id=str(actor_id),
            details=updates,
        )


class RoomNotificationService:
    """Envía notificaciones de eventos de salas."""

    def __init__(self, notification_backend: Any) -> None:
        self.notification_backend = notification_backend

    def notify_room_created(self, room_name: str, capacity: int) -> None:
        self.notification_backend.send_email(
            to='admin@company.com',
            subject=f'Nueva sala creada: {room_name}',
            body=f'La sala {room_name} ha sido creada con capacidad {capacity}',
        )

    def notify_room_updated(self, room_name: str) -> None:
        self.notification_backend.send_email(
            to='admin@company.com',
            subject=f'Sala actualizada: {room_name}',
            body=f'La sala {room_name} ha sido actualizada',
        )


class CacheService:
    """Gestiona la caché de datos."""

    def __init__(self, cache_backend: Any) -> None:
        self.cache_backend = cache_backend

    def invalidate(self, cache_key: str) -> None:
        self.cache_backend.invalidate(cache_key)


class RoomService:
    """Servicio de aplicación para gestión de salas."""

    def __init__(
        self,
        repository: Any,
        validator: RoomValidator,
        builder: RoomBuilder,
        audit_service: RoomAuditService,
        notification_service: RoomNotificationService,
        cache_service: CacheService,
    ) -> None:
        self.repository = repository
        self.validator = validator
        self.builder = builder
        self.audit_service = audit_service
        self.notification_service = notification_service
        self.cache_service = cache_service

    def create_room(
        self,
        name: str,
        location: str,
        capacity: int,
        description: Optional[str],
        equipment: Optional[list[str]],
        created_by_user_id: UUID,
    ) -> dict[str, Any]:
        self._validate_room_data(name, location, capacity, description)
        self._validate_no_duplicate_name(name)

        room_dict = self.builder.build_room_dict(name, location, capacity, description, equipment, created_by_user_id)
        saved_room = self._persist_room(room_dict)

        self._record_audit_creation(saved_room, created_by_user_id, name, capacity)
        self._notify_creation(name, capacity)
        self._invalidate_cache()

        return saved_room

    def update_room(self, room_id: str, updates: dict[str, Any], user_id: UUID) -> dict[str, Any]:
        room = self._get_room_or_fail(room_id)

        for field_name, new_value in updates.items():
            self._validate_field_update(field_name, new_value, room)
            self._apply_field_update(room, field_name, new_value)

        room['updated_at'] = datetime.now(timezone.utc)
        room['updated_by'] = str(user_id)

        updated_room = self._persist_room(room)
        self._record_audit_update(updated_room, user_id, updates)
        self._notify_update(updated_room['name'])
        self._invalidate_cache()

        return updated_room

    def _validate_room_data(self, name: str, location: str, capacity: int, description: Optional[str]) -> None:
        self.validator.validate_all_fields(name, location, capacity, description)

    def _validate_no_duplicate_name(self, name: str) -> None:
        if self.repository.exists_name(name.strip()):
            raise ValueError("ROOM_NAME_ALREADY_EXISTS")

    def _validate_field_update(self, field_name: str, new_value: Any, current_room: dict[str, Any]) -> None:
        if field_name == 'name' and new_value:
            self.validator.validate_name(new_value)
            if self.repository.exists_name(new_value.strip(), exclude_id=current_room['id']):
                raise ValueError("ROOM_NAME_ALREADY_EXISTS")
        elif field_name == 'location' and new_value:
            self.validator.validate_location(new_value)
        elif field_name == 'capacity' and new_value is not None:
            self.validator.validate_capacity(new_value)
        elif field_name == 'description':
            self.validator.validate_description(new_value)

    def _persist_room(self, room: dict[str, Any]) -> dict[str, Any]:
        return self.repository.save(room)

    def _get_room_or_fail(self, room_id: str) -> dict[str, Any]:
        room = self.repository.find_by_id(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        return room

    def _apply_field_update(self, room: dict[str, Any], field_name: str, new_value: Any) -> None:
        if field_name == 'name' and new_value:
            room['name'] = new_value.strip()
        elif field_name == 'location' and new_value:
            room['location'] = new_value.strip()
        elif field_name == 'capacity' and new_value is not None:
            room['capacity'] = new_value
        elif field_name == 'description':
            room['description'] = new_value.strip() if new_value else None
        elif field_name == 'equipment':
            room['equipment'] = new_value if new_value else []

    def _record_audit_creation(self, room: dict[str, Any], actor_id: UUID, name: str, capacity: int) -> None:
        try:
            self.audit_service.record_creation(room['id'], actor_id, name, capacity)
        except Exception as error:
            logger.error(f"Error registrando auditoría de creación: {error}")

    def _record_audit_update(self, room: dict[str, Any], actor_id: UUID, updates: dict[str, Any]) -> None:
        try:
            self.audit_service.record_update(room['id'], actor_id, updates)
        except Exception as error:
            logger.error(f"Error registrando auditoría de actualización: {error}")

    def _notify_creation(self, room_name: str, capacity: int) -> None:
        try:
            self.notification_service.notify_room_created(room_name, capacity)
        except Exception as error:
            logger.error(f"Error notificando creación: {error}")

    def _notify_update(self, room_name: str) -> None:
        try:
            self.notification_service.notify_room_updated(room_name)
        except Exception as error:
            logger.error(f"Error notificando actualización: {error}")

    def _invalidate_cache(self) -> None:
        try:
            self.cache_service.invalidate('all_rooms')
        except Exception as error:
            logger.error(f"Error invalidando caché: {error}")
```

---

## 6) Captura de comportamiento antes de refactorizar

Antes de cambiar el código, lo ideal es escribir tests que capturen la conducta actual. La idea es detectar regresiones y verificar que la refactorización no rompe el comportamiento.

```python
import pytest
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime, timezone


def test_create_and_manage_room_valid_name():
    mock_repository = Mock()
    mock_repository.exists_name.return_value = False
    mock_repository.save.return_value = {
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
    mock_audit = Mock()
    mock_notification = Mock()

    result = create_and_manage_room(
        name='Sala Madrid',
        location='Edificio A - Planta 2',
        capacity=10,
        description=None,
        equipment_list=[],
        created_by_user_id=uuid4(),
        repository=mock_repository,
        audit_service=mock_audit,
        notification_service=mock_notification,
    )

    assert result['name'] == 'Sala Madrid'
    mock_repository.save.assert_called_once()
    mock_audit.log.assert_called_once()
```

---

## 7) Verificación de no regresión

Comando recomendado:

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

Asegura:
- Que se cumple el comportamiento actual
- Que la refactorización no rompe la lógica
- Que la cobertura sigue siendo alta

---

## 8) Recomendación final

El flujo ideal es:

1. Escribir tests del código actual.
2. Ejecutarlos y confirmar que pasan.
3. Refactorizar aplicando SRP, DRY, nombres descriptivos, type hints y docstrings.
4. Ejecutar los mismos tests.
5. Verificar cobertura y regresión cero.

Este proceso minimiza riesgo y permite mejorar la calidad sin romper el negocio.
```
