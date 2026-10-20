import 'package:sqflite/sqflite.dart';

import '../../models/actividad.dart';
import '../../models/finca.dart';
import '../exceptions/finca_exceptions.dart';
import 'finca_repository.dart';

/// Implementación de [FincaRepository] con sqflite — ver specs/gestion-finca/plan.md §5 para el
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
      limit: tamanoPaginaActividades,
      offset: pagina * tamanoPaginaActividades,
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
  Future<void> actualizarActividad(Actividad actividad) async {
    await db.update(
      'actividad',
      actividad.toMap(),
      where: 'id = ?',
      whereArgs: [actividad.id],
    );
  }

  @override
  Future<void> eliminarActividad(String id) async {
    await db.delete('actividad', where: 'id = ?', whereArgs: [id]);
  }

  @override
  Future<double> calcularInversionTotal() async {
    final resultado = await db.rawQuery('SELECT COALESCE(SUM(monto), 0) AS total FROM actividad');
    return (resultado.first['total'] as num).toDouble();
  }
}
