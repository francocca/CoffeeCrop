import 'package:flutter_test/flutter_test.dart';

import 'package:coffecrop/utils/formatters.dart';

void main() {
  final ahora = DateTime(2026, 10, 14, 15, 30);

  group('formatearHace', () {
    test('devuelve "Hoy" para el mismo día, sin importar la hora', () {
      // Arrange
      final temprano = DateTime(2026, 10, 14, 0, 5);

      // Act
      final texto = formatearHace(temprano, ahora: ahora);

      // Assert
      expect(texto, 'Hoy');
    });

    test('devuelve "Ayer" para el día anterior, aunque pasen menos de 24 horas', () {
      // Arrange
      final anoche = DateTime(2026, 10, 13, 23, 50);

      // Act
      final texto = formatearHace(anoche, ahora: ahora);

      // Assert
      expect(texto, 'Ayer');
    });

    test('devuelve "Hace N días" para fechas anteriores', () {
      // Arrange
      final fecha = DateTime(2026, 10, 4, 18, 0);

      // Act
      final texto = formatearHace(fecha, ahora: ahora);

      // Assert
      expect(texto, 'Hace 10 días');
    });
  });
}
