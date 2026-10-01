import 'package:sqflite/sqflite.dart';

import '../../models/actividad.dart';
import '../../models/finca.dart';
import 'finca_repository.dart';

/// Implementación de [FincaRepository] con sqflite — ver plan.md §5 para el
/// detalle de cada consulta SQL.
class SqfliteFincaRepository implements FincaRepository {
  final Database db;

  const SqfliteFincaRepository(this.db);

  @override
  Future<Finca?> obtenerFinca() async {
    final filas = await db.query('finca', limit: 1);
    if (filas.isEmpty) return null;
    return Finca.fromMap(filas.first);
  }

  @override
  Future<void> guardarFinca(Finca finca) async {
    await db.insert(
      'finca',
      finca.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  @override
  Future<List<Actividad>> listarActividades({required int pagina}) {
    throw UnimplementedError('Se implementa en la Tarea 7');
  }

  @override
  Future<void> agregarActividad(Actividad actividad) {
    throw UnimplementedError('Se implementa en la Tarea 7');
  }

  @override
  Future<void> actualizarActividad(Actividad actividad) {
    throw UnimplementedError('Se implementa en la Tarea 8');
  }

  @override
  Future<void> eliminarActividad(String id) {
    throw UnimplementedError('Se implementa en la Tarea 8');
  }

  @override
  Future<double> calcularInversionTotal() {
    throw UnimplementedError('Se implementa en la Tarea 7');
  }
}
