import 'package:sqflite/sqflite.dart';

import '../../models/actividad.dart';
import '../../models/finca.dart';
import '../exceptions/finca_exceptions.dart';
import 'finca_repository.dart';

const _tamanoPagina = 20;

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
  Future<List<Actividad>> listarActividades({required int pagina}) async {
    final filas = await db.query(
      'actividad',
      orderBy: 'fecha DESC',
      limit: _tamanoPagina,
      offset: pagina * _tamanoPagina,
    );
    return filas.map(Actividad.fromMap).toList();
  }

  @override
  Future<void> agregarActividad(Actividad actividad) async {
    final resultado = await db.rawQuery('SELECT COUNT(*) AS total FROM finca');
    final hayFinca = (resultado.first['total'] as int) > 0;
    if (!hayFinca) {
      throw const NoFincaException();
    }
    await db.insert('actividad', actividad.toMap());
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
  Future<double> calcularInversionTotal() async {
    final resultado = await db.rawQuery('SELECT COALESCE(SUM(monto), 0) AS total FROM actividad');
    return (resultado.first['total'] as num).toDouble();
  }
}
