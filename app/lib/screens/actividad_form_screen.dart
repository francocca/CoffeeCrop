import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../data/exceptions/finca_exceptions.dart';
import '../data/repositories/finca_repository.dart';
import '../models/actividad.dart';
import '../models/finca.dart';
import '../theme/app_colors.dart';
import 'finca_form_screen.dart';

/// Formulario para registrar o editar una actividad — US-003 y US-005.
class ActividadFormScreen extends StatefulWidget {
  final FincaRepository repository;
  final Actividad? actividadExistente;

  const ActividadFormScreen({
    super.key,
    required this.repository,
    this.actividadExistente,
  });

  @override
  State<ActividadFormScreen> createState() => _ActividadFormScreenState();
}

class _ActividadFormScreenState extends State<ActividadFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombreController;
  late final TextEditingController _montoController;
  late DateTime _fecha;

  Finca? _finca;
  bool _cargando = true;
  bool _guardando = false;
  String? _errorGeneral;

  bool get _esEdicion => widget.actividadExistente != null;

  @override
  void initState() {
    super.initState();
    final existente = widget.actividadExistente;
    _nombreController = TextEditingController(text: existente?.nombre ?? '');
    _montoController = TextEditingController(
      text: existente == null ? '' : _formatearMonto(existente.monto),
    );
    _fecha = existente?.fecha ?? DateTime.now();
    _cargarFinca();
  }

  @override
  void dispose() {
    _nombreController.dispose();
    _montoController.dispose();
    super.dispose();
  }

  Future<void> _cargarFinca() async {
    final finca = await widget.repository.obtenerFinca();
    if (!mounted) return;
    setState(() {
      _finca = finca;
      _cargando = false;
    });
  }

  Future<void> _irACrearFinca() async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => FincaFormScreen(repository: widget.repository)),
    );
    if (!mounted) return;
    setState(() => _cargando = true);
    await _cargarFinca();
  }

  Future<void> _elegirFecha() async {
    final hoy = DateTime.now();
    final elegida = await showDatePicker(
      context: context,
      initialDate: _fecha.isAfter(hoy) ? hoy : _fecha,
      firstDate: DateTime(2000),
      lastDate: hoy,
    );
    if (elegida != null) setState(() => _fecha = elegida);
  }

  Future<void> _guardar() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _guardando = true;
      _errorGeneral = null;
    });

    try {
      final existente = widget.actividadExistente;
      final actividad = Actividad(
        id: existente?.id ?? const Uuid().v4(),
        fincaId: existente?.fincaId ?? _finca!.id,
        nombre: _nombreController.text.trim(),
        monto: _parsearMonto(_montoController.text)!,
        fecha: _fecha,
        fechaCreacion: existente?.fechaCreacion ?? DateTime.now(),
      );
      if (_esEdicion) {
        await widget.repository.actualizarActividad(actividad);
      } else {
        await widget.repository.agregarActividad(actividad);
      }
      if (mounted) Navigator.of(context).pop(true);
    } on InvalidActivityDataException catch (e) {
      setState(() => _errorGeneral = e.message);
    } on NoFincaException catch (e) {
      setState(() => _errorGeneral = e.message);
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      appBar: AppBar(
        title: Text(_esEdicion ? 'Editar actividad' : 'Registrar actividad'),
        backgroundColor: AppColors.scaffoldBackground,
        elevation: 0,
      ),
      body: SafeArea(
        child: _cargando
            ? const Center(child: CircularProgressIndicator())
            : _finca == null && !_esEdicion
                ? _SinFinca(onCrearFinca: _irACrearFinca)
                : _buildFormulario(),
      ),
    );
  }

  Widget _buildFormulario() {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (_errorGeneral != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.expense.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(_errorGeneral!, style: const TextStyle(color: AppColors.expense)),
            ),
            const SizedBox(height: 16),
          ],
          TextFormField(
            controller: _nombreController,
            decoration: const InputDecoration(
              labelText: 'Actividad o compra (ej. fungicida, rastrillo, pago de obreros)',
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              final texto = value?.trim() ?? '';
              if (texto.isEmpty) return 'El nombre es obligatorio.';
              if (texto.length > 100) return 'Máximo 100 caracteres.';
              return null;
            },
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _montoController,
            decoration: const InputDecoration(
              labelText: 'Monto (COP)',
              prefixText: '\$ ',
              border: OutlineInputBorder(),
            ),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            validator: (value) {
              final monto = _parsearMonto(value ?? '');
              if (monto == null) return 'Ingresá un monto válido.';
              if (monto < 0) return 'El monto no puede ser negativo.';
              return null;
            },
          ),
          const SizedBox(height: 16),
          InkWell(
            onTap: _elegirFecha,
            child: InputDecorator(
              decoration: const InputDecoration(
                labelText: 'Fecha',
                border: OutlineInputBorder(),
                suffixIcon: Icon(Icons.calendar_today, size: 20),
              ),
              child: Text(_formatearFecha(_fecha)),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _guardando ? null : _guardar,
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            child: _guardando
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  static double? _parsearMonto(String texto) =>
      double.tryParse(texto.trim().replaceAll(',', '.'));

  static String _formatearMonto(double monto) =>
      monto == monto.roundToDouble() ? monto.toStringAsFixed(0) : monto.toString();

  static String _formatearFecha(DateTime fecha) =>
      '${fecha.day.toString().padLeft(2, '0')}/${fecha.month.toString().padLeft(2, '0')}/${fecha.year}';
}

class _SinFinca extends StatelessWidget {
  final VoidCallback onCrearFinca;

  const _SinFinca({required this.onCrearFinca});

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
              'Primero registrá tu finca',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            const Text(
              'Para registrar actividades necesitás tener tu finca creada.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: onCrearFinca,
              style: FilledButton.styleFrom(backgroundColor: AppColors.primary),
              child: const Text('Registrar mi finca'),
            ),
          ],
        ),
      ),
    );
  }
}
