from burr_evaluator.utils.get_jinja_env import get_jinja_env

class TranslationTable:
    translation_table: str
    def __init__(self, mapping_name, translation_table) -> None:
        self.mapping_name = mapping_name
        self.translation_table = translation_table
        
    def get_d2rq_mapping(self):
        return get_jinja_env().get_template('translationtable.j2').render(mapping_name = self.mapping_name, translations=self.translation_table)
    
    def __str__(self):
        return self.get_d2rq_mapping()