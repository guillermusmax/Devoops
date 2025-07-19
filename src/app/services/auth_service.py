"""
🥤 NovaLat - Servicio de Autenticación
Servicio de autenticación y autorización con JWT
"""

import os
import jwt
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

class AuthService:
    """Servicio de autenticación para NovaLat"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "novalat-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # Configurar hashing de contraseñas
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Usuarios simulados (en producción esto vendría de una base de datos)
        self.users = {
            "user-123": {
                "id": "user-123",
                "username": "admin",
                "email": "admin@novalat.com",
                "full_name": "Administrador NovaLat",
                "role": "ADMIN",
                "permissions": ["read", "write", "delete", "audit"],
                "is_active": True
            },
            "user-456": {
                "id": "user-456",
                "username": "operator",
                "email": "operator@novalat.com",
                "full_name": "Operador de Planta",
                "role": "OPERATOR",
                "permissions": ["read", "write"],
                "is_active": True
            },
            "user-789": {
                "id": "user-789",
                "username": "auditor",
                "email": "auditor@novalat.com",
                "full_name": "Auditor de Calidad",
                "role": "AUDITOR",
                "permissions": ["read", "audit"],
                "is_active": True
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generar hash de contraseña"""
        return self.pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autenticar usuario"""
        # En un sistema real, esto consultaría la base de datos
        for user in self.users.values():
            if user["username"] == username:
                # Simular verificación de contraseña (en producción sería real)
                if password == "password123":  # Contraseña de prueba
                    return user
        return None
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Crear token de acceso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            
            if user_id is None:
                raise ValueError("Token inválido: sub claim faltante")
            
            # Verificar que el usuario existe y está activo
            user = self.users.get(user_id)
            if not user or not user["is_active"]:
                raise ValueError("Usuario no encontrado o inactivo")
            
            return user
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expirado")
        except jwt.JWTError as e:
            raise ValueError(f"Token inválido: {e}")
    
    def has_permission(self, user: Dict[str, Any], permission: str) -> bool:
        """Verificar si el usuario tiene un permiso específico"""
        return permission in user.get("permissions", [])
    
    def has_role(self, user: Dict[str, Any], role: str) -> bool:
        """Verificar si el usuario tiene un rol específico"""
        return user.get("role") == role
    
    def has_audit_permission(self, user: Dict[str, Any]) -> bool:
        """Verificar si el usuario tiene permisos de auditoría"""
        return self.has_permission(user, "audit") or self.has_role(user, "ADMIN")
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener usuario por ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Obtener usuario por nombre de usuario"""
        for user in self.users.values():
            if user["username"] == username:
                return user
        return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo usuario (simulado)"""
        user_id = f"user-{len(self.users) + 1}"
        
        new_user = {
            "id": user_id,
            "username": user_data["username"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "role": user_data.get("role", "USER"),
            "permissions": user_data.get("permissions", ["read"]),
            "is_active": True
        }
        
        self.users[user_id] = new_user
        logger.info(f"Usuario creado: {user_id}")
        
        return new_user
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Actualizar usuario (simulado)"""
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        
        # Actualizar campos permitidos
        allowed_fields = ["email", "full_name", "role", "permissions", "is_active"]
        for field in allowed_fields:
            if field in user_data:
                user[field] = user_data[field]
        
        logger.info(f"Usuario actualizado: {user_id}")
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Eliminar usuario (simulado)"""
        if user_id not in self.users:
            return False
        
        del self.users[user_id]
        logger.info(f"Usuario eliminado: {user_id}")
        return True
    
    def list_users(self, role: Optional[str] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Listar usuarios con filtros"""
        users = list(self.users.values())
        
        if role:
            users = [user for user in users if user["role"] == role]
        
        if is_active is not None:
            users = [user for user in users if user["is_active"] == is_active]
        
        return users
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Obtener permisos de un usuario"""
        user = self.get_user_by_id(user_id)
        return user.get("permissions", []) if user else []
    
    def check_resource_access(self, user: Dict[str, Any], resource_type: str, action: str) -> bool:
        """Verificar acceso a un recurso específico"""
        # Reglas de acceso basadas en rol y permisos
        role = user.get("role")
        permissions = user.get("permissions", [])
        
        # Administradores tienen acceso completo
        if role == "ADMIN":
            return True
        
        # Reglas específicas por tipo de recurso
        if resource_type == "traceability_event":
            if action in ["read", "write"]:
                return "read" in permissions and "write" in permissions
            elif action == "delete":
                return "delete" in permissions
        
        elif resource_type == "supply_chain_order":
            if action in ["read", "write"]:
                return "read" in permissions and "write" in permissions
            elif action == "approve":
                return role in ["ADMIN", "MANAGER"]
        
        elif resource_type == "audit_log":
            return "audit" in permissions or role == "AUDITOR"
        
        return False 