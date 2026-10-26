# Cuentas

## Contenido del proyecto
1. Scrip que genera la base de datos
2. Interfaz Gráfica
3. Iconos

## Operaciones CRUD
1. Agregar cuenta de ahorro
2. Agregar cuenta de crédito

### Campos para crear ambos casos
- Número de cuenta
- Apellido paterno
- Apellido materno
- Nombre
- Saldo con el que se abre la cuenta
- fecha de apertura de la cuenta
- Para "cuenta de crédito" se pide el monto de crédito

### Eliminar cuenta

### Actualizar
- [ ] Apellido paterno
- [ ] Apellido materno
- [ ] Nombre
- [ ] Monto de crédito de las cuentas de crédito
    _si la modificacion deja el monto de crédito menor al adeudo, rechazar_
- [ ] Pagar credito. Si hay adeudo, los depositos pagan el crédito

### Consultar
- [ ] Todas las cuentas
- [ ] Por número de cuenta
- [ ] Solo cuentas de ahorro
- [ ] Solo cuentas de crédito
- [ ] Cuentas con saldo menor o igual a una cantidad

## Interfaz Gráfica
- [ ] Incrementar saldo a alguna cuenta
- [ ] Retirar de alguna cuenta    
    
    _La cantidad debe ser menor o igual al saldo de la cuenta, si no, enviar mensaje_

- [ ] Cuenta de credito
    _Retirar primero del saldo y luego del límite de crédito_
    _Si el monto a retirar excede la suma del saldo y crédito, enviar mensaje_

- [ ] Limpiar los controles que agregan nuevas cuentas despues de crearla 
- [ ] Botón para limpiar campos
- [ ] Cargar datos desde archivos csv o xlsx a la tabla
- [ ] Guardar datos a archivos csv o xlsx 

_xlsx en lugar del antiguo xls, se dio la indicación que puede ser xslx o solo csv_

## Clases

### Cuentas:
| Cuenta | Cuenta Crédito
| :--- | :--- |
| Numero de cuenta | Numero de cuenta |
| Apellido Paterno | Apelldido Paterno |
| Apellido Materno | Apelldido Materno |
| Nombre | Nombre |
| Saldo | Saldo |
| | Crédito |
| | Adeudo |

## Refactor
_Según indicaciones, se puede mejorar la actividad con deciciones propias_
1. Separar los datos de usuario de los datos de la cuenta
2. En la realidad un usuario puede tener tantas cuentas como quiera 
- Puede tener 1 o varias cuentas normales
- Puede tener 1 o varias cuentas de crédito
3. El número de cuenta ya no se pide al usuario como se haría en una situación real
```javascript
    usuario {
        id,
        apellido paterno,
        apellido materno,
        nombre
    }

    cuenta {
        número de cuenta,    
        saldo,
        fecha de creación
    }

    cuenta crédito(cuenta) {        
        numero de cuenta,
        límite de crédito,
        credito usado
    }


```
x

## Estructura del proyecto
`MSC26_4_1_GARCIA_ALBERTO/`

| Carpeta | Propósito |
| :--- | :--- |
| `data/` | Archivos de datos que se cargan o guardan desde la tabla (.csv / .xlsx) |
| `db/` | Script SQL que genera la base de datos y la clase/módulo de conexión a MySQL |
| `domain/` | **Modelo**: clases Cliente, Cuenta (ahorro) y CuentaCredito |
| `icons/` | Iconos usados por la interfaz gráfica |
| `repositories/` | **Repositorio**: único lugar con SQL (CRUD y consultas). Usa `db/Connection` y devuelve objetos de `domain/` |
| `services/` | Lógica de negocio: depósitos, retiros y validaciones de saldo/crédito. Llama a `repositories/`, no escribe SQL |
| `ui/` | **Vista**: ventanas, formularios y tabla. Llama a `services/`, nunca a `db/` |
| `utilities/` | Funciones auxiliares: validación de campos, formato de datos, lectura/escritura de CSV/XLSX |
