import os
import json
from typing import List, Dict, Optional

class ProfileManager:
    def __init__(self, profiles_dir: str = None):
        """
        Initialize the ProfileManager.
        
        Args:
            profiles_dir (str, optional): The base directory for profiles. 
                Defaults to the src/profiles directory relative to this file.
        """
        if profiles_dir is None:
            # Default to the directory containing this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.profiles_dir = current_dir
        else:
            self.profiles_dir = profiles_dir
            
        self.materials_dir = os.path.join(self.profiles_dir, 'materials')
        self.machines_dir = os.path.join(self.profiles_dir, 'machines')
        
        self._materials_cache: Dict[str, dict] = {}
        self._machines_cache: Dict[str, dict] = {}
        
        self._load_all_profiles()
        
    def _load_all_profiles(self) -> None:
        """Loads all profiles into cache upon initialization."""
        # Load materials
        self._materials_cache = {}
        if os.path.exists(self.materials_dir):
            for filename in os.listdir(self.materials_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.materials_dir, filename)
                    with open(filepath, 'r') as f:
                        try:
                            data = json.load(f)
                            self._validate_material(data)
                            self._materials_cache[data['id']] = data
                        except (json.JSONDecodeError, ValueError) as e:
                            print(f"Error loading material {filename}: {e}")

        # Load machines
        self._machines_cache = {}
        if os.path.exists(self.machines_dir):
            for filename in os.listdir(self.machines_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.machines_dir, filename)
                    with open(filepath, 'r') as f:
                        try:
                            data = json.load(f)
                            self._validate_machine(data)
                            self._machines_cache[data['id']] = data
                        except (json.JSONDecodeError, ValueError) as e:
                            print(f"Error loading machine {filename}: {e}")

    def _validate_material(self, data: dict) -> None:
        """Validates that a material profile has all required fields."""
        required_fields = ["name", "id", "category", "temperature", "pressure_sensitivity"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required material field: {field}")

    def _validate_machine(self, data: dict) -> None:
        """Validates that a machine profile has all required fields."""
        required_fields = ["name", "id", "nozzle_diameter", "layer_height", "extrusion_width"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required machine field: {field}")

    def load_materials(self) -> List[dict]:
        """Returns a list of all loaded material profiles."""
        return list(self._materials_cache.values())

    def load_machines(self) -> List[dict]:
        """Returns a list of all loaded machine profiles."""
        return list(self._machines_cache.values())

    def get_material(self, material_id: str) -> dict:
        """
        Gets a material profile by ID.
        
        Args:
            material_id: The ID of the material to retrieve.
            
        Returns:
            dict: The material profile data.
            
        Raises:
            KeyError: If the material ID is not found.
        """
        if material_id not in self._materials_cache:
            raise KeyError(f"Material with id '{material_id}' not found.")
        return self._materials_cache[material_id]

    def get_machine(self, machine_id: str) -> dict:
        """
        Gets a machine profile by ID.
        
        Args:
            machine_id: The ID of the machine to retrieve.
            
        Returns:
            dict: The machine profile data.
            
        Raises:
            KeyError: If the machine ID is not found.
        """
        if machine_id not in self._machines_cache:
            raise KeyError(f"Machine with id '{machine_id}' not found.")
        return self._machines_cache[machine_id]

    def list_materials(self) -> List[str]:
        """Returns a list of all material names."""
        return [mat['name'] for mat in self._materials_cache.values()]

    def list_machines(self) -> List[str]:
        """Returns a list of all machine names."""
        return [mach['name'] for mach in self._machines_cache.values()]

    def save_material(self, data: dict) -> None:
        """Saves a material profile to disk and updates the cache."""
        self._validate_material(data)
        mat_id = data['id']
        filename = f"{mat_id}.json"
        filepath = os.path.join(self.materials_dir, filename)
        
        os.makedirs(self.materials_dir, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        self._materials_cache[mat_id] = data
        
    def save_machine(self, data: dict) -> None:
        """Saves a machine profile to disk and updates the cache."""
        self._validate_machine(data)
        mach_id = data['id']
        filename = f"{mach_id}.json"
        filepath = os.path.join(self.machines_dir, filename)
        
        os.makedirs(self.machines_dir, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        self._machines_cache[mach_id] = data
        
    def delete_material(self, material_id: str) -> None:
        """Deletes a material profile from disk and cache."""
        if material_id in self._materials_cache:
            filename = f"{material_id}.json"
            filepath = os.path.join(self.materials_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            del self._materials_cache[material_id]
            
    def delete_machine(self, machine_id: str) -> None:
        """Deletes a machine profile from disk and cache."""
        if machine_id in self._machines_cache:
            filename = f"{machine_id}.json"
            filepath = os.path.join(self.machines_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            del self._machines_cache[machine_id]
