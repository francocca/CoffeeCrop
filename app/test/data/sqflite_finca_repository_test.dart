import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_common_ffi.dart';

import 'package:coffecrop/data/repositories/sqflite_finca_repository.dart';
import 'package:coffecrop/models/finca.dart';

void main() {
  late Database db;
  late SqfliteFincaRepository repository;

  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  setUp(() async {
    db = await databaseFactory.openDatabase(inMemoryDatabasePath);
    await db.execute('''
      CREATE TABLE finca (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        numero_plantas INTEGER NOT NULL,
        fecha_creacion TEXT NOT NULL
      );
    ''');
    await db.execute('''
      CREATE TABLE actividad (
        id TEXT PRIMARY KEY,
        finca_id TEXT NOT NULL,
        nombre TEXT NOT NULL,
        monto REAL NOT NULL,
        fecha TEXT NOT NULL,
        fecha_creacion TEXT NOT NULL,
        FOREIGN KEY (finca_id) REFERENCES finca(id)
      );
    ''');
    repository = SqfliteFincaRepository(db);
  });

  tearDown(() async {
    await db.close();
  });

  group('obtenerFinca', () {
    test('devuelve null cuando no hay finca registrada', () async {
      // Arrange: base de datos vacía (setUp)

      // Act
      final finca = await repository.obtenerFinca();

      // Assert
      expect(finca, isNull);
    });

    test('devuelve la finca guardada previamente', () async {
      // Arrange
      await repository.guardarFinca(Finca(
        id: '1',
        nombre: 'Finca El Cafetal',
        numeroPlantas: 1700,
        fechaCreacion: DateTime(2026, 1, 1),
      ));

      // Act
      final finca = await repository.obtenerFinca();

      // Assert
      expect(finca, isNotNull);
      expect(finca!.nombre, 'Finca El Cafetal');
      expect(finca.numeroPlantas, 1700);
    });
  });

  group('guardarFinca', () {
    test('reemplaza los datos existentes al editar (mismo id)', () async {
      // Arrange
      await repository.guardarFinca(Finca(
        id: '1',
        nombre: 'Finca Original',
        numeroPlantas: 1000,
        fechaCreacion: DateTime(2026, 1, 1),
      ));

      // Act
      await repository.guardarFinca(Finca(
        id: '1',
        nombre: 'Finca Editada',
        numeroPlantas: 1500,
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      final finca = await repository.obtenerFinca();

      // Assert
      expect(finca!.nombre, 'Finca Editada');
      expect(finca.numeroPlantas, 1500);
    });
  });
}
