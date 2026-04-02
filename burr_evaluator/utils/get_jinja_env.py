from jinja2 import Environment, FileSystemLoader

def get_jinja_env(template_directory= './burr_evaluator/mapping_parser/d2rq_mapping/templates'):
        file_loader = FileSystemLoader(template_directory)
        return Environment(loader=file_loader)