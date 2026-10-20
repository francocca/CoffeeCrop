import '../../models/actividad.dart';
import '../../models/finca.dart';

/// Tamaño fijo de página de [FincaRepository.listarActividades] (DEC-004).
const tamanoPaginaActividades = 20;

/// Contrato de acceso a datos de la finca — ver specs/gestion-finca/spec.md §5.
///
/// Las pantallas dependen de esta interfaz, no de una implementación concreta,
/// para no acoplarse al motor de base de datos (sqflite).
abstract class FincaRepository {
  Future<Finca?> obtenerFinca();
  Future<void> guardarFinca(Finca finca);

  /// Paginado: [pagina] empieza en 0, de a [tamanoPaginaActividades] (ver DEC-004).
  Future<List<Actividad>> listarActividades({required int pagina});

  /// Lanza [NoFincaException] si no hay finca registrada (BR-005).
  Future<void> agregarActividad(Actividad actividad);

  Future<void> actualizarActividad(Actividad actividad);
  Future<void> eliminarActividad(String id);

  Future<double> calcularInversionTotal();
}
