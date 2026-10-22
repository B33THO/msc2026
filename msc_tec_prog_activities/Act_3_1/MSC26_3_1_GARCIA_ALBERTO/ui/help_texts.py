from classes.base_employee import BaseEmployee
from classes.fee_employee import FeeEmployee
from classes.employee import Employee
from utilities.formatters import Formatter
from utilities.validators import Validator


class HelpTexts:
    """Textos (HTML) del menú Ayuda. Se arman con las constantes de las clases para que no se desactualicen."""

    @staticmethod
    def how_to_use() -> str:
        return f'''
        <h3>Cómo usar la aplicación</h3>
        <p><b>Agregar empleado</b><br>
        Botón <i>Agregar Empleado</i> o <i>Menu → Agregar Empleado</i>. Capture los datos y elija el tipo:</p>
        <ul>
          <li><b>Base:</b> capture la fecha de ingreso. El sueldo por hora inicial lo fija el puesto.</li>
          <li><b>Honorarios:</b> capture las horas trabajadas (1 a {FeeEmployee.MAX_HOURS}).
              El sueldo por hora inicial es fijo: {Formatter.money(FeeEmployee.HOURLY_SALARY)}.</li>
        </ul>
        <p>El botón <i>Limpiar</i> borra el formulario.</p>

        <p><b>Buscar</b><br>
        Escriba un nombre, apellido o NSS en el campo de búsqueda; la tabla se filtra mientras escribe.</p>

        <p><b>Ver detalle, editar y eliminar</b><br>
        Seleccione una fila de la tabla para habilitar los botones.</p>
        <ul>
          <li><b>Ver Detalle</b> (o doble clic en la fila): datos del empleado y desglose de su salario.</li>
          <li><b>Editar:</b> se pueden cambiar nombre, apellidos, fecha de nacimiento, lugar de procedencia,
              sueldo por hora y horas trabajadas. El NSS, tipo, puesto y fecha de ingreso no cambian.</li>
          <li><b>Eliminar:</b> pide confirmación antes de borrar.</li>
        </ul>

        <p><b>Validaciones</b></p>
        <ul>
          <li>NSS de 5 dígitos que no empiece con 0 y que no esté repetido.</li>
          <li>Nombre, apellidos y lugar de procedencia con al menos una letra.</li>
          <li>Edad mínima de {Employee.MIN_AGE} años (también a la fecha de ingreso);
              no se permiten fechas futuras.</li>
          <li>Sueldo por hora mayor que 0 y hasta {Formatter.money(Validator.MAX_AMOUNT)}, con máximo 2 decimales.</li>
        </ul>
        <p>Consulte <i>Ayuda → Fórmulas de salario</i> para ver cómo se calcula el salario.</p>
        '''

    @staticmethod
    def salary_formulas() -> str:
        rows = ''.join(f'<tr><td>{position}</td><td align="right">{Formatter.money(salary)}</td></tr>'
                       for position, salary in BaseEmployee.HOURLY_SALARIES.items())
        seniority = Formatter.percent(BaseEmployee.SENIORITY_RATE)
        extra = Formatter.percent(FeeEmployee.EXTRA_HOUR_RATE)

        # Ejemplos: primer puesto con 10 años de servicio y honorarios con 5 horas extra
        example_position, example_hourly = next(iter(BaseEmployee.HOURLY_SALARIES.items()))
        example_years = 10
        example_base = (example_hourly * BaseEmployee.WEEKLY_HOURS
                        * (1 + BaseEmployee.SENIORITY_RATE * example_years))
        example_extra = 5
        example_hours = FeeEmployee.NORMAL_HOURS + example_extra
        example_fee = (example_hours * FeeEmployee.HOURLY_SALARY
                       * (1 + FeeEmployee.EXTRA_HOUR_RATE * example_extra))
        return f'''
        <h3>Fórmulas de salario</h3>
        <p><b>Empleado base</b><br>
        Salario = sueldo por hora × {BaseEmployee.WEEKLY_HOURS} horas × (1 + {seniority} por cada año de servicio)</p>
        <p>Los años de servicio son años completos desde la fecha de ingreso.<br>
        <i>Ejemplo ({example_position}, {example_years} años de servicio):</i>
        {Formatter.money(example_hourly)} × {BaseEmployee.WEEKLY_HOURS} × (1 + {example_years} × {BaseEmployee.SENIORITY_RATE:g})
        = {Formatter.money(example_base)}</p>
        <p>Sueldo por hora inicial según el puesto:</p>
        <table cellspacing="0" cellpadding="3" border="1">
          <tr><th align="left">Puesto</th><th align="right">Sueldo / hora</th></tr>
          {rows}
        </table>

        <p><b>Empleado de honorarios</b><br>
        Salario = horas trabajadas × sueldo por hora × (1 + {extra} por cada hora extra)</p>
        <p>Las horas normales son de 1 a {FeeEmployee.NORMAL_HOURS}; cada hora arriba de {FeeEmployee.NORMAL_HOURS}
        es hora extra (máximo {FeeEmployee.MAX_HOURS} horas en total).<br>
        Sueldo por hora inicial: {Formatter.money(FeeEmployee.HOURLY_SALARY)}.<br>
        <i>Ejemplo ({example_hours} horas, {example_extra} extra):</i>
        {example_hours} × {Formatter.money(FeeEmployee.HOURLY_SALARY)} × (1 + {example_extra} × {FeeEmployee.EXTRA_HOUR_RATE:g})
        = {Formatter.money(example_fee)}</p>

        <p>El sueldo por hora de cada empleado se puede actualizar con <i>Editar Empleado</i>.</p>
        '''

    @staticmethod
    def about() -> str:
        return '''
        <h3>Empleados</h3>
        <p>Actividad 3.1 – Administración de empleados base y de honorarios con interfaz gráfica.</p>
        <p>Alberto García<br>
        Maestría en Sistemas Computacionales, 2026</p>
        <p>Desarrollado con Python y PyQt6.</p>
        '''
