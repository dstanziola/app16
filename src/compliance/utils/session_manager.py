"""
Gestor de sesiones del sistema de compliance.

Este módulo implementa el manejo completo de sesiones de compliance,
incluyendo control de estado de fases, persistencia de datos y
transiciones válidas según la metodología TDD establecida.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from src.compliance.models.compliance_models import CompliancePhase, ComplianceStatus


class SessionState(Enum):
    """Estados de sesión de compliance."""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


@dataclass
class SessionData:
    """Datos de sesión de compliance."""
    session_id: str
    current_phase: CompliancePhase
    state: SessionState
    created_at: datetime
    last_activity: datetime
    checkpoints: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Procesar datos después de inicialización."""
        if isinstance(self.current_phase, str):
            self.current_phase = CompliancePhase(self.current_phase)
        if isinstance(self.state, str):
            self.state = SessionState(self.state)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.last_activity, str):
            self.last_activity = datetime.fromisoformat(self.last_activity)


class SessionManager:
    """
    Gestor de sesiones del sistema de compliance.
    
    Proporciona funcionalidad completa para crear, gestionar y persistir
    sesiones de compliance con control de estado y transiciones de fase.
    """
    
    def __init__(self, session_dir: str = None):
        """
        Inicializar gestor de sesiones.
        
        Args:
            session_dir: Directorio para almacenar archivos de sesión
        """
        self.current_session_id: Optional[str] = None
        self.current_phase: CompliancePhase = CompliancePhase.ANALYSIS
        self.sessions: Dict[str, SessionData] = {}
        self.session_dir = session_dir or os.path.join(os.getcwd(), 'temp', 'sessions')
        self.session_timeout_hours = 2
        
        # Crear directorio de sesiones si no existe
        os.makedirs(self.session_dir, exist_ok=True)
        
    def create_session(self) -> str:
        """
        Crear nueva sesión de compliance.
        
        Returns:
            str: Identificador único de la sesión
        """
        # Cerrar sesión activa si existe
        if self.current_session_id:
            self.close_session()
            
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session_data = SessionData(
            session_id=session_id,
            current_phase=CompliancePhase.ANALYSIS,
            state=SessionState.ACTIVE,
            created_at=now,
            last_activity=now,
            checkpoints=[],
            metadata={}
        )
        
        self.sessions[session_id] = session_data
        self.current_session_id = session_id
        self.current_phase = CompliancePhase.ANALYSIS
        
        return session_id
        
    def get_current_session(self) -> Optional[SessionData]:
        """
        Obtener datos de la sesión actual.
        
        Returns:
            SessionData: Datos de la sesión actual o None si no hay sesión activa
        """
        if not self.current_session_id:
            return None
            
        return self.sessions.get(self.current_session_id)
        
    def advance_phase(self) -> bool:
        """
        Avanzar a la siguiente fase de compliance.
        
        Returns:
            bool: True si el avance fue exitoso
        """
        if not self.current_session_id:
            return False
            
        phase_order = [
            CompliancePhase.ANALYSIS,
            CompliancePhase.PLANNING,
            CompliancePhase.IMPLEMENTATION,
            CompliancePhase.VALIDATION,
            CompliancePhase.CONFIRMATION
        ]
        
        current_index = phase_order.index(self.current_phase)
        if current_index >= len(phase_order) - 1:
            return False  # Ya está en la fase final
            
        self.current_phase = phase_order[current_index + 1]
        
        # Actualizar sesión actual
        session = self.sessions[self.current_session_id]
        session.current_phase = self.current_phase
        session.last_activity = datetime.now()
        
        return True
        
    def save_session(self) -> str:
        """
        Guardar sesión actual en archivo.
        
        Returns:
            str: Ruta del archivo guardado
        """
        if not self.current_session_id:
            raise ValueError("No hay sesión activa para guardar")
            
        session = self.sessions[self.current_session_id]
        file_path = os.path.join(
            self.session_dir, 
            f"session_{self.current_session_id}.json"
        )
        
        # Preparar datos para serialización
        session_dict = asdict(session)
        session_dict['created_at'] = session.created_at.isoformat()
        session_dict['last_activity'] = session.last_activity.isoformat()
        session_dict['current_phase'] = session.current_phase.value
        session_dict['state'] = session.state.value
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_dict, f, indent=2, ensure_ascii=False)
            
        return file_path
        
    def load_session(self, file_path: str) -> str:
        """
        Cargar sesión desde archivo.
        
        Args:
            file_path: Ruta del archivo de sesión
            
        Returns:
            str: ID de la sesión cargada
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_dict = json.load(f)
                
            session_data = SessionData(**session_dict)
            
            self.current_session_id = session_data.session_id
            self.current_phase = session_data.current_phase
            self.sessions[session_data.session_id] = session_data
            
            return session_data.session_id
            
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Archivo de sesión inválido: {e}")
            
    def register_checkpoint(self, checkpoint_data: Dict[str, Any]):
        """
        Registrar finalización de checkpoint.
        
        Args:
            checkpoint_data: Datos del checkpoint completado
        """
        if not self.current_session_id:
            return
            
        session = self.sessions[self.current_session_id]
        
        # Agregar timestamp si no existe
        checkpoint_entry = checkpoint_data.copy()
        if 'timestamp' not in checkpoint_entry:
            checkpoint_entry['timestamp'] = datetime.now().isoformat()
            
        session.checkpoints.append(checkpoint_entry)
        session.last_activity = datetime.now()
        
    def get_session_history(self) -> List[Dict[str, Any]]:
        """
        Obtener historial de checkpoints de la sesión actual.
        
        Returns:
            List[Dict]: Lista de checkpoints registrados
        """
        if not self.current_session_id:
            return []
            
        session = self.sessions[self.current_session_id]
        return session.checkpoints.copy()
        
    def close_session(self) -> Optional[SessionData]:
        """
        Cerrar sesión activa.
        
        Returns:
            SessionData: Datos de la sesión cerrada
        """
        if not self.current_session_id:
            return None
            
        session = self.sessions[self.current_session_id]
        session.state = SessionState.CLOSED
        session.last_activity = datetime.now()
        
        closed_session = session
        self.current_session_id = None
        self.current_phase = CompliancePhase.ANALYSIS
        
        return closed_session
        
    def get_phase_progress(self) -> Dict[str, Any]:
        """
        Obtener progreso de la fase actual.
        
        Returns:
            Dict: Información de progreso
        """
        if not self.current_session_id:
            return {
                'current_phase': None,
                'completed_steps': 0,
                'total_steps': 0,
                'percentage': 0.0
            }
            
        session = self.sessions[self.current_session_id]
        
        # Contar checkpoints de la fase actual
        current_phase_checkpoints = [
            cp for cp in session.checkpoints 
            if cp.get('phase') == self.current_phase
        ]
        
        # Calcular pasos completados
        completed_steps = 0
        total_steps = 0
        
        for checkpoint in current_phase_checkpoints:
            validations = checkpoint.get('validations', {})
            if isinstance(validations, dict):
                total_steps += len(validations)
                completed_steps += sum(1 for v in validations.values() if v)
                
        percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0.0
        
        return {
            'current_phase': self.current_phase.value,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'percentage': round(percentage, 2)
        }
        
    def validate_phase_transition(self) -> bool:
        """
        Validar si se pueden cumplir los requerimientos para transición de fase.
        
        Returns:
            bool: True si la transición es válida
        """
        if not self.current_session_id:
            return False
            
        session = self.sessions[self.current_session_id]
        
        # Buscar checkpoints completados para la fase actual
        current_phase_checkpoints = [
            cp for cp in session.checkpoints 
            if cp.get('phase') == self.current_phase and 
               cp.get('status') == ComplianceStatus.COMPLETED
        ]
        
        if not current_phase_checkpoints:
            return False
            
        # Verificar que todas las validaciones estén completadas
        for checkpoint in current_phase_checkpoints:
            validations = checkpoint.get('validations', {})
            if isinstance(validations, dict):
                if not all(validations.values()):
                    return False
                    
        return True
        
    def check_session_timeout(self) -> bool:
        """
        Verificar si la sesión actual ha expirado.
        
        Returns:
            bool: True si la sesión ha expirado
        """
        if not self.current_session_id:
            return False
            
        session_age = self._get_session_age()
        timeout_seconds = self.session_timeout_hours * 3600
        
        return session_age > timeout_seconds
        
    def _get_session_age(self) -> int:
        """
        Obtener edad de la sesión actual en segundos.
        
        Returns:
            int: Edad de la sesión en segundos
        """
        if not self.current_session_id:
            return 0
            
        session = self.sessions[self.current_session_id]
        now = datetime.now()
        age = now - session.last_activity
        
        return int(age.total_seconds())
        
    def serialize_session_data(self) -> str:
        """
        Serializar datos de sesión actual.
        
        Returns:
            str: Datos serializados en JSON
        """
        if not self.current_session_id:
            return "{}"
            
        session = self.sessions[self.current_session_id]
        session_dict = asdict(session)
        
        # Convertir datetime a string
        session_dict['created_at'] = session.created_at.isoformat()
        session_dict['last_activity'] = session.last_activity.isoformat()
        session_dict['current_phase'] = session.current_phase.value
        session_dict['state'] = session.state.value
        
        return json.dumps(session_dict, ensure_ascii=False)
        
    def deserialize_session_data(self, serialized_data: str) -> Dict[str, Any]:
        """
        Deserializar datos de sesión.
        
        Args:
            serialized_data: Datos serializados en JSON
            
        Returns:
            Dict: Datos deserializados
        """
        return json.loads(serialized_data)
