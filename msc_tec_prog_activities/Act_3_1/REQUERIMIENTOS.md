# Act 3.1 – Empleados: lista de requerimientos

Fuente: `Empleados.pdf`. **E** = explícito en el PDF, **D** = deducido (necesario para que funcione o para resolver ambigüedades).

> Para Claude: cuando el usuario pida **"revisar avance"**, responder con una tabla de hecho/faltante por requerimiento (IDs de abajo), lista de errores encontrados en el código y porcentaje de avance por sección y total.

## A. Estructura del proyecto
| ID | Requerimiento | Tipo |
|---|---|---|
| A1 | Proyecto Python con nomenclatura del curso (`MSC26_3_1_GARCIA_ALBERTO`) | E |
| A2 | Organizado en **paquetes** (p. ej. `ui`, `utilities`, `models`) con `__init__.py` | E/D |
| A3 | Clases de modelo: empleado base y de honorarios (herencia de `Employee`, como en Act 2.4) | D |
| A4 | Interfaz gráfica (PyQt6 + `.ui`) | D |

## B. Interfaz
| ID | Requerimiento | Tipo |
|---|---|---|
| B1 | Contener todos los campos mencionados en el ejercicio (ver C1) | E |
| B2 | **Iconos** guardados en archivo(s) dentro del proyecto (p. ej. carpeta `icons/`), no rutas externas | E |
| B3 | Al menos **un contenedor** (`QGroupBox`, `QTabWidget`, `QFrame`…) | E |
| B4 | **Toda** la información reflejada en una **tabla** (`QTableWidget`), refrescada al agregar/actualizar/eliminar | E |
| B5 | **Validaciones** en todos los campos de captura | E |
| B6 | **Ayuda** sobre el funcionamiento dentro de la interfaz (menú Ayuda → `QMessageBox`, tooltips) | E |

## C. Agregar empleado
| ID | Requerimiento | Tipo |
|---|---|---|
| C1 | Campos: NSS, apellido paterno, apellido materno, nombre, puesto, fecha de nacimiento, lugar de origen | E |
| C2 | Selección de tipo: **base** u **honorarios** | E |
| C3 | **5 puestos** predefinidos (combo) | E |
| C4 | Base: sueldo por hora inicial **fijo según el puesto** (tabla puesto→sueldo), no se captura | E |
| C5 | Honorarios: sueldo por hora inicial fijo + **capturar horas trabajadas** | E |
| C6 | **Fecha de ingreso / años de servicio** para empleado base (el PDF no lo lista, pero el salario lo requiere) | D |
| C7 | NSS único (no duplicados) | D |
| C8 | Campo de horas solo habilitado/visible para honorarios | D |

## D. Eliminar / Actualizar / Buscar / Limpiar
| ID | Requerimiento | Tipo |
|---|---|---|
| D1 | Eliminar empleado (por NSS o fila seleccionada), con confirmación | E/D |
| D2 | Actualizar: ap. paterno, ap. materno, nombre, fecha de nacimiento, lugar (NSS, tipo y puesto **no**) | E/D |
| D3 | Actualizar sueldo base o sueldo por hora de un empleado | E |
| D4 | Buscar empleado por NSS y mostrar resultado (resaltar fila o cargar en formulario) | E |
| D5 | Botón **Limpiar** los controles del formulario de alta | E |

## E. Salario
| ID | Requerimiento | Tipo |
|---|---|---|
| E1 | Base: `sueldo_hora × 40 × (1 + 0.01 × años_servicio)` | E |
| E2 | Honorarios: `horas × sueldo_hora`, horas normales 1–40 | E |
| E3 | Honorarios: +0.2 % por cada hora extra (ver ambigüedad 2) | E |
| E4 | Mostrar el salario de un empleado seleccionado (columna en tabla o botón) | E/D |

## Ambigüedades e interpretación propuesta
1. **Años de servicio sin campo** → agregar "Fecha de ingreso" (`QDateEdit`) y calcular años completos.
2. **Horas extra vs. "1 >= horas <= 40"** → permitir > 40 con tope (60 o 168); `extra = max(0, horas - 40)`; `salario = horas × sueldo_hora × (1 + 0.002 × extra)`. Documentar la fórmula elegida en la Ayuda.
3. **Sueldo fijo de honorarios**: uno solo o por puesto. Sugerencia: un valor fijo único (o tabla por puesto por simetría).
4. **Formato NSS**: el validador actual usa 5 dígitos (como Act 2.4); el NSS real del IMSS tiene 11. Decidir y documentar.
5. **"Actualizar sueldo"** = cambia el sueldo de ese empleado, no la tabla de puestos.
6. **"Iconos en un archivo"** = carpeta de recursos (o `.qrc`) dentro del proyecto.

## Observaciones iniciales del código (2026-10-17)
- `main.py`: el `try/except` envuelve el `def __init__` en el cuerpo de la clase; no atrapa errores de ejecución. Debe ir dentro del método.
- `utilities/` sin `__init__.py`.
- `Validator.__error` solo retorna el mensaje y nadie lo usa; para la GUI conviene devolver el mensaje o lanzar excepción y mostrarlo con `QMessageBox`.
- UI solo tiene `btnAddEmployee`.
