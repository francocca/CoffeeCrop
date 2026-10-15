import 'package:coffecrop/data/exceptions/finca_exceptions.dart';
import 'package:coffecrop/data/repositories/finca_repository.dart';
import 'package:coffecrop/models/actividad.dart';
import 'package:coffecrop/models/finca.dart';

/// Repositorio en memoria, sin I/O real — para pruebas de widgets.
class FakeFincaRepository implements FincaRepository {
  Finca? finca;
  final List<Actividad> actividades = [];

  FakeFincaRepository({this.finca});

  @override
  Future<Finca?> obtenerFinca() async => finca;

  @override
  Future<void> guardarFinca(Finca nueva) async => finca = nueva;

  @override
  Future<List<Actividad>> listarActividades({required int pagina}) async {
    final ordenadas = [...actividades]..sort((a, b) => b.fecha.compareTo(a.fecha));
    return ordenadas.skip(pagina * 20).take(20).toList();
  }

  @override
  Future<void> agregarActividad(Actividad actividad) async {
    if (finca == null) throw const NoFincaException();
    actividades.add(actividad);
  }

  @override
  Future<void> actualizarActividad(Actividad actividad) async {
    final indice = actividades.indexWhere((a) => a.id == actividad.id);
    if (indice != -1) actividades[indice] = actividad;
  }

  @override
  Future<void> eliminarActividad(String id) async {
    actividades.removeWhere((a) => a.id == id);
  }

  @override
  Future<double> calcularInversionTotal() async =>
      actividades.fold<double>(0, (suma, a) => suma + a.monto);
}
