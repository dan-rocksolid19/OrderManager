from librepy.model.base_dao import BaseDAO
from librepy.model.model import Crews


class CrewDAO(BaseDAO):
    
    def __init__(self, logger):
        super().__init__(Crews, logger)
    
    def add_crew(self, name):
        """
        Create a single crew record.
        
        Args:
            name (str): The crew name
            
        Returns:
            Crews: The created crew instance
        """
        name = self.validate_string_field(name, "crew_name", max_length=150, required=True)
        
        return self.safe_execute(
            "creating crew",
            lambda: self.model_class.create(crew_name=name),
            reraise_integrity=True
        )
    
    def remove_crew(self, crew_id):
        """
        Delete crew by ID.
        
        Args:
            crew_id (int): The crew ID to delete
            
        Returns:
            bool: True if successful
        """
        crew_id = self.validate_numeric_field(crew_id, "crew_id", min_value=1, required=True)
        
        rows = self.safe_execute(
            f"deleting {self.model_class.__name__} ID {crew_id}",
            lambda: self.model_class.delete().where(self.model_class.id == crew_id).execute(),
            default_return=0,
            reraise_integrity=False
        )
        if rows == 0:
            raise Exception(f"Failed to delete {self.model_class.__name__} ID {crew_id}")
        return True
    
    def get_all_crews(self):
        """
        Return list of all crews ordered by crew_name.
        
        Returns:
            list[Crews]: List of crew instances
        """
        return self.safe_execute(
            "fetching all crews",
            lambda: list(self.model_class.select().order_by(self.model_class.crew_name)),
            default_return=[]
        )
    
    def replace_all(self, crews):
        """
        Bulk persistence: inside a transaction, delete all existing rows and insert the provided names.
        Used by the dialog's Save button.
        
        Args:
            crews (list[str]): List of crew names to replace all existing crews with
            
        Returns:
            bool: True if successful
        """
        if not isinstance(crews, list):
            raise ValueError("crews must be a list")
        
        validated_crews = []
        for crew_name in crews:
            validated_name = self.validate_string_field(crew_name, "crew_name", max_length=150, required=True)
            validated_crews.append(validated_name)
        
        with self.database.connection_context():
            with self.database.atomic():
                self.safe_execute(
                    "deleting all existing crews",
                    lambda: self.model_class.delete().execute(),
                    default_return=0
                )
                
                if validated_crews:
                    crew_data = [{"crew_name": name} for name in validated_crews]
                    self.safe_execute(
                        f"inserting {len(crew_data)} new crews",
                        lambda: self.model_class.insert_many(crew_data).execute(),
                        reraise_integrity=True
                    )
        
        return True 