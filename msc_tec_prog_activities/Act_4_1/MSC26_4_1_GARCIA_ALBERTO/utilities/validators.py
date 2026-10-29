#Validación de campos requeridos
def validate_required_text(value, field_name, max_length = 100):

    value = value.strip()
    field_name = field_name.strip()

    if not value:
        raise ValueError(f'El campo {field_name} es requerido')

    if len(value) > max_length:
        raise ValueError(f'El campo {field_name} debe ser menor o igual a {max_length} caracteres')

    #Regresa el texto ya sin espacios al inicio y al final
    return value


