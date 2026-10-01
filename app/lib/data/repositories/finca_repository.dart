import '../../models/actividad.dart';
import '../../models/finca.dart';

/// Contrato de acceso a datos de la finca — ver spec.md §5.
///
/// Las pantallas dependen de esta interfaz, no de una implementación concreta,
/// para no acoplarse al motor de base de datos (sqflite).
abstract class FincaRepository {
  Future<Finca?> obtenerFinca();
  Future<void> guardarFinca(Finca finca);

  /// Paginado: [pagina] empieza en 0, tamaño de página fijo de 20 (ver DEC-004).
  Future<List<Actividad>> listarActividades({required int pagina});

  /// Lanza [NoFincaException] si no hay finca registrada (BR-005).
  Future<void> agregarActividad(Actividad actividad);

  Future<void> actualizarActividad(Actividad actividad);
  Future<void> eliminarActividad(String id);

  Future<double> calcularInversionTotal();
}
