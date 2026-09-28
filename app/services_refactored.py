from typing import Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDADORES
# ============================================================================

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
        """Valida que el nombre tenga longitud válida."""
        name = name.strip() if name else ""
        if len(name) < self.NAME_MIN_LENGTH or len(name) > self.NAME_MAX_LENGTH:
            raise ValueError(f"El nombre debe tener entre {self.NAME_MIN_LENGTH} y {self.NAME_MAX_LENGTH} caracteres")
    
    def validate_location(self, location: str) -> None:
        """Valida que la ubicación tenga longitud válida."""
        location = location.strip() if location else ""
        if len(location) < self.LOCATION_MIN_LENGTH or len(location) > self.LOCATION_MAX_LENGTH:
            raise ValueError(f"La ubicación debe tener entre {self.LOCATION_MIN_LENGTH} y {self.LOCATION_MAX_LENGTH} caracteres")
    
    def validate_capacity(self, capacity: int) -> None:
        """Valida que la capacidad esté en rango válido."""
        if capacity < self.CAPACITY_MIN or capacity > self.CAPACITY_MAX:
            raise ValueError(f"La capacidad debe estar entre {self.CAPACITY_MIN} y {self.CAPACITY_MAX}")
    
    def validate_description(self, description: Optional[str]) -> None:
        """Valida que la descripción no exceda longitud máxima."""
        if description:
            desc = description.strip() if description else ""
            if len(desc) > self.DESCRIPTION_MAX_LENGTH:
                raise ValueError(f"La descripción no puede exceder {self.DESCRIPTION_MAX_LENGTH} caracteres")
    
    def validate_all_fields(
        self,
        name: str,
        location: str,
        capacity: int,
        description: Optional[str]
    ) -> None:
        """Valida todos los campos de una sala."""
        self.validate_name(name)
        self.validate_location(location)
        self.validate_capacity(capacity)
        self.validate_description(description)


# ============================================================================
# CONSTRUCTOR
# ============================================================================

class RoomBuilder:
    """Construye objetos de sala normalizados."""
    
    def build_room_dict(
        self,
        name: str,
        location: str,
        capacity: int,
        description: Optional[str],
        equipment: Optional[list[str]],
        created_by_user_id: UUID
    ) -> dict[str, Any]:
        """Construye un diccionario de sala con valores normalizados."""
        return {
            'id': str(uuid4()),
            'name': name.strip(),
            'location': location.strip(),
            'capacity': capacity,
            'description': description.strip() if description else None,
            'equipment': equipment if equipment else [],
            'is_active': True,
            'created_by': str(created_by_user_id),
            'created_at': datetime.now(timezone.utc)
        }


# ============================================================================
# AUDITORÍA
# ============================================================================

class RoomAuditService:
    """Registra eventos de salas en auditoría."""
    
    def __init__(self, audit_repository: Any) -> None:
        self.audit_repository = audit_repository
    
    def record_creation(
        self,
        room_id: str,
        actor_id: UUID,
        room_name: str,
        capacity: int
    ) -> None:
        """Registra la creación de una sala."""
        self.audit_repository.log(
            action='ROOM_CREATED',
            entity_id=room_id,
            actor_id=str(actor_id),
            details={'name': room_name, 'capacity': capacity}
        )
    
    def record_update(
        self,
        room_id: str,
        actor_id: UUID,
        updates: dict[str, Any]
    ) -> None:
        """Registra la actualización de una sala."""
        self.audit_repository.log(
            action='ROOM_UPDATED',
            entity_id=room_id,
            actor_id=str(actor_id),
            details=updates
        )


# ============================================================================
# NOTIFICACIONES
# ============================================================================

class RoomNotificationService:
    """Envía notificaciones de eventos de salas."""
    
    def __init__(self, notification_backend: Any) -> None:
        self.notification_backend = notification_backend
    
    def notify_room_created(self, room_name: str, capacity: int) -> None:
        """Notifica que se ha creado una sala."""
        self.notification_backend.send_email(
            to='admin@company.com',
            subject=f'Nueva sala creada: {room_name}',
            body=f'La sala {room_name} ha sido creada con capacidad {capacity}'
        )
    
    def notify_room_updated(self, room_name: str) -> None:
        """Notifica que se ha actualizado una sala."""
        self.notification_backend.send_email(
            to='admin@company.com',
            subject=f'Sala actualizada: {room_name}',
            body=f'La sala {room_name} ha sido actualizada'
        )


# ============================================================================
# CACHÉ
# ============================================================================

class CacheService:
    """Gestiona la caché de datos."""
    
    def __init__(self, cache_backend: Any) -> None:
        self.cache_backend = cache_backend
    
    def invalidate(self, cache_key: str) -> None:
        """Invalida una entrada de caché."""
        self.cache_backend.invalidate(cache_key)


# ============================================================================
# SERVICIO DE APLICACIÓN (ORQUESTADOR)
# ============================================================================

class RoomService:
    """
    Servicio de aplicación para gestión de salas.
    
    Orquesta validación, persistencia, auditoría y notificación.
    Cada responsabilidad está delegada a un servicio específico.
    """
    
    def __init__(
        self,
        repository: Any,
        validator: RoomValidator,
        builder: RoomBuilder,
        audit_service: RoomAuditService,
        notification_service: RoomNotificationService,
        cache_service: CacheService
    ) -> None:
        self.repository = repository
        self.validator = validator
        self.builder = builder
        self.audit_service = audit_service
        self.notification_service = notification_service
        self.cache_service = cache_service
    
    # ========================================================================
    # OPERACIÓN PRINCIPAL: CREAR SALA
    # ========================================================================
    
    def create_room(
        self,
        name: str,
        location: str,
        capacity: int,
        description: Optional[str],
        equipment: Optional[list[str]],
        created_by_user_id: UUID
    ) -> dict[str, Any]:
        """Crea una sala coordinando todos los pasos necesarios."""
        self._validate_room_data(name, location, capacity, description)
        self._validate_no_duplicate_name(name)
        
        room_dict = self.builder.build_room_dict(
            name, location, capacity, description, equipment, created_by_user_id
        )
        
        saved_room = self._persist_room(room_dict)
        self._record_audit_creation(saved_room, created_by_user_id, name, capacity)
        self._notify_creation(name, capacity)
        self._invalidate_cache()
        
        return saved_room
    
    # ========================================================================
    # OPERACIÓN PRINCIPAL: ACTUALIZAR SALA
    # ========================================================================
    
    def update_room(
        self,
        room_id: str,
        updates: dict[str, Any],
        user_id: UUID
    ) -> dict[str, Any]:
        """Actualiza una sala coordinando todos los pasos necesarios."""
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
    
    # ========================================================================
    # MÉTODOS PRIVADOS: VALIDACIÓN
    # ========================================================================
    
    def _validate_room_data(
        self,
        name: str,
        location: str,
        capacity: int,
        description: Optional[str]
    ) -> None:
        """Valida todos los campos de una sala nueva."""
        self.validator.validate_all_fields(name, location, capacity, description)
    
    def _validate_no_duplicate_name(self, name: str) -> None:
        """Valida que el nombre no exista ya en el repositorio."""
        if self.repository.exists_name(name.strip()):
            raise ValueError("ROOM_NAME_ALREADY_EXISTS")
    
    def _validate_field_update(
        self,
        field_name: str,
        new_value: Any,
        current_room: dict[str, Any]
    ) -> None:
        """Valida un campo específico antes de actualizarlo."""
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
    
    # ========================================================================
    # MÉTODOS PRIVADOS: PERSISTENCIA
    # ========================================================================
    
    def _persist_room(self, room: dict[str, Any]) -> dict[str, Any]:
        """Persiste una sala en el repositorio."""
        return self.repository.save(room)
    
    def _get_room_or_fail(self, room_id: str) -> dict[str, Any]:
        """Obtiene una sala o lanza excepción."""
        room = self.repository.find_by_id(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        return room
    
    # ========================================================================
    # MÉTODOS PRIVADOS: APLICAR CAMBIOS
    # ========================================================================
    
    def _apply_field_update(
        self,
        room: dict[str, Any],
        field_name: str,
        new_value: Any
    ) -> None:
        """Aplica la actualización de un campo específico."""
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
    
    # ========================================================================
    # MÉTODOS PRIVADOS: AUDITORÍA (sin fallar)
    # ========================================================================
    
    def _record_audit_creation(
        self,
        room: dict[str, Any],
        actor_id: UUID,
        name: str,
        capacity: int
    ) -> None:
        """Registra la creación en auditoría. No falla si hay error."""
        try:
            self.audit_service.record_creation(room['id'], actor_id, name, capacity)
        except Exception as error:
            logger.error(f"Error registrando auditoría de creación: {error}")
    
    def _record_audit_update(
        self,
        room: dict[str, Any],
        actor_id: UUID,
        updates: dict[str, Any]
    ) -> None:
        """Registra la actualización en auditoría. No falla si hay error."""
        try:
            self.audit_service.record_update(room['id'], actor_id, updates)
        except Exception as error:
            logger.error(f"Error registrando auditoría de actualización: {error}")
    
    # ========================================================================
    # MÉTODOS PRIVADOS: NOTIFICACIÓN (sin fallar)
    # ========================================================================
    
    def _notify_creation(self, room_name: str, capacity: int) -> None:
        """Notifica la creación. No falla si hay error."""
        try:
            self.notification_service.notify_room_created(room_name, capacity)
        except Exception as error:
            logger.error(f"Error notificando creación: {error}")
    
    def _notify_update(self, room_name: str) -> None:
        """Notifica la actualización. No falla si hay error."""
        try:
            self.notification_service.notify_room_updated(room_name)
        except Exception as error:
            logger.error(f"Error notificando actualización: {error}")
    
    # ========================================================================
    # MÉTODOS PRIVADOS: CACHÉ (sin fallar)
    # ========================================================================
    
    def _invalidate_cache(self) -> None:
        """Invalida caché. No falla si hay error."""
        try:
            self.cache_service.invalidate('all_rooms')
        except Exception as error:
            logger.error(f"Error invalidando caché: {error}")
