import 'package:flutter_test/flutter_test.dart';

import 'package:coffecrop/data/exceptions/finca_exceptions.dart';
import 'package:coffecrop/models/actividad.dart';

Actividad _crearActividad({
  String nombre = 'Compra de fungicida',
  double monto = 150000,
  DateTime? fecha,
}) =>
    Actividad(
      id: 'a1',
      fincaId: 'f1',
      nombre: nombre,
      monto: monto,
      fecha: fecha ?? DateTime(2026, 1, 5),
      fechaCreacion: DateTime(2026, 1, 5),
    );

void main() {
  group('Actividad — validación (BR-003)', () {
    test('acepta datos válidos', () {
      // Arrange & Act
      final actividad = _crearActividad();

      // Assert
      expect(actividad.nombre, 'Compra de fungicida');
      expect(actividad.monto, 150000);
    });

    test('acepta un nombre de exactamente 100 caracteres', () {
      // Arrange
      final nombreLimite = 'a' * 100;

      // Act
      final actividad = _crearActividad(nombre: nombreLimite);

      // Assert
      expect(actividad.nombre.length, 100);
    });

    test('acepta un monto de 0 (el límite inferior es inclusivo)', () {
      // Arrange & Act
      final actividad = _crearActividad(monto: 0);

      // Assert
      expect(actividad.monto, 0);
    });

    test('acepta la fecha de hoy', () {
      // Arrange
      final ahora = DateTime.now();

      // Act
      final actividad = _crearActividad(fecha: ahora);

      // Assert
      expect(actividad.fecha, ahora);
    });

    test('rechaza un nombre vacío', () {
      // Arrange
      crear() => _crearActividad(nombre: '');

      // Act & Assert
      expect(crear, throwsA(isA<InvalidActivityDataException>()));
    });

    test('rechaza un nombre de solo espacios', () {
      // Arrange
      crear() => _crearActividad(nombre: '    ');

      // Act & Assert
      expect(crear, throwsA(isA<InvalidActivityDataException>()));
    });

    test('rechaza un nombre de 101 caracteres', () {
      // Arrange
      crear() => _crearActividad(nombre: 'a' * 101);

      // Act & Assert
      expect(
        crear,
        throwsA(isA<InvalidActivityDataException>().having((e) => e.message, 'message', contains('nombre'))),
      );
    });

    test('rechaza un monto negativo', () {
      // Arrange
      crear() => _crearActividad(monto: -0.01);

      // Act & Assert
      expect(
        crear,
        throwsA(isA<InvalidActivityDataException>().having((e) => e.message, 'message', contains('monto'))),
      );
    });

    test('rechaza una fecha futura', () {
      // Arrange
      final manana = DateTime.now().add(const Duration(days: 1));
      crear() => _crearActividad(fecha: manana);

      // Act & Assert
      expect(
        crear,
        throwsA(isA<InvalidActivityDataException>().having((e) => e.message, 'message', contains('futura'))),
      );
    });
  });

  group('Actividad — conversión a/desde el mapa de SQLite', () {
    test('toMap usa los nombres de columna del esquema y las fechas en ISO-8601', () {
      // Arrange
      final actividad = _crearActividad();

      // Act
      final mapa = actividad.toMap();

      // Assert
      expect(mapa, {
        'id': 'a1',
        'finca_id': 'f1',
        'nombre': 'Compra de fungicida',
        'monto': 150000.0,
        'fecha': DateTime(2026, 1, 5).toIso8601String(),
        'fecha_creacion': DateTime(2026, 1, 5).toIso8601String(),
      });
    });

    test('fromMap reconstruye la misma actividad', () {
      // Arrange
      final original = _crearActividad();

      // Act
      final reconstruida = Actividad.fromMap(original.toMap());

      // Assert
      expect(reconstruida.id, original.id);
      expect(reconstruida.fincaId, original.fincaId);
      expect(reconstruida.nombre, original.nombre);
      expect(reconstruida.monto, original.monto);
      expect(reconstruida.fecha, original.fecha);
      expect(reconstruida.fechaCreacion, original.fechaCreacion);
    });

    test('fromMap acepta un monto entero (SQLite puede devolver int para REAL)', () {
      // Arrange
      final mapa = _crearActividad().toMap()..['monto'] = 50000;

      // Act
      final actividad = Actividad.fromMap(mapa);

      // Assert
      expect(actividad.monto, 50000.0);
    });
  });
}
