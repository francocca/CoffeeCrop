class ActividadFinca {
  final String nombre;
  final int diasAtras;
  final double monto;

  const ActividadFinca({
    required this.nombre,
    required this.diasAtras,
    required this.monto,
  });
}

/// Datos de ejemplo de la finca cafetera.
/// TODO: reemplazar por datos reales desde SQLite (ver Fase 1, tarea de esquema).
class MockFincaData {
  static const nombreFinca = 'Finca El Cafetal';
  static const numeroPlantas = 1700;
  static const inversionTotal = 26500000;
  static const costoPorPlanta = 15588;

  static const ultimasActividades = [
    ActividadFinca(nombre: 'Fertilización 12-6-24', diasAtras: 18, monto: 450000),
    ActividadFinca(nombre: 'Control de plagas', diasAtras: 32, monto: 380000),
    ActividadFinca(nombre: 'Limpieza de lotes', diasAtras: 45, monto: 250000),
    ActividadFinca(nombre: 'Análisis de suelo', diasAtras: 60, monto: 180000),
  ];
}
