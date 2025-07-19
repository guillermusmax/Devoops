#!/usr/bin/env python3
"""
🥤 NovaLat - Fix Metadata Script
Script para arreglar todas las referencias de metadata
"""

import re

def fix_file(file_path, replacements):
    """Arreglar un archivo con las sustituciones especificadas"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"ℹ️  No changes needed: {file_path}")
            return False
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Función principal"""
    print("🥤 NovaLat - Fixing Metadata References")
    print("=" * 50)
    
    # Definir las sustituciones necesarias
    replacements = [
        # En traceability_service.py
        ("metadata=event_db.metadata or {}", "metadata=event_db.event_metadata or {}"),
        ("metadata=db_event.metadata or {}", "metadata=db_event.event_metadata or {}"),
        
        # En supply_chain_service.py
        ("metadata=db_order.metadata or {}", "metadata=db_order.order_metadata or {}"),
        
        # En database.py - asegurar que los métodos to_dict usen los campos correctos
        ("\"metadata\": self.event_metadata,", "\"metadata\": self.event_metadata or {},"),
        ("\"metadata\": self.order_metadata,", "\"metadata\": self.order_metadata or {},"),
        ("\"metadata\": self.product_metadata,", "\"metadata\": self.product_metadata or {},"),
        ("\"metadata\": self.batch_metadata,", "\"metadata\": self.batch_metadata or {},"),
    ]
    
    # Archivos a arreglar
    files_to_fix = [
        "src/app/services/traceability_service.py",
        "src/app/services/supply_chain_service.py",
        "src/app/models/database.py"
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if fix_file(file_path, replacements):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files!")
    print("Now rebuild the Docker container:")
    print("docker-compose -f docker-compose-simple.yml down")
    print("docker-compose -f docker-compose-simple.yml up -d --build")

if __name__ == "__main__":
    main() 