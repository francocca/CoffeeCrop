import 'package:flutter/material.dart';

import '../data/repositories/finca_repository.dart';
import '../models/actividad.dart';
import '../theme/app_colors.dart';
import '../utils/formatters.dart';
import 'actividad_form_screen.dart';

/// Listado completo y paginado de actividades — US-004 y US-005.
class ActividadesListScreen extends StatefulWidget {
  final FincaRepository repository;

  const ActividadesListScreen({super.key, required this.repository});

  @override
  State<ActividadesListScreen> createState() => _ActividadesListScreenState();
}

class _ActividadesListScreenState extends State<ActividadesListScreen> {
  final _scrollController = ScrollController();
  List<Actividad> _actividades = [];
  bool _cargando = true;
  bool _cargandoMas = false;

  // Hay más páginas solo si la última página cargada vino completa (DEC-004).
  bool get _hayMas =>
      _actividades.isNotEmpty && _actividades.length % tamanoPaginaActividades == 0;
  int get _ultimaPagina =>
      _actividades.isEmpty ? 0 : (_actividades.length - 1) ~/ tamanoPaginaActividades;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_alDesplazar);
    _cargarInicial();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _alDesplazar() {
    final posicion = _scrollController.position;
    if (posicion.pixels >= posicion.maxScrollExtent - 200) _cargarMas();
  }

  Future<void> _cargarInicial() async {
    final primera = await widget.repository.listarActividades(pagina: 0);
    if (!mounted) return;
    setState(() {
      _actividades = primera;
      _cargando = false;
    });
  }

  Future<void> _cargarMas() async {
    if (_cargando || _cargandoMas || !_hayMas) return;
    setState(() => _cargandoMas = true);
    final siguiente = await widget.repository.listarActividades(pagina: _ultimaPagina + 1);
    if (!mounted) return;
    setState(() {
      _actividades = [..._actividades, ...siguiente];
      _cargandoMas = false;
    });
  }

  /// Vuelve a pedir todas las páginas ya cargadas, para conservar la posición
  /// de scroll sin saltarse ni repetir filas tras editar o eliminar.
  Future<void> _recargar() async {
    final paginas = _ultimaPagina;
    final recargadas = <Actividad>[];
    for (var pagina = 0; pagina <= paginas; pagina++) {
      recargadas.addAll(await widget.repository.listarActividades(pagina: pagina));
    }
    if (!mounted) return;
    setState(() => _actividades = recargadas);
  }

  Future<void> _editar(Actividad actividad) async {
    final cambio = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => ActividadFormScreen(
          repository: widget.repository,
          actividadExistente: actividad,
        ),
      ),
    );
    if (cambio == true) await _recargar();
  }

  Future<void> _eliminar(Actividad actividad) async {
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('¿Eliminar actividad?'),
        content: Text('Se eliminará "${actividad.nombre}" y la inversión total se recalculará.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: AppColors.expense),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmado != true) return;
    await widget.repository.eliminarActividad(actividad.id);
    await _recargar();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      appBar: AppBar(
        title: const Text('Actividades'),
        backgroundColor: AppColors.scaffoldBackground,
        elevation: 0,
      ),
      body: SafeArea(
        child: _cargando
            ? const Center(child: CircularProgressIndicator())
            : _actividades.isEmpty
                ? const _EstadoVacio()
                : ListView.separated(
                    controller: _scrollController,
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                    itemCount: _actividades.length + (_cargandoMas ? 1 : 0),
                    separatorBuilder: (_, _) => const Divider(height: 1, color: AppColors.divider),
                    itemBuilder: (context, indice) {
                      if (indice >= _actividades.length) {
                        return const Padding(
                          padding: EdgeInsets.all(16),
                          child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
                        );
                      }
                      final actividad = _actividades[indice];
                      return _ActividadFila(
                        actividad: actividad,
                        onTap: () => _editar(actividad),
                        onEliminar: () => _eliminar(actividad),
                      );
                    },
                  ),
      ),
    );
  }
}

class _ActividadFila extends StatelessWidget {
  final Actividad actividad;
  final VoidCallback onTap;
  final VoidCallback onEliminar;

  const _ActividadFila({
    required this.actividad,
    required this.onTap,
    required this.onEliminar,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.agriculture, color: AppColors.primary, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(actividad.nombre, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  Text(
                    formatearHace(actividad.fecha),
                    style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            Text(
              formatCOP(actividad.monto),
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
            ),
            IconButton(
              onPressed: onEliminar,
              tooltip: 'Eliminar',
              icon: const Icon(Icons.delete_outline, color: AppColors.textSecondary, size: 22),
            ),
          ],
        ),
      ),
    );
  }
}

class _EstadoVacio extends StatelessWidget {
  const _EstadoVacio();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.agriculture_outlined, size: 56, color: AppColors.textSecondary),
            SizedBox(height: 16),
            Text(
              'Todavía no tenés actividades registradas',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            SizedBox(height: 8),
            Text(
              'Cuando registres compras o trabajos de tu finca, van a aparecer acá.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}
