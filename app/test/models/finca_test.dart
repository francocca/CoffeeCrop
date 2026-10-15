import 'package:flutter_test/flutter_test.dart';

import 'package:coffecrop/data/exceptions/finca_exceptions.dart';
import 'package:coffecrop/models/finca.dart';

Finca _crearFinca({String nombre = 'Finca El Cafetal', int plantas = 1700}) => Finca(
      id: 'f1',
      nombre: nombre,
      numeroPlantas: plantas,
      fechaCreacion: DateTime(2026, 1, 1),
    );

void main() {
  group('Finca — validación (BR-001)', () {
    test('acepta datos válidos', () {
      // Arrange & Act
      final finca = _crearFinca();

      // Assert
      expect(finca.nombre, 'Finca El Cafetal');
      expect(finca.numeroPlantas, 1700);
    });

    test('acepta un nombre de exactamente 100 caracteres', () {
      // Arrange
      final nombreLimite = 'a' * 100;

      // Act
      final finca = _crearFinca(nombre: nombreLimite);

      // Assert
      expect(finca.nombre.length, 100);
    });

    test('acepta exactamente 1 planta', () {
      // Arrange & Act
      final finca = _crearFinca(plantas: 1);

      // Assert
      expect(finca.numeroPlantas, 1);
    });

    test('rechaza un nombre vacío', () {
      // Arrange
      crear() => _crearFinca(nombre: '');

      // Act & Assert
      expect(crear, throwsA(isA<InvalidFarmDataException>()));
    });

    test('rechaza un nombre de solo espacios', () {
      // Arrange
      crear() => _crearFinca(nombre: '    ');

      // Act & Assert
      expect(crear, throwsA(isA<InvalidFarmDataException>()));
    });

    test('rechaza un nombre de 101 caracteres', () {
      // Arrange
      crear() => _crearFinca(nombre: 'a' * 101);

      // Act & Assert
      expect(
        crear,
        throwsA(isA<InvalidFarmDataException>().having((e) => e.message, 'message', contains('nombre'))),
      );
    });

    test('rechaza 0 plantas', () {
      // Arrange
      crear() => _crearFinca(plantas: 0);

      // Act & Assert
      expect(
        crear,
        throwsA(isA<InvalidFarmDataException>().having((e) => e.message, 'message', contains('plantas'))),
      );
    });

    test('rechaza un número de plantas negativo', () {
      // Arrange
      crear() => _crearFinca(plantas: -5);

      // Act & Assert
      expect(crear, throwsA(isA<InvalidFarmDataException>()));
    });
  });

  group('Finca — conversión a/desde el mapa de SQLite', () {
    test('toMap usa los nombres de columna del esquema y la fecha en ISO-8601', () {
      // Arrange
      final finca = _crearFinca();

      // Act
      final mapa = finca.toMap();

      // Assert
      expect(mapa, {
        'id': 'f1',
        'nombre': 'Finca El Cafetal',
        'numero_plantas': 1700,
        'fecha_creacion': DateTime(2026, 1, 1).toIso8601String(),
      });
    });

    test('fromMap reconstruye la misma finca', () {
      // Arrange
      final original = _crearFinca();

      // Act
      final reconstruida = Finca.fromMap(original.toMap());

      // Assert
      expect(reconstruida.id, original.id);
      expect(reconstruida.nombre, original.nombre);
      expect(reconstruida.numeroPlantas, original.numeroPlantas);
      expect(reconstruida.fechaCreacion, original.fechaCreacion);
    });
  });
}
