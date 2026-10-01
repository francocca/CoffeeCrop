import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_common_ffi.dart';

import 'package:coffecrop/data/exceptions/finca_exceptions.dart';
import 'package:coffecrop/data/repositories/sqflite_finca_repository.dart';
import 'package:coffecrop/models/actividad.dart';
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

  group('agregarActividad', () {
    test('lanza NoFincaException si no hay finca registrada (BR-005)', () async {
      // Arrange: base de datos sin finca (setUp)
      final actividad = Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización',
        monto: 50000,
        fecha: DateTime(2026, 1, 1),
        fechaCreacion: DateTime(2026, 1, 1),
      );

      // Act & Assert
      expect(
        () => repository.agregarActividad(actividad),
        throwsA(isA<NoFincaException>()),
      );
    });

    test('inserta la actividad cuando sí existe una finca', () async {
      // Arrange
      await repository.guardarFinca(Finca(
        id: 'f1',
        nombre: 'Finca El Cafetal',
        numeroPlantas: 1700,
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      final actividad = Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización',
        monto: 50000,
        fecha: DateTime(2026, 1, 1),
        fechaCreacion: DateTime(2026, 1, 1),
      );

      // Act
      await repository.agregarActividad(actividad);
      final actividades = await repository.listarActividades(pagina: 0);

      // Assert
      expect(actividades.length, 1);
      expect(actividades.first.nombre, 'Fertilización');
    });
  });

  group('calcularInversionTotal', () {
    test('devuelve 0 cuando no hay actividades', () async {
      // Arrange: base de datos vacía (setUp)

      // Act
      final total = await repository.calcularInversionTotal();

      // Assert
      expect(total, 0);
    });

    test('suma los montos de todas las actividades', () async {
      // Arrange
      await repository.guardarFinca(Finca(
        id: 'f1',
        nombre: 'Finca El Cafetal',
        numeroPlantas: 1700,
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      await repository.agregarActividad(Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización',
        monto: 50000,
        fecha: DateTime(2026, 1, 1),
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      await repository.agregarActividad(Actividad(
        id: 'a2',
        fincaId: 'f1',
        nombre: 'Control de plagas',
        monto: 30000,
        fecha: DateTime(2026, 1, 2),
        fechaCreacion: DateTime(2026, 1, 2),
      ));

      // Act
      final total = await repository.calcularInversionTotal();

      // Assert
      expect(total, 80000);
    });
  });

  group('listarActividades', () {
    test('pagina de a 20, ordenado por fecha descendente (DEC-004)', () async {
      // Arrange: 25 actividades con fechas crecientes (la más nueva: día 25)
      await repository.guardarFinca(Finca(
        id: 'f1',
        nombre: 'Finca El Cafetal',
        numeroPlantas: 1700,
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      for (var i = 1; i <= 25; i++) {
        await repository.agregarActividad(Actividad(
          id: 'a$i',
          fincaId: 'f1',
          nombre: 'Actividad $i',
          monto: 1000.0 * i,
          fecha: DateTime(2026, 1, i),
          fechaCreacion: DateTime(2026, 1, i),
        ));
      }

      // Act
      final pagina0 = await repository.listarActividades(pagina: 0);
      final pagina1 = await repository.listarActividades(pagina: 1);

      // Assert
      expect(pagina0.length, 20);
      expect(pagina1.length, 5);
      expect(pagina0.first.nombre, 'Actividad 25'); // la más reciente primero
      expect(pagina1.last.nombre, 'Actividad 1'); // la más antigua al final
    });
  });

  group('actualizarActividad', () {
    test('actualiza los datos y se reflejan al volver a leer', () async {
      // Arrange
      await repository.guardarFinca(Finca(
        id: 'f1',
        nombre: 'Finca El Cafetal',
        numeroPlantas: 1700,
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      await repository.agregarActividad(Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización',
        monto: 50000,
        fecha: DateTime(2026, 1, 1),
        fechaCreacion: DateTime(2026, 1, 1),
      ));

      // Act
      await repository.actualizarActividad(Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización (corregida)',
        monto: 60000,
        fecha: DateTime(2026, 1, 2),
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      final actividades = await repository.listarActividades(pagina: 0);

      // Assert
      expect(actividades.length, 1);
      expect(actividades.first.nombre, 'Fertilización (corregida)');
      expect(actividades.first.monto, 60000);
    });

    test('la inversión total refleja el cambio tras editar (BR-004)', () async {
      // Arrange
      await repository.guardarFinca(Finca(
        id: 'f1',
        nombre: 'Finca El Cafetal',
        numeroPlantas: 1700,
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      await repository.agregarActividad(Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización',
        monto: 50000,
        fecha: DateTime(2026, 1, 1),
        fechaCreacion: DateTime(2026, 1, 1),
      ));

      // Act
      await repository.actualizarActividad(Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización',
        monto: 80000,
        fecha: DateTime(2026, 1, 1),
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      final total = await repository.calcularInversionTotal();

      // Assert
      expect(total, 80000);
    });
  });

  group('eliminarActividad', () {
    test('elimina la actividad y deja de aparecer en el listado', () async {
      // Arrange
      await repository.guardarFinca(Finca(
        id: 'f1',
        nombre: 'Finca El Cafetal',
        numeroPlantas: 1700,
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      await repository.agregarActividad(Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización',
        monto: 50000,
        fecha: DateTime(2026, 1, 1),
        fechaCreacion: DateTime(2026, 1, 1),
      ));

      // Act
      await repository.eliminarActividad('a1');
      final actividades = await repository.listarActividades(pagina: 0);

      // Assert
      expect(actividades, isEmpty);
    });

    test('la inversión total refleja el cambio tras eliminar (BR-004)', () async {
      // Arrange
      await repository.guardarFinca(Finca(
        id: 'f1',
        nombre: 'Finca El Cafetal',
        numeroPlantas: 1700,
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      await repository.agregarActividad(Actividad(
        id: 'a1',
        fincaId: 'f1',
        nombre: 'Fertilización',
        monto: 50000,
        fecha: DateTime(2026, 1, 1),
        fechaCreacion: DateTime(2026, 1, 1),
      ));
      await repository.agregarActividad(Actividad(
        id: 'a2',
        fincaId: 'f1',
        nombre: 'Control de plagas',
        monto: 30000,
        fecha: DateTime(2026, 1, 2),
        fechaCreacion: DateTime(2026, 1, 2),
      ));

      // Act
      await repository.eliminarActividad('a1');
      final total = await repository.calcularInversionTotal();

      // Assert
      expect(total, 30000);
    });
  });
}
