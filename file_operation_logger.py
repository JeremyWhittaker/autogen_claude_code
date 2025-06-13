#!/usr/bin/env python3
"""
File operation logging mechanism for Claude Code integration.
Tracks all file operations performed by the system for audit and rollback purposes.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

class FileOperationLogger:
    """Logs all file operations with rollback capability."""
    
    def __init__(self, log_dir: str = ".claude_logs"):
        """
        Initialize the file operation logger.
        
        Args:
            log_dir: Directory to store operation logs and backups
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.backups_dir = self.log_dir / "backups"
        self.backups_dir.mkdir(exist_ok=True)
        
        # Initialize operation log
        self.log_file = self.log_dir / "operations.json"
        self.operations: List[Dict] = []
        
        # Load existing operations if any
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.operations = json.load(f)
            except:
                self.operations = []
        
        # Set up logger
        self.logger = logging.getLogger("FileOperationLogger")
        
    def _save_log(self):
        """Save operations log to disk."""
        with open(self.log_file, 'w') as f:
            json.dump(self.operations, f, indent=2, default=str)
    
    def log_create(self, filepath: str, content: str) -> str:
        """
        Log a file creation operation.
        
        Args:
            filepath: Path to the created file
            content: Content of the file
            
        Returns:
            Operation ID for potential rollback
        """
        operation_id = f"create_{datetime.now().isoformat()}_{os.getpid()}"
        
        operation = {
            "id": operation_id,
            "type": "create",
            "filepath": str(Path(filepath).absolute()),
            "timestamp": datetime.now().isoformat(),
            "content_hash": hash(content),
            "size": len(content),
            "rolled_back": False
        }
        
        # Store content for potential rollback
        content_backup = self.backups_dir / f"{operation_id}_content.txt"
        with open(content_backup, 'w') as f:
            f.write(content)
        
        self.operations.append(operation)
        self._save_log()
        
        self.logger.info(f"Logged file creation: {filepath}")
        return operation_id
    
    def log_modify(self, filepath: str, old_content: str, new_content: str) -> str:
        """
        Log a file modification operation.
        
        Args:
            filepath: Path to the modified file
            old_content: Original content before modification
            new_content: New content after modification
            
        Returns:
            Operation ID for potential rollback
        """
        operation_id = f"modify_{datetime.now().isoformat()}_{os.getpid()}"
        
        operation = {
            "id": operation_id,
            "type": "modify",
            "filepath": str(Path(filepath).absolute()),
            "timestamp": datetime.now().isoformat(),
            "old_content_hash": hash(old_content),
            "new_content_hash": hash(new_content),
            "old_size": len(old_content),
            "new_size": len(new_content),
            "rolled_back": False
        }
        
        # Store old content for rollback
        backup_path = self.backups_dir / f"{operation_id}_backup.txt"
        with open(backup_path, 'w') as f:
            f.write(old_content)
        
        self.operations.append(operation)
        self._save_log()
        
        self.logger.info(f"Logged file modification: {filepath}")
        return operation_id
    
    def log_delete(self, filepath: str, content: str) -> str:
        """
        Log a file deletion operation.
        
        Args:
            filepath: Path to the deleted file
            content: Content of the file before deletion
            
        Returns:
            Operation ID for potential rollback
        """
        operation_id = f"delete_{datetime.now().isoformat()}_{os.getpid()}"
        
        operation = {
            "id": operation_id,
            "type": "delete",
            "filepath": str(Path(filepath).absolute()),
            "timestamp": datetime.now().isoformat(),
            "content_hash": hash(content),
            "size": len(content),
            "rolled_back": False
        }
        
        # Store content for potential restoration
        backup_path = self.backups_dir / f"{operation_id}_deleted.txt"
        with open(backup_path, 'w') as f:
            f.write(content)
        
        self.operations.append(operation)
        self._save_log()
        
        self.logger.info(f"Logged file deletion: {filepath}")
        return operation_id
    
    def rollback(self, operation_id: str) -> bool:
        """
        Rollback a specific operation.
        
        Args:
            operation_id: ID of the operation to rollback
            
        Returns:
            True if rollback was successful, False otherwise
        """
        # Find the operation
        operation = None
        for op in self.operations:
            if op["id"] == operation_id:
                operation = op
                break
        
        if not operation:
            self.logger.error(f"Operation not found: {operation_id}")
            return False
        
        if operation["rolled_back"]:
            self.logger.warning(f"Operation already rolled back: {operation_id}")
            return False
        
        try:
            filepath = Path(operation["filepath"])
            
            if operation["type"] == "create":
                # Delete the created file
                if filepath.exists():
                    filepath.unlink()
                    self.logger.info(f"Rolled back file creation: {filepath}")
                
            elif operation["type"] == "modify":
                # Restore original content
                backup_path = self.backups_dir / f"{operation_id}_backup.txt"
                if backup_path.exists():
                    with open(backup_path, 'r') as f:
                        old_content = f.read()
                    with open(filepath, 'w') as f:
                        f.write(old_content)
                    self.logger.info(f"Rolled back file modification: {filepath}")
                
            elif operation["type"] == "delete":
                # Restore deleted file
                backup_path = self.backups_dir / f"{operation_id}_deleted.txt"
                if backup_path.exists():
                    with open(backup_path, 'r') as f:
                        content = f.read()
                    with open(filepath, 'w') as f:
                        f.write(content)
                    self.logger.info(f"Rolled back file deletion: {filepath}")
            
            # Mark as rolled back
            operation["rolled_back"] = True
            self._save_log()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed for {operation_id}: {e}")
            return False
    
    def rollback_all(self, since: Optional[datetime] = None) -> int:
        """
        Rollback all operations or operations since a given time.
        
        Args:
            since: Only rollback operations after this time (if None, rollback all)
            
        Returns:
            Number of operations rolled back
        """
        rolled_back = 0
        
        # Process in reverse order (newest first)
        for operation in reversed(self.operations):
            if operation["rolled_back"]:
                continue
                
            if since and datetime.fromisoformat(operation["timestamp"]) < since:
                continue
            
            if self.rollback(operation["id"]):
                rolled_back += 1
        
        return rolled_back
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict]:
        """
        Get recent file operations.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of recent operations
        """
        return self.operations[-limit:]
    
    def clear_old_logs(self, days: int = 7):
        """
        Clear logs and backups older than specified days.
        
        Args:
            days: Number of days to keep logs
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # Filter operations
        self.operations = [
            op for op in self.operations
            if datetime.fromisoformat(op["timestamp"]).timestamp() > cutoff
        ]
        self._save_log()
        
        # Clean up old backup files
        for backup_file in self.backups_dir.iterdir():
            if backup_file.stat().st_mtime < cutoff:
                backup_file.unlink()
                self.logger.info(f"Deleted old backup: {backup_file}")


# Example usage and tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create logger instance
    logger = FileOperationLogger()
    
    # Test file creation
    test_file = "test_file.txt"
    test_content = "This is a test file created by the logger."
    
    print("Creating test file...")
    with open(test_file, 'w') as f:
        f.write(test_content)
    op_id = logger.log_create(test_file, test_content)
    print(f"Logged creation with ID: {op_id}")
    
    # Test modification
    print("\nModifying test file...")
    new_content = "This is the modified content."
    with open(test_file, 'w') as f:
        f.write(new_content)
    mod_id = logger.log_modify(test_file, test_content, new_content)
    print(f"Logged modification with ID: {mod_id}")
    
    # Show recent operations
    print("\nRecent operations:")
    for op in logger.get_recent_operations():
        print(f"- {op['type']} {op['filepath']} at {op['timestamp']}")
    
    # Test rollback
    print(f"\nRolling back modification {mod_id}...")
    if logger.rollback(mod_id):
        print("Rollback successful!")
        with open(test_file, 'r') as f:
            print(f"File content after rollback: {f.read()}")
    
    # Clean up
    if os.path.exists(test_file):
        os.unlink(test_file)
    print("\nTest completed and cleaned up.")