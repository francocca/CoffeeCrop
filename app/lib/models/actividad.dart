import '../data/exceptions/finca_exceptions.dart';

/// Entidad Actividad — ver spec.md §4 y BR-003.
class Actividad {
  final String id;
  final String fincaId;
  final String nombre;
  final double monto;
  final DateTime fecha;
  final DateTime fechaCreacion;

  Actividad({
    required this.id,
    required this.fincaId,
    required this.nombre,
    required this.monto,
    required this.fecha,
    required this.fechaCreacion,
  }) {
    if (nombre.trim().isEmpty || nombre.length > 100) {
      throw const InvalidActivityDataException(
          'El nombre de la actividad debe tener entre 1 y 100 caracteres.');
    }
    if (monto < 0) {
      throw const InvalidActivityDataException('El monto no puede ser negativo.');
    }
    if (fecha.isAfter(DateTime.now())) {
      throw const InvalidActivityDataException('La fecha no puede ser futura.');
    }
  }

  Map<String, Object?> toMap() => {
        'id': id,
        'finca_id': fincaId,
        'nombre': nombre,
        'monto': monto,
        'fecha': fecha.toIso8601String(),
        'fecha_creacion': fechaCreacion.toIso8601String(),
      };

  factory Actividad.fromMap(Map<String, Object?> map) => Actividad(
        id: map['id'] as String,
        fincaId: map['finca_id'] as String,
        nombre: map['nombre'] as String,
        monto: (map['monto'] as num).toDouble(),
        fecha: DateTime.parse(map['fecha'] as String),
        fechaCreacion: DateTime.parse(map['fecha_creacion'] as String),
      );
}
