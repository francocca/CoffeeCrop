import 'package:flutter/material.dart';

import '../data/repositories/finca_repository.dart';
import '../models/finca.dart';
import '../theme/app_colors.dart';
import '../widgets/actividades_card.dart';
import '../widgets/finca_card.dart';
import 'finca_form_screen.dart';

class HomeScreen extends StatefulWidget {
  final FincaRepository repository;

  const HomeScreen({super.key, required this.repository});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Finca? _finca;
  double _inversionTotal = 0;
  List<ActividadFinca> _actividadesRecientes = [];
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    _cargarDatos();
  }

  Future<void> _cargarDatos() async {
    setState(() => _cargando = true);

    final finca = await widget.repository.obtenerFinca();
    if (finca == null) {
      setState(() {
        _finca = null;
        _cargando = false;
      });
      return;
    }

    final inversionTotal = await widget.repository.calcularInversionTotal();
    final actividades = await widget.repository.listarActividades(pagina: 0);

    setState(() {
      _finca = finca;
      _inversionTotal = inversionTotal;
      _actividadesRecientes = actividades.take(4).map((actividad) {
        final diasAtras = DateTime.now().difference(actividad.fecha).inDays;
        return ActividadFinca(
          nombre: actividad.nombre,
          diasAtras: diasAtras,
          monto: actividad.monto,
        );
      }).toList();
      _cargando = false;
    });
  }

  Future<void> _irACrearFinca() async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => FincaFormScreen(repository: widget.repository)),
    );
    _cargarDatos();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: _cargando
            ? const Center(child: CircularProgressIndicator())
            : _finca == null
                ? _EstadoVacio(onCrear: _irACrearFinca)
                : ListView(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Finca - Resumen',
                            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.divider),
                            ),
                            child: const Icon(Icons.more_vert, size: 20),
                          ),
                        ],
                      ),
                      const SizedBox(height: 18),
                      FincaCard(
                        nombre: _finca!.nombre,
                        numeroPlantas: _finca!.numeroPlantas,
                        inversionTotal: _inversionTotal,
                      ),
                      const SizedBox(height: 16),
                      ActividadesCard(actividades: _actividadesRecientes),
                    ],
                  ),
      ),
    );
  }
}

class _EstadoVacio extends StatelessWidget {
  final VoidCallback onCrear;

  const _EstadoVacio({required this.onCrear});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.eco_outlined, size: 56, color: AppColors.textSecondary),
            const SizedBox(height: 16),
            const Text(
              'Todavía no registraste tu finca',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            const Text(
              'Creá tu finca para empezar a llevar el control de tus actividades e inversión.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: onCrear,
              style: FilledButton.styleFrom(backgroundColor: AppColors.primary),
              child: const Text('Registrar mi finca'),
            ),
          ],
        ),
      ),
    );
  }
}
