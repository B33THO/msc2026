/* ============================================================
   schema.js — definición de las tablas y datos semilla
   Escenario: una tienda. Vender un producto exige tocar DOS tablas
   (descontar Inventario.stock e insertar en Pedidos), que es justo
   lo que hace interesante a las transacciones.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

SQLSim.esquema = {

  Productos: {
    clave: 'producto_id',
    columnas: [
      { nombre: 'producto_id', tipo: 'INT' },
      { nombre: 'nombre',      tipo: 'VARCHAR' },
      { nombre: 'precio',      tipo: 'DECIMAL' }
    ],
    semilla: [
      { producto_id: 1, nombre: 'Teclado mecanico', precio: 1250.00 },
      { producto_id: 2, nombre: 'Mouse inalambrico', precio: 480.00 },
      { producto_id: 3, nombre: 'Monitor 24"',       precio: 3200.00 },
      { producto_id: 4, nombre: 'Audifonos',         precio: 890.00 },
      { producto_id: 5, nombre: 'Webcam HD',         precio: 1100.00 }
    ]
  },

  Inventario: {
    clave: 'producto_id',
    columnas: [
      { nombre: 'producto_id', tipo: 'INT' },
      { nombre: 'stock',       tipo: 'INT' }
    ],
    semilla: [
      { producto_id: 1, stock: 10 },
      { producto_id: 2, stock: 25 },
      { producto_id: 3, stock: 4  },
      { producto_id: 4, stock: 15 },
      { producto_id: 5, stock: 2  }
    ]
  },

  Pedidos: {
    clave: 'pedido_id',
    autoincremento: true,
    columnas: [
      { nombre: 'pedido_id',   tipo: 'INT' },
      { nombre: 'producto_id', tipo: 'INT' },
      { nombre: 'cantidad',    tipo: 'INT' },
      { nombre: 'total',       tipo: 'DECIMAL' },
      { nombre: 'estado',      tipo: 'VARCHAR' }
    ],
    semilla: [
      { pedido_id: 1, producto_id: 2, cantidad: 3, total: 1440.00, estado: 'COMPLETADO' },
      { pedido_id: 2, producto_id: 4, cantidad: 1, total: 890.00,  estado: 'COMPLETADO' }
    ]
  }

};

/* Orden en que se muestran los paneles de tablas */
SQLSim.ordenTablas = ['Productos', 'Inventario', 'Pedidos'];
