import '../data/exceptions/finca_exceptions.dart';

/// Entidad Finca — ver spec.md §4 y BR-001.
class Finca {
  final String id;
  final String nombre;
  final int numeroPlantas;
  final DateTime fechaCreacion;

  Finca({
    required this.id,
    required this.nombre,
    required this.numeroPlantas,
    required this.fechaCreacion,
  }) {
    if (nombre.trim().isEmpty || nombre.length > 100) {
      throw const InvalidFarmDataException(
          'El nombre de la finca debe tener entre 1 y 100 caracteres.');
    }
    if (numeroPlantas <= 0) {
      throw const InvalidFarmDataException(
          'El número de plantas debe ser mayor a 0.');
    }
  }

  Map<String, Object?> toMap() => {
        'id': id,
        'nombre': nombre,
        'numero_plantas': numeroPlantas,
        'fecha_creacion': fechaCreacion.toIso8601String(),
      };

  factory Finca.fromMap(Map<String, Object?> map) => Finca(
        id: map['id'] as String,
        nombre: map['nombre'] as String,
        numeroPlantas: map['numero_plantas'] as int,
        fechaCreacion: DateTime.parse(map['fecha_creacion'] as String),
      );
}
